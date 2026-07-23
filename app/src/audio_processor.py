"""Audio processing utilities for compressing audio before API submission."""

import io
import wave
from pydub import AudioSegment


# Gemini downsamples to 16kHz mono
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1

# Long audio handling: 16kHz mono 16-bit WAV grows ~1.9MB per minute, and
# base64 encoding adds another 33% on top. Past a few minutes the request
# payload approaches provider size limits (Gemini inline data is capped at
# ~20MB per request). Audio longer than this threshold is uploaded as MP3
# instead — audio tokens are billed per second, so compression doesn't
# change transcription cost.
MAX_INLINE_WAV_SECONDS = 360.0
LONG_AUDIO_MP3_BITRATE = "32k"
# Hard ceiling on the encoded upload payload (~3 hours of speech at 32kbps)
MAX_UPLOAD_AUDIO_BYTES = 40 * 1024 * 1024

# AGC settings
# Target peak level in dBFS (decibels relative to full scale)
# -3dB leaves headroom while ensuring good signal level
AGC_TARGET_PEAK_DBFS = -3.0
# Minimum peak level to trigger AGC (avoid amplifying noise in silent recordings)
AGC_MIN_PEAK_DBFS = -40.0
# Maximum gain to apply (prevent over-amplification of very quiet audio)
AGC_MAX_GAIN_DB = 20.0


def apply_agc(audio: AudioSegment) -> tuple[AudioSegment, dict]:
    """
    Apply automatic gain control to normalize audio levels.

    This ensures consistent audio levels for optimal transcription accuracy,
    regardless of microphone gain settings or distance from the mic.

    Args:
        audio: AudioSegment to process

    Returns:
        Tuple of (processed AudioSegment, stats dict with gain info)
    """
    stats = {
        "original_peak_dbfs": audio.max_dBFS,
        "gain_applied_db": 0.0,
        "agc_applied": False,
    }

    current_peak = audio.max_dBFS

    # Don't process if audio is essentially silent (would just amplify noise)
    if current_peak < AGC_MIN_PEAK_DBFS:
        stats["reason"] = "audio_too_quiet"
        return audio, stats

    # Calculate gain needed to reach target level
    gain_needed = AGC_TARGET_PEAK_DBFS - current_peak

    # Don't attenuate (negative gain) - only boost quiet audio
    # and don't boost already loud audio
    if gain_needed <= 0:
        stats["reason"] = "audio_loud_enough"
        return audio, stats

    # Cap the maximum gain to prevent over-amplification
    gain_to_apply = min(gain_needed, AGC_MAX_GAIN_DB)

    # Apply the gain
    audio = audio + gain_to_apply

    stats["gain_applied_db"] = round(gain_to_apply, 1)
    stats["final_peak_dbfs"] = audio.max_dBFS
    stats["agc_applied"] = True

    return audio, stats


def compress_audio_for_api(audio_data: bytes, apply_gain_control: bool = True) -> bytes:
    """
    Compress audio to optimal format for API submission.

    Processes audio through:
    1. Automatic Gain Control (AGC) - normalizes levels for consistent transcription
    2. Conversion to mono
    3. Resampling to 16kHz (Gemini's internal format)

    Args:
        audio_data: Raw WAV audio bytes
        apply_gain_control: Whether to apply AGC (default True)

    Returns:
        Compressed WAV audio bytes at 16kHz mono with normalized levels
    """
    # Load the audio from bytes
    audio = AudioSegment.from_wav(io.BytesIO(audio_data))

    # Apply AGC first (before any format conversion)
    if apply_gain_control:
        audio, agc_stats = apply_agc(audio)
        if agc_stats["agc_applied"]:
            print(f"AGC: Applied {agc_stats['gain_applied_db']}dB gain "
                  f"(peak: {agc_stats['original_peak_dbfs']:.1f}dB → {agc_stats['final_peak_dbfs']:.1f}dB)")

    # Convert to mono if stereo
    if audio.channels > 1:
        audio = audio.set_channels(TARGET_CHANNELS)

    # Resample to 16kHz if needed
    if audio.frame_rate != TARGET_SAMPLE_RATE:
        audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)

    # Export to WAV bytes
    output = io.BytesIO()
    audio.export(output, format="wav")
    compressed_data = output.getvalue()

    return compressed_data


def prepare_audio_for_api(
    audio_data: bytes,
    vad_enabled: bool = False,
    apply_gain_control: bool = True,
) -> tuple[bytes, str, float | None, float | None]:
    """Fused audio pipeline: VAD + AGC + compression in a single pass.

    When VAD is enabled, the naive sequential approach loads and converts
    audio twice (once for VAD, once for compression). This function does
    everything in a single pass: load once, convert to 16kHz mono once,
    run VAD, apply AGC, and export once. Saves ~100-200ms per transcription.

    When VAD is disabled, this is equivalent to compress_audio_for_api()
    but also returns duration info.

    Audio longer than MAX_INLINE_WAV_SECONDS is exported as MP3 instead of
    WAV to keep the base64 request payload under provider size limits.

    Args:
        audio_data: Raw WAV audio bytes from recorder
        vad_enabled: Whether to apply Voice Activity Detection
        apply_gain_control: Whether to apply Automatic Gain Control

    Returns:
        Tuple of (audio_bytes, audio_format, original_duration_secs, vad_duration_secs).
        audio_format is "wav" or "mp3". VAD duration is None if VAD is not
        enabled/available.
    """
    from .vad_processor import get_vad, is_vad_available

    # Load audio ONCE
    audio = AudioSegment.from_wav(io.BytesIO(audio_data))
    original_duration = len(audio) / 1000.0
    vad_duration = None

    # Convert to 16kHz mono ONCE (needed by both VAD and API)
    if audio.channels > 1:
        audio = audio.set_channels(TARGET_CHANNELS)
    if audio.frame_rate != TARGET_SAMPLE_RATE:
        audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)

    # Apply VAD directly on the already-converted AudioSegment
    if vad_enabled and is_vad_available():
        vad = get_vad()
        # Use internal method since audio is already 16kHz mono
        speeches = vad._get_speech_timestamps_from_audio(audio)

        if speeches:
            combined = AudioSegment.empty()
            for speech in speeches:
                start_ms = int(speech['start'] * 1000 / TARGET_SAMPLE_RATE)
                end_ms = int(speech['end'] * 1000 / TARGET_SAMPLE_RATE)
                combined += audio[start_ms:end_ms]

            if len(combined) > 0:
                vad_duration = len(combined) / 1000.0
                audio = combined
            else:
                vad_duration = original_duration
        else:
            vad_duration = original_duration

    # Apply AGC
    if apply_gain_control:
        audio, agc_stats = apply_agc(audio)
        if agc_stats["agc_applied"]:
            print(f"AGC: Applied {agc_stats['gain_applied_db']}dB gain "
                  f"(peak: {agc_stats['original_peak_dbfs']:.1f}dB → {agc_stats['final_peak_dbfs']:.1f}dB)")

    # Export ONCE — WAV for short audio, MP3 for long audio
    final_duration = len(audio) / 1000.0
    output = io.BytesIO()
    if final_duration > MAX_INLINE_WAV_SECONDS:
        audio.export(output, format="mp3", bitrate=LONG_AUDIO_MP3_BITRATE)
        audio_format = "mp3"
    else:
        audio.export(output, format="wav")
        audio_format = "wav"

    payload = output.getvalue()
    if len(payload) > MAX_UPLOAD_AUDIO_BYTES:
        raise ValueError(
            f"Audio is too long to upload ({final_duration / 60:.0f} minutes, "
            f"{len(payload) / 1024 / 1024:.0f}MB encoded). "
            f"Split the recording into shorter files."
        )

    return payload, audio_format, original_duration, vad_duration


def get_audio_info(audio_data: bytes) -> dict:
    """
    Get information about audio data.

    Args:
        audio_data: WAV audio bytes

    Returns:
        Dictionary with audio properties
    """
    with wave.open(io.BytesIO(audio_data), 'rb') as wf:
        return {
            "channels": wf.getnchannels(),
            "sample_rate": wf.getframerate(),
            "sample_width": wf.getsampwidth(),
            "frames": wf.getnframes(),
            "duration_seconds": wf.getnframes() / wf.getframerate(),
            "size_bytes": len(audio_data),
        }


def estimate_compressed_size(duration_seconds: float) -> int:
    """
    Estimate the compressed file size for a given duration.

    At 16kHz, 16-bit mono, audio is approximately 32KB per second.

    Args:
        duration_seconds: Duration of the recording

    Returns:
        Estimated size in bytes
    """
    # 16kHz * 2 bytes (16-bit) * 1 channel = 32,000 bytes/second
    # Plus ~44 bytes WAV header
    return int(duration_seconds * 32000) + 44


def combine_wav_segments(segments: list[bytes]) -> bytes:
    """
    Combine multiple WAV audio segments into a single WAV file.

    Args:
        segments: List of WAV audio bytes to combine

    Returns:
        Combined WAV audio bytes
    """
    if not segments:
        raise ValueError("No audio segments to combine")

    if len(segments) == 1:
        return segments[0]

    # Load first segment as base
    combined = AudioSegment.from_wav(io.BytesIO(segments[0]))

    # Append remaining segments
    for segment in segments[1:]:
        audio = AudioSegment.from_wav(io.BytesIO(segment))
        combined += audio

    # Export to WAV bytes
    output = io.BytesIO()
    combined.export(output, format="wav")
    return output.getvalue()


def archive_audio(audio_data: bytes, output_path: str) -> bool:
    """
    Archive audio to Opus format for efficient storage.

    Opus at ~24kbps is excellent for speech archival - about 90% smaller
    than uncompressed WAV while remaining very listenable.

    Args:
        audio_data: Raw WAV audio bytes
        output_path: Path to save the Opus file

    Returns:
        True if successful, False otherwise
    """
    try:
        audio = AudioSegment.from_wav(io.BytesIO(audio_data))

        # Ensure mono 16kHz for consistent archival
        if audio.channels > 1:
            audio = audio.set_channels(1)
        if audio.frame_rate != TARGET_SAMPLE_RATE:
            audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)

        # Export to Opus with speech-optimized bitrate
        audio.export(
            output_path,
            format="opus",
            bitrate="24k",
            parameters=["-application", "voip"]  # Optimize for speech
        )
        return True
    except Exception as e:
        print(f"Error archiving audio: {e}")
        return False

"""Audio processing utilities for compressing audio before API submission."""

import io
import wave
from pydub import AudioSegment


# Gemini downsamples to 16kHz mono
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1


def compress_audio_for_api(audio_data: bytes) -> bytes:
    """
    Compress audio to optimal format for API submission.

    Gemini downsamples audio to 16kHz mono, so we do this locally
    to reduce upload size and ensure consistent results regardless
    of recording length (up to ~5 minutes).

    Args:
        audio_data: Raw WAV audio bytes

    Returns:
        Compressed WAV audio bytes at 16kHz mono
    """
    # Load the audio from bytes
    audio = AudioSegment.from_wav(io.BytesIO(audio_data))

    # Get original properties for logging/debugging
    original_rate = audio.frame_rate
    original_channels = audio.channels
    original_size = len(audio_data)

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

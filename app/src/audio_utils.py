"""Shared audio utilities for Voice Notepad V3.

Contains common audio playback functions used by both beep feedback
and TTS announcements.
"""

import logging

# Try to use simpleaudio for playback (non-blocking, can load WAV files)
try:
    import simpleaudio as sa
    HAS_SIMPLEAUDIO = True
except ImportError:
    HAS_SIMPLEAUDIO = False

# Fallback to PyAudio if available
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

logger = logging.getLogger(__name__)


def has_audio_backend() -> bool:
    """Check if any audio playback backend is available."""
    return HAS_SIMPLEAUDIO or HAS_PYAUDIO


def play_raw_audio(audio_data: bytes, sample_rate: int = 44100, channels: int = 1, sample_width: int = 2) -> bool:
    """Play raw PCM audio data.

    Args:
        audio_data: Raw PCM audio bytes
        sample_rate: Sample rate in Hz (default 44100)
        channels: Number of audio channels (default 1 for mono)
        sample_width: Bytes per sample (default 2 for 16-bit)

    Returns:
        True if audio was played successfully, False otherwise
    """
    if HAS_SIMPLEAUDIO:
        try:
            wave_obj = sa.WaveObject(audio_data, channels, sample_width, sample_rate)
            play_obj = wave_obj.play()
            play_obj.wait_done()
            return True
        except Exception as e:
            logger.debug(f"simpleaudio playback failed: {e}")

    if HAS_PYAUDIO:
        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16 if sample_width == 2 else pyaudio.paInt8,
                channels=channels,
                rate=sample_rate,
                output=True
            )
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            return True
        except Exception as e:
            logger.debug(f"PyAudio playback failed: {e}")

    return False


def play_wav_file(filepath: str) -> bool:
    """Play a WAV file.

    Args:
        filepath: Path to the WAV file

    Returns:
        True if audio was played successfully, False otherwise
    """
    if HAS_SIMPLEAUDIO:
        try:
            wave_obj = sa.WaveObject.from_wave_file(filepath)
            play_obj = wave_obj.play()
            play_obj.wait_done()
            return True
        except Exception as e:
            logger.debug(f"simpleaudio WAV playback failed: {e}")

    if HAS_PYAUDIO:
        try:
            import wave
            with wave.open(filepath, 'rb') as wf:
                p = pyaudio.PyAudio()
                stream = p.open(
                    format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                data = wf.readframes(1024)
                while data:
                    stream.write(data)
                    data = wf.readframes(1024)
                stream.stop_stream()
                stream.close()
                p.terminate()
            return True
        except Exception as e:
            logger.debug(f"PyAudio WAV playback failed: {e}")

    return False

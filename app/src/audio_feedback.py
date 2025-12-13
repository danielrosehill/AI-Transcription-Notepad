"""Audio feedback (beeps) for Voice Notepad V3.

Generates simple beep tones for recording start/stop feedback.
"""

import math
import struct
import threading
from typing import Optional

# Try to use simpleaudio for playback (non-blocking)
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


def generate_beep(frequency: int = 880, duration_ms: int = 100, volume: float = 0.3, sample_rate: int = 44100) -> bytes:
    """Generate a simple sine wave beep.

    Args:
        frequency: Tone frequency in Hz (default 880 = A5)
        duration_ms: Duration in milliseconds
        volume: Volume from 0.0 to 1.0
        sample_rate: Audio sample rate

    Returns:
        Raw audio data as bytes (16-bit mono PCM)
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []

    for i in range(num_samples):
        # Generate sine wave
        t = i / sample_rate
        value = math.sin(2 * math.pi * frequency * t)

        # Apply simple envelope to avoid clicks (fade in/out)
        fade_samples = int(sample_rate * 0.01)  # 10ms fade
        if i < fade_samples:
            value *= i / fade_samples
        elif i > num_samples - fade_samples:
            value *= (num_samples - i) / fade_samples

        # Scale to 16-bit and apply volume
        sample = int(value * volume * 32767)
        samples.append(struct.pack('<h', sample))

    return b''.join(samples)


def generate_double_beep(freq1: int = 880, freq2: int = 1100, duration_ms: int = 80, gap_ms: int = 50, volume: float = 0.3) -> bytes:
    """Generate a double beep (two tones with a gap).

    Args:
        freq1: First tone frequency
        freq2: Second tone frequency
        duration_ms: Duration of each tone
        gap_ms: Gap between tones
        volume: Volume from 0.0 to 1.0

    Returns:
        Raw audio data as bytes
    """
    sample_rate = 44100
    beep1 = generate_beep(freq1, duration_ms, volume, sample_rate)
    gap = b'\x00\x00' * int(sample_rate * gap_ms / 1000)  # Silence
    beep2 = generate_beep(freq2, duration_ms, volume, sample_rate)
    return beep1 + gap + beep2


class AudioFeedback:
    """Manages audio feedback sounds."""

    def __init__(self):
        self._enabled = True
        # Pre-generate beep sounds
        self._start_beep = generate_beep(frequency=880, duration_ms=100, volume=0.25)  # A5, short
        self._stop_beep = generate_double_beep(freq1=880, freq2=660, duration_ms=80, volume=0.25)  # A5 down to E5

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def play_start_beep(self):
        """Play the recording start beep."""
        if self._enabled:
            self._play_async(self._start_beep)

    def play_stop_beep(self):
        """Play the recording stop beep."""
        if self._enabled:
            self._play_async(self._stop_beep)

    def _play_async(self, audio_data: bytes):
        """Play audio in a background thread to avoid blocking."""
        thread = threading.Thread(target=self._play_audio, args=(audio_data,), daemon=True)
        thread.start()

    def _play_audio(self, audio_data: bytes):
        """Play raw audio data."""
        sample_rate = 44100

        if HAS_SIMPLEAUDIO:
            try:
                # simpleaudio is the cleanest option
                wave_obj = sa.WaveObject(audio_data, 1, 2, sample_rate)
                play_obj = wave_obj.play()
                play_obj.wait_done()
                return
            except Exception:
                pass

        if HAS_PYAUDIO:
            try:
                p = pyaudio.PyAudio()
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True
                )
                stream.write(audio_data)
                stream.stop_stream()
                stream.close()
                p.terminate()
                return
            except Exception:
                pass

        # If no audio backend available, silently fail


# Global instance
_feedback: Optional[AudioFeedback] = None


def get_feedback() -> AudioFeedback:
    """Get the global AudioFeedback instance."""
    global _feedback
    if _feedback is None:
        _feedback = AudioFeedback()
    return _feedback

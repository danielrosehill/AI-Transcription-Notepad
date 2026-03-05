"""Audio feedback (PTT walkie-talkie sounds) for Voice Notepad V3.

Generates push-to-talk radio style click-chirps for recording start/stop feedback.
Uses white noise bursts mixed with tones for percussive, radio-like character.
Also loads WAV sound effects from assets/sfx/ for PTT send and completion ding.
"""

import math
import os
import random
import struct
import threading
import wave
from pathlib import Path
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

SAMPLE_RATE = 44100

# Path to bundled sound effects
_SFX_DIR = Path(__file__).parent.parent / "assets" / "sfx"


def _load_wav_pcm(filename: str) -> bytes:
    """Load a WAV file from assets/sfx/ and return raw PCM bytes (16-bit mono)."""
    path = _SFX_DIR / filename
    if not path.exists():
        return b""
    with wave.open(str(path), "rb") as wf:
        return wf.readframes(wf.getnframes())


def _white_noise(num_samples: int, volume: float, rng: random.Random) -> list[float]:
    """Generate white noise samples."""
    return [rng.uniform(-1.0, 1.0) * volume for _ in range(num_samples)]


def _sine(num_samples: int, frequency: float, volume: float, sample_rate: int = SAMPLE_RATE) -> list[float]:
    """Generate sine wave samples."""
    return [math.sin(2 * math.pi * frequency * i / sample_rate) * volume for i in range(num_samples)]


def _apply_envelope(samples: list[float], attack_ms: float, decay_ms: float, sample_rate: int = SAMPLE_RATE) -> list[float]:
    """Apply attack/decay envelope to samples. No sustain -- percussive shape."""
    n = len(samples)
    attack_samples = int(sample_rate * attack_ms / 1000)
    decay_samples = int(sample_rate * decay_ms / 1000)
    result = list(samples)
    for i in range(n):
        if i < attack_samples:
            env = i / max(attack_samples, 1)
        elif i >= n - decay_samples:
            env = (n - i) / max(decay_samples, 1)
        else:
            env = 1.0
        result[i] *= env
    return result


def _mix(*layers: list[float]) -> list[float]:
    """Mix multiple sample layers by summing them. All layers must be same length."""
    length = max(len(l) for l in layers)
    result = [0.0] * length
    for layer in layers:
        for i in range(len(layer)):
            result[i] += layer[i]
    return result


def _to_bytes(samples: list[float], master_volume: float = 1.0) -> bytes:
    """Convert float samples to 16-bit PCM bytes, with clipping."""
    out = []
    for s in samples:
        val = int(s * master_volume * 32767)
        val = max(-32767, min(32767, val))
        out.append(struct.pack('<h', val))
    return b''.join(out)


def _silence_bytes(duration_ms: float, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Generate silence as bytes."""
    return b'\x00\x00' * int(sample_rate * duration_ms / 1000)


def generate_beep(frequency: float = 880, duration_ms: int = 60, volume: float = 0.18) -> bytes:
    """Load the PTT send sound effect for recording start indicator.

    Uses the bundled ptt-send.wav asset. Falls back to generated PTT chirp
    if the WAV file is not available. Parameters kept for API compatibility.
    """
    data = _load_wav_pcm("ptt-send.wav")
    if data:
        return data
    return generate_ptt_click_chirp(volume=volume)


def generate_ptt_click_chirp(volume: float = 0.15) -> bytes:
    """PTT key-up: short rising click-chirp like keying a radio.

    Quick noise burst attack followed by a brief rising tone sweep.
    Total duration ~60ms.
    """
    rng = random.Random(42)  # Deterministic noise

    # Phase 1: Initial click -- short noise burst (8ms)
    click_len = int(SAMPLE_RATE * 0.008)
    click_noise = _white_noise(click_len, 0.7, rng)
    click_noise = _apply_envelope(click_noise, attack_ms=0.5, decay_ms=3.0)

    # Phase 2: Rising chirp (50ms) -- frequency sweep from 1200 to 2800 Hz
    chirp_len = int(SAMPLE_RATE * 0.050)
    chirp = []
    for i in range(chirp_len):
        t = i / SAMPLE_RATE
        progress = i / chirp_len
        freq = 1200 + (2800 - 1200) * progress
        # Add slight noise texture
        noise_val = rng.uniform(-1.0, 1.0) * 0.15
        tone_val = math.sin(2 * math.pi * freq * t) * 0.6
        chirp.append(tone_val + noise_val)
    chirp = _apply_envelope(chirp, attack_ms=1.0, decay_ms=15.0)

    all_samples = click_noise + chirp
    return _to_bytes(all_samples, master_volume=volume)


def generate_ptt_release(volume: float = 0.15) -> bytes:
    """PTT release: descending click like releasing the transmit button.

    Brief falling tone followed by a noise click tail.
    Total duration ~55ms.
    """
    rng = random.Random(99)

    # Phase 1: Falling chirp (40ms) -- frequency sweep from 2400 to 800 Hz
    chirp_len = int(SAMPLE_RATE * 0.040)
    chirp = []
    for i in range(chirp_len):
        t = i / SAMPLE_RATE
        progress = i / chirp_len
        freq = 2400 - (2400 - 800) * progress
        noise_val = rng.uniform(-1.0, 1.0) * 0.12
        tone_val = math.sin(2 * math.pi * freq * t) * 0.6
        chirp.append(tone_val + noise_val)
    chirp = _apply_envelope(chirp, attack_ms=1.0, decay_ms=12.0)

    # Phase 2: Tail click -- noise burst (15ms)
    tail_len = int(SAMPLE_RATE * 0.015)
    tail = _white_noise(tail_len, 0.5, rng)
    tail = _apply_envelope(tail, attack_ms=0.5, decay_ms=8.0)

    all_samples = chirp + tail
    return _to_bytes(all_samples, master_volume=volume)


def generate_double_click(volume: float = 0.14) -> bytes:
    """Quick double click for clipboard -- two very short percussive noise clicks.

    Two ~12ms noise bursts separated by a ~25ms gap.
    """
    rng = random.Random(77)

    def _single_click():
        click_len = int(SAMPLE_RATE * 0.012)
        # Noise with a slight high-freq tone for sharpness
        noise = _white_noise(click_len, 0.6, rng)
        tone = _sine(click_len, 3000, 0.3)
        mixed = _mix(noise, tone)
        return _apply_envelope(mixed, attack_ms=0.3, decay_ms=6.0)

    click1 = _single_click()
    click2 = _single_click()

    click1_bytes = _to_bytes(click1, master_volume=volume)
    gap = _silence_bytes(25)
    click2_bytes = _to_bytes(click2, master_volume=volume)

    return click1_bytes + gap + click2_bytes


def generate_rising_chirp(volume: float = 0.12) -> bytes:
    """Rising chirp for toggle-on / PTT engage.

    Quick ascending sweep with noise texture. ~45ms.
    """
    rng = random.Random(55)
    chirp_len = int(SAMPLE_RATE * 0.045)
    chirp = []
    for i in range(chirp_len):
        t = i / SAMPLE_RATE
        progress = i / chirp_len
        freq = 1000 + (3200 - 1000) * (progress ** 0.8)  # Slightly curved sweep
        noise_val = rng.uniform(-1.0, 1.0) * 0.10
        tone_val = math.sin(2 * math.pi * freq * t) * 0.55
        chirp.append(tone_val + noise_val)
    chirp = _apply_envelope(chirp, attack_ms=0.5, decay_ms=12.0)
    return _to_bytes(chirp, master_volume=volume)


def generate_falling_chirp(volume: float = 0.12) -> bytes:
    """Falling chirp for toggle-off / PTT disengage.

    Quick descending sweep with noise texture. ~45ms.
    """
    rng = random.Random(66)
    chirp_len = int(SAMPLE_RATE * 0.045)
    chirp = []
    for i in range(chirp_len):
        t = i / SAMPLE_RATE
        progress = i / chirp_len
        freq = 3200 - (3200 - 1000) * (progress ** 0.8)
        noise_val = rng.uniform(-1.0, 1.0) * 0.10
        tone_val = math.sin(2 * math.pi * freq * t) * 0.55
        chirp.append(tone_val + noise_val)
    chirp = _apply_envelope(chirp, attack_ms=0.5, decay_ms=12.0)
    return _to_bytes(chirp, master_volume=volume)


def generate_rising_double_chirp(volume: float = 0.14) -> bytes:
    """Rising double-chirp for append mode.

    Two quick ascending chirps separated by a short gap. ~110ms total.
    """
    rng = random.Random(88)

    def _single_chirp(base_freq: float, top_freq: float):
        chirp_len = int(SAMPLE_RATE * 0.035)
        chirp = []
        for i in range(chirp_len):
            t = i / SAMPLE_RATE
            progress = i / chirp_len
            freq = base_freq + (top_freq - base_freq) * progress
            noise_val = rng.uniform(-1.0, 1.0) * 0.10
            tone_val = math.sin(2 * math.pi * freq * t) * 0.55
            chirp.append(tone_val + noise_val)
        return _apply_envelope(chirp, attack_ms=0.5, decay_ms=10.0)

    chirp1 = _single_chirp(1000, 2200)
    chirp2 = _single_chirp(1400, 3000)

    chirp1_bytes = _to_bytes(chirp1, master_volume=volume)
    gap = _silence_bytes(20)
    chirp2_bytes = _to_bytes(chirp2, master_volume=volume)

    return chirp1_bytes + gap + chirp2_bytes


class AudioFeedback:
    """Manages audio feedback sounds (PTT walkie-talkie style)."""

    def __init__(self):
        self._enabled = True
        # Load WAV sound effects (with generated fallbacks)
        self._start_beep = _load_wav_pcm("ptt-send.wav") or generate_ptt_click_chirp(volume=0.15)
        self._stop_beep = _load_wav_pcm("stop.wav") or generate_ptt_release(volume=0.15)
        self._clipboard_beep = generate_double_click(volume=0.14)
        self._toggle_on_beep = generate_rising_chirp(volume=0.12)
        self._toggle_off_beep = generate_falling_chirp(volume=0.12)
        self._append_beep = generate_rising_double_chirp(volume=0.14)
        self._complete_beep = _load_wav_pcm("ding-complete.wav") or generate_ptt_release(volume=0.15)
        self._pause_beep = _load_wav_pcm("pause.wav") or generate_double_click(volume=0.14)
        self._resume_beep = _load_wav_pcm("resume.wav") or generate_rising_chirp(volume=0.12)
        self._retake_beep = _load_wav_pcm("retake.wav") or generate_falling_chirp(volume=0.12)
        self._transcribe_beep = _load_wav_pcm("transcribe.wav") or generate_rising_chirp(volume=0.12)
        self._clear_beep = _load_wav_pcm("clear.wav") or generate_falling_chirp(volume=0.12)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def play_start_beep(self):
        """Play the recording start sound (PTT key-up click-chirp)."""
        if self._enabled:
            self._play_async(self._start_beep)

    def play_stop_beep(self):
        """Play the recording stop sound (PTT release click)."""
        if self._enabled:
            self._play_async(self._stop_beep)

    def play_clipboard_beep(self):
        """Play the clipboard copy sound (quick double click)."""
        if self._enabled:
            self._play_async(self._clipboard_beep)

    def play_toggle_on_beep(self):
        """Play the toggle-on sound (rising chirp)."""
        if self._enabled:
            self._play_async(self._toggle_on_beep)

    def play_toggle_off_beep(self):
        """Play the toggle-off sound (falling chirp)."""
        if self._enabled:
            self._play_async(self._toggle_off_beep)

    def play_append_beep(self):
        """Play the append mode sound (rising double-chirp)."""
        if self._enabled:
            self._play_async(self._append_beep)

    def play_complete_beep(self):
        """Play the transcription complete sound (ding)."""
        if self._enabled:
            self._play_async(self._complete_beep)

    def play_pause_beep(self):
        """Play the pause sound (double-tap tone)."""
        if self._enabled:
            self._play_async(self._pause_beep)

    def play_resume_beep(self):
        """Play the resume sound (rising two-note)."""
        if self._enabled:
            self._play_async(self._resume_beep)

    def play_retake_beep(self):
        """Play the retake/restart sound (descending two-note)."""
        if self._enabled:
            self._play_async(self._retake_beep)

    def play_transcribe_beep(self):
        """Play the transcribe/send sound."""
        if self._enabled:
            self._play_async(self._transcribe_beep)

    def play_clear_beep(self):
        """Play the clear/delete sound."""
        if self._enabled:
            self._play_async(self._clear_beep)

    def _play_async(self, audio_data: bytes):
        """Play audio in a background thread to avoid blocking."""
        thread = threading.Thread(target=self._play_audio, args=(audio_data,), daemon=True)
        thread.start()

    def _play_audio(self, audio_data: bytes):
        """Play raw audio data."""
        sample_rate = SAMPLE_RATE

        if HAS_SIMPLEAUDIO:
            try:
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
_feedback_lock = threading.Lock()


def get_feedback() -> AudioFeedback:
    """Get the global AudioFeedback instance (thread-safe)."""
    global _feedback
    if _feedback is None:
        with _feedback_lock:
            # Double-check pattern for thread safety
            if _feedback is None:
                _feedback = AudioFeedback()
    return _feedback

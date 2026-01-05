#!/usr/bin/env python3
"""Generate TTS audio assets using Fish Audio API.

Creates voice packs for Voice Notepad accessibility announcements using
character voices from Fish Audio.

Usage:
    ./scripts/generate_fish_tts_assets.py [--voice VOICE_NAME]

    # Generate all voice packs
    ./scripts/generate_fish_tts_assets.py --all

    # Generate specific voice pack
    ./scripts/generate_fish_tts_assets.py --voice herman
    ./scripts/generate_fish_tts_assets.py --voice wizard

Requirements:
    pip install httpx

Environment:
    FISH_API_KEY - Your Fish Audio API key
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)

# Fish Audio voice configurations
VOICES = {
    "herman": {
        "id": "0ca22adaa6e3416eb5ccb6a66bd4bee8",
        "name": "Herman Poppleberry",
        "description": "Talking donkey - expressive, friendly",
    },
    "corn": {
        "id": "9fb5c60632e240b2917e2d87b838a3fe",
        "name": "Cornelius Badonde",
        "description": "Elderly sloth - calm, quirky",
    },
    "venti": {
        "id": "e34c486929524d41b88646b4ac2f382f",
        "name": "Venti",
        "description": "Expressive natural voice",
    },
    "napoleon": {
        "id": "28dbb820ad434187bec6b14f7942e50a",
        "name": "Napoleon Hill",
        "description": "Motivational speaker - authoritative",
    },
    "wizard": {
        "id": "2b5baf5e904d43c785e24dc3fa22f87e",
        "name": "Old Wizard",
        "description": "Mystical elderly wizard",
    },
}

# Announcements to generate (same as Edge TTS version)
ANNOUNCEMENTS = {
    # Recording states
    "recording": "Recording",
    "stopped": "Recording stopped",
    "paused": "Recording paused",
    "resumed": "Recording resumed",
    "discarded": "Recording discarded",
    "appended": "Recording appended",
    "cached": "Cached",
    # Transcription states
    "transcribing": "Transcribing",
    "complete": "Complete",
    "error": "Error",
    # Output modes (transcription result destination)
    "text_in_app": "Text in app",
    "text_on_clipboard": "Text on clipboard",
    "clipboard": "Clipboard",
    "text_injected": "Text injected",
    "injection_failed": "Injection failed",
    # Output mode toggles
    "app_enabled": "App enabled",
    "app_disabled": "App disabled",
    "clipboard_enabled": "Clipboard enabled",
    "clipboard_disabled": "Clipboard disabled",
    "inject_enabled": "Inject enabled",
    "inject_disabled": "Inject disabled",
    # Settings toggles
    "vad_enabled": "Voice activity detection enabled",
    "vad_disabled": "Voice activity detection disabled",
    # Append mode
    "appending": "Appending",
    # Prompt stack changes
    "format_updated": "Format updated",
    "format_inference": "Format inference activated",
    "tone_updated": "Tone updated",
    "style_updated": "Style updated",
    "verbatim_mode": "Verbatim mode selected",
    "general_mode": "General mode selected",
    # Audio feedback mode changes
    "tts_activated": "TTS mode activated",
    "tts_deactivated": "TTS mode deactivated",
    # Settings/config actions
    "default_prompt_configured": "Default prompt configured",
    "copied_to_clipboard": "Copied to clipboard",
    # Legacy (kept for compatibility)
    "copied": "Copied",
    "injected": "Injected",
    "cleared": "Cleared",
}

# Fish Audio API endpoint
FISH_API_URL = "https://api.fish.audio/v1/tts"


def get_api_key() -> str:
    """Get Fish Audio API key from environment or .env file."""
    api_key = os.environ.get("FISH_API_KEY")
    if api_key:
        return api_key

    # Try loading from .env file
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("FISH_API_KEY="):
                    return line.strip().split("=", 1)[1]

    print("Error: FISH_API_KEY not found in environment or .env file")
    sys.exit(1)


def generate_tts(text: str, voice_id: str, api_key: str) -> bytes:
    """Generate TTS audio using Fish Audio API.

    Args:
        text: Text to convert to speech
        voice_id: Fish Audio voice/model ID
        api_key: Fish Audio API key

    Returns:
        MP3 audio bytes
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "reference_id": voice_id,
        "format": "mp3",
        "latency": "normal",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(FISH_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.content


def convert_to_wav(mp3_path: Path, wav_path: Path) -> None:
    """Convert MP3 to WAV (16kHz mono, 16-bit) using ffmpeg."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(mp3_path),
            "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
            str(wav_path)
        ],
        check=True,
        capture_output=True,
    )


def generate_voice_pack(voice_key: str, api_key: str, output_base: Path) -> None:
    """Generate all announcements for a voice pack.

    Args:
        voice_key: Voice identifier (e.g., "herman", "wizard")
        api_key: Fish Audio API key
        output_base: Base directory for TTS assets (app/assets/tts)
    """
    voice_config = VOICES[voice_key]
    voice_id = voice_config["id"]
    voice_name = voice_config["name"]

    output_dir = output_base / voice_key
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Generating voice pack: {voice_name}")
    print(f"Voice ID: {voice_id}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    total = len(ANNOUNCEMENTS)
    for i, (name, text) in enumerate(ANNOUNCEMENTS.items(), 1):
        wav_path = output_dir / f"{name}.wav"

        # Skip if already exists
        if wav_path.exists():
            print(f"[{i}/{total}] Skipping '{name}' (already exists)")
            continue

        print(f"[{i}/{total}] Generating '{text}'...", end=" ", flush=True)

        try:
            # Generate MP3 from Fish Audio
            mp3_data = generate_tts(text, voice_id, api_key)

            # Write temporary MP3
            mp3_path = output_dir / f"{name}.mp3"
            with open(mp3_path, "wb") as f:
                f.write(mp3_data)

            # Convert to WAV
            convert_to_wav(mp3_path, wav_path)

            # Remove MP3
            mp3_path.unlink()

            size = wav_path.stat().st_size
            print(f"OK ({size:,} bytes)")

            # Rate limiting - be nice to the API
            time.sleep(0.3)

        except httpx.HTTPStatusError as e:
            print(f"FAILED: HTTP {e.response.status_code}")
            if e.response.status_code == 429:
                print("  Rate limited. Waiting 10 seconds...")
                time.sleep(10)
        except subprocess.CalledProcessError:
            print("FAILED: ffmpeg conversion error")
        except Exception as e:
            print(f"FAILED: {e}")

    # Summary
    generated = list(output_dir.glob("*.wav"))
    total_size = sum(f.stat().st_size for f in generated)
    print(f"\nVoice pack '{voice_key}' complete!")
    print(f"Files: {len(generated)}/{total}")
    print(f"Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate TTS voice packs using Fish Audio"
    )
    parser.add_argument(
        "--voice", "-v",
        choices=list(VOICES.keys()),
        help="Generate specific voice pack"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Generate all voice packs"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available voices"
    )
    args = parser.parse_args()

    if args.list:
        print("\nAvailable Fish Audio voices:\n")
        for key, config in VOICES.items():
            print(f"  {key:12} - {config['name']}")
            print(f"               {config['description']}")
            print(f"               ID: {config['id']}\n")
        return

    if not args.voice and not args.all:
        parser.print_help()
        print("\n\nAvailable voices:")
        for key, config in VOICES.items():
            print(f"  {key:12} - {config['name']} ({config['description']})")
        return

    # Get API key
    api_key = get_api_key()

    # Determine output directory
    script_dir = Path(__file__).parent
    output_base = script_dir.parent / "app" / "assets" / "tts"

    if args.all:
        voices_to_generate = list(VOICES.keys())
    else:
        voices_to_generate = [args.voice]

    print(f"Fish Audio TTS Asset Generator")
    print(f"Generating {len(voices_to_generate)} voice pack(s)")
    print(f"Total announcements per pack: {len(ANNOUNCEMENTS)}")

    for voice_key in voices_to_generate:
        generate_voice_pack(voice_key, api_key, output_base)

    print("\n" + "="*60)
    print("All done!")
    print("="*60)


if __name__ == "__main__":
    main()

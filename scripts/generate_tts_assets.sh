#!/bin/bash
# Generate TTS audio assets for Voice Notepad accessibility announcements.
#
# Uses Edge TTS with British English male voice (en-GB-RyanNeural).
# Run once to generate assets, then commit them to the repository.
#
# Usage:
#     ./scripts/generate_tts_assets.py
#
# Requirements:
#     pip install edge-tts

set -e

VOICE="en-GB-RyanNeural"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/../app/assets/tts"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Generating TTS assets with voice: $VOICE"
echo "Output directory: $OUTPUT_DIR"
echo

# Announcements to generate
# Keys are filenames, values are the spoken text
declare -A ANNOUNCEMENTS=(
    # Recording states
    ["recording"]="Recording"
    ["stopped"]="Recording stopped"
    ["paused"]="Recording paused"
    ["resumed"]="Recording resumed"
    ["discarded"]="Recording discarded"
    ["appended"]="Recording appended"
    ["cached"]="Cached"

    # Transcription states
    ["transcribing"]="Transcribing"
    ["complete"]="Complete"
    ["error"]="Error"

    # Output modes
    ["text_in_app"]="Text in app"
    ["text_on_clipboard"]="Text on clipboard"
    ["text_injected"]="Text injected"
    ["injection_failed"]="Injection failed"

    # Prompt stack changes
    ["format_updated"]="Format updated"
    ["format_inference"]="Format inference activated"
    ["tone_updated"]="Tone updated"
    ["style_updated"]="Style updated"
    ["verbatim_mode"]="Verbatim mode selected"
    ["general_mode"]="General mode selected"

    # Audio feedback mode changes
    ["tts_activated"]="TTS mode activated"
    ["tts_deactivated"]="TTS mode deactivated"

    # Legacy (kept for compatibility)
    ["copied"]="Copied"
    ["injected"]="Injected"
    ["cleared"]="Cleared"
)

for name in "${!ANNOUNCEMENTS[@]}"; do
    text="${ANNOUNCEMENTS[$name]}"
    mp3_file="$OUTPUT_DIR/$name.mp3"
    wav_file="$OUTPUT_DIR/$name.wav"
    echo "Generating '$text'..."
    # Generate MP3 with edge-tts
    edge-tts --voice "$VOICE" --text "$text" --write-media "$mp3_file"
    # Convert to WAV (16kHz mono, 16-bit) for simpleaudio compatibility
    ffmpeg -y -i "$mp3_file" -ar 16000 -ac 1 -sample_fmt s16 "$wav_file" 2>/dev/null
    # Remove MP3, keep only WAV
    rm "$mp3_file"
    size=$(stat -c%s "$wav_file" 2>/dev/null || stat -f%z "$wav_file")
    echo "  Generated: $name.wav ($size bytes)"
done

echo
echo "Done! Generated ${#ANNOUNCEMENTS[@]} audio files."
total_size=$(du -sb "$OUTPUT_DIR" | cut -f1)
echo "Total size: $total_size bytes"

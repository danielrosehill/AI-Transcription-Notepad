# Audio Feedback

AI Transcription Notepad provides audio notifications for recording and transcription events. Configure the feedback mode in **Settings → Behavior → Audio feedback**.

A "Notification Mode" indicator appears in the main interface footer showing the active mode.

## Modes

| Mode | Description |
|------|-------------|
| **Beeps** | Short beep tones for events (default) |
| **Voice (TTS)** | Spoken announcements using pre-generated voice files |
| **Silent** | No audio feedback |

## Voice (TTS) Announcements

When TTS mode is active, the app speaks brief announcements for each event:

| Event | Announcement |
|-------|-------------|
| Recording started | "Recording" |
| Recording stopped | "Recording stopped" |
| Audio cached (append mode) | "Cached" |
| Transcription started | "Transcribing" |
| Transcription complete | "Complete" |
| Text copied to clipboard | "Clipboard" |
| Recording cleared | "Recording discarded" |
| Error occurred | "Error" |
| Format preset changed | "Format updated" |
| Format inference enabled | "Format inference activated" |
| Tone changed | "Tone updated" |
| Style changed | "Style updated" |
| Verbatim mode selected | "Verbatim mode selected" |
| General mode selected | "General mode selected" |
| Translation mode selected | "Translation mode" |
| TTS mode activated | "TTS mode activated" |
| TTS mode deactivated | "TTS mode deactivated" |
| Reset button pressed | "Default prompt configured" |
| Manual copy to clipboard | "Copied to clipboard" |

Text injection does not have a TTS announcement because text appearing at the cursor is self-evident.

## Technical Details

- **Voice**: British English male (en-GB-RyanNeural via Edge TTS)
- **Audio files**: Pre-generated WAV files (~1.7MB total) bundled in `app/assets/tts/`
- **Playback**: Uses the same audio system as beep notifications

### Regenerating TTS Assets

If you need to regenerate the voice files:

```bash
./scripts/generate_tts_assets.sh
```

Requires the `edge-tts` package (`pip install edge-tts`).

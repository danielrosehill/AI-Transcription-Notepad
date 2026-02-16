# Configuration

AI Transcription Notepad stores settings in `~/.config/voice-notepad-v3/`.

## API Key

You need an **OpenRouter** API key. OpenRouter is the sole provider, giving access to Gemini models with per-key cost tracking.

Set your key via environment variable:

```bash
OPENROUTER_API_KEY=your_key
```

Or configure it in Settings → API Keys within the app.

Get an API key at [openrouter.ai/keys](https://openrouter.ai/keys).

## Models

The default model is `google/gemini-3-flash-preview` (Gemini 3 Flash). You can also select `google/gemini-3-pro-preview` (Gemini 3 Pro) for higher quality output. Change the model in Settings → Models or from the toolbar dropdown.

## Behavior Settings

**Voice Activity Detection** removes silence from audio before sending to the API. This reduces file size and API costs. Uses [TEN VAD](https://github.com/TEN-framework/ten-vad), a lightweight native library bundled with the application. Enable in Settings → Behavior.

**Automatic Gain Control** normalizes audio levels for consistent transcription accuracy. Boosts quiet audio (up to +20dB) while leaving loud audio unchanged. Enable in Settings → Behavior.

**Audio Archival** saves recordings in Opus format (~24kbps) to `~/.config/voice-notepad-v3/audio-archive/`. A one-minute recording uses about 180KB.

## Cleanup Prompt

The cleanup prompt instructs the AI how to process your transcription. The default removes filler words, adds punctuation and paragraph spacing, follows verbal instructions in the recording, and returns markdown. Customize in Settings → Prompt.

## Storage Locations

Settings and data are stored in `~/.config/voice-notepad-v3/`:

- `config.json` - API keys and preferences
- `mongita/` - MongoDB-compatible transcript database
- `usage/` - Daily cost tracking
- `audio-archive/` - Opus recordings (if enabled)

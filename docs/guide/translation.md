# Translation Mode

Translation Mode automatically translates your transcriptions to a target language in a single API call. The AI handles transcription, cleanup, and translation simultaneously.

## Setup

1. Open **Settings → Translation**
2. Set your **Target Language** (the language you want output in)
3. Optionally set a **Source Language** (default: auto-detect)
4. Check **Enable Translation Mode**

Your target language persists across sessions. Toggle translation on or off as needed.

## Supported Languages

Translation supports 30+ languages:

| | | | |
|---|---|---|---|
| Arabic | Chinese (Simplified) | Chinese (Traditional) | Czech |
| Danish | Dutch | English | Finnish |
| French | German | Greek | Hebrew |
| Hindi | Hungarian | Indonesian | Italian |
| Japanese | Korean | Malay | Norwegian |
| Polish | Portuguese | Romanian | Russian |
| Spanish | Swedish | Thai | Turkish |
| Ukrainian | Vietnamese | | |

## How It Works

When translation mode is enabled:
1. You dictate in your source language (typically English)
2. The app sends audio to the AI with both the cleanup prompt and a translation instruction
3. The AI transcribes, cleans up, and translates — all in one API call
4. Output is entirely in the target language

Translation works with all format presets (email, todo, meeting notes, etc.). The AI preserves formatting, structure, and meaning while producing natural-sounding text in the target language.

## UI Indicators

- **Status bar** shows a translation indicator when active (e.g., "→ French")
- **Tooltip** explains the mode is active and how to disable it
- **Settings tab** shows color-coded status (green = enabled, gray = disabled)

## Intended Use Case

Translation mode is designed for users who consistently translate dictations into one target language — for example, dictating in English but needing output in French. Set your target language once, then toggle translation mode on and off as needed.

If you need to translate into multiple languages, update the target in Settings → Translation before translating.

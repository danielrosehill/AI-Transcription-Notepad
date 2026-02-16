# Cost Tracking

AI Transcription Notepad tracks API usage in the Cost tab via OpenRouter's API endpoints.

## OpenRouter Cost Data

The app queries three OpenRouter endpoints:

- `/api/v1/key` returns usage for your specific API key (not your entire account), showing today's, this week's, and this month's spend.
- `/api/v1/credits` returns your account balance, displayed in the status bar and Cost tab.
- `/api/v1/activity` returns per-model usage for the last 30 days.

Balance data is polled in the background at a configurable interval (default: 30 minutes). Configure the polling interval in Settings → Misc.

## Status Bar

The status bar shows `Today: $X.XXXX (N) | Bal: $X.XX` where N is the transcription count and Bal is your OpenRouter credit balance.

## Reducing Costs

Enable Voice Activity Detection to remove silence before upload, which reduces the audio size sent to the API. Gemini 3 Flash is already the most cost-effective option. Keep recordings focused rather than leaving long pauses.

## Local Storage

Cost data is stored in `~/.config/voice-notepad-v3/usage/` as daily JSON files. The Mongita database also stores per-transcription token counts and estimated costs.

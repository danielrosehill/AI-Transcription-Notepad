# Supported Models

Voice Notepad supports audio multimodal models that can directly process audio input for transcription.

## OpenRouter

OpenRouter provides access to multiple providers through a single API key.

| Model | Tier | Notes |
|-------|------|-------|
| google/gemini-2.5-flash | Standard | Recommended default |
| google/gemini-2.5-flash-lite | Budget | Fastest and cheapest |
| google/gemini-2.0-flash-001 | Standard | Previous generation |
| openai/gpt-4o-audio-preview | Premium | Highest quality |
| mistralai/voxtral-small-24b-2507 | Standard | Mistral's audio model |

## Gemini (Direct)

| Model | Tier | Notes |
|-------|------|-------|
| gemini-flash-latest | Dynamic | Always latest Flash |
| gemini-2.5-flash | Standard | Stable release |
| gemini-2.5-flash-lite | Budget | Lite version |
| gemini-2.5-pro | Premium | Pro tier |

## OpenAI (Direct)

| Model | Tier | Notes |
|-------|------|-------|
| gpt-4o-audio-preview | Premium | Full audio capabilities |
| gpt-4o-mini-audio-preview | Budget | Faster and cheaper |

## Mistral (Direct)

| Model | Tier | Notes |
|-------|------|-------|
| voxtral-small-latest | Standard | Standard Voxtral |
| voxtral-mini-latest | Budget | Smaller and faster |

## Choosing a Model

For most users, OpenRouter with google/gemini-2.5-flash provides a good balance of quality and cost with fast processing.

For lower costs, use Gemini Flash Lite variants.

For highest quality, use GPT-4o audio models.

Set your default model in Settings > Models, or select per-transcription from the toolbar dropdown.

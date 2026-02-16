# Supported Models

AI Transcription Notepad uses Google Gemini models via **OpenRouter** for audio transcription. OpenRouter provides an OpenAI-compatible API with per-key cost tracking and low latency.

## Available Models

| Model | Tier | Notes |
|-------|------|-------|
| `google/gemini-3-flash-preview` | Standard | **Default** — fast and cost-effective |
| `google/gemini-3-pro-preview` | Premium | Higher quality, used as fallback |

Gemini 3 Flash is currently in preview and is the recommended model for most transcription tasks. Gemini 3 Pro serves as the automatic fallback if Flash is unavailable.

## Choosing a Model

**Gemini 3 Flash** is recommended for most users. It provides an excellent balance of speed, quality, and cost for voice transcription.

Use **Gemini 3 Pro** when you need higher quality output for complex or nuanced transcriptions (e.g., technical documentation, multi-speaker content).

Set your default model in Settings → Models, or select per-transcription from the toolbar dropdown.

## Model Tiers

| Tier | Model | Use Case |
|------|-------|----------|
| **Standard** | Gemini 3 Flash | Daily transcription, notes, emails |
| **Premium** | Gemini 3 Pro | Complex content, detailed formatting |

## Failover Behavior

If the primary model fails, the app automatically retries with the fallback model. By default:
- **Primary**: `google/gemini-3-flash-preview`
- **Fallback**: `google/gemini-3-pro-preview`

Configure primary and fallback models in Settings → Models.

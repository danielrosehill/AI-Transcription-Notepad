# Semantic Search

Semantic Search uses AI embeddings to find similar transcriptions by meaning, not just keywords. It's available in the History window alongside text-based search.

## How It Works

1. Transcriptions are embedded in batches using Gemini's `gemini-embedding-001` model
2. Each transcription becomes a 768-dimensional vector stored locally in MongoDB
3. When you search, your query is also embedded
4. Results are ranked by cosine similarity — how closely the meaning matches

This means searching for "project deadline" can find a transcription that says "we need to finish by Friday" even though the words don't overlap.

## Using Semantic Search

1. Open the **History** window (from the History tab or menu)
2. Switch to the **Semantic Search** tab
3. Type a search query describing what you're looking for
4. Optionally filter by date range
5. Results appear ranked by similarity score (0-100%)

### Similarity Scores

- **80-100%**: Very strong match — the transcription closely relates to your query
- **60-80%**: Good match — relevant content
- **40-60%**: Moderate match — loosely related
- **Below 40%**: Weak match — may not be relevant

## Embedding Coverage

The Search tab shows embedding coverage: e.g., "Embeddings: 150 / 200 (75% coverage)"

Embeddings are generated in the background when you accumulate 100+ unembedded transcripts. This batch approach:
- Minimizes API calls
- Doesn't block the UI
- Processes oldest transcripts first

## Configuration

Configure in Settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `embedding_enabled` | `True` | Enable/disable semantic search |
| `embedding_model` | `gemini-embedding-001` | Embedding model |
| `embedding_dimensions` | `768` | Vector size |
| `embedding_batch_size` | `100` | Transcripts per batch |

## Cost

Gemini's `gemini-embedding-001` model is **free** (1,500 requests/minute). Semantic search adds no cost to your usage.

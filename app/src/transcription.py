"""Transcription API client using OpenRouter."""

import base64
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

# Patterns that match AI preamble lines (case-insensitive).
# These are checked against the first line of the response only.
_PREAMBLE_PATTERNS = [
    re.compile(r"^here(?:'s| is| are)\b", re.IGNORECASE),
    re.compile(r"^sure[,!.]?\s", re.IGNORECASE),
    re.compile(r"^certainly[,!.]?\s", re.IGNORECASE),
    re.compile(r"^of course[,!.]?\s", re.IGNORECASE),
    re.compile(r"^i'?d be (?:happy|glad|delighted) to\b", re.IGNORECASE),
    re.compile(r"^below is\b", re.IGNORECASE),
    re.compile(r"^the (?:transcri(?:bed|ption)|cleaned|polished|edited)\b", re.IGNORECASE),
    re.compile(r"^i'?ve (?:transcribed|cleaned|polished)\b", re.IGNORECASE),
    re.compile(r"^(?:okay|ok)[,!.]?\s+here\b", re.IGNORECASE),
    re.compile(r"^let me\b", re.IGNORECASE),
    re.compile(r"^absolutely[,!.]?\s", re.IGNORECASE),
]


def strip_ai_preamble(text: str) -> str:
    """Remove AI preamble/commentary from the start of a response.

    Gemini models sometimes prepend lines like "Here is the transcription:"
    despite system prompt instructions not to. This strips those lines as
    a defense-in-depth measure.
    """
    if not text:
        return text

    stripped = text.lstrip()
    if not stripped:
        return text

    # Check if the first line matches any preamble pattern
    first_newline = stripped.find("\n")
    first_line = stripped[:first_newline] if first_newline != -1 else stripped

    # Don't strip if the entire response IS the first line (very short response)
    # and doesn't look like a clear preamble ending with colon
    if first_newline == -1 and not first_line.rstrip().endswith(":"):
        return text

    for pattern in _PREAMBLE_PATTERNS:
        if pattern.search(first_line):
            # Found preamble — remove the first line and any following blank lines
            remainder = stripped[first_newline + 1:] if first_newline != -1 else ""
            result = remainder.lstrip("\n")
            if result:
                logger.debug("Stripped AI preamble: %r", first_line)
                return result
            # If stripping would leave nothing, return original
            return text

    return text


@dataclass
class TranscriptionResult:
    """Result from transcription API including usage data."""
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    actual_cost: Optional[float] = None  # Actual cost from provider (OpenRouter)
    generation_id: Optional[str] = None  # Generation ID for usage lookup


class TranscriptionClient(ABC):
    """Base class for transcription clients."""

    @abstractmethod
    def transcribe(self, audio_data: bytes, prompt: str, audio_format: str = "wav") -> TranscriptionResult:
        """Transcribe audio with cleanup prompt."""
        pass

    @abstractmethod
    def rewrite_text(self, text: str, instruction: str) -> TranscriptionResult:
        """Rewrite text with given instruction (no audio)."""
        pass

    @abstractmethod
    def generate_title(self, text: str) -> str:
        """Generate a short title for the given text."""
        pass


class OpenRouterClient(TranscriptionClient):
    """OpenRouter API client for audio transcription (OpenAI-compatible).

    This is the sole transcription backend. All models (including Gemini)
    are accessed through OpenRouter's unified API.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # Cached HTTP client shared across instances (same API key = same connection pool)
    _shared_client = None
    _shared_client_key: str = ""

    def __init__(self, api_key: str, model: str = "google/gemini-3.5-flash-lite"):
        self.api_key = api_key
        self.model = model

    def _get_client(self):
        # Reuse shared HTTP client if API key matches (avoids HTTPS handshake per call)
        if (OpenRouterClient._shared_client is not None
                and OpenRouterClient._shared_client_key == self.api_key):
            return OpenRouterClient._shared_client
        if not OPENAI_SDK_AVAILABLE:
            raise ImportError("openai package not installed")
        OpenRouterClient._shared_client = OpenAI(
            api_key=self.api_key,
            base_url=self.OPENROUTER_BASE_URL,
        )
        OpenRouterClient._shared_client_key = self.api_key
        return OpenRouterClient._shared_client

    def transcribe(self, audio_data: bytes, prompt: str, audio_format: str = "wav") -> TranscriptionResult:
        """Transcribe audio using OpenRouter's multimodal models.

        audio_format is "wav" or "mp3" — long recordings are sent as MP3
        to stay under provider request-size limits.
        """
        client = self._get_client()

        # Encode audio as base64
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "[audio]"},
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_b64,
                                "format": audio_format
                            }
                        }
                    ]
                }
            ],
            # Request usage information including cost
            extra_body={"usage": {"include": True}},
        )

        # Extract usage data
        input_tokens = 0
        output_tokens = 0
        actual_cost = None
        generation_id = None

        # Get generation ID for usage lookup
        if hasattr(response, 'id') and response.id:
            generation_id = response.id

        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0) or 0
            output_tokens = getattr(response.usage, 'completion_tokens', 0) or 0
            # OpenRouter includes cost in usage when requested
            if hasattr(response.usage, 'cost'):
                actual_cost = getattr(response.usage, 'cost', None)

        # Note: We no longer fetch cost per-transcription to minimize latency.
        # Cost is estimated from tokens using MODEL_PRICING in cost_tracker.py.
        # Actual spend is polled periodically via OpenRouter's /key endpoint.

        return TranscriptionResult(
            text=strip_ai_preamble(response.choices[0].message.content),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            actual_cost=actual_cost,
            generation_id=generation_id,
        )

    def rewrite_text(self, text: str, instruction: str) -> TranscriptionResult:
        """Rewrite text using OpenRouter (text-only, no audio)."""
        client = self._get_client()

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": instruction
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            extra_body={"usage": {"include": True}},
        )

        # Extract usage data
        input_tokens = 0
        output_tokens = 0
        actual_cost = None
        generation_id = None

        if hasattr(response, 'id') and response.id:
            generation_id = response.id

        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0) or 0
            output_tokens = getattr(response.usage, 'completion_tokens', 0) or 0
            if hasattr(response.usage, 'cost'):
                actual_cost = getattr(response.usage, 'cost', None)

        return TranscriptionResult(
            text=strip_ai_preamble(response.choices[0].message.content),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            actual_cost=actual_cost,
            generation_id=generation_id,
        )

    def generate_title(self, text: str) -> str:
        """Generate a short title using OpenRouter."""
        client = self._get_client()

        prompt = (
            "Generate a short, descriptive title for the following text. "
            "The title should be 3-6 words, suitable for a filename (no special characters). "
            "Respond with ONLY the title, no explanations or punctuation at the end."
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text[:1000]}
            ],
            max_tokens=20
        )

        # Clean up title
        title = response.choices[0].message.content.strip().strip('"\'.,!?')
        title = ''.join(c if c.isalnum() or c in ' -_' else '' for c in title)
        title = '_'.join(title.split())
        return title or "untitled"


def get_client(api_key: str, model: str) -> TranscriptionClient:
    """Factory function to get transcription client.

    All transcription uses OpenRouter as the sole backend.
    Gemini and other models are accessed through OpenRouter's unified API.
    """
    return OpenRouterClient(api_key, model)

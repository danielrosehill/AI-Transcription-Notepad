"""Transcription API clients for Gemini, OpenAI, and Mistral."""

import base64
import tempfile
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TranscriptionResult:
    """Result from transcription API including usage data."""
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class TranscriptionClient(ABC):
    """Base class for transcription clients."""

    @abstractmethod
    def transcribe(self, audio_data: bytes, prompt: str) -> TranscriptionResult:
        """Transcribe audio with cleanup prompt."""
        pass


class GeminiClient(TranscriptionClient):
    """Google Gemini API client for audio transcription."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-lite"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def transcribe(self, audio_data: bytes, prompt: str) -> TranscriptionResult:
        """Transcribe audio using Gemini's multimodal capabilities."""
        client = self._get_client()
        from google.genai import types

        response = client.models.generate_content(
            model=self.model,
            contents=[
                prompt,
                types.Part.from_bytes(data=audio_data, mime_type="audio/wav")
            ]
        )

        # Extract usage metadata
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0

        return TranscriptionResult(
            text=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )


class OpenAIClient(TranscriptionClient):
    """OpenAI API client for audio transcription."""

    def __init__(self, api_key: str, model: str = "gpt-4o-audio-preview"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def transcribe(self, audio_data: bytes, prompt: str) -> TranscriptionResult:
        """Transcribe audio using OpenAI's audio capabilities."""
        client = self._get_client()

        # Encode audio as base64
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_b64,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ]
        )

        # Extract usage data
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0) or 0
            output_tokens = getattr(response.usage, 'completion_tokens', 0) or 0

        return TranscriptionResult(
            text=response.choices[0].message.content,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )


class MistralClient(TranscriptionClient):
    """Mistral API client for audio transcription using Voxtral."""

    def __init__(self, api_key: str, model: str = "voxtral-mini-latest"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from mistralai import Mistral
            self._client = Mistral(api_key=self.api_key)
        return self._client

    def transcribe(self, audio_data: bytes, prompt: str) -> TranscriptionResult:
        """Transcribe audio using Mistral's Voxtral model."""
        client = self._get_client()

        # Encode audio as base64 (Voxtral expects raw base64, not data URL)
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        response = client.chat.complete(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": audio_b64
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )

        # Extract usage data
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0) or 0
            output_tokens = getattr(response.usage, 'completion_tokens', 0) or 0

        return TranscriptionResult(
            text=response.choices[0].message.content,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )


def get_client(provider: str, api_key: str, model: str) -> TranscriptionClient:
    """Factory function to get appropriate transcription client."""
    if provider == "gemini":
        return GeminiClient(api_key, model)
    elif provider == "openai":
        return OpenAIClient(api_key, model)
    elif provider == "mistral":
        return MistralClient(api_key, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")

"""
Thin wrapper around Google's Gemini API (Google AI Studio).

Features:
  * tenacity-based retries on transient errors
  * Native JSON mode via `response_mime_type="application/json"`
  * Fallback model + max_tokens overrides per call
  * Single import surface — every other module only imports `LLMClient`
    from this file, so swapping LLM providers is a one-file change.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Errors worth retrying on (transient network / quota / 5xx).
_RETRYABLE_ERRORS = (
    genai_errors.APIError,
    genai_errors.ServerError,
    genai_errors.ClientError,
    ConnectionError,
    TimeoutError,
)


class LLMClient:
    """Google Gemini client wrapper with sane defaults."""

    def __init__(self, model: Optional[str] = None) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. Get a key at "
                "https://aistudio.google.com/apikey and put it in your .env."
            )
        # The new google-genai SDK (replacement for google-generativeai).
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = model or settings.gemini_model
        self.fallback_model = settings.gemini_fallback_model

    # ------------------------------------------------------------------

    def _build_config(
        self,
        *,
        system_prompt: str,
        json_mode: bool,
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> "types.GenerateContentConfig":
        """Build the GenerateContentConfig for a single call."""
        effective_temp = (
            temperature if temperature is not None
            else settings.gemini_temperature
        )
        kwargs: Dict[str, Any] = {
            "system_instruction": system_prompt,
            "temperature": effective_temp,
            "max_output_tokens": max_tokens or settings.gemini_max_tokens,
        }
        if json_mode:
            # Gemini's native JSON mode — guarantees a parseable JSON object.
            kwargs["response_mime_type"] = "application/json"
        return types.GenerateContentConfig(**kwargs)

    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=20),
        retry=retry_if_exception_type(_RETRYABLE_ERRORS),
        reraise=True,
    )
    def chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> str:
        """Single-turn generation. Returns the model's text content."""
        config = self._build_config(
            system_prompt=system_prompt,
            json_mode=json_mode,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = self.client.models.generate_content(
            model=model or self.model,
            contents=user_prompt,
            config=config,
        )
        # `response.text` joins all text parts of the first candidate.
        # Returns "" if blocked by safety filter or no textual content.
        return response.text or ""

    # ------------------------------------------------------------------

    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Chat call that expects (and parses) a JSON-object response."""
        raw = self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Gemini returned non-JSON content; attempting recovery")
            # crude recovery: find first '{' and last '}'
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(raw[start: end + 1])
            raise

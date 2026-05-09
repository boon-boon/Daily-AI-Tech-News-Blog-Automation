"""
Thin wrapper around the OpenAI Chat Completions API with:
  * tenacity-based retries on transient errors
  * automatic JSON-mode response handling
  * token-aware fallback model

The rest of the codebase only ever imports `LLMClient` from this module.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """OpenAI client wrapper with sane defaults."""

    def __init__(self, model: Optional[str] = None) -> None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Set it in your .env file."
            )
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.openai_model
        self.fallback_model = settings.openai_fallback_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=20),
        retry=retry_if_exception_type(
            (APIError, APIConnectionError, RateLimitError)
        ),
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
        """Single-turn chat completion. Returns the assistant's text content."""
        kwargs: Dict[str, Any] = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature
                if temperature is not None else settings.openai_temperature,
            "max_tokens": max_tokens or settings.openai_max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

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
            logger.warning("LLM returned non-JSON content; attempting recovery")
            # crude recovery: find first '{' and last '}'
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(raw[start: end + 1])
            raise

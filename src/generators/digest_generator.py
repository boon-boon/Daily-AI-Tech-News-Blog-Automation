"""
Generate ONE consolidated daily digest article from all filtered items.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from src.processors.llm_client import LLMClient
from src.utils.logger import get_logger

from .article_generator import ArticleGenerator, GeneratedArticle
from .prompts import build_digest_system_prompt

logger = get_logger(__name__)


class DigestGenerator(ArticleGenerator):
    """Subclass that swaps in the digest system prompt."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__(llm=llm)
        self.system_prompt = build_digest_system_prompt()

    def generate_digest(self, items: List[Dict[str, Any]]) -> GeneratedArticle:
        logger.info(f"Generating consolidated daily digest from {len(items)} items")
        user_prompt = (
            "Write today's daily digest article that summarises the following "
            "news items. Strictly follow OUTPUT_FORMAT. Return ONLY the JSON "
            "object.\n\n"
            f"NEWS_ITEMS = {json.dumps(items, ensure_ascii=False)}"
        )
        payload = self.llm.chat_json(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
        )
        return self._post_process(payload, original_item=None)

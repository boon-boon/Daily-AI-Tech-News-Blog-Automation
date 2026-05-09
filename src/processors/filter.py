"""
Combined deduplication + quality filter + categorisation in a single
LLM call. Doing all three in one pass minimises token cost and latency.

Input  : List[NewsItem]
Output : List[Dict] – each dict carries the original NewsItem fields plus
         `category` and `importance_score`.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from src.fetchers.base import NewsItem
from src.utils.logger import get_logger

from .llm_client import LLMClient

logger = get_logger(__name__)


_FILTER_SYSTEM_PROMPT = """You are an expert technology news editor.
You will be given a JSON array of raw news items collected from many sources
(GitHub, official blogs, Hacker News, Hugging Face, news APIs, etc.).

Your job is to:
  1. DEDUPLICATE: collapse items that cover the same underlying news story
     (e.g. the same release announced on the official blog AND on Hacker News).
     Keep the most authoritative source for each canonical story.
  2. QUALITY FILTER: drop low-value items such as:
       - cosmetic patch bumps (X.Y.Z patch with no notable changes)
       - rumour, speculation, opinion pieces
       - generic listicles ("Top 10 JavaScript tips")
       - paywalled press releases
  3. CATEGORISE each surviving item into ONE of:
       - "Programming Language Updates"
       - "Framework & Library Releases"
       - "AI Model Releases"
       - "AI / ML Research"
       - "Developer Tools"
       - "Cloud & Infrastructure"
       - "Industry News"
  4. SCORE importance from 1 (minor) to 10 (major).

Return a SINGLE valid JSON object with this exact shape:
{
  "kept": [
    {
      "id": <integer index from the input array>,
      "category": "<one of the categories above>",
      "importance_score": <1-10 integer>,
      "rationale": "<one short sentence explaining why this item matters>"
    },
    ...
  ]
}

Constraints:
  * Keep between MIN_ITEMS and MAX_ITEMS items (you will be told the numbers).
  * Prefer items with concrete version numbers, dates, performance numbers,
    or named entities (Angular v17, GPT-4o, Llama 3.1, etc.).
  * Output JSON only. No prose, no markdown.
"""


class NewsFilter:
    """LLM-driven dedupe + filter + category."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def _build_user_prompt(
        self, items: List[NewsItem], min_items: int, max_items: int
    ) -> str:
        normalised = []
        for idx, it in enumerate(items):
            normalised.append({
                "id": idx,
                "title": it.title[:300],
                "source": it.source,
                "url": it.url,
                "summary": (it.summary or "")[:600],
                "published_at": it.published_at.isoformat() if it.published_at else None,
                "tags": it.tags[:6],
            })

        return (
            f"MIN_ITEMS={min_items}\nMAX_ITEMS={max_items}\n\n"
            f"INPUT_ITEMS = {json.dumps(normalised, ensure_ascii=False)}"
        )

    def filter(
        self,
        items: List[NewsItem],
        *,
        min_items: int,
        max_items: int,
    ) -> List[Dict[str, Any]]:
        """Run the LLM filter and return enriched item dicts."""
        if not items:
            return []

        user_prompt = self._build_user_prompt(items, min_items, max_items)
        try:
            payload = self.llm.chat_json(
                system_prompt=_FILTER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
        except Exception as exc:                                       # noqa: BLE001
            logger.exception(f"NewsFilter LLM call failed, falling back: {exc}")
            return self._heuristic_fallback(items, max_items=max_items)

        kept = payload.get("kept", []) or []
        kept = sorted(
            kept,
            key=lambda x: x.get("importance_score", 0),
            reverse=True,
        )[:max_items]

        enriched: List[Dict[str, Any]] = []
        for entry in kept:
            idx = entry.get("id")
            if not isinstance(idx, int) or idx < 0 or idx >= len(items):
                continue
            it = items[idx]
            enriched.append({
                **it.to_dict(),
                "category": entry.get("category", "Industry News"),
                "importance_score": int(entry.get("importance_score", 5)),
                "rationale": entry.get("rationale", ""),
            })
        logger.info(f"Filter kept {len(enriched)}/{len(items)} items")
        return enriched

    # ------------------------------------------------------------------
    # Fallback so an LLM outage doesn't kill the daily run entirely.
    # ------------------------------------------------------------------
    def _heuristic_fallback(
        self, items: List[NewsItem], max_items: int
    ) -> List[Dict[str, Any]]:
        """Crude dedupe by URL + title; pick the most recent N."""
        seen: set[str] = set()
        unique: List[NewsItem] = []
        for it in items:
            key = it.url or it.title.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(it)

        unique.sort(
            key=lambda x: x.published_at or x.published_at,
            reverse=True,
        ) if any(i.published_at for i in unique) else None

        result = []
        for it in unique[:max_items]:
            result.append({
                **it.to_dict(),
                "category": "Industry News",
                "importance_score": 5,
                "rationale": "Heuristic fallback (LLM unavailable).",
            })
        logger.warning(f"Used heuristic fallback; kept {len(result)} items")
        return result

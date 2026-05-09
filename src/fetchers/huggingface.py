"""
Hugging Face fetcher.

Uses the public Hub API to surface newly trending models in the last
24 hours.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from config import settings

from .base import BaseFetcher, NewsItem


class HuggingFaceFetcher(BaseFetcher):
    name = "huggingface"
    URL = "https://huggingface.co/api/models"

    def _headers(self) -> dict:
        return (
            {"Authorization": f"Bearer {settings.huggingface_token}"}
            if settings.huggingface_token
            else {}
        )

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        params = {"sort": "lastModified", "direction": -1, "limit": 25}
        resp = self.http.get(self.URL, params=params, headers=self._headers())
        resp.raise_for_status()
        models = resp.json()

        items: List[NewsItem] = []
        for m in models:
            modified = self._parse_dt(m.get("lastModified"))
            if not self.is_recent(modified, lookback_hours):
                continue
            model_id = m.get("modelId") or m.get("id")
            if not model_id:
                continue
            downloads = m.get("downloads", 0)
            likes = m.get("likes", 0)
            # filter low-signal items
            if downloads < 50 and likes < 5:
                continue

            items.append(
                NewsItem(
                    title=f"{model_id} (Hugging Face model update)",
                    url=f"https://huggingface.co/{model_id}",
                    source=self.name,
                    summary=(
                        f"Hugging Face model • {downloads} downloads • "
                        f"{likes} likes • pipeline_tag={m.get('pipeline_tag', 'n/a')}"
                    ),
                    published_at=modified,
                    tags=["huggingface", "ai", "model", m.get("pipeline_tag") or ""],
                    raw={"downloads": downloads, "likes": likes,
                         "pipeline_tag": m.get("pipeline_tag")},
                )
            )
        return items

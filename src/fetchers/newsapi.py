"""
NewsAPI.org fetcher (https://newsapi.org).

Requires a free API key (NEWSAPI_KEY env var). If no key is configured,
the fetcher gracefully returns an empty list without raising.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from config import settings

from .base import BaseFetcher, NewsItem
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NewsAPIFetcher(BaseFetcher):
    name = "newsapi"
    URL = "https://newsapi.org/v2/top-headlines"

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        if not settings.newsapi_key:
            logger.info("[newsapi] no API key configured; skipping")
            return []

        params = {
            "category": "technology",
            "language": "en",
            "pageSize": 25,
            "apiKey": settings.newsapi_key,
        }
        resp = self.http.get(self.URL, params=params)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])

        items: List[NewsItem] = []
        for art in articles:
            published = self._parse_dt(art.get("publishedAt"))
            if not self.is_recent(published, lookback_hours):
                continue
            items.append(
                NewsItem(
                    title=art.get("title") or "",
                    url=art.get("url") or "",
                    source=f"newsapi:{(art.get('source') or {}).get('name', 'unknown')}",
                    summary=(art.get("description") or art.get("content") or "")[:1500],
                    published_at=published,
                    author=art.get("author"),
                    tags=["newsapi", "tech"],
                    raw={"source": art.get("source")},
                )
            )
        return items

"""
Papers with Code 'latest' RSS fetcher.

Papers with Code provides RSS feeds for the latest papers and trending
research. We delegate the heavy lifting to feedparser.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import feedparser

from .base import BaseFetcher, NewsItem


class PapersWithCodeFetcher(BaseFetcher):
    name = "papers_with_code"
    FEED = "https://paperswithcode.com/latest.rss"

    def fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        try:
            resp = self.http.get(self.FEED)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
        except Exception:
            return []

        items: List[NewsItem] = []
        for entry in parsed.entries[:20]:
            value = entry.get("published_parsed") or entry.get("updated_parsed")
            published = datetime(*value[:6], tzinfo=timezone.utc) if value else None
            if not self.is_recent(published, lookback_hours):
                continue
            items.append(
                NewsItem(
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", ""),
                    source=self.name,
                    summary=(entry.get("summary") or "")[:1500],
                    published_at=published,
                    author=entry.get("author"),
                    tags=["ai", "research", "papers-with-code"],
                    raw={},
                )
            )
        return items

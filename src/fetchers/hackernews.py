"""
Hacker News fetcher (Algolia search API).

We use the Algolia HN search endpoint because it supports time filtering
and returns a clean JSON payload.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from .base import BaseFetcher, NewsItem


class HackerNewsFetcher(BaseFetcher):
    name = "hacker_news"
    URL = "https://hn.algolia.com/api/v1/search_by_date"

    def fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        cutoff = int(self.cutoff_datetime(lookback_hours).timestamp())
        params = {
            "tags": "story",
            "numericFilters": f"created_at_i>={cutoff},points>=80",
            "hitsPerPage": 25,
        }
        resp = self.http.get(self.URL, params=params)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])

        items: List[NewsItem] = []
        for hit in hits:
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            ts = hit.get("created_at_i")
            published = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
            items.append(
                NewsItem(
                    title=hit.get("title") or "",
                    url=url,
                    source=self.name,
                    summary=f"Hacker News • {hit.get('points', 0)} points • "
                            f"{hit.get('num_comments', 0)} comments",
                    published_at=published,
                    author=hit.get("author"),
                    tags=["hackernews"],
                    raw={
                        "points": hit.get("points"),
                        "comments": hit.get("num_comments"),
                        "object_id": hit.get("objectID"),
                    },
                )
            )
        return items

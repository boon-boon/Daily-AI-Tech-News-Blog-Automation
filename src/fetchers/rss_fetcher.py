"""
Generic RSS / Atom feed fetcher.

A single class is reused for many feeds. Three curated feed groups are
provided out of the box:
  * OFFICIAL_BLOG_FEEDS – Angular, React, Vue, Python, Node.js
  * AI_BLOG_FEEDS       – OpenAI, Google AI, Hugging Face, etc.
  * MEDIA_FEEDS         – TechCrunch, The Verge (tech), Ars Technica
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

import feedparser

from .base import BaseFetcher, NewsItem


# (label, feed_url) pairs
OFFICIAL_BLOG_FEEDS: Dict[str, str] = {
    "angular_blog": "https://blog.angular.io/feed",
    "react_blog": "https://react.dev/rss.xml",
    "vue_blog": "https://blog.vuejs.org/feed.rss",
    "python_news": "https://www.python.org/blogs/feed/",
    "nodejs_blog": "https://nodejs.org/en/feed/blog.xml",
    "typescript_blog": "https://devblogs.microsoft.com/typescript/feed/",
    "deno_blog": "https://deno.com/feed",
}

AI_BLOG_FEEDS: Dict[str, str] = {
    "openai_blog": "https://openai.com/blog/rss.xml",
    "google_ai_blog": "https://blog.google/technology/ai/rss/",
    "huggingface_blog": "https://huggingface.co/blog/feed.xml",
    "deepmind_blog": "https://deepmind.google/blog/rss.xml",
    "anthropic_news": "https://www.anthropic.com/news/rss.xml",
}

MEDIA_FEEDS: Dict[str, str] = {
    "techcrunch": "https://techcrunch.com/feed/",
    "ars_technica": "https://feeds.arstechnica.com/arstechnica/index",
    "the_verge_tech": "https://www.theverge.com/tech/rss/index.xml",
    "wired_business": "https://www.wired.com/feed/category/business/latest/rss",
}


class RSSFetcher(BaseFetcher):
    """Fetch + parse a group of RSS feeds."""

    def __init__(self, name: str, feeds: Dict[str, str]) -> None:
        super().__init__(name=name)
        self.feeds = feeds

    @staticmethod
    def _entry_dt(entry) -> datetime | None:
        for key in ("published_parsed", "updated_parsed"):
            value = entry.get(key)
            if value:
                return datetime(*value[:6], tzinfo=timezone.utc)
        return None

    def fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        items: List[NewsItem] = []
        for source_label, feed_url in self.feeds.items():
            try:
                # feedparser supports both URL and bytes; using bytes lets us reuse httpx
                resp = self.http.get(feed_url)
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
            except Exception:
                continue

            for entry in parsed.entries[:15]:
                published = self._entry_dt(entry)
                if not self.is_recent(published, lookback_hours):
                    continue
                title = (entry.get("title") or "").strip()
                link = entry.get("link") or ""
                if not title or not link:
                    continue

                summary = (entry.get("summary") or entry.get("description") or "")[:2000]
                author = entry.get("author") or parsed.feed.get("title", "")

                items.append(
                    NewsItem(
                        title=title,
                        url=link,
                        source=source_label,
                        summary=summary,
                        published_at=published,
                        author=author,
                        tags=[source_label],
                        raw={"feed": feed_url},
                    )
                )
        return items

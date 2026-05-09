"""
GitHub Trending fetcher.

There is no official GitHub Trending API. We scrape the public
trending HTML page (https://github.com/trending) which is rate-limit-friendly
when called at most a few times per day.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from bs4 import BeautifulSoup

from config import settings

from .base import BaseFetcher, NewsItem


class GitHubTrendingFetcher(BaseFetcher):
    name = "github_trending"
    BASE_URL = "https://github.com/trending"

    def fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        items: List[NewsItem] = []
        # `since` accepts daily/weekly/monthly. Daily aligns with our 24h goal.
        languages = settings.github_trending_languages or [""]
        for lang in languages:
            url = f"{self.BASE_URL}/{lang}?since=daily" if lang else f"{self.BASE_URL}?since=daily"
            try:
                resp = self.http.get(url)
                resp.raise_for_status()
            except Exception:
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            for repo_card in soup.select("article.Box-row")[:10]:
                title_el = repo_card.select_one("h2 a")
                if not title_el:
                    continue
                repo_path = title_el.get("href", "").strip("/")
                if not repo_path:
                    continue

                desc_el = repo_card.select_one("p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                stars_today_el = repo_card.select_one(
                    "span.d-inline-block.float-sm-right"
                )
                stars_today = stars_today_el.get_text(strip=True) if stars_today_el else ""

                title = f"{repo_path} (trending {lang or 'all'})"
                summary = description
                if stars_today:
                    summary = f"{description}  •  {stars_today}".strip(" •")

                items.append(
                    NewsItem(
                        title=title,
                        url=f"https://github.com/{repo_path}",
                        source=f"{self.name}:{lang or 'all'}",
                        summary=summary,
                        published_at=datetime.now(timezone.utc),
                        tags=["github", "trending"] + ([lang] if lang else []),
                        raw={"language": lang, "repo_path": repo_path},
                    )
                )
        return items

"""
GitHub Releases fetcher.

Uses the official REST API to pull recent releases for a curated list
of repositories (Angular, React, Vue, Python, Node, etc.).
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from config import settings

from .base import BaseFetcher, NewsItem


class GitHubReleasesFetcher(BaseFetcher):
    name = "github_releases"
    API_BASE = "https://api.github.com"

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            h["Authorization"] = f"Bearer {settings.github_token}"
        return h

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        items: List[NewsItem] = []
        for repo in settings.github_tracked_repos:
            url = f"{self.API_BASE}/repos/{repo}/releases?per_page=5"
            try:
                resp = self.http.get(url, headers=self._headers())
                resp.raise_for_status()
                releases = resp.json()
            except Exception:
                continue

            for release in releases:
                pub = self._parse_dt(release.get("published_at"))
                if not self.is_recent(pub, lookback_hours):
                    continue
                if release.get("draft") or release.get("prerelease"):
                    # skip drafts; keep prereleases optional
                    pass

                title = f"{repo} {release.get('name') or release.get('tag_name', '')}".strip()
                items.append(
                    NewsItem(
                        title=title,
                        url=release.get("html_url", f"https://github.com/{repo}/releases"),
                        source=f"{self.name}:{repo}",
                        summary=(release.get("body") or "")[:1500],
                        published_at=pub,
                        author=(release.get("author") or {}).get("login"),
                        tags=["github", "release", repo.split("/")[-1]],
                        raw={
                            "repo": repo,
                            "tag_name": release.get("tag_name"),
                            "prerelease": release.get("prerelease", False),
                        },
                    )
                )
        return items

"""
Common types and the abstract base class for all news fetchers.

All fetchers normalise their results into a uniform `NewsItem` shape so the
downstream processors / generator never need to know which source they
originated from.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NewsItem:
    """Canonical representation of a single news story."""

    title: str
    url: str
    source: str                      # e.g. "github_trending", "angular_blog"
    summary: str = ""
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.published_at:
            d["published_at"] = self.published_at.isoformat()
        # Drop heavyweight raw blob from dicts intended for the LLM
        d.pop("raw", None)
        return d


class BaseFetcher(ABC):
    """
    Abstract base for all fetchers.

    Subclasses implement `fetch()` and may use `self.http` (a shared
    `httpx.Client` with sane defaults) for network calls.
    """

    name: str = "base"
    timeout: float = 20.0

    def __init__(self, name: Optional[str] = None) -> None:
        if name:
            self.name = name
        self.http = httpx.Client(
            timeout=self.timeout,
            headers={
                "User-Agent": (
                    "DailyTechNewsBot/1.0 (+https://example.com) "
                    "Python-httpx"
                )
            },
            follow_redirects=True,
        )

    # ---- Public API -------------------------------------------------------

    def safe_fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        """Wrap `fetch()` so a single failing source never aborts the run."""
        try:
            items = self.fetch(lookback_hours=lookback_hours)
            logger.info(f"[{self.name}] fetched {len(items)} items")
            return items
        except Exception as exc:                                      # noqa: BLE001
            logger.exception(f"[{self.name}] fetch failed: {exc}")
            return []

    @abstractmethod
    def fetch(self, lookback_hours: int = 24) -> List[NewsItem]:
        """Subclasses fetch and return a list of NewsItem."""

    # ---- Helpers ----------------------------------------------------------

    @staticmethod
    def cutoff_datetime(lookback_hours: int) -> datetime:
        """Compute the UTC cutoff datetime for the lookback window."""
        return datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    @staticmethod
    def is_recent(published_at: Optional[datetime], lookback_hours: int) -> bool:
        if not published_at:
            return True   # be permissive if we cannot determine a date
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        cutoff = BaseFetcher.cutoff_datetime(lookback_hours)
        return published_at >= cutoff

    def __del__(self) -> None:
        try:
            self.http.close()
        except Exception:                                             # noqa: BLE001
            pass

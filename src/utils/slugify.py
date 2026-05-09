"""URL slug helpers."""

from __future__ import annotations

from datetime import date
from slugify import slugify


def slugify_title(title: str, max_length: int = 80) -> str:
    """Convert an article title into a clean URL slug."""
    return slugify(title, max_length=max_length, word_boundary=True, save_order=True)


def build_permalink(title: str, publish_date: date | None = None) -> str:
    """Build a clean permalink path: '/2026/05/09/angular-v17-released'."""
    pd = publish_date or date.today()
    return f"/{pd.year:04d}/{pd.month:02d}/{pd.day:02d}/{slugify_title(title)}"

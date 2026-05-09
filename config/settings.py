"""
Centralised, typed configuration loaded from environment / .env.

All modules import `settings` from here so that environment access happens
exactly once and is easy to mock in tests.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load .env from project root if present
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _csv(env_value: str | None) -> List[str]:
    """Parse a comma-separated env value into a clean list."""
    if not env_value:
        return []
    return [item.strip() for item in env_value.split(",") if item.strip()]


def _bool(env_value: str | None, default: bool = False) -> bool:
    if env_value is None:
        return default
    return env_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # ---- LLM (Google Gemini via Google AI Studio) ----
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_fallback_model: str = os.getenv(
        "GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite"
    )
    gemini_max_tokens: int = int(os.getenv("GEMINI_MAX_TOKENS", "4000"))
    gemini_temperature: float = float(os.getenv("GEMINI_TEMPERATURE", "0.4"))

    # ---- Blog identity ----
    blog_name: str = os.getenv("BLOG_NAME", "Daily Tech Pulse")
    blog_author: str = os.getenv("BLOG_AUTHOR", "Daily Tech Pulse Editorial")
    blog_base_url: str = os.getenv("BLOG_BASE_URL", "https://example.com").rstrip("/")
    blog_language: str = os.getenv("BLOG_LANGUAGE", "en")
    blog_default_category: str = os.getenv("BLOG_DEFAULT_CATEGORY", "Technology")

    # ---- Scheduler ----
    run_time: str = os.getenv("RUN_TIME", "08:00")
    timezone: str = os.getenv("TIMEZONE", "Asia/Kuala_Lumpur")
    scheduler_mode: str = os.getenv("SCHEDULER_MODE", "cron")  # 'cron' or 'oneshot'

    # ---- Sources ----
    newsapi_key: str = os.getenv("NEWSAPI_KEY", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    huggingface_token: str = os.getenv("HUGGINGFACE_TOKEN", "")

    github_trending_languages: List[str] = field(
        default_factory=lambda: _csv(os.getenv("GITHUB_TRENDING_LANGUAGES",
                                               "python,javascript,typescript,rust,go"))
    )
    github_tracked_repos: List[str] = field(
        default_factory=lambda: _csv(os.getenv("GITHUB_TRACKED_REPOS",
                                               "angular/angular,facebook/react,vuejs/core,"
                                               "python/cpython,nodejs/node,microsoft/TypeScript,"
                                               "vercel/next.js,sveltejs/svelte"))
    )

    lookback_hours: int = int(os.getenv("LOOKBACK_HOURS", "24"))
    min_items: int = int(os.getenv("MIN_ITEMS", "5"))
    max_items: int = int(os.getenv("MAX_ITEMS", "12"))

    # ---- Article strategy ----
    article_mode: str = os.getenv("ARTICLE_MODE", "individual")  # 'individual' or 'digest'

    # ---- Paths ----
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "./output")).resolve()
    log_dir: Path = Path(os.getenv("LOG_DIR", "./logs")).resolve()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # ---- WordPress ----
    publish_to_wordpress: bool = _bool(os.getenv("PUBLISH_TO_WORDPRESS"), False)
    wordpress_url: str = os.getenv("WORDPRESS_URL", "").rstrip("/")
    wordpress_username: str = os.getenv("WORDPRESS_USERNAME", "")
    wordpress_app_password: str = os.getenv("WORDPRESS_APP_PASSWORD", "")
    wordpress_default_status: str = os.getenv("WORDPRESS_DEFAULT_STATUS", "draft")
    wordpress_default_category_id: str = os.getenv("WORDPRESS_DEFAULT_CATEGORY_ID", "")

    # Convenience derived dirs
    @property
    def markdown_dir(self) -> Path:
        return self.output_dir / "markdown"

    @property
    def html_dir(self) -> Path:
        return self.output_dir / "html"

    @property
    def metadata_dir(self) -> Path:
        return self.output_dir / "metadata"

    def ensure_dirs(self) -> None:
        for d in (self.output_dir, self.markdown_dir, self.html_dir,
                  self.metadata_dir, self.log_dir):
            d.mkdir(parents=True, exist_ok=True)


# Singleton-style instance used everywhere
settings = Settings()
settings.ensure_dirs()

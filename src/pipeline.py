"""
End-to-end daily pipeline: fetch -> filter -> generate -> publish.

This module is what both the scheduler and the CLI invoke. Each phase
is wrapped in try/except so a partial failure produces logs and a
fallback post rather than a hard crash.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from config import settings

from src.fetchers import build_default_fetchers
from src.fetchers.base import NewsItem
from src.generators.article_generator import ArticleGenerator, GeneratedArticle
from src.generators.digest_generator import DigestGenerator
from src.processors.filter import NewsFilter
from src.publishers.local import LocalPublisher
from src.publishers.wordpress import WordPressPublisher
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DailyPipeline:
    """Run the entire daily blog generation workflow."""

    def __init__(self) -> None:
        self.fetchers = build_default_fetchers()
        self.filter = NewsFilter()
        self.local_publisher = LocalPublisher()
        self.wp_publisher = WordPressPublisher()
        self._article_gen: ArticleGenerator | None = None
        self._digest_gen: DigestGenerator | None = None

    # ------------------------------------------------------------------
    # Lazy generator init so a missing OPENAI_API_KEY only fails when
    # actually needed (e.g. allows `--list-sources` style commands).
    # ------------------------------------------------------------------
    @property
    def article_gen(self) -> ArticleGenerator:
        if self._article_gen is None:
            self._article_gen = ArticleGenerator()
        return self._article_gen

    @property
    def digest_gen(self) -> DigestGenerator:
        if self._digest_gen is None:
            self._digest_gen = DigestGenerator()
        return self._digest_gen

    # ------------------------------------------------------------------

    def fetch_all(self) -> List[NewsItem]:
        """Run every fetcher and return a flat list of NewsItem."""
        all_items: List[NewsItem] = []
        for fetcher in self.fetchers:
            all_items.extend(fetcher.safe_fetch(lookback_hours=settings.lookback_hours))
        logger.info(f"Total raw items collected: {len(all_items)}")
        return all_items

    # ------------------------------------------------------------------

    def run(self) -> List[GeneratedArticle]:
        """Run the full pipeline once and return the published articles."""
        run_start = datetime.utcnow()
        logger.info(
            f"=== Daily run starting (mode={settings.article_mode}, "
            f"lookback={settings.lookback_hours}h) ==="
        )

        # 1) Fetch
        raw_items = self.fetch_all()

        # 2) Filter / dedupe / categorise
        if raw_items:
            try:
                filtered = self.filter.filter(
                    raw_items,
                    min_items=settings.min_items,
                    max_items=settings.max_items,
                )
            except Exception as exc:                                  # noqa: BLE001
                logger.exception(f"Filtering failed: {exc}")
                filtered = []
        else:
            filtered = []

        # 3) Generate
        articles: List[GeneratedArticle] = []
        if not filtered:
            logger.warning("No items survived filtering; generating fallback post.")
            try:
                articles.append(self.article_gen.generate_no_news_post())
            except Exception as exc:                                  # noqa: BLE001
                logger.exception(f"Even the fallback post failed: {exc}")
        else:
            if settings.article_mode == "digest":
                try:
                    articles.append(self.digest_gen.generate_digest(filtered))
                except Exception as exc:                              # noqa: BLE001
                    logger.exception(f"Digest generation failed: {exc}")
            else:
                for item in filtered:
                    try:
                        articles.append(self.article_gen.generate(item))
                    except Exception as exc:                          # noqa: BLE001
                        logger.exception(
                            f"Article generation failed for "
                            f"'{item.get('title','?')[:60]}': {exc}"
                        )

        # 4) Publish
        for article in articles:
            try:
                self.local_publisher.write(article)
            except Exception as exc:                                  # noqa: BLE001
                logger.exception(f"Local publish failed for '{article.title}': {exc}")
            try:
                self.wp_publisher.publish(article)
            except Exception as exc:                                  # noqa: BLE001
                logger.exception(f"WordPress publish failed for '{article.title}': {exc}")

        elapsed = (datetime.utcnow() - run_start).total_seconds()
        logger.info(
            f"=== Daily run finished in {elapsed:.1f}s — "
            f"raw={len(raw_items)} kept={len(filtered)} "
            f"published={len(articles)} ==="
        )
        return articles

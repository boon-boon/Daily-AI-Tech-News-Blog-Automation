"""
Optional WordPress REST API publisher.

Uses an Application Password (Users -> Profile -> Application Passwords)
which is the recommended modern auth method (no XML-RPC required).
"""

from __future__ import annotations

import base64
from typing import Any, Dict, Optional

import httpx

from config import settings
from src.generators.article_generator import GeneratedArticle
from src.utils.html_renderer import render_markdown_to_html
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WordPressPublisher:
    """POST articles to a WordPress site via the REST API."""

    def __init__(self) -> None:
        self.enabled = settings.publish_to_wordpress
        self.base = settings.wordpress_url
        self.username = settings.wordpress_username
        self.password = settings.wordpress_app_password
        self.default_status = settings.wordpress_default_status
        self.default_category = settings.wordpress_default_category_id

        if self.enabled:
            if not all([self.base, self.username, self.password]):
                logger.warning(
                    "WordPress publishing enabled but credentials are incomplete; "
                    "publishing will be skipped."
                )
                self.enabled = False

    def _auth_header(self) -> Dict[str, str]:
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    def publish(self, article: GeneratedArticle) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            logger.info("WordPress publishing disabled; skipping")
            return None

        # Render the body to HTML for WordPress
        # Include TLDR, body, FAQ, sources, JSON-LD scripts
        from src.publishers.local import LocalPublisher
        body_md = LocalPublisher()._build_markdown_body(article)
        body_html = render_markdown_to_html(body_md)

        # Append JSON-LD blocks for SEO
        if article.structured_data.get("blog_posting") or article.structured_data.get("faq_page"):
            import json
            for key in ("blog_posting", "faq_page"):
                schema = article.structured_data.get(key)
                if schema:
                    body_html += (
                        f'\n<script type="application/ld+json">'
                        f'{json.dumps(schema, ensure_ascii=False)}'
                        f'</script>'
                    )

        payload: Dict[str, Any] = {
            "title": article.title,
            "slug": article.slug,
            "content": body_html,
            "excerpt": article.meta_description,
            "status": self.default_status,
            "meta": {
                "_yoast_wpseo_metadesc": article.meta_description,
                "_yoast_wpseo_focuskw": (article.tags or [""])[0],
            },
        }
        if self.default_category:
            try:
                payload["categories"] = [int(self.default_category)]
            except ValueError:
                pass

        url = f"{self.base}/wp-json/wp/v2/posts"
        try:
            resp = httpx.post(
                url,
                json=payload,
                headers=self._auth_header(),
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Published to WordPress: {data.get('link', '')}")
            return data
        except Exception as exc:                                       # noqa: BLE001
            logger.exception(f"WordPress publish failed: {exc}")
            return None

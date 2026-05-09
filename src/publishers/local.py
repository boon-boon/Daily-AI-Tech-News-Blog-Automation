"""
Local file publisher.

Each generated article is written out as three files in `output/`:
  * `markdown/<date>-<slug>.md` – Hugo/Hexo-compatible Markdown with
                                  YAML front matter
  * `html/<date>-<slug>.html`   – Standalone HTML5 document with meta
                                  tags and JSON-LD structured data
  * `metadata/<date>-<slug>.json` – Full machine-readable metadata blob
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml

from config import settings
from src.generators.article_generator import GeneratedArticle
from src.utils.html_renderer import (
    build_full_html_document,
    render_markdown_to_html,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LocalPublisher:
    """Persist articles to disk in three formats."""

    def __init__(self) -> None:
        settings.ensure_dirs()
        self.markdown_dir: Path = settings.markdown_dir
        self.html_dir: Path = settings.html_dir
        self.metadata_dir: Path = settings.metadata_dir

    # ------------------------------------------------------------------

    @staticmethod
    def _filename(article: GeneratedArticle, ext: str) -> str:
        date_part = article.published_at.strftime("%Y-%m-%d")
        return f"{date_part}-{article.slug}.{ext}"

    def _build_front_matter(self, article: GeneratedArticle) -> str:
        fm = {
            "title": article.title,
            "slug": article.slug,
            "permalink": article.permalink,
            "date": article.published_at.isoformat(),
            "description": article.meta_description,
            "category": article.category,
            "tags": article.tags,
            "author": settings.blog_author,
            "canonical_url": article.canonical_url,
            "tldr": article.tldr,
            "sources": article.sources,
            "image_suggestions": article.image_suggestions,
            "schema": article.structured_data,
        }
        return yaml.safe_dump(
            fm, sort_keys=False, allow_unicode=True, default_flow_style=False
        )

    def _build_markdown_body(self, article: GeneratedArticle) -> str:
        """Compose the full Markdown body (TL;DR + body + FAQ + sources)."""
        parts: List[str] = []
        parts.append(f"# {article.title}\n")
        if article.tldr:
            parts.append(f"> **TL;DR** — {article.tldr}\n")
        parts.append(article.body_markdown.strip() + "\n")

        if article.faq:
            parts.append("## Frequently Asked Questions\n")
            for q in article.faq:
                parts.append(f"### {q.get('question', '').strip()}\n")
                parts.append(f"{q.get('answer', '').strip()}\n")

        if article.sources:
            parts.append("## Sources\n")
            for s in article.sources:
                label = s.get("label", "Source").strip()
                url = s.get("url", "").strip()
                if url:
                    parts.append(f"- [{label}]({url})")
            parts.append("")

        if article.image_suggestions:
            parts.append("<!-- Suggested image placements:")
            for img in article.image_suggestions:
                parts.append(
                    f"  - {img.get('placement','')} :: "
                    f"{img.get('description','')} (alt='{img.get('alt_text','')}')"
                )
            parts.append("-->")
        return "\n".join(parts)

    # ------------------------------------------------------------------

    def write(self, article: GeneratedArticle) -> Dict[str, str]:
        """Write all three formats. Returns the file paths."""
        front_matter = self._build_front_matter(article)
        body = self._build_markdown_body(article)

        # ---- Markdown ----
        md_path = self.markdown_dir / self._filename(article, "md")
        md_content = f"---\n{front_matter}---\n\n{body}\n"
        md_path.write_text(md_content, encoding="utf-8")

        # ---- HTML ----
        body_html = render_markdown_to_html(body)
        structured_blocks = []
        if article.structured_data.get("blog_posting"):
            structured_blocks.append(article.structured_data["blog_posting"])
        if article.structured_data.get("faq_page"):
            structured_blocks.append(article.structured_data["faq_page"])

        full_html = build_full_html_document(
            title=article.title,
            meta_description=article.meta_description,
            canonical_url=article.canonical_url,
            language=settings.blog_language,
            body_html=body_html,
            structured_data=structured_blocks,
            tags=article.tags,
            published_iso=article.published_at.isoformat(),
            author=settings.blog_author,
        )
        html_path = self.html_dir / self._filename(article, "html")
        html_path.write_text(full_html, encoding="utf-8")

        # ---- Metadata ----
        meta_path = self.metadata_dir / self._filename(article, "json")
        meta_path.write_text(
            json.dumps(article.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info(f"Wrote article '{article.title}' to disk")
        return {
            "markdown": str(md_path),
            "html": str(html_path),
            "metadata": str(meta_path),
        }

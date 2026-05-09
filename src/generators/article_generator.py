"""
Generate one SEO+GEO-optimised blog article per filtered news item.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import settings
from src.processors.llm_client import LLMClient
from src.utils.logger import get_logger
from src.utils.slugify import build_permalink, slugify_title

from .prompts import build_article_system_prompt, build_no_news_system_prompt

logger = get_logger(__name__)


@dataclass
class GeneratedArticle:
    """Final article ready to be published or stored."""

    title: str
    slug: str
    permalink: str
    meta_description: str
    category: str
    tags: List[str]
    tldr: str
    body_markdown: str
    faq: List[Dict[str, str]] = field(default_factory=list)
    image_suggestions: List[Dict[str, str]] = field(default_factory=list)
    sources: List[Dict[str, str]] = field(default_factory=list)
    structured_data: Dict[str, Any] = field(default_factory=dict)
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    canonical_url: str = ""
    raw_llm_payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "permalink": self.permalink,
            "canonical_url": self.canonical_url,
            "meta_description": self.meta_description,
            "category": self.category,
            "tags": self.tags,
            "tldr": self.tldr,
            "body_markdown": self.body_markdown,
            "faq": self.faq,
            "image_suggestions": self.image_suggestions,
            "sources": self.sources,
            "structured_data": self.structured_data,
            "published_at": self.published_at.isoformat(),
        }


class ArticleGenerator:
    """Wraps the LLM call that turns a single news item into a full article."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.system_prompt = build_article_system_prompt()
        self.no_news_system_prompt = build_no_news_system_prompt()

    # ------------------------------------------------------------------

    def _build_user_prompt(self, item: Dict[str, Any]) -> str:
        """Inject one news item into the user prompt as JSON."""
        return (
            "Write a complete article for the following news item. "
            "Strictly follow OUTPUT_FORMAT. Return ONLY the JSON object.\n\n"
            f"NEWS_ITEM = {json.dumps(item, ensure_ascii=False)}"
        )

    def _post_process(
        self,
        payload: Dict[str, Any],
        original_item: Optional[Dict[str, Any]] = None,
    ) -> GeneratedArticle:
        """Convert the LLM JSON payload into a `GeneratedArticle`."""
        title = payload.get("title", "Untitled").strip()
        slug = (payload.get("slug") or slugify_title(title)).strip()
        permalink = build_permalink(title)
        canonical = f"{settings.blog_base_url}{permalink}"
        published_at = datetime.now(timezone.utc)

        # Make sure the structured data carries publish info even if the LLM
        # forgot some fields.
        structured = payload.get("structured_data") or {}
        bp = structured.get("blog_posting") or {}
        bp.setdefault("@context", "https://schema.org")
        bp.setdefault("@type", "BlogPosting")
        bp.setdefault("headline", title)
        bp.setdefault("description", payload.get("meta_description", ""))
        bp.setdefault("datePublished", published_at.isoformat())
        bp.setdefault("dateModified", published_at.isoformat())
        bp.setdefault("author",
                      {"@type": "Organization", "name": settings.blog_author})
        bp.setdefault("publisher",
                      {"@type": "Organization", "name": settings.blog_name})
        bp.setdefault("mainEntityOfPage", canonical)
        bp.setdefault("articleSection",
                      payload.get("category", settings.blog_default_category))
        bp.setdefault("keywords", ", ".join(payload.get("tags", [])))
        structured["blog_posting"] = bp

        # Make sure FAQ schema reflects the FAQ list
        if payload.get("faq"):
            structured["faq_page"] = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q.get("question", ""),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": q.get("answer", ""),
                        },
                    }
                    for q in payload["faq"]
                ],
            }

        # Make sure the source URL of the original item appears in sources.
        sources = payload.get("sources", []) or []
        if original_item and original_item.get("url"):
            if not any(s.get("url") == original_item["url"] for s in sources):
                sources.append({
                    "label": original_item.get("source", "Source"),
                    "url": original_item["url"],
                })

        return GeneratedArticle(
            title=title,
            slug=slug,
            permalink=permalink,
            canonical_url=canonical,
            meta_description=payload.get("meta_description", "")[:200],
            category=payload.get("category", settings.blog_default_category),
            tags=payload.get("tags", []),
            tldr=payload.get("tldr", ""),
            body_markdown=payload.get("body_markdown", ""),
            faq=payload.get("faq", []),
            image_suggestions=payload.get("image_suggestions", []),
            sources=sources,
            structured_data=structured,
            published_at=published_at,
            raw_llm_payload=payload,
        )

    # ------------------------------------------------------------------

    def generate(self, item: Dict[str, Any]) -> GeneratedArticle:
        """Generate a single article from a filtered news item dict."""
        logger.info(f"Generating article for: {item.get('title', '')[:80]}")
        payload = self.llm.chat_json(
            system_prompt=self.system_prompt,
            user_prompt=self._build_user_prompt(item),
        )
        return self._post_process(payload, original_item=item)

    def generate_no_news_post(self) -> GeneratedArticle:
        """Generate the fallback 'no major updates today' post."""
        logger.warning("Generating 'no major updates today' fallback article")
        user_prompt = (
            "Write today's 'no major updates' notice. Strictly follow "
            "OUTPUT_FORMAT. Return ONLY the JSON object."
        )
        payload = self.llm.chat_json(
            system_prompt=self.no_news_system_prompt,
            user_prompt=user_prompt,
        )
        return self._post_process(payload, original_item=None)

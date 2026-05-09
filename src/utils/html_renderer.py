"""
Render Markdown -> HTML and assemble the final standalone HTML document
including <head> meta tags and JSON-LD structured data.
"""

from __future__ import annotations

import html
import json
from typing import Any, Dict

import markdown as md_lib

_MD_EXTENSIONS = [
    "extra",        # tables, fenced_code, footnotes, attr_list, etc.
    "sane_lists",
    "toc",
    "smarty",
]


def render_markdown_to_html(markdown_text: str) -> str:
    """Render Markdown body content to HTML."""
    return md_lib.markdown(markdown_text, extensions=_MD_EXTENSIONS, output_format="html5")


def _escape(value: str) -> str:
    return html.escape(value or "", quote=True)


def _jsonld_block(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{payload}\n</script>'


def build_full_html_document(
    *,
    title: str,
    meta_description: str,
    canonical_url: str,
    language: str,
    body_html: str,
    structured_data: list[Dict[str, Any]] | None = None,
    tags: list[str] | None = None,
    published_iso: str = "",
    author: str = "",
) -> str:
    """Assemble a complete, standalone HTML5 document."""
    structured_data = structured_data or []
    tags = tags or []
    meta_keywords = ", ".join(tags)
    jsonld = "\n".join(_jsonld_block(d) for d in structured_data)

    return f"""<!DOCTYPE html>
<html lang="{_escape(language)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)}</title>
  <meta name="description" content="{_escape(meta_description)}">
  <meta name="keywords" content="{_escape(meta_keywords)}">
  <meta name="author" content="{_escape(author)}">
  <link rel="canonical" href="{_escape(canonical_url)}">

  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{_escape(title)}">
  <meta property="og:description" content="{_escape(meta_description)}">
  <meta property="og:url" content="{_escape(canonical_url)}">
  <meta property="article:published_time" content="{_escape(published_iso)}">

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{_escape(title)}">
  <meta name="twitter:description" content="{_escape(meta_description)}">

  {jsonld}
</head>
<body>
<article>
{body_html}
</article>
</body>
</html>
"""

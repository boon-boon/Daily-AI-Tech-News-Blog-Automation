#!/usr/bin/env python3
"""
covers.py
─────────
Generates a cover image (SVG) for each article from data the article
already carries — its category and its `thumbnail` gradient colors.

Why generated rather than hand-picked: the scheduled task writes 5-8 new
articles every morning, so hand-sourcing art doesn't scale. These covers
are deterministic, dependency-free, tiny (~1 KB), and sharp at any size.

    from covers import build_cover, cover_rel_path

    build_cover(article, out_dir)      # writes <out_dir>/<slug>.svg
    cover_rel_path(article)            # "assets/img/covers/<slug>.svg"

Design note — the composition is CENTERED and carries no headline on
purpose. The UI renders these into containers of several different aspect
ratios with `object-fit: cover`, so anything near an edge gets cropped
away; and on the homepage the headline already sits right next to the
image, so repeating it there was redundant. What's left is a branded,
crop-safe graphic that reads correctly at any ratio.

The path is deliberately RELATIVE (no leading slash) so it resolves
against the Angular app's <base href>, which is "/<repo-name>/" on a
GitHub Pages project site.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any, Dict

# 1200x630 is the standard Open Graph ratio, so the same file works as an
# on-page cover and as a social/link-preview image.
WIDTH = 1200
HEIGHT = 630

WORDMARK = "TechPulse."
DEFAULT_GRADIENT = {"c1": "#7c5cff", "c2": "#00d4ff"}

SANS = "system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

CENTER_X = WIDTH // 2
WORDMARK_Y = 300
RULE_Y = 336
CATEGORY_Y = 384


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _valid_color(value: Any, fallback: str) -> str:
    """Only let plain hex colors through — these get interpolated into SVG."""
    if isinstance(value, str) and re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", value.strip()):
        return value.strip()
    return fallback


def render_cover_svg(article: Dict[str, Any]) -> str:
    """Return the full SVG document for one article's cover."""
    title = article.get("title", "") or "Untitled"
    category = (article.get("category", "") or "").upper()

    thumb = article.get("thumbnail") or DEFAULT_GRADIENT
    c1 = _valid_color(thumb.get("c1"), DEFAULT_GRADIENT["c1"])
    c2 = _valid_color(thumb.get("c2"), DEFAULT_GRADIENT["c2"])

    category_row = ""
    if category:
        category_row = (
            f'  <text x="{CENTER_X}" y="{CATEGORY_Y}" text-anchor="middle" font-family="{SANS}" '
            f'font-size="26" font-weight="600" letter-spacing="3" fill="#ffffff" fill-opacity="0.85">'
            f"{_esc(category)}</text>"
        )

    # aria-label carries the headline, so the cover isn't an unlabelled image
    # for anyone reaching it through a screen reader.
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" \
viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{_esc(title)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/>
      <stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.76" cy="0.16" r="0.7">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.26"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="scrim" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000000" stop-opacity="0.06"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0.34"/>
    </linearGradient>
    <!-- Full-bleed dot texture: reads as intentional at every crop. -->
    <pattern id="dots" width="44" height="44" patternUnits="userSpaceOnUse">
      <circle cx="3" cy="3" r="2.5" fill="#ffffff" fill-opacity="0.11"/>
    </pattern>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#dots)"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#glow)"/>
  <!-- The scrim keeps white type legible over light gradients too. -->
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#scrim)"/>

  <text x="{CENTER_X}" y="{WORDMARK_Y}" text-anchor="middle" font-family="{SANS}" font-size="62" \
font-weight="700" fill="#ffffff" fill-opacity="0.97">{_esc(WORDMARK)}</text>

  <rect x="{CENTER_X - 40}" y="{RULE_Y}" width="80" height="3" rx="1.5" fill="#ffffff" fill-opacity="0.55"/>

{category_row}
</svg>
"""


# ---------- public api -------------------------------------------------------

def cover_filename(article: Dict[str, Any]) -> str:
    return f"{article.get('slug', 'untitled')}.svg"


def cover_rel_path(article: Dict[str, Any]) -> str:
    """Path as referenced from the web app — relative, so <base href> applies."""
    return f"assets/img/covers/{cover_filename(article)}"


def build_cover(article: Dict[str, Any], out_dir: Path, overwrite: bool = True) -> Path:
    """Write the article's cover SVG into out_dir. Returns the written path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / cover_filename(article)
    if out_file.exists() and not overwrite:
        return out_file
    out_file.write_text(render_cover_svg(article), encoding="utf-8")
    return out_file

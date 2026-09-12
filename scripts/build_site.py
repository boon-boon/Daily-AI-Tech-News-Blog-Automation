#!/usr/bin/env python3
"""
build_site.py
─────────────
Reads per-article JSON files written by the scheduled Claude task and
produces the static website:

  data/articles/<YYYY-MM-DD>/<slug>.json   ──┐
                                              │
                                              ▼
  web/posts/<YYYY-MM-DD>/<slug>.html        (one per article)
  data/daily.json                           (homepage data)

Run it after every scheduled task run:

    python3 scripts/build_site.py
    python3 scripts/build_site.py --date 2026-06-11    # rebuild a specific day
    python3 scripts/build_site.py --all                # rebuild all days

Has zero dependencies beyond `markdown` and `pyyaml`, both already in
requirements.txt. No LLM call, no network — pure templating.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import markdown as md_lib
except ImportError:
    print("ERROR: install 'markdown' first → pip install markdown pyyaml", file=sys.stderr)
    sys.exit(1)


from covers import build_cover, cover_rel_path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "data" / "articles"
POSTS_DIR    = ROOT / "web" / "posts"
TEMPLATE     = ROOT / "web" / "article.html"

# Generated article covers. They land in the Angular app's static assets so
# `ng build` copies them into the published site with no extra step.
# See scripts/covers.py.
COVERS_DIR = ROOT / "angular-web" / "public" / "assets" / "img" / "covers"

# Absolute origin, used only for og:image — social scrapers reject relative
# URLs. On-page image paths stay relative so the app's <base href> applies.
SITE_BASE = "https://boon-boon.github.io/Daily-AI-Tech-News-Blog-Automation"

# daily.json is written to TWO locations:
#   - data/daily.json        → source of truth committed to the repo root
#   - web/data/daily.json    → published copy GitHub Pages serves at /data/daily.json
DAILY_JSON         = ROOT / "data" / "daily.json"
DAILY_JSON_WEB_OUT = ROOT / "web" / "data" / "daily.json"

BLOG_NAME    = "Daily Tech Pulse"
BLOG_AUTHOR  = "Daily Tech Pulse Editorial"
BLOG_BASE    = ""          # leave empty for relative URLs, set in CI to absolute


# ---------- helpers ----------------------------------------------------------

def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def render_markdown(text: str) -> str:
    return md_lib.markdown(text or "", extensions=["extra", "sane_lists", "toc", "smarty"], output_format="html5")


def reading_time(text: str) -> int:
    return max(1, round(len((text or "").split()) / 220))


def category_slug(category: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (category or "").lower()).strip("-")


def render_faq_html(faq: List[Dict[str, str]]) -> str:
    parts = []
    for q in faq or []:
        parts.append(
            f"<details>\n"
            f"  <summary>{esc(q.get('question',''))}</summary>\n"
            f"  <p>{esc(q.get('answer',''))}</p>\n"
            f"</details>"
        )
    return "\n".join(parts)


def render_sources_html(sources: List[Dict[str, str]]) -> str:
    return "\n".join(
        f'  <li><a href="{esc(s.get("url",""))}" target="_blank" rel="noopener">{esc(s.get("label","Source"))}</a></li>'
        for s in (sources or [])
    )


def render_tags_html(tags: List[str]) -> str:
    return "\n".join(f'  <span class="chip">{esc(t)}</span>' for t in (tags or []))


def build_structured_data(article: Dict[str, Any], canonical_url: str) -> str:
    """Two JSON-LD blocks: BlogPosting + FAQPage."""
    blog_posting = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": article["title"],
        "description": article.get("meta_description", ""),
        "datePublished": article["published_at"],
        "dateModified": article["published_at"],
        "author": {"@type": "Organization", "name": BLOG_AUTHOR},
        "publisher": {"@type": "Organization", "name": BLOG_NAME},
        "mainEntityOfPage": canonical_url,
        "articleSection": article.get("category", ""),
        "keywords": ", ".join(article.get("tags", [])),
    }
    blocks = [f'<script type="application/ld+json">\n{json.dumps(blog_posting, indent=2)}\n</script>']
    if article.get("faq"):
        faq_page = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q.get("question", ""),
                    "acceptedAnswer": {"@type": "Answer", "text": q.get("answer", "")},
                }
                for q in article["faq"]
            ],
        }
        blocks.append(f'<script type="application/ld+json">\n{json.dumps(faq_page, indent=2)}\n</script>')
    return "\n".join(blocks)


# ---------- core ------------------------------------------------------------

def render_article_page(article: Dict[str, Any], date: str) -> str:
    """Fill web/article.html template with article data and return the HTML."""
    template = TEMPLATE.read_text(encoding="utf-8")
    canonical_url = f"{BLOG_BASE}/posts/{date}/{article['slug']}.html"
    published_iso = article["published_at"]
    try:
        published_human = datetime.fromisoformat(published_iso.replace("Z", "+00:00")).strftime("%B %d, %Y")
    except ValueError:
        published_human = published_iso

    replacements = {
        "{{ARTICLE_TITLE}}":     esc(article["title"]),
        "{{META_DESCRIPTION}}":  esc(article.get("meta_description", "")),
        "{{CANONICAL_URL}}":     esc(canonical_url),
        "{{OG_IMAGE}}":          esc(article.get("og_image", "/assets/img/og-default.svg")),
        "{{PUBLISHED_ISO}}":     esc(published_iso),
        "{{PUBLISHED_HUMAN}}":   esc(published_human),
        "{{CATEGORY}}":          esc(article.get("category", "")),
        "{{AUTHOR}}":            esc(BLOG_AUTHOR),
        "{{READING_TIME}}":      str(article.get("reading_time_min") or reading_time(article.get("body_markdown", ""))),
        "{{TLDR}}":              esc(article.get("tldr", "")),
        "{{BODY_HTML}}":         render_markdown(article.get("body_markdown", "")),
        "{{FAQ_HTML}}":          render_faq_html(article.get("faq", [])),
        "{{SOURCES_HTML}}":      render_sources_html(article.get("sources", [])),
        "{{TAGS_HTML}}":         render_tags_html(article.get("tags", [])),
        "{{JSON_LD_BLOCKS}}":    build_structured_data(article, canonical_url),
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    return template


def _running_total(previous_daily: Optional[Dict[str, Any]], date: str, count: int) -> int:
    """
    Lifetime article count, safe to recompute.

    daily.json always describes exactly one day, so its `date_iso` tells us
    whether this day has already been added to the total. Rebuilding the same
    day returns the total unchanged; a new day adds that day's articles.
    """
    prev = previous_daily or {}
    prev_total = prev.get("stats", {}).get("articles_published_total", 0)
    if prev.get("date_iso") == date:
        return prev_total
    return prev_total + count


def render_daily_json(date: str, articles: List[Dict[str, Any]], previous_daily: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build the homepage data file from one day's articles."""
    if not articles:
        return previous_daily or {}

    # Featured = highest importance_score
    articles_sorted = sorted(articles, key=lambda a: a.get("importance_score", 0), reverse=True)
    featured_src = articles_sorted[0]
    latest_src   = articles_sorted[1:]

    def _card(a: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id":               a["slug"],
            "title":            a["title"],
            "category":         a.get("category", ""),
            "excerpt":          (a.get("meta_description") or a.get("tldr") or "")[:240],
            "tldr":             a.get("tldr", ""),
            "permalink":        f"/posts/{date}/{a['slug']}.html",
            "published_at":     a["published_at"],
            "reading_time_min": a.get("reading_time_min") or reading_time(a.get("body_markdown", "")),
            "tags":             a.get("tags", []),
            "sources":          a.get("sources", []),
            "thumbnail":        a.get("thumbnail", {"c1": "#7c5cff", "c2": "#00d4ff"}),
            # Generated cover. The UI still keeps `thumbnail` as the fallback
            # gradient if the image ever fails to load.
            "image":            cover_rel_path(a),
        }

    # Per-category counts for the homepage cards
    cats_default = (previous_daily or {}).get("categories") or [
        {"slug": "ai-ml",         "name": "AI & ML",         "color_from": "#7c5cff", "color_to": "#00d4ff",
         "description": "Models, research, OpenAI, Anthropic, Google, Hugging Face."},
        {"slug": "startups",      "name": "Startups",        "color_from": "#22d3ee", "color_to": "#10b981",
         "description": "Funding rounds, launches, and founders moving the industry."},
        {"slug": "programming",   "name": "Programming",     "color_from": "#f59e0b", "color_to": "#ef4444",
         "description": "Language and framework releases."},
        {"slug": "open-source",   "name": "Open Source",     "color_from": "#06b6d4", "color_to": "#8b5cf6",
         "description": "GitHub trending and beloved projects."},
        {"slug": "cybersecurity", "name": "Cybersecurity",   "color_from": "#ef4444", "color_to": "#f59e0b",
         "description": "CVEs, breaches, and defensive techniques."},
        {"slug": "gadgets",       "name": "Gadgets",         "color_from": "#10b981", "color_to": "#06b6d4",
         "description": "Hardware reviews and benchmarks."},
    ]
    counts: Dict[str, int] = {}
    for a in articles:
        counts[category_slug(a.get("category", ""))] = counts.get(category_slug(a.get("category", "")), 0) + 1
    for cat in cats_default:
        cat["article_count_today"] = counts.get(cat["slug"], 0)
        # Try matching by raw category name too (e.g. "AI Models" → ai-ml bucket)
        if cat["slug"] == "ai-ml":
            cat["article_count_today"] += counts.get("ai-models", 0) + counts.get("ai-ml-research", 0)
        if cat["slug"] == "programming":
            cat["article_count_today"] += counts.get("framework-library-releases", 0)

    return {
        "version":      "1.0",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "date_iso":     date,
        "date_human":   datetime.fromisoformat(date).strftime("%B %d, %Y"),
        "timezone":     "Asia/Kuala_Lumpur",
        "stats": {
            # Idempotent: rebuilding a day that's already counted must not
            # inflate the running total (the build gets re-run often — from
            # run.bat, from CI, or by the scheduled task retrying).
            "articles_published_total": _running_total(previous_daily, date, len(articles)),
            "sources_monitored": 52,
            "daily_update_time": "08:00 MYT",
            "automation_percent": 100,
        },
        "featured":        _card(featured_src),
        "latest":          [_card(a) for a in latest_src],
        "github_trending": (previous_daily or {}).get("github_trending", []),
        "categories":      cats_default,
        "community_pulse": (previous_daily or {}).get("community_pulse"),
    }


def build_day(date: str) -> int:
    """Render every article in data/articles/<date>/ and refresh daily.json."""
    src_dir = ARTICLES_DIR / date
    if not src_dir.is_dir():
        print(f"[skip] no articles for {date}", file=sys.stderr)
        return 0

    # The legacy static `web/` frontend is optional — the Angular app is the
    # published site now. If its template is gone, skip that half of the build
    # rather than failing the whole run (daily.json and covers still matter).
    render_legacy_html = TEMPLATE.exists()
    if not render_legacy_html:
        print(f"[skip] {TEMPLATE.relative_to(ROOT)} not found — skipping legacy web/ pages")
    else:
        dst_dir = POSTS_DIR / date
        dst_dir.mkdir(parents=True, exist_ok=True)

    articles: List[Dict[str, Any]] = []
    for jf in sorted(src_dir.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[error] {jf}: {e}", file=sys.stderr)
            continue
        articles.append(data)

        # 1. Cover image, generated from the article's own title/category/colors.
        cover_file = build_cover(data, COVERS_DIR)
        print(f"[ok] {cover_file.relative_to(ROOT)}")

        # 2. Backfill og_image on the source JSON so article pages get a
        #    social/link-preview image. Only set when absent, so a
        #    hand-picked image is never overwritten.
        if not data.get("og_image"):
            data["og_image"] = f"{SITE_BASE}/{cover_rel_path(data)}"
            jf.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[ok] og_image set on {jf.relative_to(ROOT)}")

        # 3. Legacy static HTML page, when the template still exists.
        if render_legacy_html:
            html_out = render_article_page(data, date)
            out_file = POSTS_DIR / date / f"{data['slug']}.html"
            out_file.write_text(html_out, encoding="utf-8")
            print(f"[ok] {out_file.relative_to(ROOT)}")

    # Refresh daily.json for the latest date only
    latest_date = max(d.name for d in ARTICLES_DIR.iterdir() if d.is_dir())
    if date == latest_date:
        previous = json.loads(DAILY_JSON.read_text()) if DAILY_JSON.exists() else None
        payload = json.dumps(
            render_daily_json(date, articles, previous),
            indent=2,
            ensure_ascii=False,
        )
        # Write to both the source-of-truth location and the publishable copy
        # so GitHub Pages can serve /data/daily.json from the /web folder.
        DAILY_JSON.write_text(payload, encoding="utf-8")
        DAILY_JSON_WEB_OUT.parent.mkdir(parents=True, exist_ok=True)
        DAILY_JSON_WEB_OUT.write_text(payload, encoding="utf-8")
        print(f"[ok] data/daily.json + web/data/daily.json updated for {date}")

    return len(articles)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", help="Build a single date (YYYY-MM-DD).")
    p.add_argument("--all",  action="store_true", help="Rebuild every date folder.")
    args = p.parse_args()

    if args.all:
        dates = sorted(d.name for d in ARTICLES_DIR.iterdir() if d.is_dir())
    elif args.date:
        dates = [args.date]
    else:
        # default: today (in local time)
        dates = [datetime.now().astimezone().strftime("%Y-%m-%d")]
        if not (ARTICLES_DIR / dates[0]).is_dir():
            # fall back to latest available date
            existing = sorted(d.name for d in ARTICLES_DIR.iterdir() if d.is_dir())
            if existing:
                dates = [existing[-1]]
            else:
                print("No articles found anywhere under data/articles/", file=sys.stderr)
                return 1

    total = sum(build_day(d) for d in dates)
    print(f"\nBuilt {total} article page(s) across {len(dates)} day(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

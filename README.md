# Daily Tech Pulse

A fully automated daily AI / tech news blog. A **Claude scheduled task** wakes up every morning at 08:00 Malaysia time, fetches the last 24 hours of news from 15+ sources, writes 5–8 SEO + GEO optimized articles, saves them as JSON, and runs a small Python build script that renders the static website. Everything ships through `git push` to GitHub Pages.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  Claude scheduled task  (Cowork — daily at 08:00 MYT)       │
│  ──────────────────────────────────────────────             │
│  Reads prompts/daily_news_brief.md, web_fetch's HN +        │
│  GitHub + RSS feeds, filters / dedupes / scores, writes a   │
│  full article per story, saves JSON files.                  │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
            data/articles/<YYYY-MM-DD>/<slug>.json
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│  scripts/build_site.py                                      │
│  ──────────────────────                                     │
│  For each article JSON:                                     │
│    fills web/article.html template                          │
│    writes web/posts/<date>/<slug>.html                      │
│    refreshes data/daily.json for the homepage               │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
                  git add + git push
                       │
                       ▼
              GitHub Pages serves /
              GitHub Pages serves /posts/<date>/<slug>.html
              data-loader.js fetches /data/daily.json
```

The architecture has three pieces and one rule:

- **Claude does the thinking** (fetch, filter, write) — scheduled task in Cowork.
- **Python does the templating** (`scripts/build_site.py`) — pure string-replace, no LLM call.
- **GitHub serves the hosting** — static files, no server.
- **Rule**: the JSON files in `data/articles/` are the source of truth. Everything else can be regenerated from them.

## Folder structure

```
.
├── data/
│   ├── daily.json                ← homepage data (auto-refreshed)
│   ├── schema.json               ← JSON Schema for daily.json
│   ├── articles/
│   │   ├── schema.json           ← JSON Schema for each article
│   │   └── <YYYY-MM-DD>/
│   │       └── <slug>.json       ← one per article — Claude writes these
│   └── README.md
├── web/
│   ├── index.html                ← homepage (hydrated from daily.json)
│   ├── article.html              ← per-article template (filled by build_site)
│   ├── 404.html
│   ├── robots.txt
│   ├── posts/
│   │   └── <YYYY-MM-DD>/
│   │       └── <slug>.html       ← generated per-article pages
│   └── assets/
│       ├── css/main.css
│       ├── css/article.css
│       ├── js/main.js
│       └── js/data-loader.js
├── scripts/
│   └── build_site.py             ← the only Python code that runs
├── prompts/
│   └── daily_news_brief.md       ← full instructions for the scheduled task
├── requirements.txt              ← just `markdown`
└── README.md
```

## Quick start

```bash
# 1) Install the one Python dependency
pip install -r requirements.txt

# 2) Run the build script against the sample article
python3 scripts/build_site.py
# → writes web/posts/2026-06-11/claude-fable-5-launch.html

# 3) Preview the site locally
cd web && python3 -m http.server 8080
# open http://localhost:8080
```

## The daily scheduled task

The task `daily-tech-news-blog` was created in Cowork's Scheduled section. It runs **at 08:00 every day** (local time).

To inspect or edit it:

- **List**: see all scheduled tasks via Cowork's sidebar → Scheduled.
- **Source of truth**: `prompts/daily_news_brief.md` — the full self-contained spec including SEO + GEO rules, source list, and JSON shape.
- **Manual run**: open the task in Cowork and click **Run now**. The first manual run is recommended so you can pre-approve the `web_fetch`, `Write`, and `Bash` tools.

The task will:

1. Determine today's date in Asia/Kuala_Lumpur.
2. Fetch news from Hacker News, GitHub Trending + Releases, and 9 official RSS feeds (Angular, React, Python, Node, OpenAI, Google AI, Hugging Face, Anthropic, TechCrunch).
3. Filter, dedupe, categorize, importance-score; keep the top 5–8 stories.
4. Write a full SEO + GEO article per story as `data/articles/<date>/<slug>.json`.
5. Run `python3 scripts/build_site.py` to render HTML and refresh `data/daily.json`.
6. `git add` + `git commit` + `git push` (if the repo has a remote).
7. Report back in chat with the day's titles and the featured pick.

## Deploying to GitHub Pages

```bash
git init
git add .
git commit -m "Initial site"

# Create a public repo and push (requires gh CLI)
gh repo create daily-tech-pulse --public --source=. --remote=origin --push

# In the repo on GitHub:
#   Settings → Pages → Source: "Deploy from a branch"
#                      Branch: main, Folder: /web
```

Update `BLOG_BASE` in `scripts/build_site.py` (currently empty for relative URLs) to your published site URL so canonical links resolve correctly:

```python
BLOG_BASE = "https://yourname.github.io"
```

## Adding new sources

Edit `prompts/daily_news_brief.md`. The scheduled task reads it at the start of each run, so changes take effect on the next 08:00 trigger — no code change needed.

## How the website renders

- `web/index.html` ships as static HTML for instant first paint.
- On load, `assets/js/data-loader.js` fetches `/data/daily.json` and re-renders the featured card, latest grid, GitHub trending, categories, and community-pulse sections from the fresh data.
- Each article page (`web/posts/<date>/<slug>.html`) is fully static and SEO-ready — JSON-LD `BlogPosting` + `FAQPage` baked in, no JS required to read.

## Why a single JSON file per article?

- **Decoupled**: Claude could write them, you could write them by hand, or a future replacement could generate them — as long as they match `data/articles/schema.json`, the website renders.
- **Versioned by date folder**: each day's output is its own folder. Easy to roll back, regenerate, or archive.
- **No build step beyond `build_site.py`**: no Astro, no Next.js, no SSG framework. `python3 scripts/build_site.py` is the entire build.
- **Diffable**: every daily commit shows exactly which articles were added.

## Validating articles

```bash
python3 -c "
import json, jsonschema, pathlib
schema = json.load(open('data/articles/schema.json'))
for p in pathlib.Path('data/articles').rglob('*.json'):
    if p.name == 'schema.json': continue
    jsonschema.validate(json.load(open(p)), schema)
    print(f'✓ {p}')
"
```

Add `jsonschema` to the daily task's bash step if you want CI-style enforcement.

## License

MIT. Use, fork, modify.

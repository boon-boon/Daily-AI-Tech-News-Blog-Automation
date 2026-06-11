# Daily Tech Pulse — Web Frontend

Modern, dark-first, futuristic AI tech news blog. Vanilla HTML/CSS/JS. Zero build step. Deploys to GitHub Pages.

## Folder structure

```
web/
├── index.html             # Homepage — hydrated from /data/daily.json at runtime
├── article.html           # Per-article template — filled by scripts/build_site.py
├── 404.html
├── robots.txt
├── feed.xml               # Optional RSS feed
├── posts/
│   └── <YYYY-MM-DD>/
│       └── <slug>.html    # Generated article pages (one per article)
└── assets/
    ├── css/
    │   ├── main.css       # Design system + components
    │   └── article.css    # Long-form prose styles
    ├── js/
    │   ├── main.js        # Nav, scroll reveal, magnetic CTA, newsletter
    │   └── data-loader.js # Fetches /data/daily.json, hydrates homepage
    └── img/
```

## Local preview

```bash
cd web
python3 -m http.server 8080
# open http://localhost:8080
```

## How content gets here

The Claude scheduled task (defined in `prompts/daily_news_brief.md`) writes one JSON file per article to `data/articles/<YYYY-MM-DD>/<slug>.json`. Then `scripts/build_site.py` reads each one, fills `article.html` with its content, and writes `web/posts/<YYYY-MM-DD>/<slug>.html`. It also refreshes `data/daily.json` so the homepage shows the new featured story and card grid.

So:

```
data/articles/<date>/<slug>.json  ──►  scripts/build_site.py  ──►  web/posts/<date>/<slug>.html
                                                              └►  data/daily.json (homepage)
```

## Deploy to GitHub Pages

1. Push everything to a repo.
2. In **Settings → Pages**, set source to your branch, folder `/web`.
3. Update `BLOG_BASE` in `scripts/build_site.py` to your published URL (currently empty for relative URLs).

A simple cadence: the scheduled task runs at 08:00 MYT → writes JSON → runs `build_site.py` → `git push`. GitHub Pages picks it up automatically. No CI required.

## Customizing the design

- **Brand colors** — edit `--accent-blue`, `--accent-purple`, `--accent-cyan` in `:root` of `assets/css/main.css`.
- **Logo** — replace the inline `<svg>` in the `.nav__brand` block of `index.html` and `article.html`.
- **Hero copy** — edit the `<h1>` and `.hero__lede` in `index.html`.
- **Newsletter provider** — wire the `form.addEventListener('submit', ...)` block in `assets/js/main.js` to your provider's endpoint (Buttondown, Mailchimp, ConvertKit, etc.).

## Template tokens (filled by `build_site.py`)

For reference, here are the `{{TOKENS}}` in `article.html` and which article-JSON field fills each one:

| Token | From article JSON |
|---|---|
| `{{ARTICLE_TITLE}}` | `title` |
| `{{META_DESCRIPTION}}` | `meta_description` |
| `{{CANONICAL_URL}}` | derived: `<BLOG_BASE>/posts/<date>/<slug>.html` |
| `{{OG_IMAGE}}` | `og_image` (defaults to `/assets/img/og-default.svg`) |
| `{{PUBLISHED_ISO}}` | `published_at` |
| `{{PUBLISHED_HUMAN}}` | parsed from `published_at` |
| `{{CATEGORY}}` | `category` |
| `{{AUTHOR}}` | hardcoded constant `BLOG_AUTHOR` in `build_site.py` |
| `{{READING_TIME}}` | `reading_time_min` or computed from `body_markdown` |
| `{{TLDR}}` | `tldr` |
| `{{BODY_HTML}}` | `markdown.markdown(body_markdown)` |
| `{{FAQ_HTML}}` | `faq[]` rendered as `<details><summary>Q</summary><p>A</p></details>` |
| `{{SOURCES_HTML}}` | `sources[]` rendered as `<li><a>label</a></li>` |
| `{{TAGS_HTML}}` | `tags[]` rendered as `<span class="chip">tag</span>` |
| `{{JSON_LD_BLOCKS}}` | generated: `BlogPosting` + `FAQPage` JSON-LD `<script>` blocks |

## Performance

- ~30 KB CSS, ~10 KB JS (gzipped), ~13 KB per article page.
- No fonts blocking render — Inter loaded with `preconnect`.
- All animations respect `prefers-reduced-motion`.
- Sticky nav uses `position: sticky` (no JS jank).
- Article pages are 100% static — no JS required for content.

## Accessibility

- Semantic landmarks (`<header>`, `<nav>`, `<main>`, `<footer>`).
- ARIA labels on icon-only buttons and the mobile drawer.
- Visible focus rings (`:focus-visible`).
- Color-contrast tested against WCAG AA on the dark surface.
- `prefers-reduced-motion` shuts down the animated mesh and reveal animations.

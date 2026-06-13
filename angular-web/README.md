# TechPulse Daily — Angular Frontend

An Angular single-page app that renders the daily AI/developer news produced by
the Python automation backend in the parent folder. It reads the exact same data
contract as the existing static `web/` site (`daily.json` + per-article JSON), so
the two frontends are interchangeable.

## What it does

- **Home** (`/`) — featured story, daily stats, GitHub trending & releases,
  category grid, and a "community pulse" of top developer discussions.
- **Article** (`/posts/<YYYY-MM-DD>/<slug>`) — H1 title, TL;DR box, Markdown body
  rendered to HTML, image-placeholder cards with ALT text, FAQ accordion, and
  official source links.
- **Category** (`/category/<slug>`) — filtered view of the day's stories.
- **SEO/GEO** — per-page `<title>`, meta description, Open Graph + Twitter cards,
  canonical link, and JSON-LD (`TechArticle` + `FAQPage`) injected per article.

## Tech

Angular 22 (standalone components, signals, lazy-loaded routes), the
`@angular/build` application builder, and `marked` for Markdown. No backend of its
own — it's a static build that fetches JSON.

## Quick start

```bash
cd angular-web
npm install
npm run sync-data     # copy ../data into public/data (named by slug)
npm start             # dev server at http://localhost:4200
```

Production build:

```bash
npm run build         # outputs to dist/techpulse/browser
```

## Data flow

```
Python backend → data/daily.json
              → data/articles/<date>/<file>.json
                        │
            npm run sync-data   (scripts/sync-data.mjs)
                        ▼
   public/data/daily.json
   public/data/articles/<date>/<slug>.json   ← renamed to match the route
                        │
                  served as /data/*
                        ▼
        NewsService (HttpClient) → components
```

`sync-data` renames each article file to `<slug>.json` so the filename matches the
permalink route (`/posts/<date>/<slug>`). Re-run it after every backend refresh —
e.g. add it as the last step of the daily 8:00 AM job, or run the Angular build in
the same pipeline.

To point the SPA at data hosted elsewhere (CDN, the Python server, WordPress),
change `dataBase` in `src/app/services/news.service.ts`.

## SEO & SSR (important)

Angular renders **client-side**, so crawlers that don't execute JavaScript won't
see the meta tags or JSON-LD this app injects. Two ways to handle that:

1. **Rely on the static backend output** — the Python pipeline already emits fully
   crawlable HTML under `web/posts/`. Use that for Google SGE / AI crawlers and
   treat this Angular app as the richer interactive UI. (Default assumption.)
2. **Enable SSR / prerendering** for the Angular app:
   ```bash
   ng add @angular/ssr
   ```
   Because the route set is known at build time (one route per article), static
   **prerendering** is the best fit — it produces crawlable HTML per article with
   all meta/JSON-LD baked in, while keeping SPA navigation after first load.

## Project structure

```
angular-web/
├── angular.json, tsconfig*.json, package.json
├── scripts/sync-data.mjs          # copy + rename backend data → public/data
├── public/
│   ├── favicon.svg, robots.txt
│   ├── assets/img/og-default.svg
│   └── data/                       # generated (gitignored)
└── src/
    ├── index.html, main.ts, styles.css
    └── app/
        ├── app.component.ts        # shell: header + footer
        ├── app.config.ts           # router + HttpClient providers
        ├── app.routes.ts           # lazy routes
        ├── models/                 # Article, DailyData (mirror schema.json)
        ├── services/               # NewsService, SeoService
        ├── pipes/markdown.pipe.ts  # marked → sanitized HTML
        ├── utils/links.ts          # permalink → router commands
        └── pages/                  # home, article, category, not-found
```

## Deploy

The build output (`dist/techpulse/browser`) is fully static — host it on Netlify,
Vercel, GitHub Pages, S3/CloudFront, or any web server. Configure a SPA fallback
(serve `index.html` for unknown routes) so deep links work.

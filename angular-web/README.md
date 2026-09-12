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
`@angular/build` application builder with SSR + static prerendering
(`@angular/ssr`, `outputMode: "static"`), and `marked` for Markdown. No server
needed at runtime — the production build is fully static HTML.

## Quick start

```bash
cd angular-web
npm install
npm run sync-data     # copy ../data into public/data (named by slug)
npm start             # dev server at http://localhost:4200
```

Production build (must run `sync-data` first — the prerenderer reads
`public/data/articles` at build time to know every article route to bake):

```bash
npm run sync-data
npm run build         # outputs to dist/techpulse/browser — every route prerendered
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

## SEO & SSR

Every route is statically prerendered at build time (`outputMode: "static"` in
`angular.json` + `src/app/app.routes.server.ts`), so the shipped HTML already
has the real `<title>`, meta description, Open Graph tags, and JSON-LD
(`TechArticle` + `FAQPage`) baked in per page — no JavaScript required for a
crawler to see them. SPA navigation still kicks in for a human visitor after
first load.

`app.routes.server.ts` builds the list of routes to prerender:

- `/posts/:date/:slug` — enumerated from every file under
  `public/data/articles/<date>/*.json` at build time. This means
  **`npm run sync-data` must run before `npm run build`** — otherwise there's
  nothing to prerender and only the shell routes get built.
- `/category/:slug` — a fixed list of the six category slugs (kept in sync
  with `CATEGORY_KEYWORDS` in `category.component.ts`).
- everything else — prerendered as-is.

If you add a new category, update both `CATEGORY_SLUGS` in
`app.routes.server.ts` and `CATEGORY_KEYWORDS` in `category.component.ts`.

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
        ├── app.routes.ts           # lazy routes (browser)
        ├── app.routes.server.ts    # prerender plan (build-time route enumeration)
        ├── app.config.server.ts    # server providers
        ├── main.server.ts, server.ts   # SSR/prerender entry points
        ├── models/                 # Article, DailyData (mirror schema.json)
        ├── services/               # NewsService, SeoService
        ├── pipes/markdown.pipe.ts  # marked → sanitized HTML
        ├── utils/links.ts          # permalink → router commands
        └── pages/                  # home, article, category, not-found
```

## Deploy

The build output (`dist/techpulse/browser`) is fully static — every known route
is a real `index.html` file, so no SPA fallback is required for the routes that
exist. Host it on Netlify, Vercel, GitHub Pages, S3/CloudFront, or any web
server. A fallback to `index.html` for genuinely unknown paths is still a good
idea so client-side routing can show the 404 page instead of a raw 404 from the
host.

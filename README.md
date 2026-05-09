# Daily AI Tech News Blog Automation

A fully automated, production-ready system that:

1. **Wakes up every day at 08:00 Malaysia time** (configurable).
2. **Fetches the last 24 hours** of tech news from GitHub Trending & Releases, official framework blogs (Angular, React, Vue, Python, Node.js, TypeScript), AI/ML sources (OpenAI, Google AI, Hugging Face, DeepMind, Papers with Code), Hacker News, and NewsAPI.
3. **Filters, deduplicates, and categorises** with Google Gemini (default: `gemini-2.5-flash`, via Google AI Studio).
4. **Generates SEO + GEO optimised blog articles** (Markdown + HTML + JSON-LD structured data).
5. **Saves locally** in clean directory structure and **optionally publishes to WordPress** via REST API.
6. Falls back gracefully to a *"No major updates today"* post if all sources are quiet, never breaking the daily cadence.

---

## Project Structure

```
daily-tech-news-blog/
├── main.py                   # CLI entry: --once / --schedule / --fetch-only
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── README.md
├── config/
│   └── settings.py           # Typed env-driven settings
├── src/
│   ├── pipeline.py           # End-to-end orchestrator
│   ├── scheduler.py          # `schedule` library wrapper (TZ-aware)
│   ├── fetchers/             # One file per source, all return NewsItem
│   │   ├── base.py
│   │   ├── github_trending.py
│   │   ├── github_releases.py
│   │   ├── rss_fetcher.py    # Angular/React/Vue/Python/Node/AI blogs/media
│   │   ├── hackernews.py
│   │   ├── newsapi.py
│   │   ├── huggingface.py
│   │   └── papers_with_code.py
│   ├── processors/
│   │   ├── llm_client.py     # Google Gemini wrapper w/ retries + native JSON mode
│   │   └── filter.py         # LLM dedupe + quality filter + categorise
│   ├── generators/
│   │   ├── prompts.py        # SEO + GEO rules embedded here
│   │   ├── article_generator.py
│   │   └── digest_generator.py
│   ├── publishers/
│   │   ├── local.py          # Markdown (YAML front matter) + HTML + JSON
│   │   └── wordpress.py      # REST API publishing
│   └── utils/
│       ├── logger.py         # loguru, rotating daily log files
│       ├── slugify.py
│       └── html_renderer.py  # Markdown → HTML5 + JSON-LD <script>
├── deploy/
│   ├── crontab.sample
│   ├── run-daily.sh
│   └── daily-tech-news.service   # systemd unit
├── output/                   # Created at runtime
│   ├── markdown/
│   ├── html/
│   └── metadata/
└── logs/
```

---

## 1. Quick Start (Local)

```bash
# 1) Clone
git clone <your-fork-url> daily-tech-news-blog
cd daily-tech-news-blog

# 2) Create a virtualenv
python3.10 -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate

# 3) Install
pip install --upgrade pip
pip install -r requirements.txt

# 4) Configure
cp .env.example .env
# edit .env and set GEMINI_API_KEY (and optional NEWSAPI_KEY, GITHUB_TOKEN, etc.)

# 5) Smoke test the fetchers (no LLM/publish)
python main.py --fetch-only | head

# 6) Full pipeline once
python main.py --once

# 7) Run the long-lived scheduler
python main.py --schedule
```

Generated articles will appear under `output/markdown/`, `output/html/`, `output/metadata/`.

---

## 2. Obtaining API Keys

| Service | Required? | How to get it |
|---|---|---|
| **Google Gemini (AI Studio)** | **Yes** | https://aistudio.google.com/apikey — sign in with a Google account, click *Create API key*, paste into `GEMINI_API_KEY`. Free tier covers far more than one daily run. The default model is `gemini-2.5-flash`; switch to `gemini-2.5-flash-lite` for absolute lowest cost or `gemini-2.5-pro` for highest quality by setting `GEMINI_MODEL`. |
| **NewsAPI** | Optional but recommended | https://newsapi.org/register — free tier (100 reqs/day) is enough. Paste into `NEWSAPI_KEY`. If empty, the NewsAPI fetcher is silently skipped. |
| **GitHub** | Optional (raises rate limit) | https://github.com/settings/tokens — create a fine-grained token with public read access, paste into `GITHUB_TOKEN`. Anonymous calls also work but are limited to 60/hour. |
| **Hugging Face** | Optional | https://huggingface.co/settings/tokens — read token, paste into `HUGGINGFACE_TOKEN`. |
| **WordPress** | Optional | In WP admin: Users → Profile → Application Passwords → create a new one. Set `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_APP_PASSWORD`, and `PUBLISH_TO_WORDPRESS=true`. |

---

## 3. Configuration Reference (`.env`)

| Key | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | Your Google AI Studio key. **Required.** |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model used for filtering and article generation. Options: `gemini-2.5-flash-lite`, `gemini-2.5-flash`, `gemini-2.5-pro`. |
| `GEMINI_FALLBACK_MODEL` | `gemini-2.5-flash-lite` | Cheaper fallback model. |
| `GEMINI_MAX_TOKENS` | `4000` | Max output tokens per call. |
| `GEMINI_TEMPERATURE` | `0.4` | Lower = more deterministic. Articles are factual; keep low. |
| `BLOG_NAME` | `Daily Tech Pulse` | Used in JSON-LD `publisher`. |
| `BLOG_AUTHOR` | `Daily Tech Pulse Editorial` | Used in JSON-LD `author` and YAML front matter. |
| `BLOG_BASE_URL` | `https://example.com` | Used to build canonical URLs. |
| `RUN_TIME` | `08:00` | Daily run time, in `TIMEZONE`. |
| `TIMEZONE` | `Asia/Kuala_Lumpur` | Any IANA timezone name. |
| `SCHEDULER_MODE` | `cron` | `cron` = run forever, `oneshot` = single run when `main.py` is invoked without flags. |
| `LOOKBACK_HOURS` | `24` | Window size for "recent". |
| `MIN_ITEMS` / `MAX_ITEMS` | `5 / 12` | LLM filter bounds. |
| `ARTICLE_MODE` | `individual` | `individual` (one post per item) or `digest` (single rollup post). |
| `GITHUB_TRENDING_LANGUAGES` | `python,javascript,typescript,rust,go` | Languages to scan on github.com/trending. |
| `GITHUB_TRACKED_REPOS` | Angular, React, Vue, Python, Node, TS, Next.js, Svelte | Repos polled for new releases. |
| `OUTPUT_DIR` / `LOG_DIR` | `./output` / `./logs` | Where artefacts and logs land. |
| `PUBLISH_TO_WORDPRESS` | `false` | Set to `true` to enable the WP REST publisher. |

---

## 4. Deployment

### Option A — System cron (simple Linux server)

1. Copy the project to `/opt/daily-tech-news`.
2. Create a virtualenv inside it and install requirements.
3. Copy `.env.example` to `.env` and fill it in.
4. `chmod +x deploy/run-daily.sh` and adjust `PROJECT_DIR` if needed.
5. Install the cron entry:

   ```bash
   crontab -e
   # paste:
   0 0 * * *   /opt/daily-tech-news/deploy/run-daily.sh >> /opt/daily-tech-news/logs/cron.log 2>&1
   ```

   *(00:00 UTC corresponds to 08:00 Malaysia time. Adjust if your server is already in MYT — then use `0 8 * * *`.)*

### Option B — systemd service (long-lived scheduler)

```bash
sudo cp deploy/daily-tech-news.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now daily-tech-news
sudo journalctl -u daily-tech-news -f
```

### Option C — Docker

```bash
cp .env.example .env  # and edit
docker compose up -d --build
docker compose logs -f
```

To trigger a one-shot run inside Docker:

```bash
docker compose run --rm daily-tech-news python main.py --once
```

---

## 5. Output

For each generated article you get three files, named `<YYYY-MM-DD>-<slug>.{md,html,json}`:

- **Markdown** — Hugo/Hexo-compatible, with YAML front matter that includes the full schema, sources, and image suggestions in the metadata block.
- **HTML** — Standalone HTML5 with `<title>`, meta description, Open Graph, Twitter Card, canonical link, and inline JSON-LD (`BlogPosting` + `FAQPage`).
- **JSON metadata** — Machine-readable representation of everything (handy for piping into a static-site builder, search index, or analytics).

---

## 6. SEO + GEO Quality Controls

All generation rules are embedded directly in the LLM **system prompt** in `src/generators/prompts.py`. Editing that file is the single source of truth for article quality.

What the prompt enforces in every article:

- One H1 ≤ 65 chars, primary keyword present.
- 150–160 char meta description.
- TL;DR block at the top.
- Direct-answer opening paragraph (GEO best practice for Google SGE / ChatGPT / Perplexity).
- Q&A-style H3 subsections with immediate answers.
- FAQ section with at least 3 Q&As.
- Inline citations of authoritative sources.
- Image placeholders with descriptive ALT text.
- Two JSON-LD blocks: `BlogPosting` and `FAQPage`.
- Explicit time references (e.g. *"As of May 9, 2026"*).
- Concrete entities: version numbers, dates, benchmark numbers — no vague hype.

---

## 7. Logging & Observability

- All modules use `loguru` via `src/utils/logger.get_logger()`.
- Daily rotating log: `logs/daily-tech-news_YYYY-MM-DD.log`, kept 30 days.
- Each phase logs counts: `raw=N kept=N published=N`, plus per-fetcher success/failure.
- Any single fetcher / generator / publisher failure is caught — the daily run never aborts.
- If filtering returns zero items, a fallback *"No major updates today"* article is generated.

---

## 8. Extending

- **Add a new source**: drop a new `MyFetcher(BaseFetcher)` in `src/fetchers/`, then list it in `build_default_fetchers()`.
- **Tune SEO/GEO rules**: edit `src/generators/prompts.py` only.
- **Add a new publisher** (Ghost, Hugo git push, Notion, etc.): create `src/publishers/<name>.py` and call it from `src/pipeline.py`.

---

## 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `RuntimeError: GEMINI_API_KEY is not configured` | `.env` missing or not loaded. Run from project root. Get a key at https://aistudio.google.com/apikey. |
| Empty NewsAPI results | Free tier rate-limit exhausted, or `NEWSAPI_KEY` empty. Fetcher logs `no API key configured; skipping`. |
| 403 from GitHub | Set `GITHUB_TOKEN` to raise the anonymous rate limit. |
| Articles all from a single source | Other fetchers may be timing out — check logs. Network DNS or feed URLs may have changed. |
| Wrong run time | Confirm `TIMEZONE` is a valid IANA name and the host clock is correct (`timedatectl`). |

---

## 10. License

MIT. Use, fork, and modify freely.

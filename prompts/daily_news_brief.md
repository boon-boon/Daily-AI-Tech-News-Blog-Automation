# Daily Tech News — Scheduled Task Prompt

This is a copy of the prompt used by the daily scheduled task (see
`mcp__scheduled-tasks__list_scheduled_tasks`). Keep both in sync.

---

## Goal

Every morning at 08:00 Asia/Kuala_Lumpur, fetch the past 24 hours of
technology, AI, programming, and open-source news; filter for the 5–8
highest-value stories; write a full SEO + GEO optimized article for each;
save them as JSON files under `data/articles/<YYYY-MM-DD>/<slug>.json`;
then run the build script.

## Step-by-step

1. **Determine today's date** in Asia/Kuala_Lumpur and the lookback window
   (the previous 24 hours). Use `bash` with `TZ=Asia/Kuala_Lumpur date`.

2. **Fetch raw news** from these sources (use `web_fetch`):
   - Hacker News top stories: `https://hacker-news.firebaseio.com/v0/topstories.json`,
     then fetch the top 25 individual items to inspect title + score + url.
   - GitHub trending: `https://github.com/trending` (parse the HTML).
   - GitHub releases for: `angular/angular`, `facebook/react`, `vuejs/core`,
     `python/cpython`, `nodejs/node`, `microsoft/TypeScript`, `vercel/next.js`,
     `sveltejs/svelte`, `oven-sh/bun`, `denoland/deno`.
     Use `https://api.github.com/repos/<owner>/<repo>/releases?per_page=3`.
   - Official RSS feeds:
     - Angular blog: `https://blog.angular.io/feed`
     - React blog: `https://react.dev/rss.xml`
     - Python news: `https://www.python.org/blogs/feed/`
     - Node.js blog: `https://nodejs.org/en/feed/blog.xml`
     - OpenAI blog: `https://openai.com/blog/rss.xml`
     - Google AI blog: `https://blog.google/technology/ai/rss/`
     - Hugging Face blog: `https://huggingface.co/blog/feed.xml`
     - Anthropic news: `https://www.anthropic.com/news/rss.xml`
     - TechCrunch: `https://techcrunch.com/feed/`

3. **Filter, dedupe, score**.
   - Drop items older than 24 hours.
   - Collapse items covering the same underlying story (prefer the most
     authoritative source).
   - Drop cosmetic patch bumps, rumour pieces, listicles, paywalled
     press releases.
   - Categorize each survivor into ONE of: `AI Models`, `AI / ML Research`,
     `Programming`, `Framework & Library Releases`, `Developer Tools`,
     `Cloud & Infrastructure`, `Startups`, `Open Source`, `Cybersecurity`,
     `Gadgets`, `Industry News`.
   - Score each item's importance from 1 to 10. Keep the top 5–8.

4. **Write a full article for each kept item**. Each article must follow
   the SEO + GEO rules below and match the JSON schema in
   `data/articles/schema.json`. Save as
   `data/articles/<YYYY-MM-DD>/<slug>.json` using the `Write` tool.

5. **Run the build script** to render HTML pages and refresh the homepage:

       cd "<project root>"
       python3 scripts/build_site.py

6. **Commit and push** if the project is a git repo:

       git add data/ web/posts/ && git commit -m "Daily update YYYY-MM-DD" && git push

7. **Report back** in chat with:
   - The number of articles written and their titles.
   - The featured pick and why.
   - Any sources that failed (so they can be fixed).

---

## SEO + GEO rules — embed these in EVERY article

**SEO**

- H1 title (the `title` field): includes the primary keyword, click-worthy yet
  accurate, ≤ 65 characters where possible.
- Meta description (`meta_description` field): 150–160 characters, includes target
  keywords and a clear value proposition.
- Heading hierarchy in `body_markdown`: H2 sections, then H3 sub-sections where
  helpful. **Do not** include an H1 in `body_markdown` — the title is the H1.
- Short paragraphs (2–4 sentences). Use scannable bullet lists.
- 5–8 relevant tags.
- Image placeholders with descriptive ALT text in `image_suggestions`.
- Link to authoritative sources in the `sources` array (official release notes,
  GitHub, documentation).

**GEO (Generative Engine Optimization)**

- The opening paragraph of `body_markdown` must DIRECTLY answer the implicit
  question (what's new, what changed, why it matters) in 2–3 sentences.
- Follow with bullet-point expansions; AI engines extract these as answer
  fragments.
- Use exact, verifiable facts: version numbers, dates, performance deltas,
  benchmark scores, named entities.
- Use explicit time references — e.g. "As of <today's date>".
- Use Q&A-style sub-sections with a question as the H3 and an immediate
  one-paragraph answer below.
- Include `tldr` (2–3 sentences).
- Include at least 3 FAQ entries (`faq` array).
- Cite authoritative sources by name (e.g. "Angular official blog",
  "Google AI Blog", "Hugging Face Hub").
- Avoid hype, marketing adjectives, vague claims. Be objective, professional.

---

## JSON file shape

Each article saved to `data/articles/<YYYY-MM-DD>/<slug>.json`:

```json
{
  "slug":              "kebab-case-slug",
  "title":             "H1 title",
  "category":          "AI Models",
  "tags":              ["tag1", "tag2", "..."],
  "meta_description":  "150-160 char description with keywords",
  "tldr":              "2-3 sentence TL;DR",
  "body_markdown":     "## What's new\n\n<opening direct answer>\n\n- bullet\n- bullet\n\n## How ...",
  "faq": [
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."}
  ],
  "sources": [
    {"label": "Official blog",  "url": "https://..."},
    {"label": "Hacker News",    "url": "https://news.ycombinator.com/item?id=..."}
  ],
  "image_suggestions": [
    {"placement": "after H1", "description": "<image idea>", "alt_text": "<SEO ALT>"}
  ],
  "thumbnail":         {"c1": "#7c5cff", "c2": "#00d4ff"},
  "published_at":      "<ISO 8601 with +08:00>",
  "reading_time_min":  6,
  "importance_score":  9
}
```

Thumbnail color palette by category:

- AI Models: `#7c5cff` → `#00d4ff`
- AI / ML Research: `#7c5cff` → `#f472b6`
- Programming / Framework: `#22d3ee` → `#10b981`
- Developer Tools: `#22d3ee` → `#7c5cff`
- Cloud & Infrastructure: `#10b981` → `#22d3ee`
- Industry News: `#f59e0b` → `#ef4444`
- Cybersecurity: `#ef4444` → `#f59e0b`
- Startups: `#22d3ee` → `#10b981`
- Open Source: `#06b6d4` → `#8b5cf6`
- Gadgets: `#10b981` → `#06b6d4`

The article with the **highest `importance_score`** becomes the featured story
on the homepage. All others appear in the "Latest" grid in score order.

---

## If no news is meaningful today

Write a single short article called "No major tech updates today" with
`importance_score: 1`, a brief explanation of what was monitored, and a list
of what's expected in the coming week. Still run the build script.

## Tone

Professional, objective, explanatory. Working software engineers and ML
practitioners are the audience. No hype.

## Done.

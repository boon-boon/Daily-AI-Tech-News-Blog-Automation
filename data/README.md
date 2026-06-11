# Daily data layer

The website reads from this folder. **Two JSON shapes** matter:

| File | Shape | Written by | Read by |
|---|---|---|---|
| `daily.json` | `schema.json` | `scripts/build_site.py` | homepage (`web/index.html` via `data-loader.js`) |
| `articles/<YYYY-MM-DD>/<slug>.json` | `articles/schema.json` | Claude scheduled task | `scripts/build_site.py` |

## The daily flow

```
┌──────────────────────────────────────────────────────────┐
│  Claude scheduled task — 08:00 MYT every day              │
│  Reads prompts/daily_news_brief.md                        │
│  Fetches HN, GitHub, RSS feeds                            │
│  Filters / dedupes / scores                               │
│  Writes one JSON file per article:                        │
│     data/articles/<YYYY-MM-DD>/<slug>.json                │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  python3 scripts/build_site.py                            │
│  For each new article JSON:                               │
│    Fills web/article.html template                        │
│    Writes web/posts/<YYYY-MM-DD>/<slug>.html              │
│  Refreshes data/daily.json with:                          │
│    featured = highest importance_score                    │
│    latest   = rest, sorted by score                       │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
                git add + commit + push
                         │
                         ▼
                GitHub Pages serves it
```

## Manually testing the flow

```bash
# 1) Drop a hand-written article JSON in data/articles/<today>/<slug>.json
#    (mirror data/articles/2026-06-11/claude-fable-5.json as a template)

# 2) Run the builder
python3 scripts/build_site.py

# 3) The new article page exists at web/posts/<today>/<slug>.html
#    and data/daily.json reflects the new featured / latest cards.
```

## Validating the files

```bash
python3 -c "
import json, jsonschema, pathlib
schema = json.load(open('data/articles/schema.json'))
for p in pathlib.Path('data/articles').rglob('*.json'):
    if p.name == 'schema.json': continue
    jsonschema.validate(json.load(open(p)), schema)
    print(f'OK {p}')
print()
jsonschema.validate(json.load(open('data/daily.json')), json.load(open('data/schema.json')))
print('OK data/daily.json')
"
```

Add `jsonschema` to the scheduled task's verification step if you want CI-style enforcement before each commit.

## Why a single JSON file per article?

- **Decoupled**: Claude writes them today, you (or a different tool) could write them tomorrow — as long as they match the schema, the website renders.
- **Versioned by date folder**: each day's output is its own folder. Easy to roll back, regenerate, or archive.
- **No build step beyond `build_site.py`**: no Astro, no Next.js, no SSG framework. `python3 scripts/build_site.py` is the entire build.
- **Diffable**: every daily commit shows exactly which articles were added.

## Optional: enriching with `/last30days`

If you install the `mvanhorn/last30days-skill` in Claude Code and want to surface community quotes on the homepage, add a `community_pulse` block to `daily.json`:

```json
"community_pulse": {
  "top_topics": ["..."],
  "best_takes": [
    { "source": "reddit", "subreddit_or_handle": "r/...", "quote": "...",
      "engagement": "1.5k upvotes", "url": "https://..." }
  ]
}
```

The homepage's `data-loader.js` will automatically render this as a "What people are actually saying" section when present.

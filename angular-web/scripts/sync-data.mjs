/**
 * sync-data.mjs
 * -------------------------------------------------------------
 * Copies the Python backend's generated data into the Angular app's
 * static assets so the SPA can fetch it at /data/*.
 *
 *   ../data/daily.json                      ->  public/data/daily.json
 *   ../data/articles/<date>/<file>.json     ->  public/data/articles/<date>/<slug>.json
 *                                           ->  public/data/archive.json  (generated)
 *
 * Each article file is (re)named by its own `slug` field so the filename
 * matches the permalink route (/posts/<date>/<slug>). Run after every
 * backend build:   npm run sync-data
 *
 * archive.json is an index of EVERY article across every date, newest first.
 * daily.json only ever describes a single day, so search and the archive page
 * would otherwise have no way to reach anything published before today.
 * It is generated here rather than in build_site.py because this script is the
 * step that actually runs in CI.
 *
 * Pure Node, no dependencies.
 */
import { readdir, readFile, writeFile, mkdir, copyFile, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const SRC = join(ROOT, '..', 'data'); // the Python project's data/ folder
const DEST = join(ROOT, 'public', 'data');
const PUBLIC = join(ROOT, 'public');

/** Canonical public origin + base href. Mirrors SITE_BASE in scripts/build_site.py. */
const SITE_BASE = 'https://boon-boon.github.io/Daily-AI-Tech-News-Blog-Automation';

const XML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' };
const xmlEscape = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => XML_ESCAPES[c]);

/**
 * Slim card for the archive index. Deliberately omits body_markdown and faq —
 * the index is downloaded whole by the search page, so it has to stay small.
 */
function toIndexEntry(article, date) {
  return {
    id: article.slug,
    date,
    title: article.title,
    category: article.category ?? '',
    excerpt: (article.meta_description || article.tldr || '').slice(0, 240),
    permalink: `/posts/${date}/${article.slug}`,
    published_at: article.published_at ?? `${date}T00:00:00+08:00`,
    reading_time_min: article.reading_time_min ?? null,
    tags: article.tags ?? [],
    thumbnail: article.thumbnail ?? { c1: '#7c5cff', c2: '#00d4ff' },
    image: `assets/img/covers/${article.slug}.svg`,
  };
}

/** RSS 2.0 feed for the archive entries passed in (already newest-first). */
function renderRss(entries) {
  const now = new Date().toUTCString();
  const items = entries
    .map((a) => {
      const link = `${SITE_BASE}${a.permalink}`;
      return `    <item>
      <title>${xmlEscape(a.title)}</title>
      <link>${xmlEscape(link)}</link>
      <guid isPermaLink="true">${xmlEscape(link)}</guid>
      <pubDate>${new Date(a.published_at).toUTCString()}</pubDate>
      <category>${xmlEscape(a.category)}</category>
      <description>${xmlEscape(a.excerpt)}</description>
    </item>`;
    })
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>TechPulse Daily</title>
    <link>${SITE_BASE}/</link>
    <atom:link href="${SITE_BASE}/feed.xml" rel="self" type="application/rss+xml" />
    <description>A daily digest of AI and developer news, refreshed every morning at 8:00 AM Malaysia time.</description>
    <language>en</language>
    <lastBuildDate>${now}</lastBuildDate>
${items}
  </channel>
</rss>
`;
}

async function main() {
  if (!existsSync(SRC)) {
    console.error(`[sync-data] source not found: ${SRC}`);
    process.exit(1);
  }
  await mkdir(DEST, { recursive: true });

  // 1. daily.json (homepage feed)
  const daily = join(SRC, 'daily.json');
  if (existsSync(daily)) {
    await copyFile(daily, join(DEST, 'daily.json'));
    console.log('[sync-data] daily.json');
  }

  // 2. articles/<date>/<slug>.json, collecting the archive index as we go
  const index = [];
  const srcArticles = join(SRC, 'articles');
  if (existsSync(srcArticles)) {
    const dates = await readdir(srcArticles);
    for (const date of dates) {
      const dateDir = join(srcArticles, date);
      if (!(await stat(dateDir)).isDirectory()) continue;
      const outDir = join(DEST, 'articles', date);
      await mkdir(outDir, { recursive: true });

      for (const file of await readdir(dateDir)) {
        if (!file.endsWith('.json')) continue;
        const raw = await readFile(join(dateDir, file), 'utf8');
        let article;
        try {
          article = JSON.parse(raw);
        } catch {
          continue; // skip schema.json / non-article files
        }
        const slug = article.slug;
        if (!slug) continue;
        await writeFile(join(outDir, `${slug}.json`), raw);
        index.push(toIndexEntry(article, date));
        console.log(`[sync-data] articles/${date}/${slug}.json`);
      }
    }
  }

  // 3. archive.json — the cross-date index powering search and /archive
  index.sort((a, b) => (a.published_at < b.published_at ? 1 : -1));
  await writeFile(
    join(DEST, 'archive.json'),
    JSON.stringify(
      { version: '1.0', generated_at: new Date().toISOString(), count: index.length, articles: index },
      null,
      2,
    ),
  );
  console.log(`[sync-data] archive.json (${index.length} articles)`);

  // 4. feed.xml — RSS 2.0, newest 50 stories
  await writeFile(join(PUBLIC, 'feed.xml'), renderRss(index.slice(0, 50)));
  console.log('[sync-data] feed.xml');

  console.log('[sync-data] done.');
}

main().catch((e) => {
  console.error('[sync-data] failed:', e);
  process.exit(1);
});

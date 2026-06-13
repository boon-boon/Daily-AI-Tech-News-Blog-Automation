/**
 * sync-data.mjs
 * -------------------------------------------------------------
 * Copies the Python backend's generated data into the Angular app's
 * static assets so the SPA can fetch it at /data/*.
 *
 *   ../data/daily.json                      ->  public/data/daily.json
 *   ../data/articles/<date>/<file>.json     ->  public/data/articles/<date>/<slug>.json
 *
 * Each article file is (re)named by its own `slug` field so the filename
 * matches the permalink route (/posts/<date>/<slug>). Run after every
 * backend build:   npm run sync-data
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

  // 2. articles/<date>/<slug>.json
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
        let slug;
        try {
          slug = JSON.parse(raw).slug;
        } catch {
          continue; // skip schema.json / non-article files
        }
        if (!slug) continue;
        await writeFile(join(outDir, `${slug}.json`), raw);
        console.log(`[sync-data] articles/${date}/${slug}.json`);
      }
    }
  }

  console.log('[sync-data] done.');
}

main().catch((e) => {
  console.error('[sync-data] failed:', e);
  process.exit(1);
});

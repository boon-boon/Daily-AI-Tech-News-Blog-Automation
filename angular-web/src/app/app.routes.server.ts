import { RenderMode, ServerRoute } from '@angular/ssr';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

/**
 * Fixed category slugs (mirrors CATEGORY_KEYWORDS in category.component.ts).
 * These don't come from the daily data feed — they're a small, hand-picked
 * taxonomy — so they can just be listed here.
 */
const CATEGORY_SLUGS = [
  'ai-ml',
  'developer-tools',
  'cloud',
  'programming',
  'open-source',
  'industry',
];

/**
 * Enumerate every `<date>/<slug>` pair under public/data/articles so the
 * prerenderer knows every /posts/:date/:slug route to build.
 *
 * Runs at build time (Node, not the browser) against the same JSON files
 * `npm run sync-data` copies from ../data — so run `npm run sync-data`
 * before `ng build`.
 */
function getArticlePrerenderParams(): { date: string; slug: string }[] {
  const articlesDir = join(process.cwd(), 'public/data/articles');
  if (!existsSync(articlesDir)) {
    return [];
  }

  const params: { date: string; slug: string }[] = [];
  for (const dateEntry of readdirSync(articlesDir)) {
    const dateDir = join(articlesDir, dateEntry);
    if (!statSync(dateDir).isDirectory()) continue;

    for (const file of readdirSync(dateDir)) {
      if (!file.endsWith('.json')) continue;
      params.push({ date: dateEntry, slug: file.replace(/\.json$/, '') });
    }
  }
  return params;
}

export const serverRoutes: ServerRoute[] = [
  {
    path: 'posts/:date/:slug',
    renderMode: RenderMode.Prerender,
    getPrerenderParams: async () => getArticlePrerenderParams(),
  },
  {
    path: 'category/:slug',
    renderMode: RenderMode.Prerender,
    getPrerenderParams: async () => CATEGORY_SLUGS.map((slug) => ({ slug })),
  },
  {
    path: '**',
    renderMode: RenderMode.Prerender,
  },
];

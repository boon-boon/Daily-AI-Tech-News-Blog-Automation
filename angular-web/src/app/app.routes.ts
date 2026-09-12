import { Routes } from '@angular/router';

/**
 * Route table.
 *
 * Article URLs mirror the Python backend's permalink scheme:
 *   /posts/<YYYY-MM-DD>/<slug>
 * which maps to data/articles/<YYYY-MM-DD>/<slug>.json
 *
 * All pages are lazy-loaded standalone components for a small initial bundle.
 */
export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () =>
      import('./pages/home/home.component').then((m) => m.HomeComponent),
    title: 'TechPulse Daily — AI & Developer News',
  },
  {
    path: 'archive',
    loadComponent: () =>
      import('./pages/archive/archive.component').then(
        (m) => m.ArchiveComponent,
      ),
    title: 'Archive — TechPulse Daily',
  },
  {
    path: 'about',
    loadComponent: () =>
      import('./pages/about/about.component').then((m) => m.AboutComponent),
    title: 'How TechPulse is made — TechPulse Daily',
  },
  {
    path: 'category/:slug',
    loadComponent: () =>
      import('./pages/category/category.component').then(
        (m) => m.CategoryComponent,
      ),
  },
  {
    path: 'posts/:date/:slug',
    loadComponent: () =>
      import('./pages/article/article.component').then(
        (m) => m.ArticleComponent,
      ),
  },
  {
    path: '404',
    loadComponent: () =>
      import('./pages/not-found/not-found.component').then(
        (m) => m.NotFoundComponent,
      ),
    title: 'Not found — TechPulse Daily',
  },
  { path: '**', redirectTo: '404' },
];

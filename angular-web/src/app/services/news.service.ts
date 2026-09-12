import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map, shareReplay } from 'rxjs/operators';

import { DailyData } from '../models/daily.model';
import { Article } from '../models/article.model';
import { ArchiveIndex } from '../models/archive.model';

/**
 * Fetches the data produced by the Python automation backend.
 *
 * Files are served as static assets under /data (copied into public/data by
 * `npm run sync-data`). Both the homepage feed and per-article documents share
 * the same contract as the existing static `web/` site, so the two frontends
 * stay interchangeable.
 */
@Injectable({ providedIn: 'root' })
export class NewsService {
  private readonly http = inject(HttpClient);

  /** Base path for the JSON data. Override here if hosting data elsewhere. */
  private readonly dataBase = 'data';

  /** daily.json is small and immutable per page load — cache it. */
  private daily$?: Observable<DailyData>;

  /** Load the homepage feed (featured story, trending, categories, pulse). */
  getDaily(): Observable<DailyData> {
    if (!this.daily$) {
      this.daily$ = this.http
        .get<DailyData>(`${this.dataBase}/daily.json`)
        .pipe(shareReplay({ bufferSize: 1, refCount: false }));
    }
    return this.daily$;
  }

  /**
   * Load a single article by date + slug.
   * @param date YYYY-MM-DD (matches the data/articles/<date>/ folder)
   * @param slug URL-safe slug (the JSON filename without extension)
   */
  getArticle(date: string, slug: string): Observable<Article | null> {
    return this.http
      .get<Article>(`${this.dataBase}/articles/${date}/${slug}.json`)
      .pipe(catchError(() => of(null)));
  }

  /** archive.json is fetched once per page load and reused across searches. */
  private archive$?: Observable<ArchiveIndex>;

  /**
   * Load the full cross-date article index (every article ever published).
   * Backs the archive page and site search. Falls back to an empty index so a
   * missing file degrades to "no results" rather than a broken page.
   */
  getArchive(): Observable<ArchiveIndex> {
    if (!this.archive$) {
      this.archive$ = this.http
        .get<ArchiveIndex>(`${this.dataBase}/archive.json`)
        .pipe(
          catchError(() =>
            of({ version: '1.0', generated_at: '', count: 0, articles: [] }),
          ),
          shareReplay({ bufferSize: 1, refCount: false }),
        );
    }
    return this.archive$;
  }

  /** Articles published on a given category, derived from the daily feed. */
  getByCategory(slug: string): Observable<DailyData> {
    return this.getDaily().pipe(map((d) => d));
  }
}

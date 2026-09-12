import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { NewsService } from '../../services/news.service';
import { SeoService } from '../../services/seo.service';
import { ArchiveEntry } from '../../models/archive.model';
import { permalinkToCommands } from '../../utils/links';

const PAGE_SIZE = 12;

/**
 * Archive + search in one page.
 *
 * Browsing every story and searching them are the same operation with a
 * different filter, so they share a route: /archive shows everything, and
 * /archive?q=... narrows it. Both paginate. The whole index is small enough
 * to filter in memory, so there is no search backend to run.
 */
@Component({
  selector: 'app-archive',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DatePipe, RouterLink],
  template: `
    <div class="container">
      <span class="kicker" style="margin-top:8px;display:inline-block">Archive</span>
      <h1 class="article-title">Every story we've published</h1>
      <p class="article-dek" style="max-width:640px">
        Search the full archive by headline, topic, or tag.
      </p>

      <form class="search-bar" role="search" (submit)="$event.preventDefault()">
        <label class="sr-only" for="archive-search">Search articles</label>
        <input
          id="archive-search"
          type="search"
          class="search-bar__input"
          placeholder="Search headlines, topics, tags…"
          autocomplete="off"
          [value]="query()"
          (input)="onQuery($any($event.target).value)"
        />
        @if (query()) {
          <button type="button" class="search-bar__clear" (click)="onQuery('')">
            Clear
          </button>
        }
      </form>

      @if (loading()) {
        <div class="state">
          <div class="spinner"></div>
          Loading archive…
        </div>
      } @else {
        <p class="result-count" aria-live="polite">
          @if (query()) {
            {{ filtered().length }}
            {{ filtered().length === 1 ? 'result' : 'results' }} for
            “{{ query() }}”
          } @else {
            {{ filtered().length }} articles
          }
        </p>

        @if (pageItems().length) {
          <section class="section">
            <div class="feed">
              @for (a of pageItems(); track a.id) {
                <article class="story">
                  <a class="story__text" [routerLink]="route(a.permalink)">
                    <span class="kicker">{{ a.category }}</span>
                    <h2 class="story__title">{{ a.title }}</h2>
                    <p class="story__dek">{{ a.excerpt }}</p>
                    <div class="byline">
                      <strong>TechPulse</strong>
                      <span class="dot">·</span>
                      <span>{{ a.published_at | date: 'MMM d, y' }}</span>
                      <span class="dot">·</span>
                      <span>{{ a.reading_time_min || 4 }} min read</span>
                    </div>
                  </a>
                  <a
                    class="story__thumb"
                    [routerLink]="route(a.permalink)"
                    [style.background]="thumb(a)"
                    aria-hidden="true"
                    tabindex="-1"
                  >
                    @if (a.image) {
                      <img
                        class="thumb-img"
                        [src]="a.image"
                        alt=""
                        loading="lazy"
                        (error)="onImgError($event)"
                      />
                    }
                  </a>
                </article>
              }
            </div>
          </section>

          @if (totalPages() > 1) {
            <nav class="pager" aria-label="Archive pagination">
              <button
                class="btn-pill"
                [disabled]="page() === 1"
                (click)="goTo(page() - 1)"
              >
                ← Newer
              </button>
              <span class="pager__status">
                Page {{ page() }} of {{ totalPages() }}
              </span>
              <button
                class="btn-pill"
                [disabled]="page() === totalPages()"
                (click)="goTo(page() + 1)"
              >
                Older →
              </button>
            </nav>
          }
        } @else {
          <div class="state">
            <p>No stories match “{{ query() }}”.</p>
            <button class="btn-pill" (click)="onQuery('')">
              Show all articles
            </button>
          </div>
        }
      }
    </div>
  `,
})
export class ArchiveComponent implements OnInit {
  private readonly route_ = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly news = inject(NewsService);
  private readonly seo = inject(SeoService);

  protected readonly all = signal<ArchiveEntry[]>([]);
  protected readonly loading = signal(true);
  protected readonly query = signal('');
  protected readonly page = signal(1);

  protected readonly filtered = computed(() => {
    const terms = this.query().toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return this.all();
    return this.all().filter((a) => {
      const haystack = [a.title, a.excerpt, a.category, ...(a.tags ?? [])]
        .join(' ')
        .toLowerCase();
      return terms.every((t) => haystack.includes(t));
    });
  });

  protected readonly totalPages = computed(() =>
    Math.max(1, Math.ceil(this.filtered().length / PAGE_SIZE)),
  );

  protected readonly pageItems = computed(() => {
    const start = (this.page() - 1) * PAGE_SIZE;
    return this.filtered().slice(start, start + PAGE_SIZE);
  });

  ngOnInit(): void {
    this.seo.clearJsonLd();
    this.seo.setTags({
      title: 'Archive — TechPulse Daily',
      description:
        'Search and browse every AI and developer story published on TechPulse Daily.',
      type: 'website',
    });

    // The URL is the source of truth for q/page, so search results stay
    // shareable and the back button moves through them.
    this.route_.queryParamMap.subscribe((params) => {
      this.query.set(params.get('q') ?? '');
      const p = Number(params.get('page') ?? '1');
      this.page.set(Number.isFinite(p) && p > 0 ? p : 1);
    });

    this.news.getArchive().subscribe((index) => {
      this.all.set(index.articles ?? []);
      this.loading.set(false);
    });
  }

  protected onQuery(value: string): void {
    this.router.navigate([], {
      relativeTo: this.route_,
      queryParams: { q: value || null, page: null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  protected goTo(page: number): void {
    this.router.navigate([], {
      relativeTo: this.route_,
      queryParams: { page: page > 1 ? page : null },
      queryParamsHandling: 'merge',
    });
  }

  protected route(permalink: string): string[] {
    return permalinkToCommands(permalink);
  }

  protected thumb(a: ArchiveEntry): string {
    const t = a.thumbnail;
    return t
      ? `linear-gradient(135deg, ${t.c1}, ${t.c2})`
      : 'linear-gradient(135deg, #f2f2f2, #e6e6e6)';
  }

  protected onImgError(e: Event): void {
    (e.target as HTMLElement).style.display = 'none';
  }
}

import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

import { NewsService } from '../../services/news.service';
import { SeoService } from '../../services/seo.service';
import { CategorySummary, FeaturedRef } from '../../models/daily.model';
import { permalinkToCommands } from '../../utils/links';

/**
 * Maps a category slug to the article-category keywords it should collect.
 * Article `category` values (e.g. "AI Models", "Cloud & Infrastructure") don't
 * match category names 1:1, so we match on keywords instead.
 */
const CATEGORY_KEYWORDS: Record<string, string[]> = {
  'ai-ml': ['ai models', 'ai /', 'ml', 'machine learning', 'model'],
  'developer-tools': ['developer tools', 'developer', 'sdk', 'tool'],
  cloud: ['cloud', 'infra'],
  programming: ['programming', 'language', 'framework', 'library'],
  'open-source': ['open source', 'open-source'],
  industry: ['industry', 'startup', 'business', 'partnership'],
};

@Component({
  selector: 'app-category',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, DatePipe],
  template: `
    <div class="container">
      @if (category(); as c) {
        <span class="kicker" style="margin-top:8px;display:inline-block">
          {{ c.article_count_today }} stories today
        </span>
        <h1 class="article-title">{{ c.name }}</h1>
        <p class="article-dek" style="max-width:640px">{{ c.description }}</p>

        <section class="section">
          @if (articles().length) {
            <div class="feed">
              @for (a of articles(); track a.id) {
                <article class="story">
                  <a class="story__text" [routerLink]="route(a.permalink)">
                    <span class="kicker">{{ a.category }}</span>
                    <h2 class="story__title">{{ a.title }}</h2>
                    <p class="story__dek">{{ a.excerpt }}</p>
                    <div class="byline">
                      <strong>TechPulse</strong>
                      <span class="dot">·</span>
                      <span>{{ a.published_at | date: 'MMM d' }}</span>
                      <span class="dot">·</span>
                      <span>{{ a.reading_time_min || 4 }} min read</span>
                    </div>
                  </a>
                  <a
                    class="story__thumb"
                    [routerLink]="route(a.permalink)"
                    [style.background]="thumb(a)"
                    aria-hidden="true"
                  >
                    @if (a.image) {
                      <img class="thumb-img" [src]="a.image" alt="" loading="lazy" (error)="onImgError($event)" />
                    }
                  </a>
                </article>
              }
            </div>
          } @else {
            <div class="state">
              <p>No stories in this section today. Check back after the 8:00 AM refresh.</p>
              <a class="btn-pill" routerLink="/">Back to home</a>
            </div>
          }
        </section>
      } @else {
        <div class="state">
          <div class="spinner"></div>
          Loading section…
        </div>
      }
    </div>
  `,
})
export class CategoryComponent implements OnInit {
  private readonly activatedRoute = inject(ActivatedRoute);
  private readonly news = inject(NewsService);
  private readonly seo = inject(SeoService);

  protected readonly category = signal<CategorySummary | null>(null);
  protected readonly articles = signal<FeaturedRef[]>([]);

  ngOnInit(): void {
    this.seo.clearJsonLd();
    combineLatest([this.activatedRoute.paramMap, this.news.getDaily()])
      .pipe(
        map(([params, daily]) => {
          const slug = params.get('slug') ?? '';
          const cat = daily.categories.find((c) => c.slug === slug) ?? null;
          const pool = [daily.featured, ...daily.latest];
          const keywords = CATEGORY_KEYWORDS[slug] ?? [slug.replace(/-/g, ' ')];
          const matches = cat
            ? pool.filter((a) => {
                const ac = (a.category ?? '').toLowerCase();
                return keywords.some((k) => ac.includes(k));
              })
            : [];
          return { cat, matches };
        }),
      )
      .subscribe(({ cat, matches }) => {
        this.category.set(cat);
        this.articles.set(matches);
        if (cat) {
          this.seo.setTags({
            title: `${cat.name} — TechPulse`,
            description: cat.description,
            type: 'website',
          });
        }
      });
  }

  protected route(permalink: string): string[] {
    return permalinkToCommands(permalink);
  }

  protected thumb(a: FeaturedRef): string {
    const t = a.thumbnail;
    return t
      ? `linear-gradient(135deg, ${t.c1}, ${t.c2})`
      : 'linear-gradient(135deg, #f2f2f2, #e6e6e6)';
  }

  /** Hide a broken cover image so the gradient fallback shows through. */
  protected onImgError(e: Event): void {
    (e.target as HTMLElement).style.display = 'none';
  }
}

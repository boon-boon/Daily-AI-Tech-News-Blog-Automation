import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { AsyncPipe, DecimalPipe, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Observable } from 'rxjs';

import { NewsService } from '../../services/news.service';
import { SeoService } from '../../services/seo.service';
import { DailyData, FeaturedRef } from '../../models/daily.model';
import { permalinkToCommands } from '../../utils/links';

@Component({
  selector: 'app-home',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [AsyncPipe, DecimalPipe, DatePipe, RouterLink],
  template: `
    @if (daily$ | async; as d) {
      <div class="container">
        <!-- Featured lead -->
        <section class="lead">
          <div class="lead__text">
            <span class="kicker">{{ d.featured.category }}</span>
            <h1 class="lead__title">
              <a [routerLink]="route(d.featured.permalink)">{{ d.featured.title }}</a>
            </h1>
            <p class="lead__dek">{{ d.featured.tldr }}</p>
            <div class="byline">
              <span class="byline__av" aria-hidden="true">TP</span>
              <strong>TechPulse</strong>
              <span class="dot">·</span>
              <span>{{ d.featured.published_at | date: 'MMM d' }}</span>
              <span class="dot">·</span>
              <span>{{ d.featured.reading_time_min || 5 }} min read</span>
            </div>
            <div class="lead__cta">
              <a class="btn-pill" [routerLink]="route(d.featured.permalink)">
                Read the story
              </a>
            </div>
          </div>
          <a
            class="lead__thumb"
            [routerLink]="route(d.featured.permalink)"
            [style.background]="thumb(d.featured)"
            aria-hidden="true"
            tabindex="-1"
          >
            @if (d.featured.image) {
              <img class="thumb-img" [src]="d.featured.image" alt="" loading="lazy" (error)="onImgError($event)" />
            }
          </a>
        </section>

        <div class="feedwrap">
          <section class="feed" aria-labelledby="feed-head">
            <div class="feed__head" id="feed-head">Latest</div>
            @for (a of d.latest; track a.id) {
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
                  tabindex="-1"
                >
                  @if (a.image) {
                    <img class="thumb-img" [src]="a.image" alt="" loading="lazy" (error)="onImgError($event)" />
                  }
                </a>
              </article>
            }
          </section>

          <aside class="rail" aria-label="More from TechPulse">
            <!-- Trending releases — ranked by stars (the ordinal signature) -->
            <section class="rail__block">
              <div class="rail__head">Trending releases</div>
              <ol class="rank">
                @for (r of d.github_trending; track r.repo; let i = $index) {
                  <li class="rank__item">
                    <span class="rank__num">{{ ord(i) }}</span>
                    <a class="rank__body" [href]="r.url" target="_blank" rel="noopener">
                      <div class="rank__repo">{{ r.repo }}</div>
                      <div class="rank__meta">
                        {{ r.language }} · ★{{ r.stars_total | number }}
                        <span class="up">+{{ r.stars_today | number }} today</span>
                      </div>
                    </a>
                  </li>
                }
              </ol>
            </section>

            <section class="rail__block">
              <div class="rail__head">Discover by topic</div>
              <div class="chips">
                @for (c of d.categories; track c.slug) {
                  <a class="chip-tag" [routerLink]="['/category', c.slug]">{{ c.name }}</a>
                }
              </div>
            </section>

            <section class="rail__block">
              <div class="rail__head">Community pulse</div>
              @for (take of takes(d); track take.url) {
                <div class="mini-take">
                  <blockquote>“{{ take.quote }}”</blockquote>
                  <span class="by">{{ take.author }} · {{ take.source }}</span>
                </div>
              }
            </section>
          </aside>
        </div>
      </div>
    } @else {
      <div class="state">
        <div class="spinner"></div>
        Loading today’s stories…
      </div>
    }
  `,
})
export class HomeComponent implements OnInit {
  private readonly news = inject(NewsService);
  private readonly seo = inject(SeoService);

  protected readonly daily$: Observable<DailyData> = this.news.getDaily();

  ngOnInit(): void {
    this.seo.clearJsonLd();
    this.daily$.subscribe((d) => {
      this.seo.setTags({
        title: `TechPulse — AI & developer news for ${d.date_human}`,
        description:
          'A daily digest of AI and developer news, refreshed every morning at 8:00 AM Malaysia time. Today: ' +
          d.featured.title,
        type: 'website',
      });
      this.seo.setJsonLd({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'TechPulse',
        description: 'Automated daily AI and developer technology news.',
      });
    });
  }

  protected route(permalink: string): string[] {
    return permalinkToCommands(permalink);
  }

  /** Background for a story thumbnail tile. Falls back to a neutral wash. */
  protected thumb(a: FeaturedRef): string {
    const t = a.thumbnail;
    return t
      ? `linear-gradient(135deg, ${t.c1}, ${t.c2})`
      : 'linear-gradient(135deg, #f2f2f2, #e6e6e6)';
  }

  /** Zero-padded ordinal for the trending list (01, 02, …). */
  protected ord(i: number): string {
    return String(i + 1).padStart(2, '0');
  }

  /** Hide a broken cover image so the gradient fallback shows through. */
  protected onImgError(e: Event): void {
    (e.target as HTMLElement).style.display = 'none';
  }

  /** Top community takes for the rail. */
  protected takes(d: DailyData) {
    return d.community_pulse.best_takes.slice(0, 3);
  }
}

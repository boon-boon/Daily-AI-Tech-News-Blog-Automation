import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { switchMap } from 'rxjs/operators';

import { NewsService } from '../../services/news.service';
import { SeoService } from '../../services/seo.service';
import { Article } from '../../models/article.model';
import { MarkdownPipe } from '../../pipes/markdown.pipe';

@Component({
  selector: 'app-article',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DatePipe, RouterLink, MarkdownPipe],
  template: `
    @if (loading()) {
      <div class="state">
        <div class="spinner"></div>
        Loading article…
      </div>
    } @else if (article(); as a) {
      <article class="container article-wrap">
        <nav class="breadcrumbs" aria-label="Breadcrumb">
          <a routerLink="/">Home</a> › <span>{{ a.category }}</span>
        </nav>

        <span class="kicker">{{ a.category }}</span>
        <h1 class="article-title">{{ a.title }}</h1>
        <p class="article-dek">{{ a.tldr }}</p>

        <div class="article-meta">
          <span class="byline__av" aria-hidden="true">TP</span>
          <strong style="color:var(--ink);font-weight:500">TechPulse</strong>
          <span class="dot">·</span>
          <time [attr.datetime]="a.published_at">
            {{ a.published_at | date: 'MMMM d, y' }}
          </time>
          @if (a.reading_time_min) {
            <span class="dot">·</span>
            <span>{{ a.reading_time_min }} min read</span>
          }
        </div>

        @if (a.sources?.length) {
          <p class="source-credit">
            <span class="source-credit__lbl">Reported from</span>
            @for (s of a.sources ?? []; track s.url; let last = $last) {
              <a [href]="s.url" target="_blank" rel="noopener nofollow">{{
                sourceHost(s.url)
              }}</a>@if (!last) {<span aria-hidden="true">, </span>}
            }
          </p>
        }

        <!-- Lead image placeholder -->
        @if (leadImage(a); as img) {
          <figure class="img-placeholder">
            <div class="lbl">Suggested image · {{ img.placement }}</div>
            <p style="margin:6px 0 0">{{ img.description }}</p>
            <p style="margin:6px 0 0;font-style:italic">ALT: {{ img.alt_text }}</p>
          </figure>
        }

        <!-- Body -->
        <div class="prose" [innerHTML]="a.body_markdown | markdown"></div>

        <!-- Tags -->
        @if (a.tags?.length) {
          <div class="tag-row" style="margin:30px 0">
            @for (t of a.tags ?? []; track t) {
              <span class="tag">#{{ t }}</span>
            }
          </div>
        }

        <!-- FAQ -->
        @if (a.faq?.length) {
          <section class="section faq">
            <div class="section-head"><h2>Frequently asked questions</h2></div>
            @for (f of a.faq ?? []; track f.question) {
              <details>
                <summary>{{ f.question }}</summary>
                <p>{{ f.answer }}</p>
              </details>
            }
          </section>
        }

        <!-- Sources -->
        @if (a.sources?.length) {
          <section class="section sources">
            <div class="section-head"><h2>Official sources</h2></div>
            <ul>
              @for (s of a.sources ?? []; track s.url) {
                <li>
                  <a [href]="s.url" target="_blank" rel="noopener">{{ s.label }}</a>
                </li>
              }
            </ul>
          </section>
        }

        <div style="margin-top:40px">
          <a class="btn" routerLink="/">← Back to today’s stories</a>
        </div>
      </article>
    } @else {
      <div class="state">
        <h2>Article not found</h2>
        <p>This story may have been removed or the link is incorrect.</p>
        <a class="btn btn-primary" routerLink="/">Go to homepage</a>
      </div>
    }
  `,
})
export class ArticleComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly news = inject(NewsService);
  private readonly seo = inject(SeoService);

  protected readonly article = signal<Article | null>(null);
  protected readonly loading = signal(true);

  ngOnInit(): void {
    this.route.paramMap
      .pipe(
        switchMap((params) => {
          this.loading.set(true);
          const date = params.get('date') ?? '';
          const slug = params.get('slug') ?? '';
          return this.news.getArticle(date, slug);
        }),
      )
      .subscribe((a) => {
        this.article.set(a);
        this.loading.set(false);
        if (a) this.applySeo(a);
      });
  }

  /** Bare hostname for the compact credit line, e.g. "anthropic.com". */
  protected sourceHost(url: string): string {
    try {
      return new URL(url).hostname.replace(/^www\./, '');
    } catch {
      return url;
    }
  }

  /** Lead image suggestion (the one placed "after H1"), if any. */
  protected leadImage(a: Article) {
    return (
      a.image_suggestions?.find((i) => /h1/i.test(i.placement ?? '')) ??
      a.image_suggestions?.[0] ??
      null
    );
  }

  private applySeo(a: Article): void {
    const url = typeof location !== 'undefined' ? location.href : '';
    this.seo.setTags({
      title: a.title,
      description: a.meta_description,
      url,
      image: a.og_image,
      type: 'article',
      publishedAt: a.published_at,
      tags: a.tags,
    });
    this.seo.setArticleJsonLd(a, url);
  }
}

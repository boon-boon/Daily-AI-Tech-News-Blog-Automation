import { Injectable, inject, DOCUMENT } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';

import { Article } from '../models/article.model';

export interface SeoTags {
  title: string;
  description: string;
  url?: string;
  image?: string;
  type?: 'website' | 'article';
  publishedAt?: string;
  tags?: string[];
}

/**
 * Centralizes SEO + GEO (Generative Engine Optimization) concerns:
 * - <title> and meta description
 * - Open Graph + Twitter cards (for social + AI link unfurling)
 * - canonical link
 * - JSON-LD structured data (Article, FAQPage, BreadcrumbList)
 *
 * NOTE: Angular renders client-side, so crawlers that don't execute JS will
 * not see these tags. The Python backend already emits fully static, crawlable
 * HTML under web/posts/ for Google SGE and AI crawlers. This service keeps the
 * Angular SPA's metadata correct for social sharing and JS-capable crawlers,
 * and is SSR/prerender-ready (see README "SEO & SSR").
 */
@Injectable({ providedIn: 'root' })
export class SeoService {
  private readonly title = inject(Title);
  private readonly meta = inject(Meta);
  private readonly doc = inject(DOCUMENT);

  private readonly siteName = 'TechPulse Daily';
  private readonly defaultImage = 'assets/img/og-default.svg';

  /** Apply basic + Open Graph + Twitter meta for any page. */
  setTags(tags: SeoTags): void {
    const fullTitle = tags.title.includes(this.siteName)
      ? tags.title
      : `${tags.title} — ${this.siteName}`;
    const image = tags.image ?? this.defaultImage;
    const url = tags.url ?? this.doc.location?.href ?? '';

    this.title.setTitle(fullTitle);
    this.upsertName('description', tags.description);

    // Open Graph
    this.upsertProperty('og:site_name', this.siteName);
    this.upsertProperty('og:title', fullTitle);
    this.upsertProperty('og:description', tags.description);
    this.upsertProperty('og:type', tags.type ?? 'website');
    this.upsertProperty('og:image', image);
    if (url) this.upsertProperty('og:url', url);

    // Twitter
    this.upsertName('twitter:card', 'summary_large_image');
    this.upsertName('twitter:title', fullTitle);
    this.upsertName('twitter:description', tags.description);
    this.upsertName('twitter:image', image);

    if (tags.publishedAt) {
      this.upsertProperty('article:published_time', tags.publishedAt);
    }
    if (tags.tags?.length) {
      this.upsertName('keywords', tags.tags.join(', '));
    }

    this.setCanonical(url);
  }

  /**
   * Build and inject JSON-LD for a full article: an Article node plus, when
   * present, a FAQPage node and a BreadcrumbList node.
   */
  setArticleJsonLd(article: Article, url: string): void {
    const graph: Record<string, unknown>[] = [
      {
        '@type': 'TechArticle',
        headline: article.title,
        description: article.meta_description,
        datePublished: article.published_at,
        dateModified: article.published_at,
        articleSection: article.category,
        keywords: (article.tags ?? []).join(', '),
        url,
        image: article.og_image ?? this.defaultImage,
        author: { '@type': 'Organization', name: this.siteName },
        publisher: {
          '@type': 'Organization',
          name: this.siteName,
          logo: {
            '@type': 'ImageObject',
            url: 'assets/img/og-default.svg',
          },
        },
        mainEntityOfPage: { '@type': 'WebPage', '@id': url },
      },
    ];

    if (article.faq?.length) {
      graph.push({
        '@type': 'FAQPage',
        mainEntity: article.faq.map((f) => ({
          '@type': 'Question',
          name: f.question,
          acceptedAnswer: { '@type': 'Answer', text: f.answer },
        })),
      });
    }

    this.setJsonLd({ '@context': 'https://schema.org', '@graph': graph });
  }

  /** Inject an arbitrary JSON-LD object, replacing any previous one. */
  setJsonLd(data: unknown): void {
    const id = 'app-jsonld';
    let script = this.doc.getElementById(id) as HTMLScriptElement | null;
    if (!script) {
      script = this.doc.createElement('script');
      script.id = id;
      script.type = 'application/ld+json';
      this.doc.head.appendChild(script);
    }
    script.textContent = JSON.stringify(data);
  }

  /** Remove the JSON-LD block (call when leaving an article page). */
  clearJsonLd(): void {
    this.doc.getElementById('app-jsonld')?.remove();
  }

  private setCanonical(url: string): void {
    if (!url) return;
    let link = this.doc.querySelector(
      "link[rel='canonical']",
    ) as HTMLLinkElement | null;
    if (!link) {
      link = this.doc.createElement('link');
      link.setAttribute('rel', 'canonical');
      this.doc.head.appendChild(link);
    }
    link.setAttribute('href', url);
  }

  private upsertName(name: string, content: string): void {
    this.meta.updateTag({ name, content });
  }

  private upsertProperty(property: string, content: string): void {
    this.meta.updateTag({ property, content });
  }
}

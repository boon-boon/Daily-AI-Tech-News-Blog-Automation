/**
 * TypeScript mirror of data/articles/schema.json (the Python backend's output).
 * One Article object is written per story per day to:
 *   data/articles/<YYYY-MM-DD>/<slug>.json
 */

export interface ArticleSource {
  label: string;
  url: string;
}

export interface ArticleFaq {
  question: string;
  answer: string;
}

export interface ImageSuggestion {
  placement?: string;
  description?: string;
  alt_text?: string;
}

export interface Thumbnail {
  c1: string;
  c2: string;
}

export type ArticleCategory =
  | 'AI Models'
  | 'AI / ML Research'
  | 'Programming'
  | 'Framework & Library Releases'
  | 'Developer Tools'
  | 'Cloud & Infrastructure'
  | 'Startups'
  | 'Open Source'
  | 'Cybersecurity'
  | 'Gadgets'
  | 'Industry News';

export interface Article {
  slug: string;
  title: string;
  category: ArticleCategory | string;
  tags?: string[];
  meta_description: string;
  tldr: string;
  /** Full article body in Markdown. Does NOT include the H1 (title is the H1). */
  body_markdown: string;
  faq?: ArticleFaq[];
  sources?: ArticleSource[];
  image_suggestions?: ImageSuggestion[];
  thumbnail?: Thumbnail;
  published_at: string;
  reading_time_min?: number;
  importance_score?: number;
  og_image?: string;
}

/**
 * TypeScript mirror of data/daily.json (the homepage feed produced by the
 * Python backend's build step). This is the single index the home page reads.
 */
import { ArticleSource, Thumbnail } from './article.model';

export interface DailyStats {
  articles_published_total: number;
  sources_monitored: number;
  daily_update_time: string;
  automation_percent: number;
}

export interface FeaturedRef {
  id: string;
  title: string;
  category: string;
  excerpt: string;
  tldr: string;
  /** e.g. "/posts/2026-06-11/claude-fable-5-launch.html" */
  permalink: string;
  published_at: string;
  reading_time_min?: number;
  tags?: string[];
  sources?: ArticleSource[];
  thumbnail?: Thumbnail;
  /** Optional cover image URL. Falls back to the gradient thumbnail if absent or it fails to load. */
  image?: string;
}

export interface GithubRepo {
  repo: string;
  url: string;
  description: string;
  language: string;
  language_color: string;
  stars_total: number;
  stars_today: number;
  latest_release?: string;
  is_release?: boolean;
}

export interface CategorySummary {
  slug: string;
  name: string;
  description: string;
  article_count_today: number;
  color_from: string;
  color_to: string;
}

export interface CommunityTake {
  source: string;
  author: string;
  quote: string;
  engagement: string;
  url: string;
}

export interface CommunityPulse {
  top_topics: string[];
  best_takes: CommunityTake[];
}

export interface DailyData {
  version: string;
  generated_at: string;
  date_iso: string;
  date_human: string;
  timezone: string;
  stats: DailyStats;
  featured: FeaturedRef;
  latest: FeaturedRef[];
  github_trending: GithubRepo[];
  categories: CategorySummary[];
  community_pulse: CommunityPulse;
}

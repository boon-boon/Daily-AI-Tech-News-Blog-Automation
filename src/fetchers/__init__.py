"""News fetcher registry."""

from typing import List, Type

from .base import BaseFetcher, NewsItem
from .github_trending import GitHubTrendingFetcher
from .github_releases import GitHubReleasesFetcher
from .rss_fetcher import RSSFetcher, OFFICIAL_BLOG_FEEDS, AI_BLOG_FEEDS, MEDIA_FEEDS
from .hackernews import HackerNewsFetcher
from .newsapi import NewsAPIFetcher
from .huggingface import HuggingFaceFetcher
from .papers_with_code import PapersWithCodeFetcher


def build_default_fetchers() -> List[BaseFetcher]:
    """Construct the default fetcher pipeline."""
    fetchers: List[BaseFetcher] = [
        GitHubTrendingFetcher(),
        GitHubReleasesFetcher(),
        RSSFetcher(name="OfficialBlogs", feeds=OFFICIAL_BLOG_FEEDS),
        RSSFetcher(name="AIBlogs", feeds=AI_BLOG_FEEDS),
        RSSFetcher(name="TechMedia", feeds=MEDIA_FEEDS),
        HackerNewsFetcher(),
        NewsAPIFetcher(),
        HuggingFaceFetcher(),
        PapersWithCodeFetcher(),
    ]
    return fetchers


__all__ = [
    "BaseFetcher",
    "NewsItem",
    "GitHubTrendingFetcher",
    "GitHubReleasesFetcher",
    "RSSFetcher",
    "HackerNewsFetcher",
    "NewsAPIFetcher",
    "HuggingFaceFetcher",
    "PapersWithCodeFetcher",
    "build_default_fetchers",
]

from urllib.parse import urlparse

from app.collectors.github import GitHubCollector
from app.collectors.rss import RSSCollector
from app.collectors.webpage import WebpageCollector


def collector_for_url(url: str):
    return GitHubCollector() if "github.com" in urlparse(url).netloc.lower() else WebpageCollector()


def collector_for_source(source_type: str):
    if source_type in {"github", "github_search"}: return GitHubCollector()
    if source_type == "rss": return RSSCollector()
    return WebpageCollector()


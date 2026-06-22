import feedparser

from app.collectors.base import CollectedProject
from app.services.http import safe_get_text


class RSSCollector:
    async def collect_source(self, url: str, query: str = "") -> list[CollectedProject]:
        content, _ = await safe_get_text(url)
        feed = feedparser.parse(content)
        return [CollectedProject(url=e.link, title=e.get("title", "Untitled"), description=e.get("summary", ""), content=e.get("summary", ""), source_type="rss") for e in feed.entries[:20]]

    async def collect_url(self, url: str) -> CollectedProject:
        items = await self.collect_source(url)
        if not items: raise ValueError("RSS feed contains no entries")
        return items[0]

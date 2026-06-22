from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.collectors.base import CollectedProject
from app.services.http import safe_get_text


class WebpageCollector:
    async def collect_url(self, url: str) -> CollectedProject:
        html, final_url = await safe_get_text(url)
        soup = BeautifulSoup(html, "html.parser")
        for node in soup(["script", "style", "nav", "footer", "noscript"]):
            node.decompose()
        title = (soup.title.string.strip() if soup.title and soup.title.string else urlparse(url).netloc)
        description_node = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        description = description_node.get("content", "") if description_node else ""
        text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
        source_type = self.detect_type(url)
        return CollectedProject(url=final_url, title=title, description=description, content=text[:50000], source_type=source_type)

    async def collect_source(self, url: str, query: str = "") -> list[CollectedProject]:
        return [await self.collect_url(url)]

    @staticmethod
    def detect_type(url: str) -> str:
        host = urlparse(url).netloc.lower()
        if "hackster.io" in host: return "hackster"
        if "huggingface.co" in host: return "huggingface"
        if "youtube.com" in host or "youtu.be" in host: return "youtube"
        return "webpage"

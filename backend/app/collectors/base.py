from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass
class CollectedProject:
    url: str
    title: str
    description: str = ""
    content: str = ""
    source_type: str = "webpage"
    stars: int = 0
    views: int = 0
    likes: int = 0
    external_created_at: datetime | None = None
    external_updated_at: datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class Collector(Protocol):
    async def collect_url(self, url: str) -> CollectedProject: ...
    async def collect_source(self, url: str, query: str = "") -> list[CollectedProject]: ...


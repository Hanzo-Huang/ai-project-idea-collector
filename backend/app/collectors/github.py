import re
from datetime import datetime

import httpx

from app.collectors.base import CollectedProject
from app.config import get_config


class GitHubCollector:
    api_url = "https://api.github.com"

    def __init__(self) -> None:
        token = get_config().github_token
        self.headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-project-collector"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    @staticmethod
    def _repo_path(url: str) -> str:
        match = re.search(r"github\.com/([^/]+/[^/#?]+)", url)
        if not match:
            raise ValueError("Not a GitHub repository URL")
        return match.group(1).removesuffix(".git")

    async def collect_url(self, url: str) -> CollectedProject:
        path = self._repo_path(url)
        async with httpx.AsyncClient(headers=self.headers, timeout=20, follow_redirects=True) as client:
            response = await client.get(f"{self.api_url}/repos/{path}")
            response.raise_for_status()
            repo = response.json()
            readme_response = await client.get(f"{self.api_url}/repos/{path}/readme", headers={**self.headers, "Accept": "application/vnd.github.raw+json"})
        readme = readme_response.text if readme_response.is_success else ""
        return self._normalize(repo, readme)

    async def collect_source(self, url: str, query: str = "") -> list[CollectedProject]:
        path = url.rstrip("/").split("/")[-1]
        is_search = bool(query) or "search" in url
        endpoint = f"{self.api_url}/search/repositories" if is_search else f"{self.api_url}/users/{path}/repos"
        params = {"q": query, "sort": "updated", "per_page": 20} if is_search else {"sort": "updated", "per_page": 20}
        async with httpx.AsyncClient(headers=self.headers, timeout=25) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
        payload = response.json()
        repos = payload.get("items", payload)
        return [self._normalize(repo) for repo in repos]

    @staticmethod
    def _normalize(repo: dict, readme: str = "") -> CollectedProject:
        def dt(value: str | None) -> datetime | None:
            return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None

        topics = repo.get("topics", [])
        return CollectedProject(
            url=repo["html_url"], title=repo.get("full_name") or repo.get("name", "GitHub project"),
            description=repo.get("description") or "", content=(readme or repo.get("description") or "")[:50000],
            source_type="github", stars=repo.get("stargazers_count", 0),
            external_created_at=dt(repo.get("created_at")), external_updated_at=dt(repo.get("updated_at")),
            extra={"language": repo.get("language"), "topics": topics, "forks": repo.get("forks_count", 0), "license": (repo.get("license") or {}).get("spdx_id")},
        )


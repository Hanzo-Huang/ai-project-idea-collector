import uuid
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import selectinload

from app.collectors import collector_for_source
from app.database import SessionLocal
from app.models import CollectionLog, Project, Source, Tag
from app.services.pipeline import ingest_collected, ingest_url


mcp = FastMCP(
    "AI Project Idea Collector",
    instructions=(
        "Manage a collection of AI projects and discovery sources. Use search_projects before "
        "making recommendations, and use get_project when full project details are needed."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
)


def _project_data(project: Project) -> dict:
    return {
        "id": str(project.id),
        "url": project.url,
        "title": project.title,
        "description": project.description,
        "summary": project.summary,
        "source_type": project.source_type,
        "project_type": project.project_type,
        "subtype": project.subtype,
        "difficulty": project.difficulty,
        "hardware_requirements": project.hardware_requirements,
        "software_requirements": project.software_requirements,
        "inspired_ideas": project.inspired_ideas,
        "idea_value": project.idea_value,
        "stars": project.stars,
        "views": project.views,
        "likes": project.likes,
        "status": project.status,
        "error": project.error,
        "tags": [tag.name for tag in project.tags],
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def _source_data(source: Source) -> dict:
    return {
        "id": str(source.id),
        "name": source.name,
        "type": source.type,
        "url": source.url,
        "query": source.query,
        "enabled": source.enabled,
        "collection_prompt": source.collection_prompt,
        "refresh_interval": source.refresh_interval,
        "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
    }


@mcp.tool(
    description="Add a GitHub repository, video, article, model, demo, or generic webpage to the collection by URL.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True),
)
async def add_project(url: str) -> dict:
    async with SessionLocal() as db:
        project = await ingest_url(db, url)
        project = (await db.execute(
            select(Project).options(selectinload(Project.tags)).where(Project.id == project.id)
        )).scalar_one()
        return _project_data(project)


@mcp.tool(
    description="Search collected projects using keywords and optional classification filters.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
)
async def search_projects(
    query: str = "",
    project_type: str = "",
    subtype: str = "",
    source_type: str = "",
    difficulty: str = "",
    tag: str = "",
    sort: str = "idea_value",
    limit: int = 10,
) -> dict:
    limit = max(1, min(limit, 50))
    async with SessionLocal() as db:
        stmt = select(Project).options(selectinload(Project.tags)).distinct()
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(Project.title.ilike(pattern), Project.summary.ilike(pattern), Project.description.ilike(pattern)))
        if project_type: stmt = stmt.where(Project.project_type == project_type)
        if subtype: stmt = stmt.where(Project.subtype == subtype)
        if source_type: stmt = stmt.where(Project.source_type == source_type)
        if difficulty: stmt = stmt.where(Project.difficulty == difficulty)
        if tag: stmt = stmt.join(Project.tags).where(Tag.name == tag.lower())
        order = {
            "newest": Project.created_at,
            "popular": Project.stars + Project.views + Project.likes,
            "updated": Project.updated_at,
            "idea_value": Project.idea_value,
        }.get(sort, Project.idea_value)
        projects = (await db.execute(stmt.order_by(desc(order)).limit(limit))).scalars().unique().all()
        return {"count": len(projects), "projects": [_project_data(project) for project in projects]}


@mcp.tool(
    description="Get complete details for one collected project by UUID.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
)
async def get_project(project_id: str) -> dict:
    async with SessionLocal() as db:
        project = (await db.execute(
            select(Project).options(selectinload(Project.tags)).where(Project.id == uuid.UUID(project_id))
        )).scalar_one_or_none()
        if not project: raise ValueError("Project not found")
        return _project_data(project)


@mcp.tool(
    description="Permanently delete a collected project by UUID.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False),
)
async def delete_project(project_id: str) -> dict:
    async with SessionLocal() as db:
        project = await db.get(Project, uuid.UUID(project_id))
        if not project: return {"deleted": False, "reason": "Project not found"}
        await db.delete(project); await db.commit()
        return {"deleted": True, "project_id": project_id}


@mcp.tool(
    description="List all configured automatic collection sources.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
)
async def list_sources() -> dict:
    async with SessionLocal() as db:
        sources = (await db.execute(select(Source).order_by(Source.created_at.desc()))).scalars().all()
        return {"count": len(sources), "sources": [_source_data(source) for source in sources]}


@mcp.tool(
    description="Add an automatic collection source. Supported types: github, github_search, hackster, huggingface, rss, blog, youtube.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True),
)
async def add_source(
    name: str,
    source_type: str,
    url: str,
    query: str = "",
    refresh_interval: int = 360,
    collection_prompt: str = "",
    enabled: bool = True,
) -> dict:
    allowed = {"github", "github_search", "hackster", "huggingface", "rss", "blog", "youtube"}
    if source_type not in allowed: raise ValueError(f"Unsupported source type. Choose one of: {', '.join(sorted(allowed))}")
    if refresh_interval < 5: raise ValueError("refresh_interval must be at least 5 minutes")
    async with SessionLocal() as db:
        source = Source(name=name, type=source_type, url=url, query=query, refresh_interval=refresh_interval, collection_prompt=collection_prompt, enabled=enabled)
        db.add(source); await db.commit(); await db.refresh(source)
        return _source_data(source)


@mcp.tool(
    description="Enable or disable a source, rename it, or change its collection schedule and prompt.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False),
)
async def update_source(
    source_id: str,
    name: str | None = None,
    enabled: bool | None = None,
    refresh_interval: int | None = None,
    collection_prompt: str | None = None,
) -> dict:
    if refresh_interval is not None and refresh_interval < 5: raise ValueError("refresh_interval must be at least 5 minutes")
    async with SessionLocal() as db:
        source = await db.get(Source, uuid.UUID(source_id))
        if not source: raise ValueError("Source not found")
        for key, value in {"name": name, "enabled": enabled, "refresh_interval": refresh_interval, "collection_prompt": collection_prompt}.items():
            if value is not None: setattr(source, key, value)
        await db.commit(); await db.refresh(source)
        return _source_data(source)


@mcp.tool(
    description="Run one configured source immediately and add newly discovered projects.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True),
)
async def collect_source(source_id: str) -> dict:
    async with SessionLocal() as db:
        source = await db.get(Source, uuid.UUID(source_id))
        if not source: raise ValueError("Source not found")
        log = CollectionLog(source_id=source.id, status="running"); db.add(log); await db.commit()
        try:
            items = await collector_for_source(source.type).collect_source(source.url, source.query)
            added = 0
            for item in items:
                _, created = await ingest_collected(db, item, source.id); added += int(created)
            now = datetime.now(timezone.utc)
            source.last_checked_at = now; log.status = "complete"; log.projects_found = len(items); log.projects_added = added; log.finished_at = now
            await db.commit()
            return {"source_id": source_id, "found": len(items), "added": added}
        except Exception as exc:
            log.status = "failed"; log.message = str(exc)[:2000]; log.finished_at = datetime.now(timezone.utc); await db.commit()
            raise RuntimeError(f"Collection failed: {exc}") from exc


import uuid

from qdrant_client import AsyncQdrantClient, models as qm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.collectors import collector_for_url
from app.collectors.base import CollectedProject
from app.models import Embedding, MetricHistory, Project, RawDocument, Tag
from app.services.ai import analyze_project, embed_text
from app.services.settings import resolved_settings

COLLECTION = "projects"


async def ingest_url(db: AsyncSession, url: str, source_id: uuid.UUID | None = None) -> Project:
    existing = (await db.execute(select(Project).where(Project.url == url))).scalar_one_or_none()
    if existing: return existing
    project = Project(url=url, title=url, source_id=source_id, status="processing")
    db.add(project)
    await db.commit(); await db.refresh(project)
    try:
        item = await collector_for_url(url).collect_url(url)
        await enrich_project(db, project, item)
    except Exception as exc:
        project.status = "failed"; project.error = str(exc)[:2000]
        await db.commit(); await db.refresh(project)
    return project


async def ingest_collected(db: AsyncSession, item: CollectedProject, source_id: uuid.UUID | None = None) -> tuple[Project, bool]:
    existing = (await db.execute(select(Project).where(Project.url == item.url))).scalar_one_or_none()
    if existing: return existing, False
    project = Project(url=item.url, title=item.title, source_id=source_id, status="processing")
    db.add(project); await db.commit(); await db.refresh(project)
    try: await enrich_project(db, project, item)
    except Exception as exc:
        project.status = "failed"; project.error = str(exc)[:2000]; await db.commit()
    return project, True


async def enrich_project(db: AsyncSession, project: Project, item: CollectedProject) -> None:
    project = (await db.execute(
        select(Project)
        .options(selectinload(Project.tags), selectinload(Project.documents))
        .where(Project.id == project.id)
    )).scalar_one()
    settings = await resolved_settings(db)
    analysis = await analyze_project(item.title, item.description, item.content, item.extra, settings)
    project.title = item.title; project.description = item.description; project.summary = analysis.get("summary", "")
    project.source_type = item.source_type; project.project_type = analysis.get("project_type", "Application")
    project.subtype = analysis.get("subtype", "Other"); project.difficulty = analysis.get("difficulty", "Intermediate")
    project.hardware_requirements = analysis.get("hardware_requirements", []); project.software_requirements = analysis.get("software_requirements", [])
    project.idea_value = float(analysis.get("idea_value", 0)); project.inspired_ideas = analysis.get("inspired_ideas", [])
    project.stars = item.stars; project.views = item.views; project.likes = item.likes
    project.external_created_at = item.external_created_at; project.external_updated_at = item.external_updated_at
    project.extra = {
        **item.extra,
        "target_platforms": analysis.get("target_platforms", []),
        "rk_compatibility": analysis.get("rk_compatibility", 0),
        "adaptation_notes": analysis.get("adaptation_notes", []),
        "big_event_relevance": analysis.get("big_event_relevance", False),
    }
    project.status = "ready"; project.error = None
    project.documents.append(RawDocument(content=item.content, metadata_={"source_type": item.source_type}))
    for name in analysis.get("tags", [])[:12]:
        clean = str(name).strip().lower()[:100]
        if not clean: continue
        tag = (await db.execute(select(Tag).where(Tag.name == clean))).scalar_one_or_none()
        if not tag: tag = Tag(name=clean); db.add(tag); await db.flush()
        project.tags.append(tag)
    db.add(MetricHistory(project_id=project.id, stars=item.stars, views=item.views, likes=item.likes))
    await db.commit(); await db.refresh(project)
    vector = await embed_text(f"{project.title}\n{project.summary}\n{' '.join(t.name for t in project.tags)}\nRK compatibility: {project.extra.get('rk_compatibility', 0)}\nPlatforms: {' '.join(project.extra.get('target_platforms') or [])}", settings)
    if vector: await store_vector(db, project, vector, settings)


async def store_vector(db: AsyncSession, project: Project, vector: list[float], settings: dict) -> None:
    try:
        client = AsyncQdrantClient(url=str(settings["qdrant_url"]))
        collections = await client.get_collections()
        if COLLECTION not in {c.name for c in collections.collections}:
            await client.create_collection(COLLECTION, vectors_config=qm.VectorParams(size=len(vector), distance=qm.Distance.COSINE))
        point_id = str(project.id)
        await client.upsert(COLLECTION, points=[qm.PointStruct(id=point_id, vector=vector, payload={"project_id": point_id, "title": project.title})])
        db.add(Embedding(project_id=project.id, qdrant_point_id=point_id, provider=str(settings["embedding_provider"]), model=str(settings["embedding_model"])))
        await db.commit(); await client.close()
    except Exception:
        pass

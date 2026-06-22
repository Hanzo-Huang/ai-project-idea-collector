import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from qdrant_client import AsyncQdrantClient
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Project, Tag
from app.schemas import ProjectCreate, ProjectList, ProjectOut
from app.services.ai import embed_text
from app.services.pipeline import COLLECTION, ingest_url
from app.services.settings import resolved_settings

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=201)
async def add_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    return await ingest_url(db, str(payload.url))


@router.get("", response_model=ProjectList)
async def list_projects(
    q: str = "", semantic: bool = False, project_type: str | None = None, subtype: str | None = None,
    source_type: str | None = None, tag: str | None = None, difficulty: str | None = None,
    hardware: str | None = None, min_stars: int | None = None, min_views: int | None = None,
    min_likes: int | None = None, created_after: datetime | None = None, updated_after: datetime | None = None,
    sort: str = Query("newest", pattern="^(newest|popular|updated|idea_value)$"), page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100), db: AsyncSession = Depends(get_db),
):
    stmt = select(Project).distinct()
    if project_type: stmt = stmt.where(Project.project_type == project_type)
    if subtype: stmt = stmt.where(Project.subtype == subtype)
    if source_type: stmt = stmt.where(Project.source_type == source_type)
    if difficulty: stmt = stmt.where(Project.difficulty == difficulty)
    if tag: stmt = stmt.join(Project.tags).where(Tag.name == tag.lower())
    if hardware: stmt = stmt.where(Project.hardware_requirements.contains([hardware]))
    if min_stars is not None: stmt = stmt.where(Project.stars >= min_stars)
    if min_views is not None: stmt = stmt.where(Project.views >= min_views)
    if min_likes is not None: stmt = stmt.where(Project.likes >= min_likes)
    if created_after: stmt = stmt.where(Project.created_at >= created_after)
    if updated_after: stmt = stmt.where(Project.updated_at >= updated_after)
    semantic_ids: list[uuid.UUID] = []
    if q and semantic:
        settings = await resolved_settings(db); vector = await embed_text(q, settings)
        if vector:
            try:
                client = AsyncQdrantClient(url=str(settings["qdrant_url"]))
                hits = await client.query_points(COLLECTION, query=vector, limit=100)
                semantic_ids = [uuid.UUID(str(p.id)) for p in hits.points]; await client.close()
            except Exception: pass
    if semantic_ids: stmt = stmt.where(Project.id.in_(semantic_ids))
    elif q: stmt = stmt.where(or_(Project.title.ilike(f"%{q}%"), Project.summary.ilike(f"%{q}%"), Project.description.ilike(f"%{q}%")))
    count = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    order = {"newest": Project.created_at, "popular": Project.stars + Project.views + Project.likes, "updated": func.coalesce(Project.external_updated_at, Project.updated_at), "idea_value": Project.idea_value}[sort]
    items = (await db.execute(stmt.order_by(desc(order)).offset((page - 1) * page_size).limit(page_size))).scalars().unique().all()
    return ProjectList(items=items, total=count, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectOut)
async def project_detail(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project: raise HTTPException(404, "Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project: raise HTTPException(404, "Project not found")
    await db.delete(project); await db.commit()


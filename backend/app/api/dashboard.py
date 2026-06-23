from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Project, Source

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    projects = (await db.execute(select(func.count(Project.id)))).scalar_one()
    sources = (await db.execute(select(func.count(Source.id)).where(Source.enabled.is_(True)))).scalar_one()
    types = dict((await db.execute(select(Project.project_type, func.count(Project.id)).group_by(Project.project_type))).all())
    recent = (await db.execute(select(Project).order_by(Project.created_at.desc()).limit(6))).scalars().all()
    return {"projects": projects, "active_sources": sources, "average_idea_value": round(float((await db.execute(select(func.avg(Project.idea_value)))).scalar() or 0), 1), "types": types, "recent": [{"id": str(p.id), "title": p.title, "summary": p.summary, "type": p.project_type, "source_type": p.source_type, "idea_value": p.idea_value, "stars": p.stars, "status": p.status} for p in recent]}

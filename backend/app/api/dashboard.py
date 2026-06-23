from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CollectionLog, Project, Source

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    projects = (await db.execute(select(func.count(Project.id)))).scalar_one()
    sources = (await db.execute(select(func.count(Source.id)).where(Source.enabled.is_(True)))).scalar_one()
    types = dict((await db.execute(select(Project.project_type, func.count(Project.id)).group_by(Project.project_type))).all())
    recent = (await db.execute(select(Project).order_by(Project.created_at.desc()).limit(6))).scalars().all()
    return {"projects": projects, "active_sources": sources, "average_idea_value": round(float((await db.execute(select(func.avg(Project.idea_value)))).scalar() or 0), 1), "types": types, "recent": [{"id": str(p.id), "title": p.title, "summary": p.summary, "type": p.project_type, "source_type": p.source_type, "idea_value": p.idea_value, "stars": p.stars, "status": p.status} for p in recent]}


@router.get("/tasks")
async def tasks(db: AsyncSession = Depends(get_db)):
    project_rows = (await db.execute(select(Project).order_by(desc(Project.updated_at)).limit(20))).scalars().all()
    log_rows = (await db.execute(select(CollectionLog).order_by(desc(CollectionLog.started_at)).limit(10))).scalars().all()
    active = sum(1 for project in project_rows if project.status in {"pending", "processing"}) + sum(1 for log in log_rows if log.status == "running")
    failed = sum(1 for project in project_rows if project.status == "failed") + sum(1 for log in log_rows if log.status == "failed")
    return {
        "active": active,
        "failed": failed,
        "projects": [
            {
                "id": str(project.id),
                "title": project.title,
                "url": project.url,
                "status": project.status,
                "error": project.error,
                "updated_at": project.updated_at.isoformat(),
            }
            for project in project_rows
            if project.status in {"pending", "processing", "failed"} or not project.summary
        ][:10],
        "collections": [
            {
                "id": str(log.id),
                "status": log.status,
                "message": log.message,
                "projects_found": log.projects_found,
                "projects_added": log.projects_added,
                "started_at": log.started_at.isoformat(),
                "finished_at": log.finished_at.isoformat() if log.finished_at else None,
            }
            for log in log_rows
        ],
    }

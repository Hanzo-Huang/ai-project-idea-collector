import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors import collector_for_source
from app.database import get_db
from app.models import CollectionLog, Source
from app.schemas import SourceCreate, SourceOut, SourceUpdate
from app.services.pipeline import ingest_collected

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def list_sources(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Source).order_by(Source.created_at.desc()))).scalars().all()


@router.post("", response_model=SourceOut, status_code=201)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    source = Source(**payload.model_dump()); db.add(source); await db.commit(); await db.refresh(source); return source


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(source_id: uuid.UUID, payload: SourceUpdate, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source: raise HTTPException(404, "Source not found")
    for key, value in payload.model_dump(exclude_none=True).items(): setattr(source, key, value)
    await db.commit(); await db.refresh(source); return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source: raise HTTPException(404, "Source not found")
    await db.delete(source); await db.commit()


@router.post("/{source_id}/collect")
async def collect_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source: raise HTTPException(404, "Source not found")
    log = CollectionLog(source_id=source.id, status="running"); db.add(log); await db.commit()
    try:
        items = await collector_for_source(source.type).collect_source(source.url, source.query)
        added = 0
        for item in items:
            _, created = await ingest_collected(db, item, source.id); added += int(created)
        source.last_checked_at = datetime.now(timezone.utc); log.status = "complete"; log.projects_found = len(items); log.projects_added = added; log.finished_at = datetime.now(timezone.utc)
        await db.commit(); return {"found": len(items), "added": added}
    except Exception as exc:
        log.status = "failed"; log.message = str(exc); log.finished_at = datetime.now(timezone.utc); await db.commit(); raise HTTPException(502, str(exc)) from exc


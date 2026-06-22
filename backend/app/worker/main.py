import asyncio
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.collectors import collector_for_source
from app.database import SessionLocal, init_db
from app.models import CollectionLog, Source
from app.services.pipeline import ingest_collected
from app.services.settings import resolved_settings


async def collect_due_sources() -> None:
    async with SessionLocal() as db:
        settings = await resolved_settings(db)
        if not settings.get("auto_collection_enabled", True): return
        sources = (await db.execute(select(Source).where(Source.enabled.is_(True)))).scalars().all()
        now = datetime.now(timezone.utc)
        for source in sources:
            if source.last_checked_at and source.last_checked_at + timedelta(minutes=source.refresh_interval) > now: continue
            log = CollectionLog(source_id=source.id, status="running"); db.add(log); await db.commit()
            try:
                items = await collector_for_source(source.type).collect_source(source.url, source.query); added = 0
                for item in items:
                    _, created = await ingest_collected(db, item, source.id); added += int(created)
                source.last_checked_at = now; log.status = "complete"; log.projects_found = len(items); log.projects_added = added
            except Exception as exc:
                log.status = "failed"; log.message = str(exc)[:2000]
            log.finished_at = datetime.now(timezone.utc); await db.commit()


async def main() -> None:
    await init_db()
    async with SessionLocal() as db: interval = int((await resolved_settings(db))["collector_interval"])
    scheduler = AsyncIOScheduler(); scheduler.add_job(collect_due_sources, "interval", minutes=interval, max_instances=1); scheduler.start()
    await collect_due_sources(); await asyncio.Event().wait()


if __name__ == "__main__": asyncio.run(main())


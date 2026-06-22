from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import SettingsUpdate
from app.services.settings import public_settings, save_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)): return await public_settings(db)


@router.put("")
async def update_settings(payload: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    await save_settings(db, payload.model_dump(exclude_none=True)); return await public_settings(db)


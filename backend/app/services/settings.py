from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config
from app.models import Setting

SECRET_KEYS = {"llm_api_key", "embedding_api_key"}
SETTING_KEYS = {
    "llm_base_url", "llm_api_key", "llm_model", "embedding_provider", "embedding_base_url",
    "embedding_api_key", "embedding_model", "qdrant_url", "postgres_url", "collector_interval",
    "classification_prompt", "source_filtering_prompt", "auto_collection_enabled",
}


async def resolved_settings(db: AsyncSession) -> dict[str, str | int | bool]:
    config = get_config()
    values = {key: getattr(config, key) for key in SETTING_KEYS}
    rows = (await db.execute(select(Setting))).scalars().all()
    for row in rows:
        if row.key in {"collector_interval"}: values[row.key] = int(row.value)
        elif row.key == "auto_collection_enabled": values[row.key] = row.value.lower() == "true"
        else: values[row.key] = row.value
    return values


async def public_settings(db: AsyncSession) -> dict:
    values = await resolved_settings(db)
    for key in SECRET_KEYS:
        values[f"{key}_configured"] = bool(values.pop(key, ""))
    return values


async def save_settings(db: AsyncSession, updates: dict) -> None:
    for key, value in updates.items():
        if key not in SETTING_KEYS or value is None or (key in SECRET_KEYS and value == ""): continue
        row = await db.get(Setting, key)
        text = str(value).lower() if isinstance(value, bool) else str(value)
        if row: row.value = text
        else: db.add(Setting(key=key, value=text, is_secret=key in SECRET_KEYS))
    await db.commit()


import json

import httpx
from openai import AsyncOpenAI

from app.services.analysis import fallback_analysis, normalize_analysis

PROJECT_TYPES = ["Agent", "Model", "Application", "Dataset", "Tool / Framework", "Hardware Demo", "Tutorial / Blog", "AI Event / Trend"]


async def analyze_project(title: str, description: str, content: str, extra: dict, settings: dict) -> dict:
    fallback = fallback_analysis(title, description or content, extra)
    if not settings.get("llm_api_key"):
        return fallback
    client = AsyncOpenAI(api_key=str(settings["llm_api_key"]), base_url=str(settings["llm_base_url"]), timeout=30)
    prompt = f'''{settings.get("classification_prompt", "Classify this AI project.")}
Return strict JSON with: summary, project_type, subtype, tags (array), difficulty (Beginner/Intermediate/Advanced), hardware_requirements (array), software_requirements (array), idea_value (0-10), inspired_ideas (array), target_platforms (array), rk_compatibility (0-10), adaptation_notes (array), big_event_relevance (boolean).
Allowed project types: {PROJECT_TYPES}.
Target boards: RK3576 and RK3588. Score rk_compatibility by how useful this is for Rockchip edge AI/NPU demos, board tutorials, product ideas, or ecosystem tracking. For AI events, explain how the event could inspire board content.
Title: {title}\nDescription: {description}\nContent: {content[:12000]}'''
    try:
        response = await client.chat.completions.create(model=str(settings["classification_model"]), messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"}, temperature=0.2)
        analysis = json.loads(response.choices[0].message.content or "{}")
        return normalize_analysis(analysis if isinstance(analysis, dict) else {}, fallback)
    except Exception:
        return fallback


async def embed_text(text: str, settings: dict) -> list[float] | None:
    if settings.get("embedding_provider") == "ollama":
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f'{str(settings["embedding_base_url"]).rstrip("/")}/api/embed', json={"model": settings["embedding_model"], "input": text})
                response.raise_for_status()
                return response.json()["embeddings"][0]
        except Exception:
            return None
    if not settings.get("embedding_api_key"): return None
    client = AsyncOpenAI(api_key=str(settings["embedding_api_key"]), base_url=str(settings["embedding_base_url"]))
    result = await client.embeddings.create(model=str(settings["embedding_model"]), input=text[:8000])
    return result.data[0].embedding

import json
import re

import httpx
from openai import AsyncOpenAI

PROJECT_TYPES = ["Agent", "Model", "Application", "Dataset", "Tool / Framework", "Hardware Demo", "Tutorial / Blog"]


def fallback_analysis(title: str, text: str, extra: dict) -> dict:
    content = f"{title} {text}".lower()
    project_type, subtype = "Application", "Other"
    rules = [
        ("agent", "Agent", "Workflow Agent"), ("dataset", "Dataset", "Other"),
        ("framework", "Tool / Framework", "Other"), ("tutorial", "Tutorial / Blog", "Other"),
        ("llm", "Model", "LLM"), ("vlm", "Model", "VLM"), ("embedding", "Model", "Embedding Model"),
        ("robot", "Hardware Demo", "Robotics Agent"), ("yolo", "Application", "YOLO trained model"),
    ]
    for needle, kind, sub in rules:
        if needle in content: project_type, subtype = kind, sub; break
    tags = list(dict.fromkeys([*(extra.get("topics") or []), *re.findall(r"\b(ai|llm|rag|agent|robotics|vision|yolo|edge|python|typescript)\b", content)]))[:8]
    summary = text.strip().replace("\n", " ")[:500] or f"{title} is a collected AI project."
    return {"summary": summary, "project_type": project_type, "subtype": subtype, "tags": tags or ["ai"], "difficulty": "Intermediate", "hardware_requirements": [], "software_requirements": [extra.get("language")] if extra.get("language") else [], "idea_value": 6.5, "inspired_ideas": [f"Adapt {title} to a focused industry workflow", f"Create an edge-friendly demo based on {title}"]}


async def analyze_project(title: str, description: str, content: str, extra: dict, settings: dict) -> dict:
    if not settings.get("llm_api_key"):
        return fallback_analysis(title, description or content, extra)
    client = AsyncOpenAI(api_key=str(settings["llm_api_key"]), base_url=str(settings["llm_base_url"]))
    prompt = f'''{settings.get("classification_prompt", "Classify this AI project.")}
Return strict JSON with: summary, project_type, subtype, tags (array), difficulty (Beginner/Intermediate/Advanced), hardware_requirements (array), software_requirements (array), idea_value (0-10), inspired_ideas (array).
Allowed project types: {PROJECT_TYPES}.
Title: {title}\nDescription: {description}\nContent: {content[:12000]}'''
    response = await client.chat.completions.create(model=str(settings["classification_model"]), messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"}, temperature=0.2)
    return json.loads(response.choices[0].message.content or "{}")


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

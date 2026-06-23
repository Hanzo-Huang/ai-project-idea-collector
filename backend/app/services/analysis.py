import re

from app.services.rk import rk_signals


def _clean_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


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
        if needle in content:
            project_type, subtype = kind, sub
            break
    tags = list(dict.fromkeys([*(extra.get("topics") or []), *re.findall(r"\b(ai|llm|rag|agent|robotics|vision|yolo|edge|python|typescript)\b", content)]))[:8]
    summary = text.strip().replace("\n", " ")[:500] or f"{title} is a collected AI project."
    return {
        "summary": summary,
        "project_type": project_type,
        "subtype": subtype,
        "tags": tags or ["ai"],
        "difficulty": "Intermediate",
        "hardware_requirements": [],
        "software_requirements": [extra.get("language")] if extra.get("language") else [],
        "idea_value": 6.5,
        "inspired_ideas": [f"Adapt {title} to an RK3576/RK3588 edge AI workflow", f"Create a board-ready demo based on {title}"],
        **rk_signals(title, text, extra),
    }


def normalize_analysis(analysis: dict, fallback: dict) -> dict:
    merged = {**fallback, **{key: value for key, value in analysis.items() if value not in (None, "", [], {})}}
    for key in ["tags", "hardware_requirements", "software_requirements", "inspired_ideas", "target_platforms", "adaptation_notes"]:
        items = _clean_list(merged.get(key))
        merged[key] = items or fallback.get(key, [])
    try:
        merged["idea_value"] = max(0, min(10, float(merged.get("idea_value", fallback["idea_value"]))))
    except (TypeError, ValueError):
        merged["idea_value"] = fallback["idea_value"]
    try:
        merged["rk_compatibility"] = max(0, min(10, float(merged.get("rk_compatibility", fallback["rk_compatibility"]))))
    except (TypeError, ValueError):
        merged["rk_compatibility"] = fallback["rk_compatibility"]
    merged["big_event_relevance"] = bool(merged.get("big_event_relevance", fallback.get("big_event_relevance", False)))
    return merged

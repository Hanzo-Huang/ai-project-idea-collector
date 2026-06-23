import re

from app.services.rk import rk_signals

KNOWN_PLATFORMS = ["RK3562", "RK3566", "RK3568", "RK3576", "RK3588", "RV1126B", "RV1103", "RV1106", "RV1109", "RV1126", "RK1808"]


def _clean_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def clean_markdown(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#|]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detected_platforms(text: str) -> list[str]:
    found = []
    upper = text.upper()
    for platform in KNOWN_PLATFORMS:
        if platform.upper() in upper:
            found.append(platform)
    return found


def rockchip_summary(title: str, text: str) -> str | None:
    content = clean_markdown(text)
    lower = f"{title} {content}".lower()
    platforms = detected_platforms(content)
    platform_text = f" It explicitly supports {', '.join(platforms)}." if platforms else ""
    if "rknn model zoo" in lower or "rknn_model_zoo" in lower:
        return (
            "RKNN Model Zoo is a Rockchip RKNPU SDK example collection for deploying mainstream AI algorithms. "
            "It covers RKNN export plus Python API and C API inference workflows for board-side demos."
            f"{platform_text}"
        )
    if "rkllm" in lower or "rkllm-toolkit" in lower:
        return (
            "RKLLM is a Rockchip LLM deployment stack for converting trained language models into RKLLM format and running inference on Rockchip development boards through the RKLLM C API."
            f"{platform_text}"
        )
    if "rknn" in lower or "rockchip" in lower or "rknpu" in lower:
        return f"{title} is a Rockchip edge AI project related to RKNN/RKNPU deployment, useful for RK3576/RK3588 board demos.{platform_text}"
    return None


def rockchip_requirements(title: str, text: str, extra: dict) -> tuple[list[str], list[str]]:
    content = f"{title} {text}".lower()
    hardware = detected_platforms(text)
    software = []
    for name, needle in [
        ("RKNPU SDK", "rknpu"),
        ("RKNN Toolkit", "rknn"),
        ("RKLLM Toolkit", "rkllm"),
        ("Python API", "python api"),
        ("C API", "capi"),
        ("ONNX export", "onnx"),
    ]:
        if needle in content:
            software.append(name)
    if extra.get("language"):
        software.append(str(extra["language"]))
    return list(dict.fromkeys(hardware)), list(dict.fromkeys(software))


def fallback_analysis(title: str, text: str, extra: dict) -> dict:
    content = f"{title} {text}".lower()
    project_type, subtype = "Application", "Other"
    rules = [
        ("agent", "Agent", "Workflow Agent"), ("dataset", "Dataset", "Other"),
        ("framework", "Tool / Framework", "Other"), ("tutorial", "Tutorial / Blog", "Other"),
        ("llm", "Model", "LLM"), ("vlm", "Model", "VLM"), ("embedding", "Model", "Embedding Model"),
        ("rkllm", "Tool / Framework", "Other"), ("rknn", "Tool / Framework", "Other"),
        ("robot", "Hardware Demo", "Robotics Agent"), ("yolo", "Application", "YOLO trained model"),
    ]
    for needle, kind, sub in rules:
        if needle in content:
            project_type, subtype = kind, sub
            break
    tags = list(dict.fromkeys([*(extra.get("topics") or []), *re.findall(r"\b(ai|llm|rag|agent|robotics|vision|yolo|edge|python|typescript|rknn|rkllm|rknpu|rockchip|onnx)\b", content)]))[:8]
    summary = rockchip_summary(title, text) or clean_markdown(text)[:500] or f"{title} is a collected AI project."
    hardware, software = rockchip_requirements(title, text, extra)
    signals = rk_signals(title, text, extra)
    return {
        "summary": summary,
        "project_type": project_type,
        "subtype": subtype,
        "tags": tags or ["ai"],
        "difficulty": "Intermediate",
        "hardware_requirements": hardware,
        "software_requirements": software,
        "idea_value": max(6.5, min(9.0, float(signals["rk_compatibility"]))),
        "inspired_ideas": [
            f"Turn {title} into an RK3576/RK3588 quick-start tutorial with model conversion and board-side inference steps.",
            f"Create a Seeed-style demo showing camera/audio/input pipeline, RKNN or RKLLM conversion, and performance notes.",
            f"Compare supported boards and identify which models are practical for RK3576 versus RK3588.",
        ],
        **signals,
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

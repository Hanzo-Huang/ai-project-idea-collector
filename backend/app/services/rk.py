TARGET_PLATFORMS = ["RK3576", "RK3588"]


def rk_signals(title: str, text: str, extra: dict) -> dict:
    content = f"{title} {text} {' '.join(extra.get('topics') or [])}".lower()
    platforms = []
    if "rk3576" in content:
        platforms.append("RK3576")
    if "rk3588" in content or "rknn" in content or "rockchip" in content:
        platforms.append("RK3588")
    edge_terms = ["edge", "npu", "rknn", "onnx", "yolo", "opencv", "camera", "robot", "audio", "tts", "stt", "vlm", "ocr", "detection", "segmentation"]
    score = min(10, 3 + sum(1 for term in edge_terms if term in content))
    if platforms:
        score = max(score, 8)
    notes = []
    if "onnx" in content or "pytorch" in content or "yolo" in content:
        notes.append("Check ONNX export and RKNN conversion path.")
    if "camera" in content or "opencv" in content or "detection" in content:
        notes.append("Good fit for camera/NPU demo content.")
    if "llm" in content or "vlm" in content:
        notes.append("Verify memory footprint and quantized runtime on board.")
    return {
        "target_platforms": platforms or TARGET_PLATFORMS,
        "rk_compatibility": score,
        "adaptation_notes": notes or ["Evaluate model size, runtime dependencies, and RKNN/ONNX deployment path."],
        "big_event_relevance": any(term in content for term in ["release", "launch", "conference", "paper", "benchmark", "open source", "open-source"]),
    }

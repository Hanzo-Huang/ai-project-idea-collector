def normalized_message(message: str) -> str:
    return " ".join(message.lower().strip().strip("?!.,;:").split())


def direct_answer(message: str) -> str | None:
    normalized = normalized_message(message)
    if normalized in {"hi", "hello", "hey", "yo", "你好", "hi there", "hello there"}:
        return "Hi! I can help you search your collected AI projects, compare them, and turn them into new project ideas."
    if normalized in {"who are you", "what are you", "who r u", "what can you do"}:
        return "I am the AI Project Idea Collector assistant. I answer using your saved project collection, cite source URLs, and help brainstorm related ideas."
    if normalized in {"help", "how to use", "what should i ask"}:
        return "Ask me things like: \"Find edge AI projects using YOLO\", \"Give me ideas from robotics agents\", or \"Which projects are good for technical wiki content?\""
    return None


def clean_history(history: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned = []
    for item in history[-8:]:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            cleaned.append({"role": role, "content": content[:1200]})
    return cleaned

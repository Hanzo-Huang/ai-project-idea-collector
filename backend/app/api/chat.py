from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Project
from app.schemas import ChatCitation, ChatRequest, ChatResponse
from app.services.chat import clean_history, direct_answer
from app.services.settings import resolved_settings

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    if answer := direct_answer(payload.message):
        return ChatResponse(answer=answer, citations=[])

    words = [w for w in payload.message.split() if len(w) > 3][:8]
    stmt = select(Project).where(Project.status == "ready")
    if words: stmt = stmt.where(or_(*[Project.title.ilike(f"%{w}%") for w in words], *[Project.summary.ilike(f"%{w}%") for w in words]))
    projects = (await db.execute(stmt.order_by(Project.idea_value.desc()).limit(8))).scalars().all()
    if not projects: projects = (await db.execute(select(Project).where(Project.status == "ready").order_by(Project.idea_value.desc()).limit(8))).scalars().all()
    citations = [ChatCitation(id=p.id, title=p.title, url=p.url) for p in projects]
    context = "\n".join(f"[{i+1}] {p.title}: {p.summary} URL: {p.url}" for i, p in enumerate(projects))
    settings = await resolved_settings(db)
    if not settings.get("llm_api_key"):
        answer = "Here are the closest projects in your collection:\n\n" + "\n".join(f"- {p.title}: {p.summary[:180]} ({p.url})" for p in projects)
        return ChatResponse(answer=answer, citations=citations)
    client = AsyncOpenAI(api_key=str(settings["llm_api_key"]), base_url=str(settings["llm_base_url"]))
    messages = [
        {
            "role": "system",
            "content": (
                "You are the AI Project Idea Collector assistant. Use only the supplied project context for project recommendations, comparisons, and idea generation. "
                "Cite relevant projects as [1], [2]. If the context does not contain enough evidence, say that clearly and suggest what to collect next. "
                "Be concise, fluent, and do not invent sources."
            ),
        },
        *clean_history(payload.history),
        {"role": "user", "content": f"PROJECT CONTEXT:\n{context or 'No matching projects found.'}\n\nQUESTION: {payload.message}"},
    ]
    response = await client.chat.completions.create(model=str(settings["chat_model"]), messages=messages, temperature=0.1, max_tokens=700)
    return ChatResponse(answer=response.choices[0].message.content or "", citations=citations)

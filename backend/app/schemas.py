import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    url: str
    title: str
    description: str
    summary: str
    source_type: str
    project_type: str
    subtype: str
    difficulty: str
    hardware_requirements: list[str]
    software_requirements: list[str]
    inspired_ideas: list[str]
    idea_value: float
    stars: int
    views: int
    likes: int
    status: str
    error: str | None
    extra: dict[str, Any]
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime
    external_created_at: datetime | None
    external_updated_at: datetime | None


class ProjectList(BaseModel):
    items: list[ProjectOut]
    total: int
    page: int
    page_size: int


class ProjectCreate(BaseModel):
    url: HttpUrl


class SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: Literal["github", "github_search", "hackster", "huggingface", "rss", "blog", "youtube"]
    url: str
    query: str = ""
    enabled: bool = True
    collection_prompt: str = ""
    refresh_interval: int = Field(default=360, ge=5)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    collection_prompt: str | None = None
    refresh_interval: int | None = Field(default=None, ge=5)


class SourceOut(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SettingsUpdate(BaseModel):
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    embedding_provider: Literal["openai", "ollama"] | None = None
    embedding_base_url: str | None = None
    embedding_api_key: str | None = None
    embedding_model: str | None = None
    qdrant_url: str | None = None
    postgres_url: str | None = None
    collector_interval: int | None = Field(default=None, ge=1)
    classification_prompt: str | None = None
    source_filtering_prompt: str | None = None
    auto_collection_enabled: bool | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=20)


class ChatCitation(BaseModel):
    id: uuid.UUID
    title: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[ChatCitation]


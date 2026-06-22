import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


project_tags = Table(
    "project_tags",
    Base.metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(Text, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String(50), default="webpage", index=True)
    project_type: Mapped[str] = mapped_column(String(50), default="Application", index=True)
    subtype: Mapped[str] = mapped_column(String(100), default="Other", index=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="Intermediate", index=True)
    hardware_requirements: Mapped[list[str]] = mapped_column(JSONB, default=list)
    software_requirements: Mapped[list[str]] = mapped_column(JSONB, default=list)
    inspired_ideas: Mapped[list[str]] = mapped_column(JSONB, default=list)
    idea_value: Mapped[float] = mapped_column(Float, default=0)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    external_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ProjectStatus.pending.value, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"))
    tags: Mapped[list["Tag"]] = relationship(secondary=project_tags, lazy="selectin")
    documents: Mapped[list["RawDocument"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Source(TimestampMixin, Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(50), index=True)
    url: Mapped[str] = mapped_column(Text)
    query: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    collection_prompt: Mapped[str] = mapped_column(Text, default="")
    refresh_interval: Mapped[int] = mapped_column(Integer, default=360)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)


class MetricHistory(Base):
    __tablename__ = "metrics_history"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RawDocument(Base):
    __tablename__ = "raw_documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    project: Mapped[Project] = relationship(back_populates="documents")


class Embedding(Base):
    __tablename__ = "embeddings"
    __table_args__ = (UniqueConstraint("project_id", "provider", "model"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    qdrant_point_id: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CollectionLog(Base):
    __tablename__ = "collection_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text, default="")
    projects_found: Mapped[int] = mapped_column(Integer, default=0)
    projects_added: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

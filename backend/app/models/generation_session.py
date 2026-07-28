"""
Curato AI — Generation Session Model

Represents a single content generation workflow execution.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class GenerationSession(Base, UUIDMixin, TimestampMixin):
    """
    A single end-to-end content generation run.
    Tracks the full lifecycle from trigger to completion.
    """

    __tablename__ = "generation_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )
    current_agent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Phase 7.5 Fields
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    cancelled: Mapped[bool] = mapped_column(default=False, nullable=False)
    dead_lettered: Mapped[bool] = mapped_column(default=False, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="generation_sessions")
    agent_runs = relationship(
        "AgentRun", back_populates="session", lazy="selectin", order_by="AgentRun.created_at"
    )
    research_results = relationship("ResearchResult", back_populates="session", lazy="selectin")
    topic_scores = relationship("TopicScore", back_populates="session", lazy="selectin")
    content_drafts = relationship(
        "ContentDraft", back_populates="session", lazy="selectin", order_by="ContentDraft.version"
    )
    feedback_entries = relationship("Feedback", back_populates="session", lazy="selectin")
    integration_links = relationship("IntegrationLink", back_populates="session", lazy="selectin")
    workflow_logs = relationship(
        "WorkflowLog", back_populates="session", lazy="selectin", order_by="WorkflowLog.created_at"
    )

    def __repr__(self) -> str:
        return f"<GenerationSession {self.id} status={self.status}>"

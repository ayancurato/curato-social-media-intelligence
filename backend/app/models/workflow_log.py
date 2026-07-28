"""
Curato AI — Workflow Log Model

Step-by-step audit trail for every workflow execution.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class WorkflowLog(Base, UUIDMixin, TimestampMixin):
    """
    Granular log entries for workflow execution.
    Provides a complete audit trail for debugging and observability.
    """

    __tablename__ = "workflow_logs"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info"
    )  # info, warning, error, debug
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    session = relationship("GenerationSession", back_populates="workflow_logs")

    def __repr__(self) -> str:
        return f"<WorkflowLog [{self.level}] {self.message[:50]}>"

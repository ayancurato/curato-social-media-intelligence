"""
Curato AI — Agent Run Model

Records each individual agent execution within a generation session.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AgentRun(Base, UUIDMixin, TimestampMixin):
    """
    Records a single agent's execution within a workflow.
    Stores input/output data as JSONB for full traceability.
    """

    __tablename__ = "agent_runs"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    token_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    session = relationship("GenerationSession", back_populates="agent_runs")

    def __repr__(self) -> str:
        return f"<AgentRun {self.agent_name} status={self.status}>"

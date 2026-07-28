"""
Curato AI — Feedback Model

Stores feedback from the Chief Editor and CMO agents.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Feedback(Base, UUIDMixin, TimestampMixin):
    """
    Feedback from Agent 5 (Chief Editor) or Agent 6 (CMO).
    Tracks approval decisions and revision notes.
    """

    __tablename__ = "feedback"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    draft_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_drafts.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_notes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    iteration_number: Mapped[int] = mapped_column(default=1, nullable=False)

    # Relationships
    session = relationship("GenerationSession", back_populates="feedback_entries")

    def __repr__(self) -> str:
        return f"<Feedback by={self.agent_name} approved={self.approved}>"

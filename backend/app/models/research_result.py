"""
Curato AI — Research Result Model

Stores structured output from the Research Intelligence agent.
"""

import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ResearchResult(Base, UUIDMixin, TimestampMixin):
    """
    Structured research output from Agent 1 (Research Intelligence).
    Contains trending topics, industry news, competitor analysis, etc.
    """

    __tablename__ = "research_results"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    sources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    session = relationship("GenerationSession", back_populates="research_results")

    def __repr__(self) -> str:
        return f"<ResearchResult session={self.session_id}>"

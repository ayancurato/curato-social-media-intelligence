"""
Curato AI — Topic Score Model

Stores prioritized topic rankings from Agent 2.
"""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TopicScore(Base, UUIDMixin, TimestampMixin):
    """
    A scored and prioritized topic from Agent 2 (Topic Prioritization).
    Each generation session may produce multiple scored topics.
    """

    __tablename__ = "topic_scores"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_title: Mapped[str] = mapped_column(String(500), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trending_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    session = relationship("GenerationSession", back_populates="topic_scores")

    def __repr__(self) -> str:
        return f"<TopicScore '{self.topic_title}' score={self.overall_score}>"

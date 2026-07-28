"""
Curato AI — Human Evaluation Model
Tracks structured human feedback for closing the AI alignment loop.
"""

import uuid
from sqlalchemy import ForeignKey, Integer, Text, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class HumanEvaluation(Base, UUIDMixin, TimestampMixin):
    """
    Records structured human evaluations for a completed session or specific draft.
    """
    
    __tablename__ = "human_evaluations"

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
        index=True,
    )
    
    evaluator_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Dimensional Scores (1-5 scale)
    hook_quality: Mapped[int] = mapped_column(Integer, nullable=False)
    authority: Mapped[int] = mapped_column(Integer, nullable=False)
    clarity: Mapped[int] = mapped_column(Integer, nullable=False)
    readability: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement: Mapped[int] = mapped_column(Integer, nullable=False)
    brand_voice: Mapped[int] = mapped_column(Integer, nullable=False)
    business_alignment: Mapped[int] = mapped_column(Integer, nullable=False)
    originality: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Binary/Aggregate
    publishable: Mapped[bool] = mapped_column(default=False)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)

    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint('hook_quality >= 1 AND hook_quality <= 5', name='check_hook_quality_range'),
        CheckConstraint('authority >= 1 AND authority <= 5', name='check_authority_range'),
        CheckConstraint('clarity >= 1 AND clarity <= 5', name='check_clarity_range'),
        CheckConstraint('overall_rating >= 1 AND overall_rating <= 5', name='check_overall_rating_range'),
    )

    # Relationships
    session = relationship("GenerationSession", backref="human_evaluations")
    draft = relationship("ContentDraft")

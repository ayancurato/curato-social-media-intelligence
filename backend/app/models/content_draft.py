"""
Curato AI — Content Draft Model

Stores content drafts from the Writer and revisions after Editor feedback.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ContentDraft(Base, UUIDMixin, TimestampMixin):
    """
    A content draft produced by Agent 4 (Content Writer).
    Version tracks revision iterations through the approval loop.
    """

    __tablename__ = "content_drafts"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="linkedin")
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hashtags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    media_suggestions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    agent_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="content_writer"
    )

    # Relationships
    session = relationship("GenerationSession", back_populates="content_drafts")

    def __repr__(self) -> str:
        return f"<ContentDraft v{self.version} platform={self.platform}>"

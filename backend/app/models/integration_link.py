"""
Curato AI — Integration Link Model

Stores links to generated Google Docs / Google Sheets.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class IntegrationLink(Base, UUIDMixin, TimestampMixin):
    """
    External integration links (Google Docs, Google Sheets, etc.)
    associated with a generation session.
    """

    __tablename__ = "integration_links"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # google_doc, google_sheet
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    session = relationship("GenerationSession", back_populates="integration_links")

    def __repr__(self) -> str:
        return f"<IntegrationLink type={self.link_type}>"

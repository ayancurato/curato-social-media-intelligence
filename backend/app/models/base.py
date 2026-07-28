"""
Curato AI — SQLAlchemy Base Model & Mixins

Provides DeclarativeBase, UUID primary key mixin, and timestamp mixin.
All models inherit from these to ensure consistency.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all Curato AI models."""

    pass


class UUIDMixin:
    """Mixin that adds a UUID primary key column."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
        nullable=False,
    )

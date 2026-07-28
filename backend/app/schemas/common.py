"""
Curato AI — Common Schemas

Shared response envelopes and utility schemas.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    data: T | None = None
    error: str | None = None
    message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

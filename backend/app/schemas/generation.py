"""
Curato AI — Generation Schemas

Pydantic models for generation history and detail views.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class GenerationDetailResponse(BaseModel):
    """Full detail view of a generation session with all related data."""

    id: UUID
    status: str
    current_agent: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration_ms: int | None = None
    retry_count: int = 0
    error_message: str | None = None

    # Related data
    agent_runs: list[dict[str, Any]] = Field(default_factory=list)
    content_drafts: list[dict[str, Any]] = Field(default_factory=list)
    feedback_entries: list[dict[str, Any]] = Field(default_factory=list)
    integration_links: list[dict[str, Any]] = Field(default_factory=list)

    created_at: datetime

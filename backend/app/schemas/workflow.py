"""
Curato AI — Workflow Schemas

Pydantic models for workflow trigger, status, and history endpoints.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Trigger ──────────────────────────────────────────────────────────────────


class WorkflowTriggerRequest(BaseModel):
    """Request body for triggering a new generation workflow."""

    # Future: additional parameters like target platform, content type, etc.
    notes: str | None = Field(None, description="Optional notes for this generation run")


class WorkflowTriggerResponse(BaseModel):
    """Response after successfully triggering a workflow."""

    session_id: UUID
    status: str
    message: str


# ── Status ───────────────────────────────────────────────────────────────────


class AgentStatusDetail(BaseModel):
    """Status of a single agent within the workflow."""

    agent_name: str
    status: str  # pending, running, completed, failed, skipped
    duration_ms: int | None = None
    attempt_number: int = 1
    error: str | None = None


class WorkflowStatusResponse(BaseModel):
    """Current status of a running or completed workflow."""

    session_id: UUID
    status: str
    current_agent: str | None = None
    agents: list[AgentStatusDetail] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration_ms: int | None = None
    error_message: str | None = None
    retry_count: int = 0


# ── Logs ─────────────────────────────────────────────────────────────────────


class WorkflowLogEntry(BaseModel):
    """A single log entry from the workflow."""

    id: UUID
    level: str
    agent_name: str | None = None
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime


# ── History ──────────────────────────────────────────────────────────────────


class GenerationSummary(BaseModel):
    """Summary of a past generation session for the history table."""

    id: UUID
    status: str
    current_agent: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration_ms: int | None = None
    retry_count: int = 0
    created_at: datetime


# ── WebSocket Events ─────────────────────────────────────────────────────────


class WebSocketEvent(BaseModel):
    """Real-time event sent to dashboard via WebSocket."""

    event_type: str  # workflow_started, agent_started, agent_completed, etc.
    session_id: UUID
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

"""Curato AI — Schemas package."""

from app.schemas.common import ErrorResponse, PaginatedResponse, ResponseEnvelope
from app.schemas.workflow import (
    WebSocketEvent,
    WorkflowLogEntry,
    WorkflowStatusResponse,
    WorkflowTriggerRequest,
    WorkflowTriggerResponse,
)
from app.schemas.agent import AgentInput, AgentOutput
from app.schemas.generation import GenerationDetailResponse

__all__ = [
    "ResponseEnvelope",
    "PaginatedResponse",
    "ErrorResponse",
    "WorkflowTriggerRequest",
    "WorkflowTriggerResponse",
    "WorkflowStatusResponse",
    "WorkflowLogEntry",
    "WebSocketEvent",
    "AgentInput",
    "AgentOutput",
    "GenerationDetailResponse",
]

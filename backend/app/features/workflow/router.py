"""
Curato AI — Workflow API Router

REST endpoints for triggering and monitoring workflows.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import CurrentUser, get_current_user
from app.features.workflow.service import WorkflowService
from app.schemas.common import PaginatedResponse, ResponseEnvelope
from app.schemas.workflow import (
    GenerationSummary,
    WorkflowLogEntry,
    WorkflowStatusResponse,
    WorkflowTriggerRequest,
    WorkflowTriggerResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/workflow", tags=["Workflow"])

# NOTE: _background_run_workflow removed. The WorkflowService.trigger_workflow() method
# dispatches via a dedicated OS Thread (see service.py). That is the ONLY dispatch path.
# Having BackgroundTasks here AND a Thread in service.py caused every session to execute
# TWICE (plus a third time from the poller). Do not add dispatch logic here.


@router.post(
    "/trigger",
    response_model=ResponseEnvelope[WorkflowTriggerResponse],
    summary="Trigger a new content generation workflow",
)
async def trigger_workflow(
    request: WorkflowTriggerRequest | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[WorkflowTriggerResponse]:
    """
    Start a new content generation workflow.

    Creates a GenerationSession in DB and dispatches execution via a
    dedicated OS Thread (inside WorkflowService.trigger_workflow). 
    Returns the session ID immediately for real-time WebSocket tracking.

    IDEMPOTENCY: WorkflowService will not dispatch if a session for this
    user is already in RUNNING state. The orchestrator adds a second
    idempotency check at the top of execute().
    """
    logger.info("Workflow trigger requested via HTTP", user_id=str(user.id), initiator="http_endpoint")
    service = WorkflowService(db)
    result = await service.trigger_workflow(user.id)

    return ResponseEnvelope(
        success=True,
        data=result,
        message="Workflow triggered successfully",
    )


@router.get(
    "/{session_id}/status",
    response_model=ResponseEnvelope[WorkflowStatusResponse],
    summary="Get workflow status",
)
async def get_workflow_status(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[WorkflowStatusResponse]:
    """Get the current status of a running or completed workflow."""
    service = WorkflowService(db)
    result = await service.get_workflow_status(session_id)
    return ResponseEnvelope(success=True, data=result)


@router.get(
    "/{session_id}/logs",
    response_model=ResponseEnvelope[list[WorkflowLogEntry]],
    summary="Get workflow logs",
)
async def get_workflow_logs(
    session_id: UUID,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[list[WorkflowLogEntry]]:
    """Get execution logs for a workflow session."""
    service = WorkflowService(db)
    logs = await service.get_workflow_logs(session_id, limit)
    return ResponseEnvelope(success=True, data=logs)


@router.get(
    "/history",
    response_model=ResponseEnvelope[PaginatedResponse[GenerationSummary]],
    summary="Get generation history",
)
async def get_workflow_history(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[PaginatedResponse[GenerationSummary]]:
    """Get paginated list of past generation sessions."""
    service = WorkflowService(db)
    items, total = await service.get_workflow_history(page, page_size)

    total_pages = (total + page_size - 1) // page_size

    return ResponseEnvelope(
        success=True,
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )

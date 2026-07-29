"""
Curato AI — Workflow API Router

REST endpoints for triggering and monitoring workflows.
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
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


async def _background_run_workflow(session_id: str) -> None:
    """
    Background task wrapper for workflow execution.
    This runs AFTER the HTTP response is sent and the DB session is committed,
    so the GenerationSession row is guaranteed to exist.
    """
    print(f"[BACKGROUND TASK] Starting workflow for session {session_id}", flush=True)
    from app.workers.tasks import _run_workflow
    try:
        await _run_workflow(session_id)
        print(f"[BACKGROUND TASK] Workflow completed for session {session_id}", flush=True)
    except Exception as e:
        print(f"[BACKGROUND TASK] Workflow FAILED for session {session_id}: {e}", flush=True)
        logger.error("Background workflow task failed", session_id=session_id, error=str(e))


@router.post(
    "/trigger",
    response_model=ResponseEnvelope[WorkflowTriggerResponse],
    summary="Trigger a new content generation workflow",
)
async def trigger_workflow(
    background_tasks: BackgroundTasks,
    request: WorkflowTriggerRequest | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[WorkflowTriggerResponse]:
    """
    Start a new content generation workflow.

    This creates a generation session and dispatches the workflow
    as a background task (runs after response is sent so the DB commit
    has already happened). Returns the session ID for real-time tracking.
    """
    service = WorkflowService(db)
    result = await service.trigger_workflow(user.id)

    # BackgroundTasks runs AFTER the response is sent + DB is committed.
    # This guarantees the GenerationSession row exists when the task reads it.
    background_tasks.add_task(_background_run_workflow, str(result.session_id))

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

"""
Curato AI — Generations Router

REST endpoints for viewing generation history and details.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.generation_session import GenerationSession
from app.schemas.common import ResponseEnvelope
from app.schemas.generation import GenerationDetailResponse

router = APIRouter(prefix="/generations", tags=["Generations"])


@router.get(
    "/{session_id}",
    response_model=ResponseEnvelope[GenerationDetailResponse],
    summary="Get generation details",
)
async def get_generation_detail(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[GenerationDetailResponse]:
    """Get full details of a generation session including all related data."""
    session = await db.get(GenerationSession, session_id)
    if session is None:
        raise NotFoundError(message=f"Generation '{session_id}' not found")

    # Build agent runs list
    agent_runs = [
        {
            "id": str(run.id),
            "agent_name": run.agent_name,
            "status": run.status,
            "duration_ms": run.duration_ms,
            "attempt_number": run.attempt_number,
            "error_message": run.error_message,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
        for run in (session.agent_runs or [])
    ]

    # Build content drafts list
    content_drafts = [
        {
            "id": str(draft.id),
            "version": draft.version,
            "platform": draft.platform,
            "title": draft.title,
            "body": draft.body,
            "hashtags": draft.hashtags,
            "created_at": draft.created_at.isoformat() if draft.created_at else None,
        }
        for draft in (session.content_drafts or [])
    ]

    # Build feedback list
    feedback_entries = [
        {
            "id": str(fb.id),
            "agent_name": fb.agent_name,
            "approved": fb.approved,
            "feedback_text": fb.feedback_text,
            "iteration_number": fb.iteration_number,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }
        for fb in (session.feedback_entries or [])
    ]

    # Build integration links
    integration_links = [
        {
            "id": str(link.id),
            "link_type": link.link_type,
            "url": link.url,
            "title": link.title,
        }
        for link in (session.integration_links or [])
    ]

    detail = GenerationDetailResponse(
        id=session.id,
        status=session.status,
        current_agent=session.current_agent,
        started_at=session.started_at,
        completed_at=session.completed_at,
        total_duration_ms=session.total_duration_ms,
        retry_count=session.retry_count,
        error_message=session.error_message,
        agent_runs=agent_runs,
        content_drafts=content_drafts,
        feedback_entries=feedback_entries,
        integration_links=integration_links,
        created_at=session.created_at,
    )

    return ResponseEnvelope(success=True, data=detail)

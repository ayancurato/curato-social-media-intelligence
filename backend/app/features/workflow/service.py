"""
Curato AI — Workflow Service

Business logic layer for workflow operations.
Bridges the API layer and the orchestrator engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.agent_run import AgentRun
from app.models.generation_session import GenerationSession
from app.models.workflow_log import WorkflowLog
from app.schemas.workflow import (
    AgentStatusDetail,
    GenerationSummary,
    WorkflowLogEntry,
    WorkflowStatusResponse,
    WorkflowTriggerResponse,
)

logger = get_logger(__name__)


class WorkflowService:
    """Service layer for workflow operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def trigger_workflow(self, user_id: UUID) -> WorkflowTriggerResponse:
        """
        Create a new generation session and dispatch it for execution.

        Returns the session ID for the client to track via WebSocket.
        """
        session = GenerationSession(
            user_id=user_id,
            status="pending",
            started_at=datetime.now(timezone.utc),
        )
        self._db.add(session)
        await self._db.flush()

        logger.info(
            "Workflow triggered",
            session_id=str(session.id),
            user_id=str(user_id),
        )

        # Dispatch asynchronously without Celery (Bypassing Redis for local test)
        import asyncio
        from app.workers.tasks import _run_workflow

        # Create a background task that runs independently of this request
        task = asyncio.create_task(_run_workflow(str(session.id)))
        
        def _on_done(t: asyncio.Task) -> None:
            if t.cancelled():
                logger.warning("Workflow background task was cancelled", session_id=str(session.id))
            elif t.exception():
                logger.error("Workflow background task failed", session_id=str(session.id), error=str(t.exception()))
        
        task.add_done_callback(_on_done)

        return WorkflowTriggerResponse(
            session_id=session.id,
            status="pending",
            message="Content generation workflow has been triggered.",
        )

    async def get_workflow_status(self, session_id: UUID) -> WorkflowStatusResponse:
        """Get the current status of a workflow session."""
        session = await self._db.get(GenerationSession, session_id)
        if session is None:
            raise NotFoundError(message=f"Session '{session_id}' not found")

        # Get agent runs for this session
        result = await self._db.execute(
            select(AgentRun)
            .where(AgentRun.session_id == session_id)
            .order_by(AgentRun.created_at)
        )
        agent_runs = result.scalars().all()

        agents = [
            AgentStatusDetail(
                agent_name=run.agent_name,
                status=run.status,
                duration_ms=run.duration_ms,
                attempt_number=run.attempt_number,
                error=run.error_message,
            )
            for run in agent_runs
        ]

        return WorkflowStatusResponse(
            session_id=session.id,
            status=session.status,
            current_agent=session.current_agent,
            agents=agents,
            started_at=session.started_at,
            completed_at=session.completed_at,
            total_duration_ms=session.total_duration_ms,
            error_message=session.error_message,
            retry_count=session.retry_count,
        )

    async def get_workflow_logs(
        self,
        session_id: UUID,
        limit: int = 100,
    ) -> list[WorkflowLogEntry]:
        """Get workflow logs for a session."""
        session = await self._db.get(GenerationSession, session_id)
        if session is None:
            raise NotFoundError(message=f"Session '{session_id}' not found")

        result = await self._db.execute(
            select(WorkflowLog)
            .where(WorkflowLog.session_id == session_id)
            .order_by(WorkflowLog.created_at)
            .limit(limit)
        )
        logs = result.scalars().all()

        return [
            WorkflowLogEntry(
                id=log.id,
                level=log.level,
                agent_name=log.agent_name,
                message=log.message,
                details=log.details,
                timestamp=log.created_at,
            )
            for log in logs
        ]

    async def get_workflow_history(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GenerationSummary], int]:
        """Get paginated list of past generation sessions."""
        # Count total
        count_result = await self._db.execute(
            select(GenerationSession)
        )
        total = len(count_result.scalars().all())

        # Fetch page
        offset = (page - 1) * page_size
        result = await self._db.execute(
            select(GenerationSession)
            .order_by(desc(GenerationSession.created_at))
            .offset(offset)
            .limit(page_size)
        )
        sessions = result.scalars().all()

        items = [
            GenerationSummary(
                id=s.id,
                status=s.status,
                current_agent=s.current_agent,
                started_at=s.started_at,
                completed_at=s.completed_at,
                total_duration_ms=s.total_duration_ms,
                retry_count=s.retry_count,
                created_at=s.created_at,
            )
            for s in sessions
        ]

        return items, total

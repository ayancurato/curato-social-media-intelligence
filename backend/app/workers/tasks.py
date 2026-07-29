"""
Curato AI — Celery Tasks

Background tasks for workflow execution.
"""

import asyncio
from uuid import UUID

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="curato.execute_workflow",
    bind=True,
    max_retries=1,
    soft_time_limit=600,
    time_limit=900,
)
def execute_workflow_task(self, session_id: str) -> dict:
    """
    Celery task that executes a full content generation workflow.

    This runs in a Celery worker process. It creates its own
    async event loop and database session to execute the orchestrator.
    """
    logger.info("Celery task started", session_id=session_id, task_id=self.request.id)

    try:
        result = asyncio.get_event_loop().run_until_complete(
            _run_workflow(session_id)
        )
        logger.info("Celery task completed", session_id=session_id)
        return result
    except RuntimeError:
        # No event loop running — create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_run_workflow(session_id))
            logger.info("Celery task completed", session_id=session_id)
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(
            "Celery task failed",
            session_id=session_id,
            error=str(e),
        )
        raise


async def _run_workflow(session_id: str, initiator: str = "unknown") -> dict:
    """Execute the workflow within an async context with its own DB session.
    
    Args:
        session_id: The session UUID string to execute.
        initiator: Who triggered this call — used for structured logging only.
                   Values: 'http_thread', 'poller', 'celery_task', 'unknown'.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

    from app.core.config import get_settings
    from app.features.agents.registry import create_agent_registry
    from app.features.workflow.orchestrator import WorkflowOrchestrator
    from app.features.websocket.manager import get_connection_manager

    settings = get_settings()

    db_url = settings.database_url
    if "asyncpg" in db_url and "sslmode=" in db_url:
        db_url = db_url.replace("sslmode=", "ssl=")

    # Create a dedicated engine for the worker process
    engine = create_async_engine(
        db_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as db:
        try:
            # Create agent registry
            agent_registry = create_agent_registry()

            # Create notification callback for WebSocket events
            ws_manager = get_connection_manager()

            async def notify(session_id: UUID, event_type: str, data: dict) -> None:
                await ws_manager.broadcast_to_session(
                    session_id=session_id,
                    event_type=event_type,
                    data=data,
                )

            # Create and execute orchestrator
            orchestrator = WorkflowOrchestrator(
                db=db,
                agent_registry=agent_registry,
                notification_callback=notify,
            )

            result = await orchestrator.execute(UUID(session_id), initiator=initiator)

            await db.commit()
            return result

        except Exception as e:
            # If the orchestrator's own exception handler didn't fire (e.g., because
            # setup crashed before orchestrator was created), update status here.
            import traceback
            print(f"[_run_workflow] EXCEPTION for {session_id}: {e}\n{traceback.format_exc()}", flush=True)
            try:
                from app.models.generation_session import GenerationSession
                from datetime import datetime, timezone
                session_obj = await db.get(GenerationSession, UUID(session_id))
                if session_obj and session_obj.status == "pending":
                    session_obj.status = "failed"
                    session_obj.error_message = str(e)
                    session_obj.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    print(f"[_run_workflow] Marked session {session_id} as failed", flush=True)
            except Exception as update_err:
                print(f"[_run_workflow] Could not update session status: {update_err}", flush=True)
                await db.rollback()
            raise
        finally:
            await engine.dispose()


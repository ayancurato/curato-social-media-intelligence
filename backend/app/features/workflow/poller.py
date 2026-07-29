"""
Curato AI — Workflow Poller

A long-running asyncio task started at server startup that polls for
pending GenerationSessions and executes them in the main event loop.

This approach is more reliable than per-request background tasks because:
- It runs in the main event loop (started with asyncio.create_task in lifespan)
- It's kept alive by the server's lifecycle, not a request's lifecycle
- It handles pick-up of any sessions that were created but not yet processed
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)

# Track which session IDs are currently being processed
_running_sessions: set[str] = set()


async def workflow_poller_loop() -> None:
    """
    Long-running coroutine that polls for pending sessions every 3 seconds.
    Started once at server startup and kept alive for the server's lifetime.
    """
    print("[POLLER] Workflow poller started", flush=True)
    logger.info("Workflow poller started")

    while True:
        try:
            await _process_pending_sessions()
        except Exception as e:
            logger.error("Poller iteration error", error=str(e))
        await asyncio.sleep(3)


async def _process_pending_sessions() -> None:
    """Query DB for pending sessions and dispatch each as an asyncio task."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select, text
    from app.core.config import get_settings
    from app.models.generation_session import GenerationSession

    settings = get_settings()
    db_url = settings.database_url
    if "asyncpg" in db_url and "sslmode=" in db_url:
        db_url = db_url.replace("sslmode=", "ssl=")

    engine = create_async_engine(db_url, pool_size=2, max_overflow=3, pool_pre_ping=True)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as db:
            result = await db.execute(
                select(GenerationSession)
                .where(GenerationSession.status == "pending")
                .limit(5)
            )
            pending = result.scalars().all()

            for session in pending:
                sid = str(session.id)
                if sid not in _running_sessions:
                    _running_sessions.add(sid)
                    print(f"[POLLER] Dispatching workflow for session {sid}", flush=True)
                    logger.info("Dispatching pending workflow", session_id=sid)

                    # Create an asyncio task in the MAIN event loop
                    task = asyncio.create_task(_run_session(sid))
                    # Keep strong reference to prevent GC
                    task.add_done_callback(lambda t, s=sid: _running_sessions.discard(s))
    finally:
        await engine.dispose()


async def _run_session(session_id_str: str) -> None:
    """Execute a single workflow session."""
    from app.workers.tasks import _run_workflow
    try:
        print(f"[POLLER] Running workflow {session_id_str}", flush=True)
        await _run_workflow(session_id_str)
        print(f"[POLLER] Workflow completed {session_id_str}", flush=True)
    except Exception as e:
        print(f"[POLLER] Workflow failed {session_id_str}: {e}", flush=True)
        logger.error("Workflow execution failed", session_id=session_id_str, error=str(e))
    finally:
        _running_sessions.discard(session_id_str)

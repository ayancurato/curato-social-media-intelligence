"""
Curato AI — FastAPI Application Entry Point

Initializes the FastAPI app, registers routers, middleware,
and lifecycle handlers.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager — startup and shutdown."""
    # ── Startup ──────────────────────────────────────────────────────────
    setup_logging()
    logger.info("Curato AI starting up", env=get_settings().app_env)

    # ── Workflow Poller ──────────────────────────────────────────────────
    # STABILIZATION MODE: Poller is DISABLED.
    #
    # The poller was the 3rd concurrent dispatch path — it would pick up
    # sessions still in 'pending' state ~3 seconds after the OS Thread in
    # WorkflowService already started them, causing every session to run twice.
    #
    # The orchestrator now has an idempotency guard that blocks duplicate runs,
    # but the poller is disabled here as an extra safety measure during
    # stabilization. To re-enable: uncomment the two lines below once the
    # system is confirmed to have no duplicate sessions in production.
    #
    # from app.features.workflow.poller import workflow_poller_loop
    # poller_task = asyncio.create_task(workflow_poller_loop())
    poller_task = None  # placeholder so the shutdown block below doesn't error

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    if poller_task is not None:
        poller_task.cancel()
        try:
            await poller_task
        except asyncio.CancelledError:
            pass

    from app.core.database import engine
    await engine.dispose()
    logger.info("Curato AI shut down")



def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Curato AI — Social Media Intelligence System",
        description=(
            "Enterprise-grade multi-agent AI platform for intelligent "
            "social media content generation."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # ── CORS Middleware ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ───────────────────────────────────────────────
    # register_exception_handlers(app)
    from fastapi.responses import JSONResponse
    from fastapi import Request
    import traceback
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "message": str(exc), "traceback": traceback.format_exc()}
        )

    # ── Routers ──────────────────────────────────────────────────────────
    from app.features.workflow.router import router as workflow_router
    from app.features.generations.router import router as generations_router
    from app.features.websocket.router import router as websocket_router
    from app.api.health import router as health_router

    app.include_router(workflow_router, prefix="/api/v1")
    app.include_router(generations_router, prefix="/api/v1")
    app.include_router(websocket_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1", tags=["System"])

    return app


# ── ASGI Application ─────────────────────────────────────────────────────────
app = create_app()

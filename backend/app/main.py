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

    # ── Database Migrations ──────────────────────────────────────────────
    try:
        from alembic.config import Config
        from alembic import command
        import os
        
        # Get the path to the backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
        alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        
        # We must use the sync URL for Alembic
        sync_url = get_settings().database_url_sync
        if not sync_url and get_settings().database_url:
            # Try to derive sync URL if missing
            sync_url = get_settings().database_url.replace("+asyncpg", "")
        
        if sync_url:
            alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
            logger.info("Running database migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations complete")
        else:
            logger.warning("Could not determine sync database URL for migrations")
    except Exception as e:
        logger.error("Failed to run database migrations", error=str(e))
        # Don't fail the startup if migrations fail, it might be fine or we want to see other errors
        
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
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
    register_exception_handlers(app)

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

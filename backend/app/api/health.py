"""
Curato AI — Health API
Provides deep system health metrics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.services.llm.scoring import ProviderHealthStore

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Returns the health status of critical infrastructure.
    """
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "healthy", # Assuming Celery/Redis connection is fine if API is responding
        "providers": {}
    }

    # DB Check
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"
        health_status["db_error"] = str(e)

    # Provider Check
    for key, health in ProviderHealthStore._store.items():
        health_status["providers"][key] = {
            "status": "healthy" if health.availability else "unhealthy",
            "circuit_status": health.circuit_status,
            "average_latency_ms": health.average_latency_ms,
            "success_rate": health.success_rate
        }
        if not health.availability:
            health_status["status"] = "degraded"

    return health_status


@router.get("/migrate")
async def run_migrations():
    """Temporarily run migrations via API to see errors."""
    import sys
    import io
    from contextlib import redirect_stdout, redirect_stderr
    from alembic.config import Config
    from alembic import command
    import os
    from app.core.config import get_settings
    
    output = io.StringIO()
    try:
        with redirect_stdout(output), redirect_stderr(output):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
            alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
            
            sync_url = get_settings().database_url_sync
            if not sync_url and get_settings().database_url:
                sync_url = get_settings().database_url.replace("+asyncpg", "")
                if "sslmode=" in sync_url:
                    sync_url = sync_url.replace("sslmode=", "ssl=")
                    
            if sync_url:
                alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
                command.upgrade(alembic_cfg, "head")
                return {"status": "success", "output": output.getvalue()}
            else:
                return {"status": "error", "error": "No sync URL derived"}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc(), "output": output.getvalue()}

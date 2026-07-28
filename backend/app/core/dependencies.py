"""
Curato AI — Dependency Injection Wiring

Central location for all FastAPI dependencies.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user


async def get_session(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """Alias for database session dependency."""
    yield db


def get_config() -> Settings:
    """Get application settings."""
    return get_settings()


__all__ = [
    "get_db",
    "get_session",
    "get_config",
    "get_current_user",
    "CurrentUser",
    "Settings",
]

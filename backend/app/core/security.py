"""
Curato AI — Authentication Middleware (Stubbed)

Provides a stubbed auth layer ready for Clerk or Auth.js integration.
In development mode, returns a mock user. In production, will validate
tokens from the configured auth provider.
"""

from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, Request
from pydantic import BaseModel

from app.core.config import Settings, get_settings


class CurrentUser(BaseModel):
    """Represents the authenticated user in the request context."""

    id: UUID
    email: str
    name: str
    role: str  # "admin" | "team_member"


# ── Mock user for development ────────────────────────────────────────────────
_MOCK_USER = CurrentUser(
    id=uuid4(),
    email="team@curato.ai",
    name="Curato Team",
    role="admin",
)


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """
    Get the current authenticated user.

    In development: returns a mock user.
    In production: will validate the auth token from the request header
    and return the authenticated user.

    To integrate Clerk:
        1. Install `clerk-backend-api`
        2. Validate the session token from `Authorization` header
        3. Map Clerk user to CurrentUser model

    To integrate Auth.js:
        1. Validate the JWT from `Authorization` header
        2. Decode and map claims to CurrentUser model
    """
    if settings.app_env == "development":
        return _MOCK_USER

    # TODO: Implement real auth validation
    # token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    # if not token:
    #     raise HTTPException(status_code=401, detail="Not authenticated")
    # user_data = await validate_token(token)
    # return CurrentUser(**user_data)

    return _MOCK_USER


def require_role(allowed_roles: list[str]) -> Any:
    """
    Dependency that checks if the current user has one of the allowed roles.

    Usage:
        @router.post("/admin-only", dependencies=[Depends(require_role(["admin"]))])
    """

    async def _check_role(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=403,
                detail=f"Role '{user.role}' is not authorized for this action.",
            )
        return user

    return _check_role

"""
Curato AI — Exception Handling

Custom exception hierarchy and FastAPI exception handlers.
"""

from typing import Any
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================


class CuratoBaseError(Exception):
    """Base exception for all Curato AI errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class WorkflowError(CuratoBaseError):
    """Raised when the workflow orchestrator encounters an error."""

    def __init__(
        self,
        message: str,
        session_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.session_id = session_id
        super().__init__(message, details)


class AgentError(CuratoBaseError):
    """Raised when an individual agent fails."""

    def __init__(
        self,
        message: str,
        agent_name: str,
        session_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.agent_name = agent_name
        self.session_id = session_id
        super().__init__(message, details)


class AgentValidationError(AgentError):
    """Raised when agent input or output validation fails."""

    pass


class AgentRetryExhaustedError(AgentError):
    """Raised when an agent exhausts all retry attempts."""

    pass


class LLMProviderError(CuratoBaseError):
    """Raised when the LLM provider fails."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.provider = provider
        super().__init__(message, details)


class ToolExecutionError(CuratoBaseError):
    """Raised when a tool in the Tool Registry fails."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.tool_name = tool_name
        super().__init__(message, details)


class NotFoundError(CuratoBaseError):
    """Raised when a resource is not found."""

    pass


# =============================================================================
# FastAPI Exception Handlers
# =============================================================================


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(AgentValidationError)
    async def agent_validation_handler(
        request: Request, exc: AgentValidationError
    ) -> JSONResponse:
        logger.error(
            "Agent validation failed",
            agent=exc.agent_name,
            error=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "agent_validation_error",
                "message": exc.message,
                "agent": exc.agent_name,
                "details": exc.details,
            },
        )

    @app.exception_handler(AgentError)
    async def agent_error_handler(request: Request, exc: AgentError) -> JSONResponse:
        logger.error(
            "Agent execution failed",
            agent=exc.agent_name,
            error=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "agent_error",
                "message": exc.message,
                "agent": exc.agent_name,
                "details": exc.details,
            },
        )

    @app.exception_handler(WorkflowError)
    async def workflow_error_handler(
        request: Request, exc: WorkflowError
    ) -> JSONResponse:
        logger.error(
            "Workflow error",
            session_id=str(exc.session_id),
            error=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "workflow_error",
                "message": exc.message,
                "session_id": str(exc.session_id) if exc.session_id else None,
                "details": exc.details,
            },
        )

    @app.exception_handler(LLMProviderError)
    async def llm_error_handler(
        request: Request, exc: LLMProviderError
    ) -> JSONResponse:
        logger.error(
            "LLM provider error",
            provider=exc.provider,
            error=exc.message,
        )
        return JSONResponse(
            status_code=502,
            content={
                "error": "llm_provider_error",
                "message": exc.message,
                "provider": exc.provider,
            },
        )

    @app.exception_handler(CuratoBaseError)
    async def base_error_handler(
        request: Request, exc: CuratoBaseError
    ) -> JSONResponse:
        logger.error("Application error", error=exc.message, details=exc.details)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
            },
        )

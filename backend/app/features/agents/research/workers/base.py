"""
Curato AI — Base Worker for Research Agent

Abstract base class for internal workers within the Research Agent.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from app.core.exceptions import AgentValidationError
from app.core.logging import get_logger
from app.features.agents.tool_registry import ToolRegistry
from app.services.llm.base import LLMProvider, LLMResponse

logger = get_logger(__name__)


class BaseWorker(ABC):
    """
    Abstract base class for internal workers in Agent 1.

    Each worker has access to the LLM and ToolRegistry, and emits
    status updates through a provided emit_event callback.
    """

    def __init__(
        self,
        llm: LLMProvider,
        tool_registry: ToolRegistry,
        model_config: Any,
        emit_event: Any,
    ) -> None:
        self.llm = llm
        self.tool_registry = tool_registry
        self.model_config = model_config
        self.emit_event = emit_event
        self._logger = get_logger(f"worker.{self.name() if callable(self.name) else self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Worker name (e.g., google_search, competitor_intelligence)"""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Core execution logic for the worker."""
        pass

    async def invoke_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Invoke a tool via the registry."""
        try:
            return await self.tool_registry.invoke(tool_name, **kwargs)
        except Exception as e:
            self._logger.error("Tool invocation failed", tool=tool_name, error=str(e))
            # Return empty or fail depending on how tools are structured
            return {"success": False, "error": str(e), "data": {}}

    async def _safe_execute(self, max_retries: int = 2, **kwargs: Any) -> dict[str, Any]:
        """Execute with retry logic for transient errors."""
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                await self.emit_event(
                    "worker_started",
                    {"worker_name": self.name() if callable(self.name() if callable(self.name) else self.name) else self.name, "attempt": attempt}
                )
                
                result = await self.execute(**kwargs)
                
                await self.emit_event(
                    "worker_completed",
                    {"worker_name": self.name() if callable(self.name() if callable(self.name) else self.name) else self.name, "success": True}
                )
                return result
                
            except AgentValidationError as e:
                # Do not retry validation errors
                self._logger.error("Validation error in worker", error=str(e))
                await self.emit_event(
                    "worker_failed",
                    {"worker_name": self.name() if callable(self.name() if callable(self.name) else self.name) else self.name, "error": str(e), "fatal": True}
                )
                return {"success": False, "error": str(e), "data": {}}
                
            except Exception as e:
                last_error = e
                self._logger.warning(
                    f"Worker {self.name() if callable(self.name) else self.name} failed attempt {attempt}",
                    error=str(e)
                )
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)

        await self.emit_event(
            "worker_failed",
            {"worker_name": self.name() if callable(self.name() if callable(self.name) else self.name) else self.name, "error": str(last_error), "fatal": False}
        )
        return {"success": False, "error": str(last_error), "data": {}}

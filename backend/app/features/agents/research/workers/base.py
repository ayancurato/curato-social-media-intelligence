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
        cache: dict[str, Any],
    ) -> None:
        self.llm = llm
        self.tool_registry = tool_registry
        self.model_config = model_config
        self.emit_event = emit_event
        self.cache = cache
        self._logger = get_logger(f"worker.{self.name() if callable(self.name) else self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Worker name (e.g., google_search, competitor_intelligence)"""
        pass

    @abstractmethod
    async def acquire_data(self, **kwargs: Any) -> Any:
        """Phase 1: Acquire data from external tools or inputs."""
        pass

    @abstractmethod
    async def synthesize_data(self, acquired_data: Any, **kwargs: Any) -> dict[str, Any]:
        """Phase 2: Synthesize acquired data using the LLM."""
        pass

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is transient and should be retried."""
        if isinstance(error, AgentValidationError):
            return False
            
        err_str = str(error).lower()
        # Retry only on explicit transient failures
        transient_keywords = [
            "429", "503", "502", "504", "timeout", "connection error", 
            "rate limit", "too many requests", "service unavailable",
            "connection refused", "connection reset"
        ]
        
        # Do NOT retry on explicit non-retryable issues
        fatal_keywords = [
            "authentication", "401", "403", "invalid request", 
            "400", "validation", "malformed", "not found", "404"
        ]
        
        for kw in fatal_keywords:
            if kw in err_str:
                return False
                
        for kw in transient_keywords:
            if kw in err_str:
                return True
                
        # Default to False for safety if unclassified, but in many LLM setups 
        # APIConnectionError etc are raised. We'll rely on the keywords above.
        # But some general exceptions might just be connection issues.
        # Let's be conservative as requested: "Retry only transient failures"
        return False


    async def invoke_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Invoke a tool via the registry."""
        try:
            return await self.tool_registry.invoke(tool_name, **kwargs)
        except Exception as e:
            self._logger.error("Tool invocation failed", tool=tool_name, error=str(e))
            # Return empty or fail depending on how tools are structured
            return {"success": False, "error": str(e), "data": {}}

    async def _safe_execute(self, max_retries: int = 2, **kwargs: Any) -> dict[str, Any]:
        """Execute with cache reuse and targeted retry logic for transient LLM errors."""
        worker_name = self.name() if callable(self.name) else self.name
        
        # Check if fully synthesized data is already in cache
        synth_key = f"{worker_name}_synthesized"
        if synth_key in self.cache:
            self._logger.info(f"Research cache hit", worker=worker_name)
            return self.cache[synth_key]

        acq_key = f"{worker_name}_acquired"
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                await self.emit_event(
                    "worker_started",
                    {"worker_name": worker_name, "attempt": attempt}
                )
                
                # Phase 1: Acquisition (reuse if cached)
                if acq_key in self.cache:
                    if attempt == 1:
                        # Should not happen on attempt 1 normally unless a higher level agent retried
                        self._logger.info("Research cache hit (acquisition only)", worker=worker_name)
                    else:
                        self._logger.info("Retrying LLM only", worker=worker_name)
                    acquired_data = self.cache[acq_key]
                else:
                    if attempt == 1:
                        self._logger.info("Research cache miss", worker=worker_name)
                    else:
                        self._logger.info("Re-running full worker", worker=worker_name)
                        
                    acquired_data = await self.acquire_data(**kwargs)
                    self.cache[acq_key] = acquired_data
                
                # Phase 2: Synthesis
                result = await self.synthesize_data(acquired_data, **kwargs)
                
                # Cache final synthesis
                self.cache[synth_key] = result
                
                await self.emit_event(
                    "worker_completed",
                    {"worker_name": worker_name, "success": True}
                )
                return result
                
            except Exception as e:
                last_error = e
                is_retryable = self._is_retryable_error(e)
                
                if not is_retryable:
                    self._logger.error(
                        f"Non-retryable error in worker {worker_name}",
                        error=str(e)
                    )
                    await self.emit_event(
                        "worker_failed",
                        {"worker_name": worker_name, "error": str(e), "fatal": True}
                    )
                    return {"success": False, "error": str(e), "data": {}}
                    
                self._logger.warning(
                    f"Transient error in worker {worker_name} attempt {attempt}",
                    error=str(e)
                )
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)

        await self.emit_event(
            "worker_failed",
            {"worker_name": worker_name, "error": str(last_error), "fatal": False}
        )
        return {"success": False, "error": str(last_error), "data": {}}

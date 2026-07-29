"""
Curato AI — Base Agent

Abstract base class that all agents must implement.
Provides the core contract: run(), validate(), retry().
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.core.exceptions import AgentError, AgentRetryExhaustedError, AgentValidationError
from app.core.logging import get_logger
from app.features.agents.config import AgentConfig, get_agent_config_manager
from app.features.agents.tool_registry import ToolRegistry, get_tool_registry
from app.services.llm.base import LLMProvider, LLMResponse

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all Curato AI agents.

    Every agent MUST implement:
    - run(input_data) → dict  — Core execution logic
    - validate_input(input_data) → bool  — Input validation
    - validate_output(output_data) → bool  — Output validation

    Provides built-in:
    - Retry with exponential backoff
    - Duration tracking
    - Structured logging
    - LLM provider access (per-agent model configuration)
    - Tool registry access (per-agent tool access)
    - Configuration management
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        llm_provider: LLMProvider | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        from app.services.llm.factory import get_llm_provider
        
        config_manager = get_agent_config_manager()
        self._config = config or config_manager.get_config(self.name() if callable(self.name) else self.name)
        self._llm = llm_provider or get_llm_provider(self._config.model.provider)
        self._tool_registry = tool_registry or get_tool_registry()
        self._logger = get_logger(f"agent.{self.name() if callable(self.name) else self.name}")

    # ── Abstract Properties ──────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent."""
        ...

    @property
    def display_name(self) -> str:
        """Human-readable name for this agent."""
        return self._config.display_name or self.name.replace("_", " ").title()

    @property
    def config(self) -> AgentConfig:
        """Get the agent's configuration."""
        return self._config

    # ── Abstract Methods (Agent Contract) ────────────────────────────────

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent's core logic.

        Args:
            input_data: Structured JSON input from the orchestrator.

        Returns:
            Structured JSON output for the next agent.
        """
        ...

    @abstractmethod
    async def validate_input(self, input_data: dict[str, Any]) -> bool:
        """
        Validate input data before execution.

        Raises:
            AgentValidationError: If input is invalid.
        """
        ...

    @abstractmethod
    async def validate_output(self, output_data: dict[str, Any]) -> bool:
        """
        Validate output data after execution.

        Raises:
            AgentValidationError: If output is invalid.
        """
        ...

    # ── Built-in Methods ─────────────────────────────────────────────────

    async def execute(
        self,
        input_data: dict[str, Any],
        session_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Full execution pipeline: validate → run → validate output.

        This is what the orchestrator calls. Do NOT override this.
        """
        self._logger.info(
            "Agent execution started",
            agent=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
            session_id=str(session_id) if session_id else None,
        )
        start_time = time.monotonic()

        try:
            # 1. Validate input
            await self.validate_input(input_data)

            # 2. Execute
            import inspect
            sig = inspect.signature(self.run)
            if "session_id" in sig.parameters:
                output_data = await self.run(session_id=str(session_id) if session_id else "", input_data=input_data)
            else:
                output_data = await self.run(input_data)

            # 3. Validate output
            await self.validate_output(output_data)

            duration_ms = int((time.monotonic() - start_time) * 1000)
            self._logger.info(
                "Agent execution completed",
                agent=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
                duration_ms=duration_ms,
                session_id=str(session_id) if session_id else None,
            )

            # Attach execution metadata
            output_data["_metadata"] = {
                "agent": self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
                "duration_ms": duration_ms,
                "model": self._config.model.model,
                "provider": self._config.model.provider,
            }

            return output_data

        except AgentValidationError:
            raise
        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            self._logger.error(
                "Agent execution failed",
                agent=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
                error=str(e),
                duration_ms=duration_ms,
            )
            raise AgentError(
                message=f"Agent '{self.name() if callable(self.name) else self.name}' failed: {str(e)}",
                agent_name=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
                session_id=session_id,
                details={"duration_ms": duration_ms},
            )

    async def retry(
        self,
        input_data: dict[str, Any],
        session_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Execute with automatic retries and exponential backoff.

        Uses retry configuration from the agent's config.
        """
        retry_config = self._config.retry
        last_error: Exception | None = None

        for attempt in range(1, retry_config.max_retries + 1):
            try:
                self._logger.info(
                    "Agent attempt",
                    agent=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
                    attempt=attempt,
                    max_retries=retry_config.max_retries,
                )
                result = await self.execute(input_data, session_id)
                return result

            except AgentValidationError:
                # Don't retry validation errors — they won't fix themselves
                raise

            except Exception as e:
                last_error = e
                if attempt < retry_config.max_retries:
                    delay = retry_config.retry_delay_seconds
                    if retry_config.exponential_backoff:
                        delay = min(
                            delay * (2 ** (attempt - 1)),
                            retry_config.max_delay_seconds,
                        )
                    self._logger.warning(
                        "Agent failed, retrying",
                        agent=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
                        attempt=attempt,
                        next_delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)

        raise AgentRetryExhaustedError(
            message=(
                f"Agent '{self.name() if callable(self.name) else self.name}' exhausted all {retry_config.max_retries} retries. "
                f"Last error: {str(last_error)}"
            ),
            agent_name=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
            session_id=session_id,
        )

    # ── LLM Helper ───────────────────────────────────────────────────────

    async def call_llm(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Call the LLM using this agent's configured model settings.

        Uses the agent's specific model config (model, temperature, etc.)
        rather than global defaults.
        """
        sys_prompt = system_prompt or self._config.prompt.system_prompt
        return await self._llm.generate(
            prompt=prompt,
            system_prompt=sys_prompt,
            model_config=self._config.model,
        )

    async def call_llm_structured(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Call the LLM and return structured JSON output."""
        sys_prompt = system_prompt or self._config.prompt.system_prompt
        return await self._llm.generate_structured(
            prompt=prompt,
            system_prompt=sys_prompt,
            model_config=self._config.model,
        )

    # ── Tool Helper ──────────────────────────────────────────────────────

    async def invoke_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Invoke a tool from the Tool Registry.

        Only tools listed in this agent's config.tools are accessible.
        """
        if tool_name not in self._config.tools:
            raise AgentError(
                message=f"Agent '{self.name() if callable(self.name) else self.name}' does not have access to tool '{tool_name}'",
                agent_name=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name,
            )
        result = await self._tool_registry.invoke(tool_name, **kwargs)
        return result

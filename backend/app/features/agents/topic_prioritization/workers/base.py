"""
Curato AI — Topic Prioritization Worker Base
"""

import json
from abc import ABC, abstractmethod
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import AgentValidationError
from app.core.logging import get_logger
from app.services.llm.base import LLMProvider

logger = get_logger(__name__)


class BaseTopicWorker(ABC):
    """
    Abstract base class for Topic Prioritization reasoning workers.
    Each worker processes the complete list of topics in a single batch pass.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    @property
    @abstractmethod
    def name(self) -> str:
        """Worker name."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining the worker's persona and JSON schema."""
        pass

    @abstractmethod
    def format_user_prompt(self, topics: list[dict[str, Any]], context: dict[str, Any] | None = None) -> str:
        """Format the input topics into the user prompt."""
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _safe_execute(self, topics: list[dict[str, Any]], context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Executes the LLM call with retry logic for transient failures.
        Validation failures raise AgentValidationError and are NOT retried.
        """
        user_prompt = self.format_user_prompt(topics, context)

        try:
            response = await self.llm.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.2, # Lower temp for reasoning
                response_format="json_object",
            )
            
            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse worker output", worker=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name, error=str(e))
                raise AgentValidationError(f"Invalid JSON from {self.name() if callable(self.name) else self.name}: {e}", agent_name=self.name() if callable(self.name) else self.name)

            return parsed

        except AgentValidationError:
            # Re-raise validation errors without triggering tenacity retry
            raise
        except Exception as e:
            logger.warning("Worker transient error, retrying", worker=self.name() if callable(self.name() if callable(self.name) else self.name) else self.name, error=str(e))
            raise

    async def evaluate_topics(self, topics: list[dict[str, Any]], context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Public entrypoint. Evaluates all topics in a single batch.
        Expected to return a dict mapping topic titles to their specific evaluations.
        """
        logger.info(f"{self.name() if callable(self.name) else self.name} starting batch evaluation", num_topics=len(topics))
        return await self._safe_execute(topics, context)

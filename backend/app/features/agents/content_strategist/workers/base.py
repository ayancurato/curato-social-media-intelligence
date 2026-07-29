"""
Curato AI — Content Strategist Workers Base
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


class BaseContentWorker(ABC):
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    @property
    @abstractmethod
    @property
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass


class BaseBatchContentWorker(BaseContentWorker):
    """Executes evaluation for all topics in a single batch pass."""

    @abstractmethod
    def format_user_prompt(self, topics: list[dict[str, Any]]) -> str:
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def evaluate_topics(self, topics: list[dict[str, Any]]) -> dict[str, Any]:
        user_prompt = self.format_user_prompt(topics)
        try:
            response = await self.llm.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                response_format="json_object",
            )
            parsed = json.loads(response.content)
            return parsed
        except AgentValidationError:
            raise
        except Exception as e:
            logger.warning("Batch Worker transient error", worker=self.name, error=str(e))
            raise


class BaseSingleContentWorker(BaseContentWorker):
    """Executes evaluation for a single topic."""

    @abstractmethod
    def format_user_prompt(self, topic: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def evaluate_topic(self, topic: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        user_prompt = self.format_user_prompt(topic, context)
        try:
            # We use higher temperature for creative workers (Hook, CTA)
            response = await self.llm.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.7, 
                response_format="json_object",
            )
            parsed = json.loads(response.content)
            return parsed
        except AgentValidationError:
            raise
        except Exception as e:
            logger.warning("Single Worker transient error", worker=self.name, error=str(e))
            raise


"""
Curato AI — Chief Editor Workers Base
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
from app.services.llm.provider import LLMProvider

logger = get_logger(__name__)


class BaseEditorWorker(ABC):
    """Base class for Chief Editor review workers."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @property
    def temperature(self) -> float:
        return 0.1

    @abstractmethod
    def format_user_prompt(self, draft_data: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def review(self, draft_data: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        user_prompt = self.format_user_prompt(draft_data, context)
        try:
            response = await self.llm.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature,
                response_format="json_object",
            )
            parsed = json.loads(response.content)
            
            # Phase 6.5: Generate prompt fingerprint and worker trace
            import hashlib
            prompt_hash = hashlib.sha256(user_prompt.encode("utf-8")).hexdigest()
            
            trace = {
                "worker_name": self.name,
                "prompt_version": "1.0.0",
                "prompt_hash": prompt_hash,
                "provider": response.provider,
                "model": response.model,
                "temperature": self.temperature,
                "tokens": {
                    "prompt_tokens": response.token_usage.prompt_tokens if response.token_usage else 0,
                    "completion_tokens": response.token_usage.completion_tokens if response.token_usage else 0,
                }
            }
            parsed["_trace"] = trace
            
            return parsed
        except AgentValidationError:
            raise
        except Exception as e:
            logger.warning(f"{self.name} transient error", error=str(e))
            raise

"""
Curato AI — LLM Provider Abstraction (Base)

Abstract interface for LLM providers. Agents interact with this
interface — never with a specific provider directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.features.agents.config import ModelConfig


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str
    model: str
    provider: str
    token_usage: TokenUsage | None = None
    finish_reason: str = ""
    raw_response: dict[str, Any] = Field(default_factory=dict)


class TokenUsage(BaseModel):
    """Token usage breakdown."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMProvider(ABC):
    """
    Abstract base for all LLM providers.

    Implementations:
    - OpenAIProvider (openai)
    - Future: AnthropicProvider, GoogleProvider, etc.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'openai')."""
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model_config: ModelConfig | None = None,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            prompt: The user prompt / message.
            system_prompt: The system-level instruction.
            model_config: Model configuration (model name, temperature, etc.).
                         If None, uses provider defaults.

        Returns:
            LLMResponse with the generated content and metadata.
        """
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        model_config: ModelConfig | None = None,
    ) -> dict[str, Any]:
        """
        Generate a structured JSON response from the LLM.

        Uses response_format="json_object" or equivalent.

        Returns:
            Parsed JSON as a dict.
        """
        ...

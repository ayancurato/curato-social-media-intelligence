"""
Curato AI — OpenAI LLM Provider

Implements the LLMProvider interface for OpenAI GPT models.
"""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.features.agents.config import ModelConfig
from app.services.llm.base import LLMProvider, LLMResponse, TokenUsage

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM provider implementation."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model_config: ModelConfig | None = None,
    ) -> LLMResponse:
        """Generate a text completion via OpenAI."""
        config = model_config or ModelConfig()

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            kwargs: dict[str, Any] = {
                "model": config.model,
                "messages": messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "top_p": config.top_p,
                "frequency_penalty": config.frequency_penalty,
                "presence_penalty": config.presence_penalty,
            }

            if config.response_format == "json_object":
                kwargs["response_format"] = {"type": "json_object"}

            response = await self._client.chat.completions.create(**kwargs)

            usage = response.usage
            token_usage = None
            if usage:
                token_usage = TokenUsage(
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                )

            choice = response.choices[0]

            logger.info(
                "OpenAI generation completed",
                model=config.model,
                tokens=usage.total_tokens if usage else 0,
                finish_reason=choice.finish_reason,
            )

            return LLMResponse(
                content=choice.message.content or "",
                model=config.model,
                provider=self.provider_name,
                token_usage=token_usage,
                finish_reason=choice.finish_reason or "",
                raw_response=response.model_dump(),
            )

        except Exception as e:
            logger.error("OpenAI generation failed", error=str(e), model=config.model)
            raise LLMProviderError(
                message=f"OpenAI API call failed: {str(e)}",
                provider=self.provider_name,
                details={"model": config.model},
            )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        model_config: ModelConfig | None = None,
    ) -> dict[str, Any]:
        """Generate a structured JSON response via OpenAI."""
        config = model_config or ModelConfig(response_format="json_object")
        if config.response_format != "json_object":
            config = config.model_copy(update={"response_format": "json_object"})

        response = await self.generate(prompt, system_prompt, config)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse structured response",
                content=response.content[:200],
                error=str(e),
            )
            raise LLMProviderError(
                message=f"Failed to parse JSON from LLM response: {str(e)}",
                provider=self.provider_name,
            )

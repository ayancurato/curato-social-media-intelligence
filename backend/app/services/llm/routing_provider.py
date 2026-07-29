"""
Curato AI — Routing LLM Provider
Wraps actual providers to implement the Provider Routing Policy Engine and Circuit Breaking failover.
"""

import time
from typing import Any, Optional
from app.services.llm.base import LLMProvider, LLMResponse
from app.services.llm.routing import RoutingPolicyEngine
from app.services.llm.circuit_breaker import CircuitBreaker
from app.services.llm.scoring import ProviderHealthStore
from app.core.logging import get_logger

logger = get_logger(__name__)


class RoutingLLMProvider(LLMProvider):
    """
    Enterprise LLM Provider that sits above actual providers.
    Automatically routes requests and handles failovers.
    """

    def __init__(self, policy: str = "Balanced", max_failovers: int = 3):
        self.policy = policy
        self.max_failovers = max_failovers

    @property
    def provider_name(self) -> str:
        return "routing"

    # We delay importing get_llm_provider to avoid circular imports if it were in factory
    def _get_underlying_provider(self, provider_name: str) -> LLMProvider:
        from app.services.llm.factory import _get_raw_llm_provider
        return _get_raw_llm_provider(provider_name)

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model_config: "ModelConfig | None" = None,
    ) -> LLMResponse:
        """Route generate() through the policy engine with failover."""
        from app.features.agents.config import ModelConfig as _ModelConfig
        config = model_config or _ModelConfig()

        excluded_models: list[str] = []
        failovers = 0
        last_error: Exception | None = None

        while failovers <= self.max_failovers:
            meta = RoutingPolicyEngine.get_best_provider(self.policy, excluded_models=excluded_models)

            if not meta:
                raise RuntimeError("No healthy providers available for routing.")

            provider_instance = self._get_underlying_provider(meta.provider)
            start_time = time.monotonic()

            try:
                # Update config with the specifically routed model
                routed_config = config.model_copy(update={"provider": meta.provider, "model": meta.model_name})
                
                response = await provider_instance.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model_config=routed_config,
                )

                latency_ms = (time.monotonic() - start_time) * 1000

                # Health record
                ProviderHealthStore.record_success(meta.provider, meta.model_name, latency_ms)
                CircuitBreaker.record_success(meta.provider, meta.model_name)

                # Overwrite metadata so it reflects the actual routed model
                response.provider = meta.provider
                response.model = meta.model_name

                return response

            except Exception as e:
                logger.warning(
                    "Provider generation failed",
                    provider=meta.provider,
                    model=meta.model_name,
                    error=str(e)
                )

                ProviderHealthStore.record_failure(meta.provider, meta.model_name)
                CircuitBreaker.record_failure(meta.provider, meta.model_name)

                excluded_models.append(meta.model_name)
                last_error = e
                failovers += 1

        raise RuntimeError(f"Workflow completely exhausted LLM failovers. Last error: {str(last_error)}")

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        model_config: "ModelConfig | None" = None,
    ) -> dict[str, Any]:
        """Route generate_structured() through the policy engine with failover."""
        from app.features.agents.config import ModelConfig as _ModelConfig
        import json

        config = model_config or _ModelConfig(response_format="json_object")
        if getattr(config, "response_format", None) != "json_object":
            config = config.model_copy(update={"response_format": "json_object"})

        excluded_models: list[str] = []
        failovers = 0
        last_error: Exception | None = None

        while failovers <= self.max_failovers:
            meta = RoutingPolicyEngine.get_best_provider(self.policy, excluded_models=excluded_models)

            if not meta:
                raise RuntimeError("No healthy providers available for routing.")

            provider_instance = self._get_underlying_provider(meta.provider)
            start_time = time.monotonic()

            try:
                # Update config with the specifically routed model
                routed_config = config.model_copy(update={"provider": meta.provider, "model": meta.model_name})
                
                result = await provider_instance.generate_structured(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model_config=routed_config,
                )

                latency_ms = (time.monotonic() - start_time) * 1000
                ProviderHealthStore.record_success(meta.provider, meta.model_name, latency_ms)
                CircuitBreaker.record_success(meta.provider, meta.model_name)

                return result

            except Exception as e:
                logger.warning(
                    "Provider structured generation failed",
                    provider=meta.provider,
                    model=meta.model_name,
                    error=str(e)
                )
                ProviderHealthStore.record_failure(meta.provider, meta.model_name)
                CircuitBreaker.record_failure(meta.provider, meta.model_name)
                excluded_models.append(meta.model_name)
                last_error = e
                failovers += 1

        raise RuntimeError(f"Structured generation exhausted failovers. Last error: {str(last_error)}")

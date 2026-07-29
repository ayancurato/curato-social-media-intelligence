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
        from app.services.llm.exceptions import classify_llm_error, LLMTransientError, LLMQuotaExhaustedError, LLMFatalError, AllProvidersExhaustedError
        from app.services.llm.budget import PromptBudgetGuard
        
        config = model_config or _ModelConfig()

        excluded_models: list[str] = []
        failovers = 0
        last_error: Exception | None = None

        while failovers <= self.max_failovers:
            meta = RoutingPolicyEngine.get_best_provider(self.policy, excluded_models=excluded_models)

            if not meta:
                raise AllProvidersExhaustedError(f"No healthy providers available for routing. Last error: {str(last_error)}")

            provider_instance = self._get_underlying_provider(meta.provider)
            start_time = time.monotonic()
            
            # Apply budget guard to avoid Context Window errors
            safe_prompt = PromptBudgetGuard.apply_budget(prompt, meta.context_window)

            try:
                logger.info(f"[ROUTER] Provider selected: {meta.provider}/{meta.model_name}")
                routed_config = config.model_copy(update={"provider": meta.provider, "model": meta.model_name})
                
                response = await provider_instance.generate(
                    prompt=safe_prompt,
                    system_prompt=system_prompt,
                    model_config=routed_config,
                )

                latency_ms = (time.monotonic() - start_time) * 1000
                ProviderHealthStore.record_success(meta.provider, meta.model_name, latency_ms)
                CircuitBreaker.record_success(meta.provider, meta.model_name)

                response.provider = meta.provider
                response.model = meta.model_name

                return response

            except Exception as raw_error:
                e = classify_llm_error(raw_error)
                
                if isinstance(e, LLMQuotaExhaustedError):
                    logger.warning(
                        f"[ROUTER] Provider unavailable (quota exhausted): {meta.provider}/{meta.model_name}",
                        error=str(e)
                    )
                    ProviderHealthStore.mark_quota_exhausted(meta.provider, meta.model_name, retry_after=e.retry_after)
                    excluded_models.append(meta.model_name)
                    
                elif isinstance(e, LLMTransientError):
                    logger.warning(
                        f"[ROUTER] Transient error on provider {meta.provider}/{meta.model_name}",
                        error=str(e)
                    )
                    ProviderHealthStore.record_failure(meta.provider, meta.model_name, reason=str(e))
                    CircuitBreaker.record_failure(meta.provider, meta.model_name, retry_after=e.retry_after)
                    if CircuitBreaker.is_open(meta.provider, meta.model_name):
                        logger.warning(f"[ROUTER] Circuit breaker opened: {meta.provider}/{meta.model_name}")
                        excluded_models.append(meta.model_name)
                        
                elif isinstance(e, LLMFatalError):
                    logger.error(
                        f"[ROUTER] Fatal error on provider {meta.provider}/{meta.model_name}. Excluding for session.",
                        error=str(e)
                    )
                    # Exclude for session, do not poison global health
                    excluded_models.append(meta.model_name)
                    
                else:
                    excluded_models.append(meta.model_name)

                last_error = e
                failovers += 1
                
                if failovers <= self.max_failovers:
                    logger.info(f"[ROUTER] Trying fallback provider (attempt {failovers})")

        logger.error("[ROUTER] No healthy providers available")
        raise AllProvidersExhaustedError(f"Workflow completely exhausted LLM failovers. Last error: {str(last_error)}")

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        model_config: "ModelConfig | None" = None,
    ) -> dict[str, Any]:
        """Route generate_structured() through the policy engine with failover."""
        from app.features.agents.config import ModelConfig as _ModelConfig
        from app.services.llm.exceptions import classify_llm_error, LLMTransientError, LLMQuotaExhaustedError, LLMFatalError, AllProvidersExhaustedError
        from app.services.llm.budget import PromptBudgetGuard
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
                raise AllProvidersExhaustedError(f"No healthy providers available for routing. Last error: {str(last_error)}")

            provider_instance = self._get_underlying_provider(meta.provider)
            start_time = time.monotonic()
            
            # Apply budget guard to avoid Context Window errors
            safe_prompt = PromptBudgetGuard.apply_budget(prompt, meta.context_window)

            try:
                logger.info(f"[ROUTER] Provider selected: {meta.provider}/{meta.model_name}")
                routed_config = config.model_copy(update={"provider": meta.provider, "model": meta.model_name})
                
                result = await provider_instance.generate_structured(
                    prompt=safe_prompt,
                    system_prompt=system_prompt,
                    model_config=routed_config,
                )

                latency_ms = (time.monotonic() - start_time) * 1000
                ProviderHealthStore.record_success(meta.provider, meta.model_name, latency_ms)
                CircuitBreaker.record_success(meta.provider, meta.model_name)

                return result

            except Exception as raw_error:
                e = classify_llm_error(raw_error)
                
                if isinstance(e, LLMQuotaExhaustedError):
                    logger.warning(
                        f"[ROUTER] Provider unavailable (quota exhausted): {meta.provider}/{meta.model_name}",
                        error=str(e)
                    )
                    ProviderHealthStore.mark_quota_exhausted(meta.provider, meta.model_name, retry_after=e.retry_after)
                    excluded_models.append(meta.model_name)
                    
                elif isinstance(e, LLMTransientError):
                    logger.warning(
                        f"[ROUTER] Transient error on provider {meta.provider}/{meta.model_name}",
                        error=str(e)
                    )
                    ProviderHealthStore.record_failure(meta.provider, meta.model_name, reason=str(e))
                    CircuitBreaker.record_failure(meta.provider, meta.model_name, retry_after=e.retry_after)
                    if CircuitBreaker.is_open(meta.provider, meta.model_name):
                        logger.warning(f"[ROUTER] Circuit breaker opened: {meta.provider}/{meta.model_name}")
                        excluded_models.append(meta.model_name)
                        
                elif isinstance(e, LLMFatalError):
                    logger.error(
                        f"[ROUTER] Fatal error on provider {meta.provider}/{meta.model_name}. Excluding for session.",
                        error=str(e)
                    )
                    excluded_models.append(meta.model_name)
                    
                else:
                    excluded_models.append(meta.model_name)

                last_error = e
                failovers += 1
                
                if failovers <= self.max_failovers:
                    logger.info(f"[ROUTER] Trying fallback provider (attempt {failovers})")

        logger.error("[ROUTER] No healthy providers available")
        raise AllProvidersExhaustedError(f"Structured generation exhausted failovers. Last error: {str(last_error)}")

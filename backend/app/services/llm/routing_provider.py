"""
Curato AI — Routing LLM Provider
Wraps actual providers to implement the Provider Routing Policy Engine and Circuit Breaking failover.
"""

import time
from typing import Any, List, Optional
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
        
    # We delay importing get_llm_provider to avoid circular imports if it were in factory
    def _get_underlying_provider(self, provider_name: str) -> LLMProvider:
        from app.services.llm.factory import _get_raw_llm_provider
        return _get_raw_llm_provider(provider_name)
        
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        excluded_models = []
        failovers = 0
        last_error = None
        
        while failovers <= self.max_failovers:
            meta = RoutingPolicyEngine.get_best_provider(self.policy, excluded_models=excluded_models)
            
            if not meta:
                raise RuntimeError("No healthy providers available for routing.")
                
            provider_instance = self._get_underlying_provider(meta.provider)
            start_time = time.monotonic()
            
            try:
                # Execution
                response = await provider_instance.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format
                )
                
                latency_ms = (time.monotonic() - start_time) * 1000
                
                # Health Record
                ProviderHealthStore.record_success(meta.provider, meta.model_name, latency_ms)
                CircuitBreaker.record_success(meta.provider, meta.model_name)
                
                # Overwrite response metadata so it reflects the actual routed model
                response.provider = meta.provider
                response.model = meta.model_name
                
                # Trace logic handles attaching the policy
                return response
                
            except Exception as e:
                logger.warning(
                    "Provider generation failed", 
                    provider=meta.provider, 
                    model=meta.model_name,
                    error=str(e)
                )
                
                # Record Failure and trip circuit if necessary
                ProviderHealthStore.record_failure(meta.provider, meta.model_name)
                CircuitBreaker.record_failure(meta.provider, meta.model_name)
                
                # Prepare failover
                excluded_models.append(meta.model_name)
                last_error = e
                failovers += 1
                
        raise RuntimeError(f"Workflow completely exhausted LLM failovers. Last error: {str(last_error)}")

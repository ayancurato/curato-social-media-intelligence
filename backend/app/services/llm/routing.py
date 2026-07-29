"""
Curato AI — Provider Routing Policy Engine
Dynamically selects the best LLM provider based on configurable policies.
"""

from typing import List, Optional
from app.services.evaluations.registry import provider_registry, ModelMetadata
from app.services.llm.scoring import ProviderHealthStore
from app.services.llm.circuit_breaker import CircuitBreaker


class RoutingPolicyEngine:
    
    @classmethod
    def get_best_provider(cls, policy: str = "Balanced", excluded_models: List[str] = None) -> Optional[ModelMetadata]:
        """
        Evaluates and ranks all registered models based on the active routing policy.
        Skips OPEN circuit breakers and explicitly excluded models.
        import time
        
        if excluded_models is None:
            excluded_models = []
            
        available_models = []
        
        for name, meta in provider_registry._models.items():
            if name in excluded_models:
                continue
                
            health = ProviderHealthStore.get_health(meta.provider, name)
            if health.cooldown_until > time.time():
                continue
                
            available_models.append(meta)
            
        if not available_models:
            return None
            
        # Sort based on policy
        if policy == "Lowest Cost":
            return sorted(available_models, key=lambda m: (
                ProviderHealthStore.get_health(m.provider, m.model_name).consecutive_failures,
                m.input_token_price + m.output_token_price
            ))[0]
        
        elif policy == "Highest Quality":
            return sorted(available_models, key=lambda m: (
                ProviderHealthStore.get_health(m.provider, m.model_name).consecutive_failures,
                m.context_window, 
                -m.input_token_price
            ), reverse=True)[0]
            
        elif policy == "Lowest Latency":
            return sorted(available_models, key=lambda m: (
                ProviderHealthStore.get_health(m.provider, m.model_name).consecutive_failures,
                ProviderHealthStore.get_health(m.provider, m.model_name).average_latency_ms
            ))[0]
            
        elif policy == "Highest Reliability":
            return sorted(available_models, key=lambda m: (
                ProviderHealthStore.get_health(m.provider, m.model_name).consecutive_failures,
                -ProviderHealthStore.get_health(m.provider, m.model_name).success_rate
            ))[0]
            
        else: # "Balanced"
            def balanced_score(m: ModelMetadata) -> float:
                health = ProviderHealthStore.get_health(m.provider, m.model_name)
                # Severe penalty for consecutive failures
                failure_penalty = health.consecutive_failures * 10000
                cost_penalty = (m.input_token_price + m.output_token_price) * 1000
                latency_penalty = health.average_latency_ms / 1000.0 if health.average_latency_ms > 0 else 1.0
                return (health.success_rate * 100) - cost_penalty - latency_penalty - failure_penalty
                
            return sorted(available_models, key=balanced_score, reverse=True)[0]

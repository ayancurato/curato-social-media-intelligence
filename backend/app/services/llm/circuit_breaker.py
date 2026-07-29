"""
Curato AI — LLM Circuit Breaker
Prevents cascading failures by tripping the circuit when an upstream provider becomes unhealthy.
"""

import time
from typing import Dict
from app.services.llm.scoring import ProviderHealthStore


class CircuitBreaker:
    """State machine for provider circuit breaking."""
    
    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT_SEC = 60
    
    _state: Dict[str, dict] = {}

    @classmethod
    def _get_state(cls, key: str) -> dict:
        if key not in cls._state:
            cls._state[key] = {
                "failures": 0,
                "status": "CLOSED", # CLOSED (Healthy), OPEN (Unhealthy), HALF_OPEN (Testing recovery)
                "last_failure_time": 0
            }
        return cls._state[key]

    @classmethod
    def is_open(cls, provider: str, model: str) -> bool:
        key = f"{provider}:{model}"
        state = cls._get_state(key)
        
        if state["status"] == "OPEN":
            if time.time() - state["last_failure_time"] > cls.RECOVERY_TIMEOUT_SEC:
                state["status"] = "HALF_OPEN"
                ProviderHealthStore.update_circuit_status(provider, model, "HALF_OPEN")
                return False
            return True
            
        return False

    @classmethod
    def record_success(cls, provider: str, model: str):
        key = f"{provider}:{model}"
        state = cls._get_state(key)
        state["failures"] = 0
        if state["status"] in ["OPEN", "HALF_OPEN"]:
            state["status"] = "CLOSED"
            ProviderHealthStore.update_circuit_status(provider, model, "CLOSED")

    @classmethod
    def record_failure(cls, provider: str, model: str, retry_after: float = None):
        key = f"{provider}:{model}"
        state = cls._get_state(key)
        state["failures"] += 1
        state["last_failure_time"] = time.time()
        
        # Determine cooldown
        cooldown = retry_after if retry_after is not None else cls.RECOVERY_TIMEOUT_SEC
        
        if state["status"] == "HALF_OPEN" or state["failures"] >= cls.FAILURE_THRESHOLD:
            state["status"] = "OPEN"
            ProviderHealthStore.update_circuit_status(provider, model, "OPEN")
            ProviderHealthStore.mark_cooldown(provider, model, cooldown)

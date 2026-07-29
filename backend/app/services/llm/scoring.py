"""
Curato AI — Provider Health & Scoring
Tracks real-time health metrics of LLM providers.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ProviderHealth:
    provider: str
    model: str
    availability: bool = True
    average_latency_ms: float = 0.0
    success_rate: float = 1.0
    failure_rate: float = 0.0
    total_requests: int = 0
    total_failures: int = 0
    circuit_status: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    # New observability fields
    cooldown_until: float = 0.0
    last_failure: float = 0.0
    last_failure_reason: str = ""
    consecutive_failures: int = 0


class ProviderHealthStore:
    """In-memory store tracking the health of all registered providers."""
    
    _store: Dict[str, ProviderHealth] = {}
    
    @classmethod
    def get_health(cls, provider: str, model: str) -> ProviderHealth:
        key = f"{provider}:{model}"
        if key not in cls._store:
            cls._store[key] = ProviderHealth(provider=provider, model=model)
        return cls._store[key]
    
    @classmethod
    def record_success(cls, provider: str, model: str, latency_ms: float):
        h = cls.get_health(provider, model)
        h.total_requests += 1
        h.average_latency_ms = ((h.average_latency_ms * (h.total_requests - 1)) + latency_ms) / h.total_requests
        h.success_rate = (h.total_requests - h.total_failures) / h.total_requests
        h.failure_rate = h.total_failures / h.total_requests
        h.consecutive_failures = 0
        
    @classmethod
    def record_failure(cls, provider: str, model: str, reason: str = ""):
        import time
        h = cls.get_health(provider, model)
        h.total_requests += 1
        h.total_failures += 1
        h.consecutive_failures += 1
        h.last_failure = time.time()
        h.last_failure_reason = reason
        h.success_rate = (h.total_requests - h.total_failures) / h.total_requests
        h.failure_rate = h.total_failures / h.total_requests

    @classmethod
    def mark_quota_exhausted(cls, provider: str, model: str, retry_after: Optional[float] = None):
        import time
        h = cls.get_health(provider, model)
        cooldown = retry_after if retry_after else 86400  # Default 24 hours
        h.cooldown_until = time.time() + cooldown
        h.last_failure = time.time()
        h.last_failure_reason = "Quota exhausted"
        
    @classmethod
    def mark_cooldown(cls, provider: str, model: str, seconds: float):
        import time
        h = cls.get_health(provider, model)
        h.cooldown_until = time.time() + seconds
        
    @classmethod
    def update_circuit_status(cls, provider: str, model: str, status: str):
        h = cls.get_health(provider, model)
        h.circuit_status = status
        if status == "OPEN":
            h.availability = False
        else:
            h.availability = True

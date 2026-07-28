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
        
    @classmethod
    def record_failure(cls, provider: str, model: str):
        h = cls.get_health(provider, model)
        h.total_requests += 1
        h.total_failures += 1
        h.success_rate = (h.total_requests - h.total_failures) / h.total_requests
        h.failure_rate = h.total_failures / h.total_requests
        
    @classmethod
    def update_circuit_status(cls, provider: str, model: str, status: str):
        h = cls.get_health(provider, model)
        h.circuit_status = status
        if status == "OPEN":
            h.availability = False
        else:
            h.availability = True

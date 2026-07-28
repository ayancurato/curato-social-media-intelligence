"""
Curato AI — LLM Provider Factory

Creates the appropriate LLM provider based on configuration.
Supports per-agent model selection.
"""

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.llm.base import LLMProvider
from app.services.llm.openai_provider import OpenAIProvider

logger = get_logger(__name__)

# ── Provider cache ───────────────────────────────────────────────────────────
_providers: dict[str, LLMProvider] = {}


def _get_raw_llm_provider(provider_name: str) -> LLMProvider:
    """Internal method to get the raw un-routed provider."""
    if provider_name in _providers:
        return _providers[provider_name]

    if provider_name == "openai":
        provider = OpenAIProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider_name}'. "
            f"Supported providers: openai. "
        )

    _providers[provider_name] = provider
    return provider


def get_llm_provider(policy_override: str | None = None) -> LLMProvider:
    """
    Get the Routing LLM Provider which handles all failover and policy routing.
    
    Args:
        policy_override: The routing policy to use (Balanced, Lowest Cost, etc.)
    """
    from app.services.llm.routing_provider import RoutingLLMProvider
    policy = policy_override or "Balanced"
    return RoutingLLMProvider(policy=policy)

"""
Curato AI — Provider Metadata Registry
Centralized registry containing capabilities and pricing for LLM providers.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ModelMetadata:
    provider: str
    model_name: str
    input_token_price: float  # Price per 1M tokens in USD
    output_token_price: float # Price per 1M tokens in USD
    context_window: int
    max_output_tokens: int
    json_mode_support: bool
    tool_calling_support: bool
    streaming_support: bool
    vision_support: bool
    default_temperature: float
    default_max_tokens: int


class ProviderRegistry:
    """
    Registry for dynamic retrieval of LLM model metadata and pricing.
    Allows easy switching between providers without altering business logic.
    """
    
    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._register_defaults()
        
    def _register_defaults(self):
        # OpenAI Models
        self.register(ModelMetadata(
            provider="openai",
            model_name="gpt-4o",
            input_token_price=5.00,
            output_token_price=15.00,
            context_window=128000,
            max_output_tokens=4096,
            json_mode_support=True,
            tool_calling_support=True,
            streaming_support=True,
            vision_support=True,
            default_temperature=0.3,
            default_max_tokens=4096
        ))
        self.register(ModelMetadata(
            provider="openai",
            model_name="gpt-4o-mini",
            input_token_price=0.15,
            output_token_price=0.60,
            context_window=128000,
            max_output_tokens=16384,
            json_mode_support=True,
            tool_calling_support=True,
            streaming_support=True,
            vision_support=True,
            default_temperature=0.3,
            default_max_tokens=4096
        ))
        
        # Anthropic Models (Unsupported in factory currently)
        # self.register(ModelMetadata(
        #     provider="anthropic",
        #     model_name="claude-3-5-sonnet-20240620",
        #     input_token_price=3.00,
        #     output_token_price=15.00,
        #     context_window=200000,
        #     max_output_tokens=8192,
        #     json_mode_support=True,
        #     tool_calling_support=True,
        #     streaming_support=True,
        #     vision_support=True,
        #     default_temperature=0.3,
        #     default_max_tokens=4096
        # ))
        
        # Google Models (Unsupported in factory currently)
        # self.register(ModelMetadata(
        #     provider="google",
        #     model_name="gemini-1.5-pro",
        #     input_token_price=3.50,
        #     output_token_price=10.50,
        #     context_window=2000000,
        #     max_output_tokens=8192,
        #     json_mode_support=True,
        #     tool_calling_support=True,
        #     streaming_support=True,
        #     vision_support=True,
        #     default_temperature=0.3,
        #     default_max_tokens=4096
        # ))

    def register(self, metadata: ModelMetadata):
        self._models[metadata.model_name] = metadata

    def get_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        return self._models.get(model_name)

    def list_supported_models(self) -> list[str]:
        return list(self._models.keys())


# Singleton instance
provider_registry = ProviderRegistry()

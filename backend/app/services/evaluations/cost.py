"""
Curato AI — Cost Calculator
Dynamically computes execution costs using the Provider Metadata Registry.
"""

from typing import Dict, Optional
from app.services.evaluations.registry import provider_registry


class CostCalculator:
    """
    Computes cost based on token usage and model pricing.
    """

    @classmethod
    def calculate_cost(cls, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculates the total cost in USD for a given execution.
        Returns 0.0 if the model is not found in the registry.
        """
        metadata = provider_registry.get_metadata(model_name)
        if not metadata:
            return 0.0
            
        input_cost = (input_tokens / 1_000_000) * metadata.input_token_price
        output_cost = (output_tokens / 1_000_000) * metadata.output_token_price
        
        return input_cost + output_cost

    @classmethod
    def aggregate_trace_costs(cls, traces: list[Dict]) -> float:
        """
        Calculates the total cost from a list of WorkerTraces.
        """
        total_cost = 0.0
        for trace in traces:
            model = trace.get("model", "")
            tokens = trace.get("tokens", {})
            input_tokens = tokens.get("prompt_tokens", 0)
            output_tokens = tokens.get("completion_tokens", 0)
            
            total_cost += cls.calculate_cost(model, input_tokens, output_tokens)
            
        return total_cost

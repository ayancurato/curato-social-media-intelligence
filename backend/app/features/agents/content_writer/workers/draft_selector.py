"""
Curato AI — Draft Selector Worker
"""

import json
from typing import Any
from app.features.agents.content_writer.workers.base import BaseWriterWorker


class DraftSelectorWorker(BaseWriterWorker):
    @property
    @property
    def name(self) -> str:
        return "Draft Selector"

    @property
    def temperature(self) -> float:
        return 0.1  # Highly analytical and deterministic

    @property
    def system_prompt(self) -> str:
        return """You are the Draft Selector.
Your job is to analyze multiple draft variations and select the absolute best one that aligns with the blueprint strategy, brand voice, and marketing objective.

OUTPUT FORMAT:
You MUST return a JSON object containing the selected draft ID.
{
    "selected_variation_id": "v2",
    "reasoning": "Variation 2 balances the founder-first tone perfectly while maintaining strong pacing."
}
"""

    def format_user_prompt(self, blueprint: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        variations = context.get("variations", []) if context else []
        
        return f"""Select the best variation for the blueprint.

BLUEPRINT:
{json.dumps(blueprint, indent=2)}

VARIATIONS:
{json.dumps(variations, indent=2)}

Return ONLY valid JSON according to the schema."""


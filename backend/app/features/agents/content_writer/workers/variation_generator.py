"""
Curato AI — Variation Generator Worker
"""

import json
from typing import Any
from app.features.agents.content_writer.workers.base import BaseWriterWorker


class VariationGeneratorWorker(BaseWriterWorker):
    @property
    @property
    def name(self) -> str:
        return "Variation Generator"

    @property
    def temperature(self) -> float:
        return 0.8  # Max creativity

    @property
    def system_prompt(self) -> str:
        return """You are the Draft Variation Generator.
Your job is to take an initial draft and create 3 distinct variations of it.
Each variation should explore a slightly different pacing, tone, or structural approach, while staying true to the Blueprint constraints.

OUTPUT FORMAT:
You MUST return a JSON object containing the variations.
{
    "variations": [
        {
            "id": "v1",
            "draft": "Variation 1 text...",
            "approach": "Aggressive pacing with shorter sentences."
        },
        {
            "id": "v2",
            "draft": "Variation 2 text...",
            "approach": "More storytelling focus."
        },
        {
            "id": "v3",
            "draft": "Variation 3 text...",
            "approach": "Data-heavy and analytical."
        }
    ]
}
"""

    def format_user_prompt(self, blueprint: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        initial_draft = context.get("draft", "") if context else ""
        
        return f"""Create 3 distinct variations of this draft based on the blueprint strategy.

BLUEPRINT:
{json.dumps(blueprint, indent=2)}

INITIAL DRAFT:
{initial_draft}

Return ONLY valid JSON according to the schema."""


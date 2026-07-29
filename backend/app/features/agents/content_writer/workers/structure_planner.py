"""
Curato AI — Content Structure Planner Worker
"""

import json
from typing import Any
from app.features.agents.content_writer.workers.base import BaseWriterWorker


class StructurePlannerWorker(BaseWriterWorker):
    @property
    @property
    def name(self) -> str:
        return "Structure Planner"

    @property
    def temperature(self) -> float:
        return 0.1  # Highly deterministic

    @property
    def system_prompt(self) -> str:
        return """You are the Content Structure Planner.
Your job is to generate a logical outline for a post based on a provided Content Blueprint.
Do NOT write the actual prose. ONLY write the structural sections.

OUTPUT FORMAT:
You MUST return a JSON object.
{
    "outline": [
        "Section 1: The Hook (Contrarian)",
        "Section 2: The Core Problem",
        "Section 3: The Framework",
        "Section 4: The Proof",
        "Section 5: The CTA"
    ],
    "reasoning": "This structure supports the PAS storytelling framework."
}
"""

    def format_user_prompt(self, blueprint: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        return f"""Create a logical outline for the following content blueprint:

{json.dumps(blueprint, indent=2)}

Return ONLY valid JSON according to the schema."""


"""
Curato AI — Angle Explorer Worker (Batch Mode)
"""

import json
from typing import Any
from app.features.agents.content_strategist.workers.base import BaseBatchContentWorker


class AngleExplorerWorker(BaseBatchContentWorker):
    @property
    @property
    def name(self) -> str:
        return "Angle Explorer"

    @property
    def system_prompt(self) -> str:
        return """You are the Lead Content Strategist.
Your job is to generate multiple strategic angles for a list of topics and select the strongest one for each.
An angle is the unique perspective or hook that makes the content interesting and differentiated.

OUTPUT FORMAT:
You MUST return a JSON object mapping each exact topic title to its angles.
{
    "evaluations": {
        "Exact Topic Title Here": {
            "primary_angle": "The counter-intuitive reality of X...",
            "secondary_angles": ["How X saves money", "Why X is the future of Y"],
            "reasoning": "This primary angle cuts through the noise by challenging conventional wisdom."
        }
    }
}
"""

    def format_user_prompt(self, topics: list[dict[str, Any]]) -> str:
        topics_subset = []
        for t in topics:
            topics_subset.append({
                "title": t.get("topic"),
                "audience": t.get("audience"),
                "intent": t.get("intent"),
                "business_alignment": t.get("business_alignment", {}).get("reasoning")
            })
            
        return f"""Evaluate the following prioritized topics and determine the best strategic angle:

{json.dumps(topics_subset, indent=2)}

Return ONLY valid JSON according to the schema."""


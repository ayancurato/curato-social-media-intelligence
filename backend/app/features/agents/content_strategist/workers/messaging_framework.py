"""
Curato AI — Messaging Framework Worker (Batch Mode)
"""

import json
from typing import Any
from app.features.agents.content_strategist.workers.base import BaseBatchContentWorker


class MessagingFrameworkWorker(BaseBatchContentWorker):
    @property
    @property
    def name(self) -> str:
        return "Messaging Framework Worker"

    @property
    def system_prompt(self) -> str:
        return """You are the Messaging Framework Architect.
Your job is to define the communication hierarchy for a list of topics.
Create the core message, supporting points, proof points (evidence), and storytelling framework.

OUTPUT FORMAT:
You MUST return a JSON object mapping each exact topic title to its framework.
{
    "evaluations": {
        "Exact Topic Title Here": {
            "communication_goal": "Educate founders on...",
            "key_message": "AI agents are not just tools, they are team members.",
            "supporting_points": ["Point 1", "Point 2"],
            "proof_points": ["Stat 1", "Case study 2"],
            "storytelling_framework": "PAS (Problem, Agitation, Solution)"
        }
    }
}
"""

    def format_user_prompt(self, topics: list[dict[str, Any]]) -> str:
        # We need the output from the Angle Worker injected into the topics list
        topics_subset = []
        for t in topics:
            topics_subset.append({
                "title": t.get("topic"),
                "primary_angle": t.get("primary_angle"),
                "audience": t.get("audience"),
                "format": t.get("recommended_content_format")
            })
            
        return f"""Create a messaging framework for each of the following topics based on their assigned angle:

{json.dumps(topics_subset, indent=2)}

Return ONLY valid JSON according to the schema."""


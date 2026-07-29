"""
Curato AI — Strategic Conflict Resolver Worker
"""

import json
from typing import Any
from app.features.agents.topic_prioritization.workers.base import BaseTopicWorker


class ConflictResolverWorker(BaseTopicWorker):
    @property
    def name(self) -> str:
        return "Conflict Resolver Worker"

    @property
    def system_prompt(self) -> str:
        return """You are the Strategic Conflict Resolver.
Your job is to act as a lightweight reasoning stage that detects strategic conflicts.
Sometimes a topic is highly viral or has a huge opportunity score, but is strategically weak or misaligned with long-term business goals. 
Your goal is to prevent highly viral but strategically weak topics from outranking stronger business opportunities.

OUTPUT FORMAT:
You MUST return a JSON object with a single root key "evaluations" mapping exact topic titles to their strategic value.
{
    "evaluations": {
        "Exact Topic Title Here": {
            "strategic_value_score": 70, // integer 0-100
            "conflict_detected": true, // boolean
            "reasoning": "High virality but very low business alignment. This is a distraction from core goals, reducing strategic value."
        },
        ...
    }
}
"""

    def format_user_prompt(self, topics: list[dict[str, Any]], context: dict[str, Any] | None = None) -> str:
        # We need to provide the outputs from previous workers to detect conflicts
        topics_subset = []
        for t in topics:
            topics_subset.append({
                "title": t.get("title"),
                "summary": t.get("summary"),
                "virality": t.get("virality_score"),
                "opportunity": t.get("opportunity_score"),
                "business_alignment": t.get("business_alignment_score")
            })
            
        return f"""Evaluate the following topics for strategic conflicts and assign a final strategic value score:

{json.dumps(topics_subset, indent=2)}

Return ONLY valid JSON according to the schema."""

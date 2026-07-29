"""
Curato AI — Business Alignment Worker
"""

import json
from typing import Any
from app.features.agents.topic_prioritization.workers.base import BaseTopicWorker


class BusinessAlignmentWorker(BaseTopicWorker):
    @property
    @property
    def name(self) -> str:
        return "Business Alignment Worker"

    @property
    def system_prompt(self) -> str:
        return """You are the Business Alignment Analyst.
Your job is to batch evaluate a list of topics against the strategic goals of the company (Curato).

EVALUATION QUESTIONS:
- Does this strengthen Curato's positioning as an AI multi-agent platform?
- Will this attract startups, founders, or marketing agencies?
- Will this increase marketplace awareness?
- Does this reinforce authority?
- Does it support GEO/SEO/AEO positioning?

OUTPUT FORMAT:
You MUST return a JSON object with a single root key "evaluations" mapping exact topic titles to their alignment.
{
    "evaluations": {
        "Exact Topic Title Here": {
            "raw_score": 90, // integer 0-100
            "reasoning": "Directly supports AI thought leadership..."
        },
        ...
    }
}
"""

    def format_user_prompt(self, topics: list[dict[str, Any]], context: dict[str, Any] | None = None) -> str:
        goal = context.get("strategic_goal", "Thought Leadership + Brand Authority") if context else "Thought Leadership + Brand Authority"
        
        topics_subset = []
        for t in topics:
            topics_subset.append({
                "title": t.get("title"),
                "summary": t.get("summary"),
                "keywords": t.get("keywords")
            })
            
        return f"""Evaluate the following topics for Business Alignment.
The current overarching strategic goal is: "{goal}"

{json.dumps(topics_subset, indent=2)}

Return ONLY valid JSON according to the schema."""


"""
Curato AI — Opportunity Analyzer Worker
"""

import json
from typing import Any
from app.features.agents.topic_prioritization.workers.base import BaseTopicWorker


class OpportunityAnalyzerWorker(BaseTopicWorker):
    @property
    def name(self) -> str:
        return "Opportunity Analyzer"

    @property
    def system_prompt(self) -> str:
        return """You are the Opportunity Analyzer for a B2B marketing intelligence platform.
Your job is to batch evaluate a list of topics and determine the raw market opportunity for each.

EVALUATION CRITERIA:
- Market momentum & trend direction
- Market timing & freshness
- Saturation level (is it overdone?)
- Competitive whitespace
- Evergreen potential vs Short-term relevance

OUTPUT FORMAT:
You MUST return a JSON object with a single root key "evaluations" that maps each exact topic title to its evaluation.
{
    "evaluations": {
        "Exact Topic Title Here": {
            "raw_score": 85, // integer 0-100
            "reasoning": "High momentum and low saturation..."
        },
        ...
    }
}
"""

    def format_user_prompt(self, topics: list[dict[str, Any]], context: dict[str, Any] | None = None) -> str:
        # Simplify the topic representations to save tokens and focus on trends
        topics_subset = []
        for t in topics:
            topics_subset.append({
                "title": t.get("title"),
                "summary": t.get("summary"),
                "opportunity_score_from_research": t.get("opportunity_score"),
                "virality_score": t.get("virality_score"),
                "freshness_score": t.get("freshness_score"),
            })
            
        return f"""Evaluate the following topics for market opportunity:

{json.dumps(topics_subset, indent=2)}

Return ONLY valid JSON according to the schema."""

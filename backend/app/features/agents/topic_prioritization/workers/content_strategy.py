"""
Curato AI — Content Strategy Worker
"""

import json
from typing import Any
from app.features.agents.topic_prioritization.workers.base import BaseTopicWorker


class ContentStrategyWorker(BaseTopicWorker):
    @property
    @property
    def name(self) -> str:
        return "Content Strategy Worker"

    @property
    def system_prompt(self) -> str:
        return """You are the Content Strategy Recommender.
Your job is to batch evaluate topics and recommend the best platform, format, and objective.

RECOMMENDATION OPTIONS:
- Platform: LinkedIn, Instagram
- Format: Carousel, Video, Founder POV, Industry Insight, Case Study, Thought Leadership, Educational, Trend Analysis, Opinion
- Objective: Thought Leadership, Lead Generation, Brand Awareness, Website Traffic, etc.

OUTPUT FORMAT:
You MUST return a JSON object with a single root key "evaluations" mapping exact topic titles to their recommendations.
{
    "evaluations": {
        "Exact Topic Title Here": {
            "recommended_platforms": ["LinkedIn"],
            "recommended_content_format": "Carousel",
            "marketing_objective": "Thought Leadership",
            "why_now": "This trend is peaking this week...",
            "reasoning": "Carousels perform best for data-heavy..."
        },
        ...
    }
}
"""

    def format_user_prompt(self, topics: list[dict[str, Any]], context: dict[str, Any] | None = None) -> str:
        topics_subset = []
        for t in topics:
            topics_subset.append({
                "title": t.get("title"),
                "summary": t.get("summary")
            })
            
        return f"""Evaluate the following topics and recommend the best content strategy:

{json.dumps(topics_subset, indent=2)}

Return ONLY valid JSON according to the schema."""


"""
Curato AI — Audience Intent Worker
"""

import json
from typing import Any
from app.features.agents.topic_prioritization.workers.base import BaseTopicWorker


class AudienceIntentWorker(BaseTopicWorker):
    @property
    def name(self) -> str:
        return "Audience Intent Worker"

    @property
    def system_prompt(self) -> str:
        return """You are the Audience Intent Classifier.
Your job is to batch evaluate topics and classify the target audience and their intent.

OUTPUT FORMAT:
You MUST return a JSON object with a single root key "evaluations" mapping exact topic titles to their classification.
{
    "evaluations": {
        "Exact Topic Title Here": {
            "audience": "Startup Founder", // e.g. Startup Founder, Marketing Agency, Growth Team, CMO
            "buyer_stage": "Awareness", // e.g. Awareness, Consideration, Decision
            "intent": "Learning", // e.g. Learning, Decision, Search, Business
            "intent_score": 85, // integer 0-100 reflecting how strong this intent is
            "reasoning": "Founders are actively learning about..."
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
                "summary": t.get("summary"),
                "audience_from_research": t.get("audience")
            })
            
        return f"""Evaluate the following topics for Audience and Intent:

{json.dumps(topics_subset, indent=2)}

Return ONLY valid JSON according to the schema."""

"""
Curato AI — Publishing Strategy Worker
"""

import json
from typing import Any
from app.features.agents.cmo.workers.base import BaseCMOWorker


class PublishingStrategyWorker(BaseCMOWorker):
    @property
    @property
    def name(self) -> str:
        return "Publishing Strategy Coordinator"

    @property
    def system_prompt(self) -> str:
        return """You are the AI CMO's Publishing Strategy Coordinator.
Your job is to determine the optimal publishing logistics for a finalized draft based on publishing guidelines and campaign priorities.

You MUST output a JSON object:
{
    "publish_now": <true/false>,
    "recommended_publish_date": "YYYY-MM-DDTHH:MM:SSZ or 'immediate'",
    "recommended_platform": "Target platform (e.g., linkedin, twitter)",
    "recommended_format": "Content format style",
    "reasoning": "Why this timing and platform were chosen."
}"""

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        draft = context.get("draft", "")
        blueprint = context.get("blueprint", {})
        marketing_knowledge = context.get("marketing_knowledge", {})
        
        return f"""Determine the optimal publishing strategy for this draft.

[DRAFT]
{draft}

[BLUEPRINT PREFERENCES]
{json.dumps(blueprint, indent=2)}

[PUBLISHING GUIDELINES]
{json.dumps(marketing_knowledge.get("publishing_guidelines", []), indent=2)}

Return the JSON strategy strictly."""


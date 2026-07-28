"""
Curato AI — CTA Strategist Worker (Single Topic Mode)
"""

import json
from typing import Any
from app.features.agents.content_strategist.workers.base import BaseSingleContentWorker


class CTAStrategistWorker(BaseSingleContentWorker):
    @property
    def name(self) -> str:
        return "CTA Strategist"

    @property
    def system_prompt(self) -> str:
        return """You are the Call-To-Action (CTA) Strategist.
Your job is to recommend the single most effective CTA for a given content topic.
The CTA must align perfectly with the marketing objective (e.g. Thought Leadership, Lead Gen) and the target audience.

OUTPUT FORMAT:
You MUST return a JSON object containing the CTA recommendation.
{
    "cta": "The exact wording of the call to action...",
    "cta_type": "Soft ask", // e.g., Soft ask, Hard ask, Engagement, Lead magnet
    "reasoning": "Since the goal is thought leadership, a soft engagement ask drives more reach."
}
"""

    def format_user_prompt(self, topic: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        return f"""Determine the best CTA for the following topic strategy:

Topic: {topic.get('topic')}
Marketing Objective: {topic.get('marketing_objective')}
Key Message: {topic.get('key_message')}
Audience: {topic.get('audience')}
Platform: {topic.get('platform', 'LinkedIn')}

Return ONLY valid JSON according to the schema."""

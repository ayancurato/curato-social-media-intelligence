"""
Curato AI — Hook Generator Worker (Single Topic Mode)
"""

import json
from typing import Any
from app.features.agents.content_strategist.workers.base import BaseSingleContentWorker


class HookGeneratorWorker(BaseSingleContentWorker):
    @property
    def name(self) -> str:
        return "Hook Generator"

    @property
    def system_prompt(self) -> str:
        return """You are the Hook Generator.
Your job is to write compelling, scroll-stopping opening hooks for a single topic.
Generate multiple hooks based on different psychological triggers (Question, Statistic, Contrarian, Story, Prediction, Pain Point) and select the strongest one.

OUTPUT FORMAT:
You MUST return a JSON object containing the hooks.
{
    "recommended_hook": "The single best hook text here...",
    "hook_type": "Contrarian",
    "alternative_hooks": [
        "A strong alternative hook 1...",
        "Another strong alternative hook 2..."
    ],
    "reasoning": "This hook works best because it immediately challenges the reader's assumptions."
}
"""

    def format_user_prompt(self, topic: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        return f"""Generate hooks for the following topic strategy:

Topic: {topic.get('topic')}
Angle: {topic.get('primary_angle')}
Key Message: {topic.get('key_message')}
Audience: {topic.get('audience')}
Platform: {topic.get('platform', 'LinkedIn')}

Return ONLY valid JSON according to the schema."""

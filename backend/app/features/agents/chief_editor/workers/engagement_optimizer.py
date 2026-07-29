"""
Curato AI — Engagement Optimizer Worker
"""

import json
from typing import Any
from app.features.agents.chief_editor.workers.base import BaseEditorWorker


class EngagementOptimizerWorker(BaseEditorWorker):
    @property
    @property
    def name(self) -> str:
        return "Engagement Optimizer"

    @property
    def temperature(self) -> float:
        return 0.3  # Slightly creative to improve pacing

    @property
    def system_prompt(self) -> str:
        return """You are the Engagement Optimizer.
Your job is to apply minor editorial fixes (flow, pacing, rhythm, transitions, minor grammar) inline.
DO NOT change the core strategic messaging, audience, CTA, or business objective.

OUTPUT FORMAT:
You MUST return a JSON object with the polished draft and engagement score.
{
    "edited_content": "The slightly polished text...",
    "engagement_score": 92,
    "reasoning": "Improved the transition between paragraph 2 and 3."
}
"""

    def format_user_prompt(self, draft_data: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        draft = draft_data.get("optimized_draft", draft_data.get("draft", ""))
        editorial_issues = context.get("editorial_issues", []) if context else []
        
        return f"""Apply minor fixes to improve engagement without changing the strategy.
Address these minor issues if possible: {json.dumps(editorial_issues)}

DRAFT:
{draft}

Return ONLY valid JSON according to the schema."""


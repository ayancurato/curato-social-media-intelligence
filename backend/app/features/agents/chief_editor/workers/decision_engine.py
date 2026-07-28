"""
Curato AI — Editorial Decision Engine
"""

import json
from typing import Any
from app.features.agents.chief_editor.workers.base import BaseEditorWorker


class DecisionEngineWorker(BaseEditorWorker):
    @property
    def name(self) -> str:
        return "Editorial Decision Engine"

    @property
    def system_prompt(self) -> str:
        return """You are the Editorial Decision Engine.
Based on the provided review feedback from the editorial, brand, and fact reviewers, make the final determination for the draft.

DECISION OPTIONS:
- "Approve": High quality, no major issues.
- "Minor Revision": Minor fixes applied inline, ready to proceed.
- "Major Revision": Significant structural or strategic misses requiring the Content Writer (Agent 4) to rewrite sections.
- "Reject": Unsalvageable or completely contradicts the brand/facts.

If Major Revision is chosen, you MUST provide a detailed `revision_plan` instructing Agent 4 what to rewrite.

OUTPUT FORMAT:
You MUST return a JSON object.
{
    "editorial_decision": "Major Revision",
    "confidence": 95,
    "reasoning": "The draft missed the core CTA completely and hallucinated a feature.",
    "revision_plan": {
        "preserve": ["The hook", "Paragraph 1"],
        "rewrite": ["Paragraph 2", "The CTA"],
        "fix": ["Remove hallucinated feature X", "Adopt a more authoritative tone"]
    }
}
"""

    def format_user_prompt(self, draft_data: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        reviews = context.get("reviews", {}) if context else {}
        
        return f"""Make the final editorial decision based on the compiled feedback.

REVIEWS:
{json.dumps(reviews, indent=2)}

Return ONLY valid JSON according to the schema."""

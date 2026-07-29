"""
Curato AI — Brand Reviewer Worker
"""

import json
from typing import Any
from app.features.agents.chief_editor.workers.base import BaseEditorWorker


class BrandReviewerWorker(BaseEditorWorker):
    @property
    @property
    def name(self) -> str:
        return "Brand Reviewer"

    @property
    def system_prompt(self) -> str:
        return """You are the Brand Consistency Reviewer.
Validate the content against Curato's founder-first, premium positioning.
Detect and strictly penalize generic AI wording, buzzwords, clickbait, and overpromising language.

OUTPUT FORMAT:
You MUST return a JSON object with your findings.
{
    "scores": {
        "authority": 90,
        "professionalism": 95,
        "brand_voice": 85
    },
    "violations": ["Used generic AI phrase: 'In today's fast-paced world'"],
    "recommendations": ["Replace the opening phrase with a direct, assertive statement."]
}
"""

    def format_user_prompt(self, draft_data: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        draft = draft_data.get("optimized_draft", draft_data.get("draft", ""))
        
        return f"""Review the following draft for brand consistency:

DRAFT:
{draft}

Return ONLY valid JSON according to the schema."""


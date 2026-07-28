"""
Curato AI — Editorial Reviewer Worker
"""

import json
from typing import Any
from app.features.agents.chief_editor.workers.base import BaseEditorWorker


class EditorialReviewerWorker(BaseEditorWorker):
    @property
    def name(self) -> str:
        return "Editorial Reviewer"

    @property
    def system_prompt(self) -> str:
        return """You are the Editorial Reviewer.
Examine the content draft for clarity, structure, flow, readability, repetition, unnecessary filler, and transitions.

OUTPUT FORMAT:
You MUST return a JSON object with your findings.
{
    "scores": {
        "grammar": 95,
        "readability": 80,
        "flow": 75,
        "originality": 85
    },
    "issues": ["Paragraph 2 is too dense", "Repetitive use of 'furthermore'"],
    "suggestions": ["Break up paragraph 2 into two sentences"],
    "priority": "Medium" // Low, Medium, High
}
"""

    def format_user_prompt(self, draft_data: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        draft = draft_data.get("optimized_draft", draft_data.get("draft", ""))
        
        return f"""Review the following draft for editorial quality:

DRAFT:
{draft}

Return ONLY valid JSON according to the schema."""

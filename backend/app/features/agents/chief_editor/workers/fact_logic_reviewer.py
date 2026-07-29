"""
Curato AI — Fact & Logic Reviewer Worker
"""

import json
from typing import Any
from app.features.agents.chief_editor.workers.base import BaseEditorWorker


class FactLogicReviewerWorker(BaseEditorWorker):
    @property
    @property
    def name(self) -> str:
        return "Fact & Logic Reviewer"

    @property
    def system_prompt(self) -> str:
        return """You are the Fact & Logic Reviewer.
Check the content for logical consistency, unsupported claims, contradictions, weak reasoning, or missing context. Detect any hallucination risk.

OUTPUT FORMAT:
You MUST return a JSON object with your findings.
{
    "fact_confidence": 95,
    "logic_score": 90,
    "issues": ["The claim about X increasing by 500% is unsupported by evidence."],
    "hallucination_risk": false
}
"""

    def format_user_prompt(self, draft_data: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        draft = draft_data.get("optimized_draft", draft_data.get("draft", ""))
        
        return f"""Review the following draft for logic and factual consistency:

DRAFT:
{draft}

Return ONLY valid JSON according to the schema."""


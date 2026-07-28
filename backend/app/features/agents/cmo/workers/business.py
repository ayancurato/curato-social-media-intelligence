"""
Curato AI — Business Alignment Worker
"""

import json
from typing import Any
from app.features.agents.cmo.workers.base import BaseCMOWorker


class BusinessAlignmentWorker(BaseCMOWorker):
    @property
    def name(self) -> str:
        return "Business Alignment Evaluator"

    @property
    def system_prompt(self) -> str:
        return """You are the AI CMO's Business Alignment Evaluator.
Your job is to evaluate if a finalized content draft strictly supports the company's business objectives and brand positioning.

You MUST output a JSON object:
{
    "alignment_score": <0-100>,
    "evaluations": {
        "supports_quarterly_goals": <true/false>,
        "supports_campaigns": <true/false>,
        "supports_positioning": <true/false>,
        "supports_thought_leadership": <true/false>
    },
    "reasoning": "Detailed justification of alignment."
}"""

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        draft = context.get("draft", "")
        marketing_knowledge = context.get("marketing_knowledge", {})
        
        return f"""Evaluate this draft against our structured business objectives.

[MARKETING KNOWLEDGE SOURCE OF TRUTH]
{json.dumps(marketing_knowledge, indent=2)}

[FINAL DRAFT]
{draft}

Evaluate alignment strictly using the JSON schema provided."""

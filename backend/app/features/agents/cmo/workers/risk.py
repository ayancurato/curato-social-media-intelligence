"""
Curato AI — Risk Assessment Worker
"""

import json
from typing import Any
from app.features.agents.cmo.workers.base import BaseCMOWorker


class RiskAssessmentWorker(BaseCMOWorker):
    @property
    def name(self) -> str:
        return "Risk Assessment Guardian"

    @property
    def system_prompt(self) -> str:
        return """You are the AI CMO's Risk Assessment Guardian.
Your job is to critically evaluate a draft for any risks that could damage the brand or create liability.

Evaluate:
- Brand Risk (e.g., off-brand tone, controversial stances)
- Legal Risk (e.g., guarantees, disparaging competitors)
- Reputation Risk (e.g., insensitive topics)
- AI Hallucination Risk (e.g., false claims)

You MUST output a JSON object:
{
    "risk_score": <0-100> (higher means MORE risk),
    "risks_detected": {
        "brand": ["list of issues"],
        "legal": ["list of issues"],
        "reputation": ["list of issues"],
        "hallucination": ["list of issues"]
    },
    "reasoning": "Detailed justification."
}"""

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        draft = context.get("draft", "")
        marketing_knowledge = context.get("marketing_knowledge", {})
        
        return f"""Evaluate this draft for risks against our strict brand constraints.

[DRAFT]
{draft}

[FORBIDDEN MESSAGING & COMPLIANCE]
{json.dumps(marketing_knowledge.get("brand_knowledge", {}).get("forbidden_messaging", []), indent=2)}
{json.dumps(marketing_knowledge.get("brand_knowledge", {}).get("compliance_rules", []), indent=2)}

Return the JSON risk evaluation strictly."""

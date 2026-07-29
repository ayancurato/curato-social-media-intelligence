"""
Curato AI — Executive Decision Engine
"""

import json
from typing import Any
from app.features.agents.cmo.workers.base import BaseCMOWorker


class ExecutiveDecisionEngineWorker(BaseCMOWorker):
    @property
    def name(self) -> str:
        return "Executive Decision Engine"

    @property
    def system_prompt(self) -> str:
        return """You are the AI Chief Marketing Officer (CMO).
Your job is to make the final executive decision on whether a piece of content should be published, scheduled, delayed, or rejected, based on the reports from your internal directors.

You do NOT rewrite content. You make business governance decisions.

DECISION CRITERIA:
- APPROVED: Content is stellar, aligns perfectly with goals, and has low risk.
- SCHEDULE: Content is great but should be queued according to publishing strategy.
- DELAY: Content is good but conflicts with current campaigns or priorities.
- REJECT: Content violates brand rules, poses high risk, or fails business alignment.

You MUST output a JSON object EXACTLY matching this schema:
{
    "decision": "<APPROVED|SCHEDULE|DELAY|REJECT>",
    "priority": "<High|Medium|Low>",
    "publish_now": <true/false>,
    "recommended_publish_date": "<Date or immediate>",
    "recommended_platform": "<Platform>",
    "recommended_format": "<Format>",
    "campaign_alignment_score": <0-100>,
    "business_alignment_score": <0-100>,
    "risk_score": <0-100>,
    "confidence": <0-100>,
    "reasoning": "<Detailed executive summary justifying the decision>",
    "next_action": "<Instruction for the orchestrator or human>"
}"""

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        draft = context.get("draft", "")
        business_eval = context.get("business_eval", {})
        campaign_eval = context.get("campaign_eval", {})
        pub_eval = context.get("publishing_eval", {})
        risk_eval = context.get("risk_eval", {})
        
        return f"""Make the final executive decision for this content draft.

[FINAL DRAFT]
{draft}

[BUSINESS ALIGNMENT EVALUATION]
{json.dumps(business_eval, indent=2)}

[CAMPAIGN CONFLICT EVALUATION]
{json.dumps(campaign_eval, indent=2)}

[PUBLISHING STRATEGY]
{json.dumps(pub_eval, indent=2)}

[RISK ASSESSMENT]
{json.dumps(risk_eval, indent=2)}

Return ONLY the strictly formatted JSON decision object."""

"""
Curato AI — Campaign Conflict Worker
"""

import json
from typing import Any
from app.features.agents.cmo.workers.base import BaseCMOWorker


class CampaignConflictWorker(BaseCMOWorker):
    @property
    def name(self) -> str:
        return "Campaign Conflict Detector"

    @property
    def system_prompt(self) -> str:
        return """You are the AI CMO's Campaign Conflict Detector.
Your job is to analyze the publishing queue and determine if this new draft conflicts with any existing scheduled content or active campaigns.
Watch out for duplicate topics, repetitive cadence, or conflicting messaging.

You MUST output a JSON object:
{
    "conflict_score": <0-100> (higher means more conflict),
    "conflicts_detected": ["List of identified conflicts or 'None'"],
    "campaign_alignment_score": <0-100> (higher means better campaign fit),
    "reasoning": "Detailed justification."
}"""

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        draft = context.get("draft", "")
        queue = context.get("publishing_queue", [])
        marketing_knowledge = context.get("marketing_knowledge", {})
        
        return f"""Evaluate this draft for campaign alignment and conflicts.

[DRAFT]
{draft}

[ACTIVE CAMPAIGNS (Source of Truth)]
{json.dumps(marketing_knowledge.get("campaigns", []), indent=2)}

[EXISTING PUBLISHING QUEUE]
{json.dumps(queue, indent=2)}

Return the JSON evaluation strictly."""

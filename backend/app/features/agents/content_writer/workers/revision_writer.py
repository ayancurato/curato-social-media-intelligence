"""
Curato AI — Revision Writer Worker
"""

import json
from typing import Any
from app.features.agents.content_writer.workers.base import BaseWriterWorker


class RevisionWriterWorker(BaseWriterWorker):
    @property
    def name(self) -> str:
        return "Revision Writer"

    @property
    def temperature(self) -> float:
        return 0.5  # Balance between adherence to plan and creative writing

    @property
    def system_prompt(self) -> str:
        return """You are Curato's AI Content Writer in Revision Mode.
Your job is to revise a draft based exactly on the Chief Editor's structured revision plan.
Preserve the sections you are told to preserve. Rewrite only the sections you are told to rewrite.
Apply the specific fixes requested.

OUTPUT FORMAT:
You MUST return a JSON object containing the revised draft text.
{
    "draft": "Your revised content draft text here...",
    "reasoning": "Explain how you applied the revision plan."
}
"""

    def format_user_prompt(self, blueprint: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        original_draft = context.get("original_draft", "") if context else ""
        revision_plan = context.get("revision_plan", {}) if context else {}
        editorial_memory = context.get("editorial_memory", []) if context else []
        
        memory_str = "\n".join([f"- {m}" for m in editorial_memory])
        
        return f"""Revise the draft strictly according to the Editor's revision plan.

BLUEPRINT:
{json.dumps(blueprint, indent=2)}

ORIGINAL DRAFT:
{original_draft}

REVISION PLAN:
{json.dumps(revision_plan, indent=2)}

PAST EDITORIAL FEEDBACK TO AVOID:
{memory_str}

Return ONLY valid JSON according to the schema."""

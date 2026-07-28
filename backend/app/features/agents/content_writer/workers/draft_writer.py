"""
Curato AI — Draft Writer Worker
"""

import json
from typing import Any
from app.features.agents.content_writer.workers.base import BaseWriterWorker


class DraftWriterWorker(BaseWriterWorker):
    @property
    def name(self) -> str:
        return "Draft Writer"

    @property
    def temperature(self) -> float:
        return 0.7  # Highly creative

    @property
    def system_prompt(self) -> str:
        return """You are Curato's AI Content Writer.
Your job is to write a complete first draft based on the provided Content Blueprint and Outline.

RULES:
- Maintain a premium, founder-first tone.
- NEVER use generic AI language ("In today's fast-paced digital landscape...").
- Do NOT use emojis unless the platform is Instagram.
- STRICTLY use the exact Hook and CTA provided in the blueprint.

OUTPUT FORMAT:
You MUST return a JSON object containing the draft text.
{
    "draft": "Your full content draft text here...",
    "reasoning": "Explain creative choices made."
}
"""

    def format_user_prompt(self, blueprint: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        outline = context.get("outline", []) if context else []
        
        return f"""Write the complete draft based on the following strategy and outline:

BLUEPRINT:
{json.dumps(blueprint, indent=2)}

OUTLINE:
{json.dumps(outline, indent=2)}

Return ONLY valid JSON according to the schema."""

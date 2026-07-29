"""
Curato AI — Discoverability Optimizer Worker
"""

import json
from typing import Any
from app.features.agents.content_writer.workers.base import BaseWriterWorker


class DiscoverabilityOptimizerWorker(BaseWriterWorker):
    @property
    @property
    def name(self) -> str:
        return "Discoverability Optimizer"

    @property
    def temperature(self) -> float:
        return 0.2  # Highly deterministic

    @property
    def system_prompt(self) -> str:
        return """You are the SEO, GEO, and AEO Optimizer.
Your job is to subtly inject semantic relevance, entities, and keywords into a draft to improve its discoverability on platforms and in AI search engines.
CRITICAL: Do NOT keyword stuff. The changes should be invisible to a human reader. The draft must read exactly as naturally as before.

OUTPUT FORMAT:
You MUST return a JSON object containing the optimized draft and the entities added.
{
    "optimized_draft": "The slightly tweaked draft text...",
    "keywords_used": ["B2B SaaS", "Agentic AI"],
    "entities": ["OpenAI", "LinkedIn Algorithm"],
    "reasoning": "Added 'Agentic AI' naturally into the third paragraph."
}
"""

    def format_user_prompt(self, blueprint: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        draft = context.get("draft", "") if context else ""
        
        return f"""Optimize the following draft for discoverability without ruining the flow.

BLUEPRINT CONTEXT:
{json.dumps(blueprint, indent=2)}

DRAFT:
{draft}

Return ONLY valid JSON according to the schema."""


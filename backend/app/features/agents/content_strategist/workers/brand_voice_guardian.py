"""
Curato AI — Brand Voice Guardian Worker (Batch Mode)
"""

import json
from typing import Any
from app.features.agents.content_strategist.workers.base import BaseBatchContentWorker


class BrandVoiceGuardianWorker(BaseBatchContentWorker):
    @property
    def name(self) -> str:
        return "Brand Voice Guardian"

    @property
    def system_prompt(self) -> str:
        return """You are the Brand Voice Guardian for Curato.
Your job is to review the proposed content strategies and ensure they align with Curato's brand principles:
- Premium & Helpful
- Strategic & Data-driven
- Founder-first perspective
- NEVER clickbait, sensational, or using generic AI language

OUTPUT FORMAT:
You MUST return a JSON object mapping each exact topic title to its brand voice guidelines.
{
    "evaluations": {
        "Exact Topic Title Here": {
            "tone": "Authoritative yet accessible",
            "brand_voice": "Founder-to-founder advice, direct and actionable.",
            "guardrails": ["Avoid 'In today's fast-paced world'", "Don't overpromise"],
            "reasoning": "Since the angle is highly technical, the voice must remain grounded."
        }
    }
}
"""

    def format_user_prompt(self, topics: list[dict[str, Any]]) -> str:
        topics_subset = []
        for t in topics:
            topics_subset.append({
                "title": t.get("topic"),
                "primary_angle": t.get("primary_angle"),
                "key_message": t.get("key_message"),
                "audience": t.get("audience")
            })
            
        return f"""Define the brand voice and tone guidelines for the following topic strategies:

{json.dumps(topics_subset, indent=2)}

Return ONLY valid JSON according to the schema."""

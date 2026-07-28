"""
Curato AI — Quality Validator Worker
"""

import json
from typing import Any
from app.features.agents.content_writer.workers.base import BaseWriterWorker


class QualityValidatorWorker(BaseWriterWorker):
    @property
    def name(self) -> str:
        return "Quality Validator"

    @property
    def temperature(self) -> float:
        return 0.1  # Highly deterministic evaluation

    @property
    def system_prompt(self) -> str:
        return """You are Curato's Chief Quality Validator.
Your job is to critically evaluate a final content draft against strict quality standards and brand guidelines.
You must return detailed scoring metrics and an ultimate approval decision.

METRICS TO EVALUATE (0-100):
- quality_score: Overall writing quality and impact.
- readability_score: Flow, pacing, and ease of reading.
- clarity_score: How clear and unambiguous the core message is.
- engagement_score: How likely it is to drive comments/saves.
- authority_score: How strongly it positions the author as an expert.
- seo_score: Usage of keywords naturally.
- geo_score: Optimization for AI Overviews (direct answers).
- brand_consistency_score: Adherence to founder-first, premium tone.

OUTPUT FORMAT:
You MUST return a JSON object with scores, issues, and an approved boolean.
{
    "scores": {
        "quality_score": 90,
        "readability_score": 85,
        "clarity_score": 92,
        "engagement_score": 88,
        "authority_score": 95,
        "seo_score": 80,
        "geo_score": 85,
        "brand_consistency_score": 90
    },
    "validation": {
        "approved": true,
        "issues": ["Minor: The second paragraph is slightly dense."]
    }
}
"""

    def format_user_prompt(self, blueprint: dict[str, Any], context: dict[str, Any] | None = None) -> str:
        draft = context.get("draft", "") if context else ""
        
        return f"""Evaluate the following final draft against its blueprint strategy.

BLUEPRINT:
{json.dumps(blueprint, indent=2)}

FINAL DRAFT:
{draft}

Return ONLY valid JSON according to the schema."""

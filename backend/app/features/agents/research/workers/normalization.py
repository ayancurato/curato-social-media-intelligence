"""
Curato AI — Normalization Worker
"""

import json
from typing import Any

from app.features.agents.research.workers.base import BaseWorker


class NormalizationWorker(BaseWorker):
    @property
    def name(self) -> str:
        return "normalization"

    async def acquire_data(self, **kwargs: Any) -> Any:
        """For normalization, acquisition is simply passing through the raw_data."""
        return kwargs.get("raw_data", [])

    async def synthesize_data(self, acquired_data: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Deduplicate similar trends, normalize keywords, and cluster related findings.
        Input is the combined output of Workers 1-4.
        """
        prompt = f"""
        You are an expert data normalizer and analyst.
        I will provide you with raw research data collected from multiple workers (Google Search, News, Competitors, Social).
        Your task is to:
        1. Deduplicate similar trends and merge their evidence.
        2. Normalize keywords and hashtags.
        3. Cluster related findings.
        4. Produce clean, structured trend objects.
        
        Every trend MUST follow this exact schema:
        - title: string
        - summary: string
        - sources: list of strings (where this trend was observed)
        - keywords: list of strings
        - hashtags: list of strings
        - competitors: list of strings (competitors discussing this)
        - audience: string (target audience)
        - opportunity_score: number (0-100, your baseline assessment before full scoring)
        - virality_score: number (0-100)
        - freshness_score: number (0-100)
        - confidence_score: number (0-100)
        - reasoning: string (why these scores were assigned)
        
        Return a strict JSON object with a 'normalized_trends' array containing these objects.
        
        Raw Data:
        {json.dumps(acquired_data, default=str)}
        """

        llm_response = await self.llm.generate_structured(
            prompt=prompt,
            system_prompt="You are a strict data normalization pipeline. Output only valid JSON.",
            model_config=self.model_config,
        )

        return {
            "success": True,
            "data": llm_response.get("normalized_trends", []),
            "source": "normalization_worker"
        }

"""
Curato AI — Content Gap Analyzer Worker
"""

import json
from typing import Any

from app.features.agents.research.workers.base import BaseWorker


class ContentGapWorker(BaseWorker):
    @property
    def name(self) -> str:
        return "content_gap"

    async def execute(self, normalized_trends: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        """
        Identify content gaps based on normalized trends.
        Find saturated topics, unexplained topics, and unanswered questions.
        """
        prompt = f"""
        You are a Content Gap Analyzer.
        Review the following normalized social and market trends.
        Your mission is to identify:
        1. Topics everyone is discussing (saturated).
        2. Topics that nobody has explained properly (opportunities).
        3. Questions that remain unanswered in the industry.
        4. Specific recommendations for Curato to become a thought leader.
        
        Return a strict JSON object with this schema:
        {{
            "content_gaps": [
                {{
                    "topic": "string",
                    "status": "saturated" | "unexplained" | "unanswered_question",
                    "description": "string",
                    "opportunity_score": number (0-100, where 100 means high potential for Curato)
                }}
            ],
            "recommended_topics": [
                {{
                    "title": "string",
                    "angle": "string",
                    "why": "string"
                }}
            ]
        }}
        
        Normalized Trends:
        {json.dumps(normalized_trends, default=str)}
        """

        llm_response = await self.llm.generate_structured(
            prompt=prompt,
            system_prompt="You are a strategic marketing analyst. Output only valid JSON.",
            model_config=self.model_config,
        )

        return {
            "success": True,
            "data": llm_response,
            "source": "content_gap_worker"
        }

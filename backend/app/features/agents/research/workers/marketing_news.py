"""
Curato AI — Marketing News Intelligence Worker
"""

import asyncio
from typing import Any

from app.features.agents.research.workers.base import BaseWorker


class MarketingNewsWorker(BaseWorker):
    @property
    def name(self) -> str:
        return "marketing_news"

    async def acquire_data(self, **kwargs: Any) -> Any:
        """Collect recent marketing news."""
        topics = [
            "marketing publications",
            "startup news",
            "AI product launch",
            "algorithm updates",
            "industry announcements"
        ]
        
        async def fetch_news(topic: str) -> dict[str, Any]:
            res = await self.invoke_tool("news_api", topic=topic, days_back=7)
            if res.success:
                return {"topic": topic, "data": res.data}
            return {"topic": topic, "error": res.error}

        tasks = [fetch_news(topic) for topic in topics]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def synthesize_data(self, acquired_data: Any, **kwargs: Any) -> dict[str, Any]:
        prompt = f"""
        Extract structured news items from the following tool outputs.
        Do NOT summarize. Return a strict JSON object with a 'news_items' array.
        Each item in the array must have:
        - headline: string
        - publication: string
        - date_published: string
        - category: string
        - significance: string (brief explanation of why this matters)

        Tool Outputs:
        {acquired_data}
        """

        llm_response = await self.llm.generate_structured(
            prompt=prompt,
            system_prompt="You are a data extraction assistant. Return ONLY valid JSON.",
            model_config=self.model_config,
        )

        return {
            "success": True,
            "data": llm_response.get("news_items", []),
            "source": "marketing_news_worker"
        }

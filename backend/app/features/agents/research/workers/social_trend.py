"""
Curato AI — Social Trend Intelligence Worker
"""

import asyncio
from typing import Any

from app.features.agents.research.workers.base import BaseWorker


class SocialTrendWorker(BaseWorker):
    @property
    @property
    def name(self) -> str:
        return "social_trend"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Research social media trends."""
        
        async def fetch_reddit() -> dict:
            res = await self.invoke_tool("reddit", subreddit="marketing", query="trends")
            return {"platform": "reddit", "data": getattr(res, 'data', {})}
            
        async def fetch_linkedin() -> dict:
            res = await self.invoke_tool("linkedin", action="trending_topics")
            return {"platform": "linkedin", "data": getattr(res, 'data', {})}
            
        async def fetch_google_trends() -> dict:
            res = await self.invoke_tool("google_trends", keywords=["marketing", "AI", "social media"], region="US")
            return {"platform": "google_trends", "data": getattr(res, 'data', {})}

        tasks = [fetch_reddit(), fetch_linkedin(), fetch_google_trends()]
        tool_outputs = await asyncio.gather(*tasks, return_exceptions=True)

        prompt = f"""
        Extract structured social trend intelligence from the following tool outputs.
        Return a strict JSON object with a 'social_trends' array.
        Each item in the array must have:
        - platform: string (e.g. 'LinkedIn', 'Reddit')
        - trending_topics: list of strings
        - trending_hashtags: list of strings
        - emerging_discussions: list of strings
        - breaking_news: list of strings (if any)
        
        Tool Outputs:
        {tool_outputs}
        """

        llm_response = await self.llm.generate_structured(
            prompt=prompt,
            system_prompt="You are a data extraction assistant. Return ONLY valid JSON.",
            model_config=self.model_config,
        )

        return {
            "success": True,
            "data": llm_response.get("social_trends", []),
            "source": "social_trend_worker"
        }


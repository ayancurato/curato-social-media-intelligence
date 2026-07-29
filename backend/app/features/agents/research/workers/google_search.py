"""
Curato AI — Google Search Intelligence Worker
"""

import asyncio
from typing import Any

from app.features.agents.research.workers.base import BaseWorker


class GoogleSearchWorker(BaseWorker):
    @property
    def name(self) -> str:
        return "google_search"

    async def acquire_data(self, **kwargs: Any) -> Any:
        """Acquire web search results for marketing topics."""
        topics = [
            "marketing trends",
            "startup news",
            "agency trends",
            "AI marketing",
            "GEO AEO SEO",
            "branding PR",
            "marketing automation"
        ]

        # We can execute a few tool calls concurrently
        async def fetch_topic(topic: str) -> dict[str, Any]:
            res = await self.invoke_tool("web_search", query=topic, num_results=5)
            if res.success:
                return {"topic": topic, "data": res.data}
            return {"topic": topic, "error": res.error}

        tasks = [fetch_topic(topic) for topic in topics]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def synthesize_data(self, acquired_data: Any, **kwargs: Any) -> dict[str, Any]:
        """Synthesize search results with LLM."""
        prompt = f"""
        Extract structured search results from the following tool outputs.
        Do NOT summarize. Return a strict JSON object with a 'search_results' array.
        Each item in the array must have:
        - title: string
        - url: string (or 'unknown' if not provided)
        - snippet: string
        - category: string (e.g. 'SEO', 'AI Marketing')
        - source_topic: string

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
            "data": llm_response.get("search_results", []),
            "source": "google_search_worker"
        }

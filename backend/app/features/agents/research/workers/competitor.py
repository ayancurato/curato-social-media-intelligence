"""
Curato AI — Competitor Intelligence Worker
"""

import asyncio
from typing import Any

from app.features.agents.research.workers.base import BaseWorker


class CompetitorWorker(BaseWorker):
    @property
    @property
    def name(self) -> str:
        return "competitor_intelligence"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Research competitor insights."""
        competitors = [
            "Breef", "DesignRush", "Clutch", "Collective OS", "Lifted by Upwork",
            "TopTal", "Sortlist", "HubSpot", "Semrush", "Ahrefs", "OpenAI",
            "Anthropic", "Perplexity", "Clay", "Canva", "Buffer", "Hootsuite",
            "Marketing Examples"
        ]
        
        # Batching tool calls to avoid rate limits / excessive wait times in stub
        # In a real implementation we would likely use a specialized competitor API or scraper
        
        async def fetch_competitor(comp: str) -> dict[str, Any]:
            # Simulate checking linkedin and generic web search
            res = await self.invoke_tool("linkedin", action=f"company_posts:{comp}")
            return {"competitor": comp, "success": res.success, "data": getattr(res, 'data', {})}

        # To keep it quick, we'll only actually fetch a few in the stub, but ask LLM to extract
        tasks = [fetch_competitor(comp) for comp in competitors[:5]] # Limit to 5 for speed
        tool_outputs = await asyncio.gather(*tasks, return_exceptions=True)

        prompt = f"""
        Extract structured competitor insights from the following tool outputs.
        Return a strict JSON object with a 'competitor_insights' array.
        Each item in the array must have:
        - company: string
        - recent_posts: list of strings (topics they posted about)
        - content_formats: list of strings (e.g. video, carousel, text)
        - posting_frequency: string
        - recurring_themes: list of strings
        - audience_engagement: string (high/medium/low or specific metrics if available)

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
            "data": llm_response.get("competitor_insights", []),
            "source": "competitor_worker"
        }


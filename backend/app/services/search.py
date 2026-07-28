"""
Curato AI — Search Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str
    content: str | None = None
    score: float | None = None


class SearchProvider(ABC):
    """Abstract interface for web search providers (Tavily, Serper, etc.)."""
    
    @abstractmethod
    async def search(self, query: str, num_results: int = 10, **kwargs: Any) -> list[SearchResultItem]:
        """Perform a web search."""
        pass
        
    @abstractmethod
    async def news(self, topic: str, days_back: int = 7, num_results: int = 10) -> list[SearchResultItem]:
        """Perform a news search."""
        pass


# ── Tavily Implementation ────────────────────────────────────────────────────

import os
from app.core.logging import get_logger

logger = get_logger(__name__)


class TavilySearchProvider(SearchProvider):
    """Tavily API implementation for search and news."""
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not found. Search tools will fail.")
            
    async def _execute_tavily(self, query: str, search_depth: str = "basic", topic: str = "general", max_results: int = 5, days_back: int | None = None) -> list[SearchResultItem]:
        if not self.api_key:
            return []
            
        import asyncio
        from tavily import TavilyClient
        
        # TavilyClient is sync by default, but we can wrap it
        client = TavilyClient(api_key=self.api_key)
        
        def _call() -> dict:
            kwargs = {
                "query": query,
                "search_depth": search_depth,
                "topic": topic,
                "max_results": max_results,
            }
            if topic == "news" and days_back is not None:
                kwargs["days_back"] = days_back
                
            return client.search(**kwargs)
            
        try:
            res = await asyncio.to_thread(_call)
            results = []
            for item in res.get("results", []):
                results.append(SearchResultItem(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""), # Tavily uses 'content' for snippet
                    score=item.get("score")
                ))
            return results
        except Exception as e:
            logger.error("Tavily search failed", error=str(e), query=query)
            raise

    async def search(self, query: str, num_results: int = 10, **kwargs: Any) -> list[SearchResultItem]:
        return await self._execute_tavily(
            query=query, 
            search_depth="advanced", 
            topic="general", 
            max_results=num_results
        )

    async def news(self, topic: str, days_back: int = 7, num_results: int = 10) -> list[SearchResultItem]:
        return await self._execute_tavily(
            query=topic, 
            search_depth="advanced", 
            topic="news", 
            max_results=num_results,
            days_back=days_back
        )


# ── Factory ──────────────────────────────────────────────────────────────────

def get_search_provider() -> SearchProvider:
    return TavilySearchProvider()

"""
Curato AI — Trends Provider Interface
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from app.core.logging import get_logger

logger = get_logger(__name__)


class TrendItem(BaseModel):
    keyword: str
    trend_data: list[dict[str, Any]] | None = None
    related_queries: list[str] | None = None


class TrendProvider(ABC):
    """Abstract interface for Google Trends data."""
    
    @abstractmethod
    async def get_trends(self, keywords: list[str], region: str = "US") -> list[TrendItem]:
        pass


# ── PyTrends Implementation ──────────────────────────────────────────────────

class PyTrendsProvider(TrendProvider):
    """Google Trends data using pytrends."""
    
    async def get_trends(self, keywords: list[str], region: str = "US") -> list[TrendItem]:
        from pytrends.request import TrendReq
        
        def _fetch() -> list[TrendItem]:
            pytrends = TrendReq(hl='en-US', tz=360)
            
            # Google Trends only allows up to 5 keywords per request
            kw_list = keywords[:5] 
            pytrends.build_payload(kw_list, cat=0, timeframe='now 7-d', geo=region, gprop='')
            
            results = []
            
            try:
                # Get interest over time
                df = pytrends.interest_over_time()
                
                # Get related queries
                related = pytrends.related_queries()
                
                for kw in kw_list:
                    trend_data = []
                    if not df.empty and kw in df.columns:
                        # Convert pandas Series to dicts
                        for date, value in df[kw].items():
                            trend_data.append({
                                "date": date.isoformat(),
                                "value": int(value)
                            })
                            
                    related_list = []
                    if related and kw in related and related[kw].get('top') is not None:
                        top_queries = related[kw]['top']
                        if not top_queries.empty:
                            related_list = top_queries['query'].tolist()[:10]
                            
                    results.append(TrendItem(
                        keyword=kw,
                        trend_data=trend_data,
                        related_queries=related_list
                    ))
            except Exception as e:
                logger.error("PyTrends fetch failed", error=str(e))
                # Return partial or empty on failure, pytrends can be brittle (rate limited)
                for kw in kw_list:
                    results.append(TrendItem(keyword=kw, trend_data=[], related_queries=[]))
                    
            return results
            
        return await asyncio.to_thread(_fetch)


# ── Factory ──────────────────────────────────────────────────────────────────

def get_trend_provider() -> TrendProvider:
    return PyTrendsProvider()

"""
Curato AI — Agent 1: Research Intelligence

Gathers trending topics, industry news, and competitor insights
using a pipeline of specialized internal workers.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import AgentValidationError
from app.features.agents.base import BaseAgent
from app.features.websocket.manager import get_connection_manager
from app.features.agents.research.workers.google_search import GoogleSearchWorker
from app.features.agents.research.workers.marketing_news import MarketingNewsWorker
from app.features.agents.research.workers.competitor import CompetitorWorker
from app.features.agents.research.workers.social_trend import SocialTrendWorker
from app.features.agents.research.workers.normalization import NormalizationWorker
from app.features.agents.research.workers.content_gap import ContentGapWorker


class ResearchAgent(BaseAgent):
    """
    Research Intelligence Agent.

    Responsibilities:
    - Run multiple specialized workers concurrently.
    - Normalize and merge findings.
    - Analyze content gaps.
    - Output structured JSON.
    """

    @property
    def name(self) -> str:
        return "research"

    async def validate_input(self, input_data: dict[str, Any]) -> bool:
        """Validate input — research agent accepts minimal input (context only)."""
        if not isinstance(input_data, dict):
            raise AgentValidationError(
                message="Input must be a dictionary",
                agent_name=self.name,
            )
        return True

    async def validate_output(self, output_data: dict[str, Any]) -> bool:
        """Validate output contains required fields."""
        required_fields = [
            "generated_at",
            "top_trends",
            "competitor_insights",
            "marketing_news",
            "social_trends",
            "content_gaps",
            "recommended_topics",
            "reasoning",
            "confidence_score"
        ]
        missing = [f for f in required_fields if f not in output_data]
        if missing:
            raise AgentValidationError(
                message=f"Output missing required fields: {missing}",
                agent_name=self.name,
                details={"missing_fields": missing},
            )
        return True

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute research intelligence gathering via internal workers.
        """
        self._logger.info("Research agent executing worker pipeline")
        
        # 1. Extract session for WS events
        session_id_str = input_data.get("session_context", {}).get("session_id")
        ws_manager = get_connection_manager()

        async def emit(event_type: str, data: dict[str, Any]) -> None:
            if session_id_str:
                import uuid
                await ws_manager.broadcast_to_session(uuid.UUID(session_id_str), event_type, data)

        await emit("worker_pipeline_started", {"agent": self.name})

        # 2. Instantiate workers
        kwargs = {
            "llm": self._llm,
            "tool_registry": self._tool_registry,
            "model_config": self._config.model,
            "emit_event": emit
        }
        
        workers = [
            GoogleSearchWorker(**kwargs),
            MarketingNewsWorker(**kwargs),
            CompetitorWorker(**kwargs),
            SocialTrendWorker(**kwargs)
        ]

        # 3. Execute Phase 1 Workers concurrently
        self._logger.info("Executing Phase 1 workers concurrently")
        tasks = [w._safe_execute(max_retries=2) for w in workers]
        phase1_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful data
        raw_data = []
        failures = 0
        
        for res in phase1_results:
            if isinstance(res, dict) and res.get("success"):
                raw_data.append(res)
            else:
                failures += 1

        confidence_score = 100 - (failures * 15)
        
        # 4. Normalization Stage
        self._logger.info("Executing Normalization Worker")
        norm_worker = NormalizationWorker(**kwargs)
        norm_res = await norm_worker._safe_execute(max_retries=2, raw_data=raw_data)
        
        normalized_trends = norm_res.get("data", []) if isinstance(norm_res, dict) else []

        # 5. Content Gap Stage
        self._logger.info("Executing Content Gap Analyzer")
        gap_worker = ContentGapWorker(**kwargs)
        gap_res = await gap_worker._safe_execute(max_retries=2, normalized_trends=normalized_trends)
        
        gap_data = gap_res.get("data", {}) if isinstance(gap_res, dict) else {}

        # 6. Construct Final Report
        await emit("generating_research_report", {"agent": self.name})
        
        # Map raw data back to specific sections for the final payload
        marketing_news = []
        competitor_insights = []
        social_trends = []
        
        for item in raw_data:
            src = item.get("source")
            if src == "marketing_news_worker":
                marketing_news.extend(item.get("data", []))
            elif src == "competitor_worker":
                competitor_insights.extend(item.get("data", []))
            elif src == "social_trend_worker":
                social_trends.extend(item.get("data", []))

        # Extract tags
        all_hashtags = set()
        all_keywords = set()
        for t in normalized_trends:
            for h in t.get("hashtags", []):
                all_hashtags.add(h)
            for k in t.get("keywords", []):
                all_keywords.add(k)

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "top_trends": normalized_trends,
            "competitor_insights": competitor_insights,
            "marketing_news": marketing_news,
            "social_trends": social_trends,
            "content_gaps": gap_data.get("content_gaps", []),
            "recommended_topics": gap_data.get("recommended_topics", []),
            "trend_scores": [{"title": t.get("title"), "opportunity": t.get("opportunity_score")} for t in normalized_trends],
            "hashtags": list(all_hashtags),
            "keywords": list(all_keywords),
            "reasoning": "Aggregated via independent research workers (Search, News, Competitor, Social) and normalized.",
            "confidence_score": max(0, confidence_score)
        }

        # Keep raw sources for persistence (will be dropped from next agent input, but stored by orchestrator)
        report["sources"] = raw_data
        
        await emit("worker_pipeline_completed", {"agent": self.name})

        return report

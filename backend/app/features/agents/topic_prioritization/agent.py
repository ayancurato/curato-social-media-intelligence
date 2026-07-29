"""
Curato AI — Topic Prioritization Agent (Agent 2)
"""

import asyncio
from typing import Any

from app.core.exceptions import AgentValidationError
from app.core.logging import get_logger
from app.features.agents.base import BaseAgent
from app.features.agents.config import get_agent_config
from app.features.agents.topic_prioritization.workers import (
    AudienceIntentWorker,
    BusinessAlignmentWorker,
    ConflictResolverWorker,
    ContentStrategyWorker,
    OpportunityAnalyzerWorker,
    PriorityEngine,
)
from app.features.websocket.manager import get_connection_manager
from app.services.llm.factory import get_llm_provider

logger = get_logger(__name__)


class TopicPrioritizationAgent(BaseAgent):
    """
    Curato AI Chief Content Strategist.
    Evaluates research from Agent 1 and ranks topics based on strategic value.
    """

    @property
    @property
    def name(self) -> str:
        return "topic_prioritization"

    async def validate_input(self, data: dict[str, Any]) -> bool:
        """Validate input from Agent 1 (Research Intelligence)."""
        if "research_results" not in data and "topics" not in data:
            raise AgentValidationError("Missing research results or topics in input")
        return True

    async def validate_output(self, data: dict[str, Any]) -> bool:
        """Ensure Top 30 and Top 5 recommendations are present."""
        if "top_30_topics" not in data:
            raise AgentValidationError("Missing top_30_topics in output")
        if "top_5_recommendations" not in data:
            raise AgentValidationError("Missing top_5_recommendations in output")
        return True

    async def run(
        self,
        session_id: str,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute the Topic Prioritization pipeline.
        """
        logger.info("Topic Prioritization Agent started", session_id=session_id)
        ws_manager = get_connection_manager()

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="topic_prioritization_started",
            payload={"message": "Initializing AI Chief Content Strategist"}
        )

        config = get_agent_config("topic_prioritization")
        llm = get_llm_provider(config.model)

        # Initialize workers
        opp_worker = OpportunityAnalyzerWorker(llm)
        biz_worker = BusinessAlignmentWorker(llm)
        aud_worker = AudienceIntentWorker(llm)
        strat_worker = ContentStrategyWorker(llm)
        conflict_worker = ConflictResolverWorker(llm)

        metadata = config.metadata or {}
        strategic_profile = metadata.get("strategic_profile", "Thought Leadership")
        profiles = metadata.get("profiles", {})
        weights = profiles.get(strategic_profile, {})

        priority_engine = PriorityEngine(weights)

        # Extract topics
        topics = input_data.get("research_results", [])
        if not topics:
            topics = input_data.get("topics", [])
            
        if not topics:
            return {"top_30_topics": [], "top_5_recommendations": []}

        # 1. Batch Execution of Reasoning Workers (Concurrently)
        await ws_manager.emit_event(
            session_id=session_id,
            event_type="topic_evaluation_started",
            payload={"message": f"Evaluating {len(topics)} topics concurrently..."}
        )

        context = {"strategic_goal": strategic_profile}

        results = await asyncio.gather(
            opp_worker.evaluate_topics(topics, context),
            biz_worker.evaluate_topics(topics, context),
            aud_worker.evaluate_topics(topics, context),
            strat_worker.evaluate_topics(topics, context),
            return_exceptions=True
        )

        evaluations = {
            "opportunity": results[0].get("evaluations", {}) if not isinstance(results[0], Exception) else {},
            "business_alignment": results[1].get("evaluations", {}) if not isinstance(results[1], Exception) else {},
            "audience_intent": results[2].get("evaluations", {}) if not isinstance(results[2], Exception) else {},
            "content_strategy": results[3].get("evaluations", {}) if not isinstance(results[3], Exception) else {},
        }

        # Handle potential errors from concurrent tasks gracefully
        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Worker {idx} failed", error=str(res))

        # 2. Conflict Resolver
        await ws_manager.emit_event(
            session_id=session_id,
            event_type="conflict_resolution_started",
            payload={"message": "Checking for strategic conflicts..."}
        )

        try:
            # We must inject the intermediate scores into the topics for the conflict resolver
            enriched_topics = []
            for t in topics:
                title = t.get("title")
                et = t.copy()
                et["opportunity_score"] = evaluations["opportunity"].get(title, {}).get("raw_score", 0)
                et["business_alignment_score"] = evaluations["business_alignment"].get(title, {}).get("raw_score", 0)
                enriched_topics.append(et)
                
            conflict_res = await conflict_worker.evaluate_topics(enriched_topics, context)
            evaluations["conflict_resolver"] = conflict_res.get("evaluations", {})
        except Exception as e:
            logger.error("Conflict resolver failed", error=str(e))
            evaluations["conflict_resolver"] = {}

        # 3. Priority Engine
        await ws_manager.emit_event(
            session_id=session_id,
            event_type="priority_ranking_started",
            payload={"message": "Calculating explainable priority scores and ranking..."}
        )

        ranked_topics = []
        for topic in topics:
            scored_topic = priority_engine.calculate_priority(topic, evaluations)
            ranked_topics.append(scored_topic)

        # Sort by priority score descending
        ranked_topics.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

        top_30 = ranked_topics[:30]
        top_5 = ranked_topics[:5]

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="topic_prioritization_completed",
            payload={"message": "Topic prioritization complete.", "top_topics": [t.get("topic") for t in top_5]}
        )

        return {
            "top_30_topics": top_30,
            "top_5_recommendations": top_5,
            "metadata": {
                "strategic_profile": strategic_profile,
                "weights_used": weights,
                "total_evaluated": len(topics)
            }
        }


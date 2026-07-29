"""
Curato AI — Content Strategist Agent (Agent 3)
"""

import asyncio
from typing import Any

from app.core.exceptions import AgentValidationError
from app.core.logging import get_logger
from app.features.agents.base import BaseAgent
from app.features.agents.config import get_agent_config
from app.features.agents.content_strategist.workers import (
    AngleExplorerWorker,
    MessagingFrameworkWorker,
    BrandVoiceGuardianWorker,
    HookGeneratorWorker,
    CTAStrategistWorker,
    BlueprintAssembler,
)
from app.features.websocket.manager import get_connection_manager
from app.services.llm.factory import get_llm_provider

logger = get_logger(__name__)


class ContentStrategistAgent(BaseAgent):
    """
    Curato AI Content Strategist.
    Transforms prioritized topics into complete strategic content blueprints.
    """

    @property
    def name(self) -> str:
        return "content_strategist"

    async def validate_input(self, data: dict[str, Any]) -> bool:
        """Validate input from Agent 2 (Topic Prioritization)."""
        if "top_5_recommendations" not in data:
            raise AgentValidationError("Missing top_5_recommendations in input", agent_name=self.name() if callable(self.name) else self.name)
        return True

    async def validate_output(self, data: dict[str, Any]) -> bool:
        """Ensure blueprints are present."""
        if "blueprints" not in data:
            raise AgentValidationError("Missing blueprints in output", agent_name=self.name() if callable(self.name) else self.name)
        return True

    async def run(
        self,
        session_id: str,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute the Content Strategist pipeline using a Hybrid execution strategy.
        """
        logger.info("Content Strategist Agent started", session_id=session_id)
        ws_manager = get_connection_manager()

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="content_strategy_started",
            payload={"message": "Initializing AI Content Strategist"}
        )

        config = get_agent_config("content_strategist")
        llm = get_llm_provider(config.model)

        # Initialize workers
        angle_worker = AngleExplorerWorker(llm)
        msg_worker = MessagingFrameworkWorker(llm)
        brand_worker = BrandVoiceGuardianWorker(llm)
        
        hook_worker = HookGeneratorWorker(llm)
        cta_worker = CTAStrategistWorker(llm)
        assembler = BlueprintAssembler()

        # Extract top 5 topics
        topics = input_data.get("top_5_recommendations", [])
        if not topics:
            return {"blueprints": []}

        # ── 1. Batch Execution (Strategic Consistency) ─────────────
        await ws_manager.emit_event(
            session_id=session_id,
            event_type="batch_strategy_started",
            payload={"message": "Generating strategic angles and messaging frameworks..."}
        )
        
        # Sequentially run the batch workers (each processes all 5 topics)
        # We run them sequentially because each depends on the previous output
        
        # Angles
        angle_res = await angle_worker.evaluate_topics(topics)
        angles_map = angle_res.get("evaluations", {})
        
        # Inject angles into a mutated topic list for messaging framework
        mutated_topics_for_msg = []
        for t in topics:
            title = t.get("topic")
            mt = t.copy()
            mt["primary_angle"] = angles_map.get(title, {}).get("primary_angle", "")
            mutated_topics_for_msg.append(mt)
            
        # Messaging
        msg_res = await msg_worker.evaluate_topics(mutated_topics_for_msg)
        msgs_map = msg_res.get("evaluations", {})
        
        # Inject messaging into mutated topic list for brand voice
        mutated_topics_for_brand = []
        for mt in mutated_topics_for_msg:
            title = mt.get("topic")
            mt2 = mt.copy()
            mt2["key_message"] = msgs_map.get(title, {}).get("key_message", "")
            mutated_topics_for_brand.append(mt2)
            
        # Brand Voice
        brand_res = await brand_worker.evaluate_topics(mutated_topics_for_brand)
        brands_map = brand_res.get("evaluations", {})

        # ── 2. Per-Topic Creative Execution ────────────────────────
        await ws_manager.emit_event(
            session_id=session_id,
            event_type="creative_execution_started",
            payload={"message": "Generating creative hooks and CTAs..."}
        )
        
        async def process_topic_creatives(topic_data: dict[str, Any]) -> dict[str, Any]:
            title = topic_data.get("topic")
            
            # Prepare rich context for creative workers
            rich_topic = topic_data.copy()
            rich_topic["primary_angle"] = angles_map.get(title, {}).get("primary_angle", "")
            rich_topic["key_message"] = msgs_map.get(title, {}).get("key_message", "")
            
            # Execute hook and CTA generation concurrently per topic
            hook_task = hook_worker.evaluate_topic(rich_topic)
            cta_task = cta_worker.evaluate_topic(rich_topic)
            
            hook_eval, cta_eval = await asyncio.gather(hook_task, cta_task, return_exceptions=True)
            
            # Fallback if exceptions occurred
            if isinstance(hook_eval, Exception):
                logger.error("Hook generator failed", error=str(hook_eval))
                hook_eval = {}
            if isinstance(cta_eval, Exception):
                logger.error("CTA strategist failed", error=str(cta_eval))
                cta_eval = {}
                
            return {
                "title": title,
                "hook_eval": hook_eval,
                "cta_eval": cta_eval
            }
            
        # Run creative workers concurrently for all topics
        creative_results = await asyncio.gather(
            *(process_topic_creatives(t) for t in topics)
        )
        
        # Map creative results by title
        creatives_map = {res["title"]: res for res in creative_results}

        # ── 3. Deterministic Assembly ──────────────────────────────
        await ws_manager.emit_event(
            session_id=session_id,
            event_type="blueprint_assembly_started",
            payload={"message": "Assembling final content blueprints..."}
        )

        blueprints = []
        for topic in topics:
            title = topic.get("topic")
            
            c_res = creatives_map.get(title, {})
            
            bp = assembler.assemble(
                topic=topic,
                angle_eval=angles_map.get(title, {}),
                msg_eval=msgs_map.get(title, {}),
                brand_eval=brands_map.get(title, {}),
                hook_eval=c_res.get("hook_eval", {}),
                cta_eval=c_res.get("cta_eval", {})
            )
            blueprints.append(bp)

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="content_strategy_completed",
            payload={"message": "Content blueprints generated."}
        )

        return {
            "blueprints": blueprints
        }

"""
Curato AI — Executive Marketing Approval Agent (Agent 6)
"""

import asyncio
from typing import Any

from app.core.logging import get_logger
from app.features.agents.base import BaseAgent
from app.features.agents.config import get_agent_config
from app.services.llm.factory import get_llm_provider
from app.features.realtime.connection import get_connection_manager
from app.services.marketing_knowledge.provider import marketing_provider

from app.features.agents.cmo.workers import (
    BusinessAlignmentWorker,
    CampaignConflictWorker,
    PublishingStrategyWorker,
    RiskAssessmentWorker,
    ExecutiveDecisionEngineWorker
)

logger = get_logger(__name__)


class CMOAgent(BaseAgent):
    @property
    def display_name(self) -> str:
        return "Executive Marketing Approval"

    def name(self) -> str:
        return "cmo"

    async def validate_input(self, data: dict[str, Any]) -> bool:
        return True  # We expect at least one draft or reviewed_draft

    async def validate_output(self, data: dict[str, Any]) -> bool:
        return True

    async def _process_single_decision(self, draft_data: dict[str, Any], session_id: str, ws_manager: Any, llm: Any, marketing_knowledge: dict) -> dict[str, Any]:
        title = draft_data.get("title", "Unknown Topic")
        draft = draft_data.get("edited_content", draft_data.get("optimized_draft", draft_data.get("draft", "")))
        
        await ws_manager.emit_event(session_id, "executive_review_started", {"topic": title})

        context = {
            "draft": draft,
            "marketing_knowledge": marketing_knowledge,
            "publishing_queue": [], # Could be retrieved from a database of scheduled drafts in the future
            "blueprint": draft_data.get("blueprint", {})
        }

        # Run parallel evaluations
        bus_worker = BusinessAlignmentWorker(llm)
        camp_worker = CampaignConflictWorker(llm)
        pub_worker = PublishingStrategyWorker(llm)
        risk_worker = RiskAssessmentWorker(llm)

        bus_task = bus_worker.process(context)
        camp_task = camp_worker.process(context)
        pub_task = pub_worker.process(context)
        risk_task = risk_worker.process(context)

        bus_eval, camp_eval, pub_eval, risk_eval = await asyncio.gather(bus_task, camp_task, pub_task, risk_task)

        # Update context for the Decision Engine
        context.update({
            "business_eval": bus_eval,
            "campaign_eval": camp_eval,
            "publishing_eval": pub_eval,
            "risk_eval": risk_eval
        })

        # Final Decision
        await ws_manager.emit_event(session_id, "executive_decision_started", {"topic": title})
        decision_engine = ExecutiveDecisionEngineWorker(llm)
        final_decision = await decision_engine.process(context)

        # Aggregate traces
        traces = []
        for res in [bus_eval, camp_eval, pub_eval, risk_eval, final_decision]:
            if "_trace" in res:
                traces.append(res["_trace"])

        final_decision["title"] = title
        final_decision["_traces"] = traces

        return final_decision

    async def run(
        self,
        session_id: str,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        
        logger.info("CMO Agent started", session_id=session_id)
        ws_manager = get_connection_manager()

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="cmo_approval_started",
            payload={"message": "AI CMO evaluating final drafts against business objectives"}
        )

        config = get_agent_config("cmo")
        llm = get_llm_provider(config.model)
        
        # Load Marketing Knowledge layer (source of truth)
        knowledge_obj = await marketing_provider.get_knowledge()
        marketing_knowledge = knowledge_obj.model_dump()
        
        meta = config.metadata or {}
        max_concurrent = meta.get("max_concurrent_pipelines", 2)
        semaphore = asyncio.Semaphore(max_concurrent)

        drafts_to_review = input_data.get("reviewed_drafts", input_data.get("drafts", []))

        async def bounded_process(draft_data: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                try:
                    return await self._process_single_decision(draft_data, session_id, ws_manager, llm, marketing_knowledge)
                except Exception as e:
                    logger.error(f"CMO Evaluation failed for '{draft_data.get('title')}'", error=str(e))
                    return {"title": draft_data.get("title"), "decision": "REJECT", "reasoning": str(e)}

        tasks = [bounded_process(d) for d in drafts_to_review]
        executive_decisions = await asyncio.gather(*tasks)

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="cmo_approval_completed",
            payload={"message": f"CMO made final executive decisions on {len(executive_decisions)} drafts."}
        )

        # Aggregate traces
        all_traces = []
        for d in executive_decisions:
            all_traces.extend(d.pop("_traces", []))

        # Check if any drafts were approved
        approved = any(d.get("decision", "") == "APPROVED" for d in executive_decisions)

        return {
            "executive_decisions": executive_decisions,
            "approved": approved,
            "_metadata": {"traces": all_traces}
        }

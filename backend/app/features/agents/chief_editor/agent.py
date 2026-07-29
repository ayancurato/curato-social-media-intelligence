"""
Curato AI — Chief Editor Agent (Agent 5)
"""

import asyncio
from typing import Any

from app.core.exceptions import AgentValidationError
from app.core.logging import get_logger
from app.features.agents.base import BaseAgent
from app.features.agents.config import get_agent_config
from app.features.agents.chief_editor.workers import (
    EditorialReviewerWorker,
    BrandReviewerWorker,
    FactLogicReviewerWorker,
    EngagementOptimizerWorker,
    DecisionEngineWorker,
)
from app.features.websocket.manager import get_connection_manager
from app.services.llm.factory import get_llm_provider

logger = get_logger(__name__)


class ChiefEditorAgent(BaseAgent):
    """
    Curato AI Chief Editor.
    Reviews drafts, scores them, and makes a final editorial decision.
    """

    @property
    def name(self) -> str:
        return "chief_editor"

    async def validate_input(self, data: dict[str, Any]) -> bool:
        if "drafts" not in data:
            raise AgentValidationError("Missing drafts in input", agent_name=self.name() if callable(self.name) else self.name)
        return True

    async def validate_output(self, data: dict[str, Any]) -> bool:
        if "reviewed_drafts" not in data:
            raise AgentValidationError("Missing reviewed_drafts in output", agent_name=self.name() if callable(self.name) else self.name)
        return True

    async def _process_single_draft(self, draft_data: dict[str, Any], session_id: str, ws_manager: Any, llm: Any) -> dict[str, Any]:
        """Executes the 5-step review pipeline for a single draft."""
        title = draft_data.get("title", "Unknown Draft")
        
        # 1. Editorial Review
        await ws_manager.emit_event(session_id, "editorial_review_started", {"topic": title})
        ed_reviewer = EditorialReviewerWorker(llm)
        ed_res = await ed_reviewer.review(draft_data)

        # 2. Brand Consistency Review
        await ws_manager.emit_event(session_id, "brand_review_started", {"topic": title})
        brand_reviewer = BrandReviewerWorker(llm)
        brand_res = await brand_reviewer.review(draft_data)

        # 3. Fact & Logic Review
        await ws_manager.emit_event(session_id, "fact_review_started", {"topic": title})
        fact_reviewer = FactLogicReviewerWorker(llm)
        fact_res = await fact_reviewer.review(draft_data)
        
        compiled_reviews = {
            "editorial": ed_res,
            "brand": brand_res,
            "fact": fact_res
        }

        # 4. Decision Engine
        await ws_manager.emit_event(session_id, "editorial_decision_started", {"topic": title})
        decision_engine = DecisionEngineWorker(llm)
        decision_res = await decision_engine.review(draft_data, context={"reviews": compiled_reviews})
        
        decision = decision_res.get("editorial_decision", "Reject")
        
        # 5. Engagement Optimizer (Only if Minor Revision or Approve to slightly polish)
        final_content = draft_data.get("optimized_draft", draft_data.get("draft", ""))
        engagement_score = 0
        if decision in ["Approve", "Minor Revision"]:
            await ws_manager.emit_event(session_id, "engagement_optimization_started", {"topic": title})
            eng_opt = EngagementOptimizerWorker(llm)
            # Pass the editorial issues so the optimizer can fix minor ones inline
            eng_res = await eng_opt.review(draft_data, context={"editorial_issues": ed_res.get("issues", [])})
            final_content = eng_res.get("edited_content", final_content)
            engagement_score = eng_res.get("engagement_score", 90)
            
            if decision == "Minor Revision":
                decision = "Approve" # We fixed it inline, so it's good to go

        # Aggregate scores
        scores = {
            "grammar": ed_res.get("scores", {}).get("grammar", 0),
            "readability": ed_res.get("scores", {}).get("readability", 0),
            "flow": ed_res.get("scores", {}).get("flow", 0),
            "authority": brand_res.get("scores", {}).get("authority", 0),
            "professionalism": brand_res.get("scores", {}).get("professionalism", 0),
            "brand_voice": brand_res.get("scores", {}).get("brand_voice", 0),
            "originality": ed_res.get("scores", {}).get("originality", 0),
            "engagement": engagement_score,
            "seo": draft_data.get("scores", {}).get("seo_score", 0), # carried over from writer
            "geo": draft_data.get("scores", {}).get("geo_score", 0),
            "aeo": draft_data.get("scores", {}).get("aeo_score", 0),
        }
        
        overall = sum(scores.values()) / max(1, len(scores))
        scores["overall"] = round(overall)
        
        # Phase 6.5: Aggregate worker traces
        traces = []
        for res in [ed_res, brand_res, fact_res, decision_res]:
            if "_trace" in res:
                traces.append(res["_trace"])
        try:
            if 'eng_res' in locals() and "_trace" in eng_res:
                traces.append(eng_res["_trace"])
        except NameError:
            pass

        return {
            "title": title,
            "editorial_decision": decision,
            "edited_content": final_content,
            "revision_plan": decision_res.get("revision_plan", {}),
            "scores": scores,
            "editorial_feedback": ed_res.get("issues", []) + ed_res.get("suggestions", []),
            "brand_violations": brand_res.get("violations", []),
            "logic_issues": fact_res.get("issues", []),
            "_traces": traces,
            "confidence": decision_res.get("confidence", 0),
            "reasoning": decision_res.get("reasoning", "")
        }

    async def run(
        self,
        session_id: str,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        
        logger.info("Chief Editor Agent started", session_id=session_id)
        ws_manager = get_connection_manager()

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="editorial_review_started",
            payload={"message": "Chief Editor reviewing drafts"}
        )

        config = get_agent_config("chief_editor")
        llm = get_llm_provider(config.model)
        
        meta = config.metadata or {}
        max_concurrent = meta.get("max_concurrent_pipelines", 2)
        semaphore = asyncio.Semaphore(max_concurrent)

        drafts = input_data.get("drafts", [])
        
        async def bounded_process(draft: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                try:
                    return await self._process_single_draft(draft, session_id, ws_manager, llm)
                except Exception as e:
                    logger.error(f"Editorial pipeline failed for '{draft.get('title')}'", error=str(e))
                    return {"title": draft.get("title"), "editorial_decision": "Reject", "reasoning": str(e)}

        tasks = [bounded_process(d) for d in drafts]
        reviewed_drafts = await asyncio.gather(*tasks)

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="editorial_review_completed",
            payload={"message": f"Successfully reviewed {len(reviewed_drafts)} drafts."}
        )
        
        all_traces = []
        for d in reviewed_drafts:
            all_traces.extend(d.pop("_traces", []))

        return {
            "reviewed_drafts": reviewed_drafts,
            "_metadata": {"traces": all_traces}
        }

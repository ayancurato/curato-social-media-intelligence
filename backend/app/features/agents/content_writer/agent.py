"""
Curato AI — Content Writer Agent (Agent 4)
"""

import asyncio
from typing import Any

from app.core.exceptions import AgentValidationError
from app.core.logging import get_logger
from app.features.agents.base import BaseAgent
from app.features.agents.config import get_agent_config
from app.features.agents.content_writer.workers import (
    StructurePlannerWorker,
    DraftWriterWorker,
    VariationGeneratorWorker,
    DraftSelectorWorker,
    PlatformOptimizerWorker,
    DiscoverabilityOptimizerWorker,
    QualityValidatorWorker,
)
from app.features.agents.content_writer.utils.fingerprint import generate_fingerprint
from app.features.websocket.manager import get_connection_manager
from app.services.llm.factory import get_llm_provider

logger = get_logger(__name__)


class ContentWriterAgent(BaseAgent):
    """
    Curato AI Content Writer.
    Transforms Content Blueprints into platform-ready drafts via a modular pipeline.
    """

    @property
    def name(self) -> str:
        return "content_writer"

    async def validate_input(self, data: dict[str, Any]) -> bool:
        if "blueprints" not in data:
            raise AgentValidationError("Missing blueprints in input")
        return True

    async def validate_output(self, data: dict[str, Any]) -> bool:
        if "drafts" not in data:
            raise AgentValidationError("Missing drafts in output")
        return True

    async def _process_single_blueprint(self, blueprint: dict[str, Any], session_id: str, ws_manager: Any, llm: Any) -> dict[str, Any]:
        """Executes the 5-step writer pipeline for a single blueprint."""
        title = blueprint.get("topic", "Unknown Topic")
        
        # 1. Structure Planner
        await ws_manager.emit_event(session_id, "structure_planning_started", {"topic": title})
        planner = StructurePlannerWorker(llm)
        outline_res = await planner.process(blueprint)
        outline = outline_res.get("outline", [])

        # 2. Draft Writer
        await ws_manager.emit_event(session_id, "drafting_started", {"topic": title})
        writer = DraftWriterWorker(llm)
        draft_res = await writer.process(blueprint, context={"outline": outline})
        initial_draft = draft_res.get("draft", "")

        # 3. Variation Generator & Selector
        await ws_manager.emit_event(session_id, "variation_generation_started", {"topic": title})
        var_gen = VariationGeneratorWorker(llm)
        var_res = await var_gen.process(blueprint, context={"draft": initial_draft})
        variations = var_res.get("variations", [])
        
        # Select best variation
        selector = DraftSelectorWorker(llm)
        sel_res = await selector.process(blueprint, context={"variations": variations})
        selected_id = sel_res.get("selected_variation_id")
        
        best_draft = initial_draft
        for v in variations:
            if v.get("id") == selected_id:
                best_draft = v.get("draft", best_draft)
                break

        # 4. Platform Optimizer (Deterministic)
        await ws_manager.emit_event(session_id, "platform_optimization_started", {"topic": title})
        plat_opt = PlatformOptimizerWorker()
        platform = blueprint.get("platform", "linkedin")
        plat_draft = plat_opt.process(best_draft, platform)

        # 5. Discoverability Optimizer (SEO/GEO)
        await ws_manager.emit_event(session_id, "discoverability_optimization_started", {"topic": title})
        seo_opt = DiscoverabilityOptimizerWorker(llm)
        seo_res = await seo_opt.process(blueprint, context={"draft": plat_draft})
        final_draft = seo_res.get("optimized_draft", plat_draft)
        keywords = seo_res.get("keywords_used", [])
        entities = seo_res.get("entities", [])

        # 6. Quality Validator
        await ws_manager.emit_event(session_id, "quality_validation_started", {"topic": title})
        validator = QualityValidatorWorker(llm)
        val_res = await validator.process(blueprint, context={"draft": final_draft})
        scores = val_res.get("scores", {})
        validation = val_res.get("validation", {"approved": False, "issues": ["Validation failed."]})

        # 7. Fingerprint Generation
        fingerprint_meta = {
            "hook_type": blueprint.get("recommended_hook"),
            "cta_type": blueprint.get("cta"),
            "platform": platform,
            "tone": blueprint.get("tone"),
            "entities": entities
        }
        fingerprint = generate_fingerprint(final_draft, fingerprint_meta)
        
        # Phase 6.5: Aggregate worker traces
        traces = []
        for res in [outline_res, draft_res, var_res, sel_res, seo_res, val_res]:
            if "_trace" in res:
                traces.append(res["_trace"])

        return {
            "title": title,
            "platform": platform,
            "content_format": blueprint.get("content_format", ""),
            "outline": outline,
            "draft": best_draft,
            "optimized_draft": final_draft,
            "keywords_used": keywords,
            "entities": entities,
            "cta": blueprint.get("cta", ""),
            "scores": scores,
            "validation": validation,
            "fingerprint": fingerprint,
            "_traces": traces
        }

    async def _process_single_revision(self, blueprint: dict[str, Any], session_id: str, ws_manager: Any, llm: Any, context: dict[str, Any]) -> dict[str, Any]:
        """Executes the revision pipeline for a single blueprint."""
        title = blueprint.get("topic", "Unknown Topic")
        
        await ws_manager.emit_event(session_id, "revision_writing_started", {"topic": title})
        
        # We need the original draft
        original_draft = context.get("original_draft", "")
        revision_plan = context.get("revision_plan", {})
        editorial_memory = context.get("editorial_memory", [])
        
        # 1. Revision Writer
        from app.features.agents.content_writer.workers.revision_writer import RevisionWriterWorker
        rev_writer = RevisionWriterWorker(llm)
        rev_res = await rev_writer.process(
            blueprint, 
            context={
                "original_draft": original_draft,
                "revision_plan": revision_plan,
                "editorial_memory": editorial_memory
            }
        )
        best_draft = rev_res.get("draft", original_draft)

        # 2. Platform Optimizer
        plat_opt = PlatformOptimizerWorker()
        platform = blueprint.get("platform", "linkedin")
        plat_draft = plat_opt.process(best_draft, platform)

        # 3. Discoverability Optimizer (SEO/GEO)
        seo_opt = DiscoverabilityOptimizerWorker(llm)
        seo_res = await seo_opt.process(blueprint, context={"draft": plat_draft})
        final_draft = seo_res.get("optimized_draft", plat_draft)
        keywords = seo_res.get("keywords_used", [])
        entities = seo_res.get("entities", [])

        # 4. Quality Validator
        validator = QualityValidatorWorker(llm)
        val_res = await validator.process(blueprint, context={"draft": final_draft})
        scores = val_res.get("scores", {})
        validation = val_res.get("validation", {"approved": False, "issues": ["Validation failed."]})

        # 5. Fingerprint Generation
        fingerprint_meta = {
            "hook_type": blueprint.get("recommended_hook"),
            "cta_type": blueprint.get("cta"),
            "platform": platform,
            "tone": blueprint.get("tone"),
            "entities": entities
        }
        fingerprint = generate_fingerprint(final_draft, fingerprint_meta)
        
        traces = []
        for res in [rev_res, seo_res, val_res]:
            if "_trace" in res:
                traces.append(res["_trace"])

        return {
            "title": title,
            "platform": platform,
            "content_format": blueprint.get("content_format", ""),
            "outline": [], # Keeping empty or pull from original if needed
            "draft": best_draft,
            "optimized_draft": final_draft,
            "keywords_used": keywords,
            "entities": entities,
            "cta": blueprint.get("cta", ""),
            "scores": scores,
            "validation": validation,
            "fingerprint": fingerprint,
            "_traces": traces
        }

    async def run(
        self,
        session_id: str,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        
        logger.info("Content Writer Agent started", session_id=session_id)
        ws_manager = get_connection_manager()
        
        revision_mode = input_data.get("revision_mode", False)
        event_type = "content_writing_started" if not revision_mode else "content_revision_started"

        await ws_manager.emit_event(
            session_id=session_id,
            event_type=event_type,
            payload={"message": "Initializing writing pipeline"}
        )

        config = get_agent_config("content_writer")
        llm = get_llm_provider(config.model)
        
        meta = config.metadata or {}
        max_concurrent = meta.get("max_concurrent_pipelines", 2)
        semaphore = asyncio.Semaphore(max_concurrent)

        # In revision mode, the input might be different, but we still need blueprints
        blueprints = input_data.get("blueprints", [])
        revision_plans = input_data.get("revision_plans", {})
        
        # We need editorial memory from the DB
        editorial_memory = []
        if revision_mode:
            try:
                from sqlalchemy import select
                from app.core.database import get_db
                from app.models.feedback import Feedback
                
                # Note: It would be better to fetch this from the Orchestrator and pass it in input_data,
                # but we'll fetch it here to satisfy the "agent can fetch past feedback" requirement directly.
                async for db in get_db():
                    result = await db.execute(
                        select(Feedback.feedback_text)
                        .where(Feedback.agent_name == "chief_editor")
                        .order_by(Feedback.created_at.desc())
                        .limit(5) # Get last 5 feedbacks
                    )
                    editorial_memory = [r for r in result.scalars().all() if r]
            except Exception as e:
                logger.error("Failed to fetch editorial memory", error=str(e))
        
        async def bounded_process(bp: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                try:
                    title = bp.get("topic")
                    if revision_mode and title in revision_plans:
                        # Find the original draft from reviewed_drafts or drafts
                        original_draft = ""
                        for d in input_data.get("reviewed_drafts", []) + input_data.get("drafts", []):
                            if d.get("title") == title:
                                original_draft = d.get("edited_content", d.get("optimized_draft", d.get("draft", "")))
                                break
                                
                        context = {
                            "original_draft": original_draft,
                            "revision_plan": revision_plans[title],
                            "editorial_memory": editorial_memory
                        }
                        return await self._process_single_revision(bp, session_id, ws_manager, llm, context)
                    else:
                        return await self._process_single_blueprint(bp, session_id, ws_manager, llm)
                except Exception as e:
                    logger.error(f"Pipeline failed for blueprint '{bp.get('topic')}'", error=str(e))
                    return {"title": bp.get("topic"), "validation": {"approved": False, "issues": [str(e)]}}

        # Execute all pipelines
        tasks = [bounded_process(bp) for bp in blueprints]
        drafts = await asyncio.gather(*tasks)

        await ws_manager.emit_event(
            session_id=session_id,
            event_type="content_writing_completed",
            payload={"message": f"Successfully drafted {len(drafts)} pieces of content."}
        )
        
        all_traces = []
        for d in drafts:
            all_traces.extend(d.pop("_traces", []))

        return {
            "drafts": drafts,
            "_metadata": {"traces": all_traces}
        }

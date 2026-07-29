"""
Curato AI — Workflow Orchestrator

The central brain of the system. Manages the complete agent pipeline,
handles the CMO approval loop, persists state, and emits real-time events.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import WorkflowError
from app.core.logging import get_logger
from app.features.agents.registry import AgentRegistry
from app.features.workflow.state import WorkflowStatus
from app.models.agent_run import AgentRun
from app.models.content_draft import ContentDraft
from app.models.feedback import Feedback
from app.models.generation_session import GenerationSession
from app.models.research_result import ResearchResult
from app.models.topic_score import TopicScore
from app.models.content_draft import ContentDraft
from app.models.feedback import Feedback
from app.models.workflow_log import WorkflowLog

logger = get_logger(__name__)

# Maximum number of revision loops before force-failing
MAX_REVISION_ITERATIONS = 5


class WorkflowOrchestrator:
    """
    Central orchestrator for the content generation pipeline.

    Executes agents in sequence, manages the CMO approval loop,
    persists all intermediate state, and broadcasts real-time events.

    Pipeline:
        Research → Topic Prioritization → Content Strategist →
        Content Writer → Chief Editor → CMO

    If CMO rejects:
        → Content Writer (with feedback) → Chief Editor → CMO
        (repeats until approved or max iterations reached)
    """

    # Ordered agent pipeline
    AGENT_PIPELINE = [
        "research",
        "topic_prioritization",
        "content_strategist",
        "content_writer",
        "chief_editor",
        "cmo",
    ]

    # Agents in the revision loop (when CMO rejects)
    REVISION_AGENTS = ["content_writer", "chief_editor", "cmo"]

    def __init__(
        self,
        db: AsyncSession,
        agent_registry: AgentRegistry,
        notification_callback: Any | None = None,
    ) -> None:
        self._db = db
        self._agents = agent_registry
        self._notify = notification_callback

    # ── Main Execution ───────────────────────────────────────────────────

    async def execute(self, session_id: UUID, initiator: str = "unknown") -> dict[str, Any]:
        """
        Execute the full content generation workflow.

        Args:
            session_id: The session to execute.
            initiator: Who triggered this execution (for structured logging).
                       Should be one of: 'http_thread', 'poller', 'retry_handler', 'unknown'.
        """
        session = await self._get_session(session_id)

        # ── IDEMPOTENCY GUARD ────────────────────────────────────────────────
        # This is the last-resort safety net against duplicate dispatch.
        # If Path 1 (Thread) and Path 2 (Poller) both reach here concurrently,
        # whichever one sees status != 'pending' will exit immediately.
        if session.status in ("running", "completed", "failed", "cancelled"):
            logger.warning(
                "Duplicate orchestrator dispatch detected and blocked",
                session_id=str(session_id),
                current_status=session.status,
                initiator=initiator,
                action="ignored",
            )
            print(
                f"[ORCHESTRATOR] DUPLICATE BLOCKED — session {session_id} "
                f"already in '{session.status}' state (initiator={initiator})",
                flush=True,
            )
            return {"success": False, "reason": "duplicate_dispatch", "status": session.status}

        logger.info(
            "Orchestrator starting workflow",
            session_id=str(session_id),
            initiator=initiator,
        )
        print(f"[ORCHESTRATOR] Starting session {session_id} (initiator={initiator})", flush=True)

        try:
            # Mark workflow as running IMMEDIATELY to block any concurrent dispatch
            await self._update_session(session, WorkflowStatus.RUNNING)
            if not session.started_at:
                session.started_at = datetime.now(timezone.utc)
            await self._db.commit()  # Commit status=running NOW so poller sees it

            await self._emit_event(session_id, "workflow_started", {})

            # Phase 7.5: Reconstruct context from previous runs if checkpointing
            pipeline_context: dict[str, Any] = {}
            completed_agents = [r.agent_name for r in session.agent_runs if r.status == "success"]

            for agent_name in self.AGENT_PIPELINE:
                # Phase 7.5: Cancellation Check
                await self._db.refresh(session)
                if session.cancelled:
                    await self._log(session_id, "warning", "Workflow cancelled by user")
                    await self._update_session(session, "cancelled")
                    return pipeline_context

                # Phase 7.5: Checkpointing
                if agent_name in completed_agents:
                    await self._log(session_id, "info", f"Skipping {agent_name}, already completed (Checkpoint).")
                    
                    # We must pull outputs from the completed run to feed the next agent
                    for run in session.agent_runs:
                        if run.agent_name == agent_name and run.status == "success" and run.output_data:
                            pipeline_context.update(run.output_data)
                    continue

                pipeline_context = await self._execute_agent(
                    session=session,
                    agent_name=agent_name,
                    input_data=pipeline_context,
                )

                # Persist research results
                if agent_name == "research":
                    await self._store_research_result(session, pipeline_context)
                    
                # Persist topic prioritization results
                if agent_name == "topic_prioritization":
                    await self._store_topic_scores(session, pipeline_context)
                    
                # Persist content strategy blueprints loosely
                if agent_name == "content_strategist":
                    await self._store_content_blueprints(session, pipeline_context)

                # Persist content drafts
                if agent_name == "content_writer":
                    await self._store_content_drafts(session, pipeline_context)

                # After Chief Editor: check for Major Revisions or Rejections
                if agent_name == "chief_editor":
                    await self._store_editor_reviews(session, pipeline_context)
                    
                    # Check if any draft needs Major Revision
                    needs_revision = any(
                        d.get("editorial_decision") == "Major Revision" 
                        for d in pipeline_context.get("reviewed_drafts", [])
                    )
                    
                    if needs_revision:
                        pipeline_context = await self._editor_revision_loop(
                            session=session,
                            context=pipeline_context,
                        )

                # After CMO: check approval
                if agent_name == "cmo":
                    approved = pipeline_context.get("approved", False)

                    if not approved:
                        # Enter revision loop
                        pipeline_context = await self._revision_loop(
                            session=session,
                            context=pipeline_context,
                        )

            # Workflow completed successfully
            session.completed_at = datetime.now(timezone.utc)
            if session.started_at:
                duration = (session.completed_at - session.started_at).total_seconds()
                session.total_duration_ms = int(duration * 1000)

            await self._update_session(session, WorkflowStatus.COMPLETED)
            await self._log(
                session_id, "info", "Workflow completed successfully",
                details={"total_duration_ms": session.total_duration_ms},
            )
            await self._emit_event(session_id, "workflow_completed", {
                "total_duration_ms": session.total_duration_ms,
            })

            # Store final content
            await self._store_final_content(session, pipeline_context)
            
            # Phase 8: Google Workspace Delivery
            try:
                from app.services.delivery.service import DeliveryService
                DeliveryService.execute_delivery(pipeline_context)
            except Exception as e:
                # We don't fail the workflow if external delivery fails
                logger.error("Failed to execute external delivery", error=str(e))

            return {
                "success": True,
                "session_id": str(session_id),
                "status": WorkflowStatus.COMPLETED.value,
                "final_content": pipeline_context.get("final_content", []),
            }

        except Exception as e:
            logger.error("Workflow execution failed", session_id=str(session_id), error=str(e))
            session.error_message = str(e)
            
            # Phase 7.5: DLQ
            session.dead_lettered = True
            session.failure_reason = str(e)
            
            session.completed_at = datetime.now(timezone.utc)
            await self._update_session(session, WorkflowStatus.FAILED)
            await self._log(session_id, "error", f"Workflow dead-lettered: {str(e)}")
            await self._emit_event(session_id, "workflow_failed", {"error": str(e)})
            await self._db.commit()
            raise WorkflowError(
                message=f"Workflow failed: {str(e)}",
                session_id=session_id,
            )

    # ── Agent Execution ──────────────────────────────────────────────────

    async def _execute_agent(
        self,
        session: GenerationSession,
        agent_name: str,
        input_data: dict[str, Any],
        attempt: int = 1,
    ) -> dict[str, Any]:
        """Execute a single agent and persist results."""
        session_id = session.id

        # Update session state
        session.current_agent = agent_name
        await self._update_session(session, WorkflowStatus.AGENT_EXECUTING)

        # Create agent run record
        agent_run = AgentRun(
            session_id=session_id,
            agent_name=agent_name,
            status="running",
            input_data=input_data,
            attempt_number=attempt,
        )
        self._db.add(agent_run)
        await self._db.flush()

        await self._log(
            session_id, "info", f"Agent '{agent_name}' started",
            agent_name=agent_name,
            details={"attempt": attempt},
        )
        await self._emit_event(session_id, "agent_started", {
            "agent_name": agent_name,
            "display_name": self._agents.get(agent_name).display_name,
            "attempt": attempt,
        })

        start_time = time.monotonic()

        try:
            # Get agent and execute with retry
            agent = self._agents.get(agent_name)

            # Inject session context into input
            enriched_input = {
                **input_data,
                "session_context": {
                    "session_id": str(session_id),
                    "agent_name": agent_name,
                    "iteration": session.retry_count + 1,
                },
            }

            output = await agent.retry(enriched_input, session_id)

            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Update agent run record
            agent_run.status = "completed"
            agent_run.output_data = output
            agent_run.duration_ms = duration_ms
            agent_run.token_usage = output.get("_metadata", {})

            await self._db.flush()

            await self._log(
                session_id, "info", f"Agent '{agent_name}' completed",
                agent_name=agent_name,
                details={"duration_ms": duration_ms},
            )
            await self._emit_event(session_id, "agent_completed", {
                "agent_name": agent_name,
                "display_name": agent.display_name,
                "duration_ms": duration_ms,
                "success": True,
            })

            # Return agent output merged with input data to accumulate context
            output.pop("_metadata", None)
            return {**input_data, **output}

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)

            agent_run.status = "failed"
            agent_run.error_message = str(e)
            agent_run.duration_ms = duration_ms
            await self._db.flush()

            await self._log(
                session_id, "error", f"Agent '{agent_name}' failed: {str(e)}",
                agent_name=agent_name,
                details={"duration_ms": duration_ms, "error": str(e)},
            )
            await self._emit_event(session_id, "agent_failed", {
                "agent_name": agent_name,
                "error": str(e),
                "duration_ms": duration_ms,
            })
            raise

    # ── Revision Loop ────────────────────────────────────────────────────

    async def _revision_loop(
        self,
        session: GenerationSession,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle the CMO rejection → Writer → Editor → CMO loop.

        Repeats until approved or max iterations reached.
        """
        iteration = 1
        current_context = context

        while not current_context.get("approved", False):
            if iteration >= MAX_REVISION_ITERATIONS:
                raise WorkflowError(
                    message=f"Maximum revision iterations ({MAX_REVISION_ITERATIONS}) reached",
                    session_id=session.id,
                )

            iteration += 1
            session.retry_count = iteration - 1

            await self._update_session(session, WorkflowStatus.REVISION_LOOP)
            await self._log(
                session.id, "info",
                f"Revision loop iteration {iteration}",
                details={"feedback": current_context.get("feedback", "")},
            )
            await self._emit_event(session.id, "revision_loop_started", {
                "iteration": iteration,
                "feedback": current_context.get("feedback", ""),
            })

            # Prepare revision input for the writer
            revision_input = {
                **current_context,
                "revision_feedback": {
                    "feedback": current_context.get("feedback", ""),
                    "revision_notes": current_context.get("revision_notes", {}),
                    "iteration": iteration,
                },
            }

            # Re-execute: Writer → Editor → CMO
            for agent_name in self.REVISION_AGENTS:
                current_context = await self._execute_agent(
                    session=session,
                    agent_name=agent_name,
                    input_data=revision_input if agent_name == "content_writer" else current_context,
                    attempt=iteration,
                )

        return current_context

    # ── State Persistence ────────────────────────────────────────────────

    async def _get_session(self, session_id: UUID) -> GenerationSession:
        """Fetch a generation session by ID."""
        session = await self._db.get(GenerationSession, session_id)
        if session is None:
            raise WorkflowError(
                message=f"Generation session '{session_id}' not found",
                session_id=session_id,
            )
        return session

    async def _update_session(
        self,
        session: GenerationSession,
        status: WorkflowStatus,
    ) -> None:
        """Update session status and commit immediately so polling can see the change."""
        session.status = status.value
        await self._db.commit()

    async def _log(
        self,
        session_id: UUID,
        level: str,
        message: str,
        agent_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Write a workflow log entry to the database."""
        log_entry = WorkflowLog(
            session_id=session_id,
            level=level,
            agent_name=agent_name,
            message=message,
            details=details,
        )
        self._db.add(log_entry)
        # Commit immediately so log entries are visible to polling connections
        await self._db.commit()

        # Also log to structured logger
        logger.info(
            message,
            session_id=str(session_id),
            level=level,
            agent=agent_name,
        )

    async def _store_final_content(
        self,
        session: GenerationSession,
        context: dict[str, Any],
    ) -> None:
        """Store the final approved content as ContentDraft records."""
        final_content = context.get("final_content", [])
        for i, draft_data in enumerate(final_content):
            draft = ContentDraft(
                session_id=session.id,
                version=session.retry_count + 1,
                platform=draft_data.get("platform", "linkedin"),
                title=draft_data.get("title", ""),
                body=draft_data.get("body", ""),
                hashtags=draft_data.get("hashtags"),
                media_suggestions=draft_data.get("media_suggestions"),
                content_metadata=draft_data,
                agent_name="content_writer",
            )
            self._db.add(draft)

        # Store CMO approval feedback
        feedback = Feedback(
            session_id=session.id,
            agent_name="cmo",
            approved=True,
            feedback_text=context.get("feedback", ""),
            iteration_number=session.retry_count + 1,
        )
        self._db.add(feedback)

        await self._db.flush()

    async def _store_research_result(
        self,
        session: GenerationSession,
        context: dict[str, Any],
    ) -> None:
        """Store the structured research data."""
        # Save output of the research agent
        research = ResearchResult(
            session_id=session.id,
            raw_data=context,
            sources=context.get("sources", {}), # Or derived from context
            summary=context.get("reasoning", ""),
            metadata_=context.get("_metadata"),
        )
        self._db.add(research)
        await self._db.flush()

    async def _store_topic_scores(
        self,
        session: GenerationSession,
        context: dict[str, Any],
    ) -> None:
        """Store prioritized topics from Agent 2."""
        top_topics = context.get("top_30_topics", [])
        
        for idx, topic in enumerate(top_topics):
            # Extract raw scores
            priority = topic.get("priority_score", 0.0)
            relevance = topic.get("business_alignment", 0.0)
            trending = topic.get("opportunity_score", 0.0)
            
            # Since topic might contain complex dict objects (like reasoning dicts), we store the whole object in metadata
            ts = TopicScore(
                session_id=session.id,
                topic_title=topic.get("topic", f"Topic {idx+1}"),
                relevance_score=relevance if isinstance(relevance, (int, float)) else relevance.get("raw_score", 0.0),
                trending_score=trending if isinstance(trending, (int, float)) else trending.get("raw_score", 0.0),
                overall_score=priority,
                rank=idx + 1,
                reasoning=topic.get("reasoning", ""),
                metadata_=topic
            )
            self._db.add(ts)
            
        await self._db.flush()

    async def _store_content_blueprints(
        self,
        session: GenerationSession,
        context: dict[str, Any],
    ) -> None:
        """
        Store the content blueprints loosely for Phase 4.
        Finds the corresponding TopicScore row and attaches the blueprint to its metadata.
        """
        from sqlalchemy import select
        
        blueprints = context.get("blueprints", [])
        if not blueprints:
            return
            
        # Fetch existing topic scores for this session to attach the blueprints
        stmt = select(TopicScore).where(TopicScore.session_id == session.id)
        result = await self._db.execute(stmt)
        topic_scores = result.scalars().all()
        
        # Create lookup by topic title
        ts_map = {ts.topic_title: ts for ts in topic_scores}
        
        for bp in blueprints:
            title = bp.get("topic")
            if title in ts_map:
                ts = ts_map[title]
                meta = ts.metadata_ or {}
                # Embed the full blueprint structure
                meta["content_blueprint"] = bp
                ts.metadata_ = meta
                
        await self._db.flush()

    async def _store_content_drafts(
        self,
        session: GenerationSession,
        context: dict[str, Any],
    ) -> None:
        """
        Store the drafted content from Agent 4 into the ContentDraft table.
        Embeds the rich metadata (outline, scores, validation, fingerprint) in content_metadata.
        """
        drafts = context.get("drafts", [])
        if not drafts:
            return
            
        for draft_data in drafts:
            # Prepare rich metadata
            meta = {
                "outline": draft_data.get("outline", []),
                "scores": draft_data.get("scores", {}),
                "validation": draft_data.get("validation", {}),
                "fingerprint": draft_data.get("fingerprint", {}),
                "keywords_used": draft_data.get("keywords_used", []),
                "cta": draft_data.get("cta", ""),
                "content_format": draft_data.get("content_format", ""),
            }
            
            draft = ContentDraft(
                session_id=session.id,
                version=1,
                platform=draft_data.get("platform", "linkedin"),
                title=draft_data.get("title", "Untitled Draft"),
                body=draft_data.get("optimized_draft", draft_data.get("draft", "")),
                hashtags=None,
                media_suggestions=None,
                content_metadata=meta,
                agent_name="content_writer"
            )
            self._db.add(draft)
            
        await self._db.flush()

    async def _store_editor_reviews(
        self,
        session: GenerationSession,
        context: dict[str, Any],
    ) -> None:
        """
        Store the editorial feedback and update the ContentDraft rows with version bumps if approved/minor.
        """
        from sqlalchemy import select
        
        reviewed_drafts = context.get("reviewed_drafts", [])
        if not reviewed_drafts:
            return

        # Fetch existing drafts for this session
        result = await self._db.execute(
            select(ContentDraft).where(ContentDraft.session_id == session.id)
        )
        existing_drafts = {d.title: d for d in result.scalars().all()}
            
        for draft_data in reviewed_drafts:
            title = draft_data.get("title")
            decision = draft_data.get("editorial_decision", "")
            
            db_draft = existing_drafts.get(title)
            
            # Save feedback for Editorial Memory
            feedback_text = " | ".join(draft_data.get("editorial_feedback", []) + draft_data.get("brand_violations", []) + draft_data.get("logic_issues", []))
            
            fb = Feedback(
                session_id=session.id,
                draft_id=db_draft.id if db_draft else None,
                agent_name="chief_editor",
                approved=(decision in ["Approve", "Minor Revision"]),
                feedback_text=feedback_text,
                revision_notes=draft_data.get("revision_plan", {}),
                iteration_number=session.retry_count + 1
            )
            self._db.add(fb)
            
            # If approved or minor revision, bump the version and update the text/metadata
            if db_draft and decision in ["Approve", "Minor Revision"]:
                db_draft.version += 1
                db_draft.body = draft_data.get("edited_content", db_draft.body)
                
                # Merge scores
                meta = dict(db_draft.content_metadata or {})
                meta["editor_scores"] = draft_data.get("scores", {})
                db_draft.content_metadata = meta
                
        await self._db.flush()

    async def _editor_revision_loop(
        self,
        session: GenerationSession,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handles the Chief Editor -> Content Writer revision loop.
        """
        iteration = 1
        current_context = context
        
        from app.features.agents.config import get_agent_config
        config = get_agent_config("chief_editor")
        max_cycles = (config.metadata or {}).get("max_revision_cycles", 2)

        while any(d.get("editorial_decision") == "Major Revision" for d in current_context.get("reviewed_drafts", [])):
            if iteration > max_cycles:
                await self._log(session.id, "warning", f"Max revision cycles ({max_cycles}) reached for Chief Editor.")
                break

            iteration += 1
            session.retry_count = iteration - 1

            await self._update_session(session, WorkflowStatus.REVISION_LOOP)
            await self._emit_event(session.id, "revision_loop_started", {
                "iteration": iteration,
                "message": "Chief Editor requested Major Revision. Routing back to Content Writer.",
            })

            # Re-execute Writer in Revision Mode
            # Provide revision_plans to the context
            revision_plans = {
                d["title"]: d.get("revision_plan", {})
                for d in current_context.get("reviewed_drafts", [])
                if d.get("editorial_decision") == "Major Revision"
            }
            
            # 1. Content Writer
            writer_input = {
                **current_context,
                "revision_mode": True,
                "revision_plans": revision_plans,
                "editorial_memory": True # Agent 4 can now fetch past feedback
            }
            current_context = await self._execute_agent(
                session=session,
                agent_name="content_writer",
                input_data=writer_input,
            )
            await self._store_content_drafts(session, current_context)
            
            # 2. Chief Editor
            current_context = await self._execute_agent(
                session=session,
                agent_name="chief_editor",
                input_data=current_context,
            )
            await self._store_editor_reviews(session, current_context)

        return current_context

    # ── Event Emission ───────────────────────────────────────────────────

    async def _emit_event(
        self,
        session_id: UUID,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """Emit a real-time event via the notification callback."""
        if self._notify:
            try:
                await self._notify(
                    session_id=session_id,
                    event_type=event_type,
                    data=data,
                )
            except Exception as e:
                logger.warning(
                    "Failed to emit event",
                    event_type=event_type,
                    error=str(e),
                )

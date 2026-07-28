"""
Curato AI — Hierarchical Workflow Tracer
Generates visual traces of a completed generation session for observability.
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent_run import AgentRun
from app.models.generation_session import GenerationSession


class WorkflowTracer:
    """
    Constructs a hierarchical text report of workflow execution.
    """

    @classmethod
    async def generate_trace_report(cls, session_id: str, db: AsyncSession) -> str:
        """
        Retrieves all AgentRuns for a session and formats a hierarchical trace.
        """
        session_obj = await db.get(GenerationSession, session_id)
        if not session_obj:
            return f"Error: Session {session_id} not found."

        result = await db.execute(
            select(AgentRun)
            .where(AgentRun.session_id == session_id)
            .order_by(AgentRun.created_at.asc())
        )
        runs = result.scalars().all()

        lines = [
            f"Workflow Trace",
            f"├── Workflow ID: {session_id}",
            f"├── Status: {session_obj.status}",
            f"├── Total Runtime: {session_obj.total_duration_ms} ms",
            f"└── Execution Flow:"
        ]

        from app.services.evaluations.cost import CostCalculator

        total_workflow_cost = 0.0

        for i, run in enumerate(runs):
            prefix = "    ├──" if i < len(runs) - 1 else "    └──"
            lines.append(f"{prefix} {run.agent_name.replace('_', ' ').title()} (Attempt {run.attempt_number})")
            
            # Sub-traces for workers inside the agent
            traces = run.token_usage.get("traces", []) if run.token_usage else []
            
            agent_cost = CostCalculator.aggregate_trace_costs(traces)
            total_workflow_cost += agent_cost
            
            for j, trace in enumerate(traces):
                sub_prefix = "    │     ├──" if i < len(runs) - 1 else "          ├──"
                if j == len(traces) - 1:
                    sub_prefix = "    │     └──" if i < len(runs) - 1 else "          └──"
                
                worker = trace.get("worker_name", "Unknown Worker")
                ms = trace.get("latency_ms", "N/A")
                model = trace.get("model", "unknown")
                lines.append(f"{sub_prefix} {worker} [{model}]")

            # Agent Summary
            agent_summary_prefix = "    │     •" if i < len(runs) - 1 else "          •"
            lines.append(f"{agent_summary_prefix} Latency: {run.duration_ms}ms | Cost: ${agent_cost:.4f}")

        lines.insert(4, f"├── Total Cost: ${total_workflow_cost:.4f}")

        return "\n".join(lines)

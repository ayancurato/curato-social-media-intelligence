"""
Curato AI — Cost Efficiency Metrics
Calculates advanced efficiency metrics across workflows.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.agent_run import AgentRun
from app.models.generation_session import GenerationSession
from app.models.human_evaluation import HumanEvaluation
from app.services.evaluations.cost import CostCalculator


class MetricsAggregator:
    
    @classmethod
    async def compute_global_efficiency(cls, db: AsyncSession) -> dict:
        """
        Computes overall cost efficiency metrics.
        """
        # Fetch all runs
        result = await db.execute(select(AgentRun))
        runs = result.scalars().all()
        
        total_cost = 0.0
        total_tokens = 0
        
        for run in runs:
            traces = run.token_usage.get("traces", []) if run.token_usage else []
            total_cost += CostCalculator.aggregate_trace_costs(traces)
            for t in traces:
                toks = t.get("tokens", {})
                total_tokens += toks.get("prompt_tokens", 0) + toks.get("completion_tokens", 0)

        # Workflows
        session_count = await db.scalar(select(func.count(GenerationSession.id)))
        
        # Human Evals
        evals_result = await db.execute(select(HumanEvaluation))
        evals = evals_result.scalars().all()
        total_quality_points = sum(e.overall_rating for e in evals)
        approved_count = sum(1 for e in evals if e.publishable)

        return {
            "Cost per Workflow": total_cost / max(1, session_count),
            "Cost per Approved Draft": total_cost / max(1, approved_count),
            "Cost per Quality Point": total_cost / max(1, total_quality_points),
            "Tokens per Quality Point": total_tokens / max(1, total_quality_points),
            "Average Tokens per Workflow": total_tokens / max(1, session_count),
            "Average Tokens per Approved Draft": total_tokens / max(1, approved_count),
        }

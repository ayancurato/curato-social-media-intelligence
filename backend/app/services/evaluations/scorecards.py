"""
Curato AI — Agent Performance Scorecards
Aggregates performance metrics per agent.
"""

from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent_run import AgentRun
from app.services.evaluations.cost import CostCalculator


class ScorecardGenerator:

    @classmethod
    async def generate_agent_scorecards(cls, db: AsyncSession) -> dict:
        """
        Generates scorecards for each agent based on history.
        """
        result = await db.execute(select(AgentRun))
        runs = result.scalars().all()

        stats = defaultdict(lambda: {
            "total_latency": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "executions": 0,
            "failures": 0,
        })

        for run in runs:
            agent = run.agent_name
            s = stats[agent]
            
            s["executions"] += 1
            s["total_latency"] += (run.duration_ms or 0)
            
            if run.status == "failed":
                s["failures"] += 1
                
            traces = run.token_usage.get("traces", []) if run.token_usage else []
            s["total_cost"] += CostCalculator.aggregate_trace_costs(traces)
            
            for t in traces:
                toks = t.get("tokens", {})
                s["total_tokens"] += toks.get("prompt_tokens", 0) + toks.get("completion_tokens", 0)

        scorecards = {}
        for agent, s in stats.items():
            execs = max(1, s["executions"])
            scorecards[agent] = {
                "Average Latency (ms)": s["total_latency"] / execs,
                "Average Cost ($)": s["total_cost"] / execs,
                "Average Token Usage": s["total_tokens"] / execs,
                "Failure Rate (%)": (s["failures"] / execs) * 100,
            }
            
        return scorecards

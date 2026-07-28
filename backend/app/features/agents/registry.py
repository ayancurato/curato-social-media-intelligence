"""
Curato AI — Agent Registry

Dependency injection container for agent instances.
The orchestrator uses this to discover and invoke agents by name.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.features.agents.base import BaseAgent

logger = get_logger(__name__)


class AgentRegistry:
    """
    Central registry for all agent instances.

    Provides agent discovery and access for the orchestrator
    without hard-coding agent references.

    Usage:
        registry = AgentRegistry()
        registry.register(ResearchAgent())
        agent = registry.get("research")
        result = await agent.execute(input_data)
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register an agent instance."""
        self._agents[agent.name] = agent
        logger.info(
            "Agent registered",
            agent=agent.name,
            display_name=agent.display_name,
        )

    def get(self, name: str) -> BaseAgent:
        """Get an agent by name. Raises KeyError if not found."""
        if name not in self._agents:
            raise KeyError(
                f"Agent '{name}' not found in registry. "
                f"Available agents: {list(self._agents.keys())}"
            )
        return self._agents[name]

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def has(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name in self._agents

    @property
    def agents(self) -> dict[str, BaseAgent]:
        """Get all registered agents."""
        return self._agents.copy()


# ── Factory ──────────────────────────────────────────────────────────────────

_registry: AgentRegistry | None = None


def create_agent_registry() -> AgentRegistry:
    """
    Create and populate the AgentRegistry with all agents.

    This is the single place where agents are wired together.
    """
    from app.features.agents.research import ResearchAgent
    from app.features.agents.topic_prioritization import TopicPrioritizationAgent
    from app.features.agents.content_strategist import ContentStrategistAgent
    from app.features.agents.content_writer import ContentWriterAgent
    from app.features.agents.chief_editor import ChiefEditorAgent
    from app.features.agents.cmo import CMOAgent

    registry = AgentRegistry()
    registry.register(ResearchAgent())
    registry.register(TopicPrioritizationAgent())
    registry.register(ContentStrategistAgent())
    registry.register(ContentWriterAgent())
    registry.register(ChiefEditorAgent())
    registry.register(CMOAgent())

    logger.info("Agent registry initialized", agents=registry.list_agents())
    return registry


def get_agent_registry() -> AgentRegistry:
    """Get or create the singleton AgentRegistry."""
    global _registry
    if _registry is None:
        _registry = create_agent_registry()
    return _registry

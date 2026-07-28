"""
Curato AI — Agent Schemas

Pydantic models for agent input/output contracts.
Each agent has its own typed input and output schema.
"""

from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Generic Agent IO (used by BaseAgent)
# =============================================================================


class AgentInput(BaseModel):
    """Base input schema for any agent. Agents extend this with their own fields."""

    session_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Shared context from the orchestrator (session metadata, previous outputs)",
    )


class AgentOutput(BaseModel):
    """Base output schema for any agent. Agents extend this with their own fields."""

    success: bool = True
    error: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Agent 1: Research Intelligence
# =============================================================================


class ResearchInput(AgentInput):
    """Input for the Research Intelligence agent."""

    pass  # Will be extended with research parameters


class ResearchOutput(AgentOutput):
    """Output from the Research Intelligence agent."""

    topics: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""


# =============================================================================
# Agent 2: Topic Prioritization
# =============================================================================


class TopicPrioritizationInput(AgentInput):
    """Input for the Topic Prioritization agent."""

    research_data: dict[str, Any] = Field(default_factory=dict)


class TopicPrioritizationOutput(AgentOutput):
    """Output from the Topic Prioritization agent."""

    ranked_topics: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Agent 3: Content Strategist
# =============================================================================


class ContentStrategistInput(AgentInput):
    """Input for the Content Strategist agent."""

    ranked_topics: list[dict[str, Any]] = Field(default_factory=list)


class ContentStrategistOutput(AgentOutput):
    """Output from the Content Strategist agent."""

    content_plan: dict[str, Any] = Field(default_factory=dict)
    platform_guidelines: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Agent 4: Content Writer
# =============================================================================


class ContentWriterInput(AgentInput):
    """Input for the Content Writer agent."""

    content_plan: dict[str, Any] = Field(default_factory=dict)
    platform_guidelines: dict[str, Any] = Field(default_factory=dict)
    revision_feedback: dict[str, Any] | None = None


class ContentWriterOutput(AgentOutput):
    """Output from the Content Writer agent."""

    drafts: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Agent 5: Chief Editor
# =============================================================================


class ChiefEditorInput(AgentInput):
    """Input for the Chief Editor agent."""

    drafts: list[dict[str, Any]] = Field(default_factory=list)
    content_plan: dict[str, Any] = Field(default_factory=dict)


class ChiefEditorOutput(AgentOutput):
    """Output from the Chief Editor agent."""

    reviewed_drafts: list[dict[str, Any]] = Field(default_factory=list)
    editorial_notes: str = ""


# =============================================================================
# Agent 6: CMO
# =============================================================================


class CMOInput(AgentInput):
    """Input for the CMO agent."""

    reviewed_drafts: list[dict[str, Any]] = Field(default_factory=list)
    editorial_notes: str = ""


class CMOOutput(AgentOutput):
    """Output from the CMO agent."""

    approved: bool = False
    feedback: str = ""
    revision_notes: dict[str, Any] = Field(default_factory=dict)
    final_content: list[dict[str, Any]] = Field(default_factory=list)

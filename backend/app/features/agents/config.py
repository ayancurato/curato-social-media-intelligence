"""
Curato AI — Agent Prompt & Model Configuration System

Provides a versioned, per-agent configuration system for prompts,
model selection, temperature, max tokens, and retry settings.

Configuration can be loaded from:
1. YAML/JSON config files (default)
2. Database (future)
3. Environment variable overrides

Each agent has its own independent configuration that can be
hot-swapped without code changes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Configuration Models
# =============================================================================


class RetryConfig(BaseModel):
    """Retry settings for an agent."""

    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    exponential_backoff: bool = True
    max_delay_seconds: float = 60.0


class ModelConfig(BaseModel):
    """LLM model configuration for an agent."""

    provider: str = "openai"
    model: str = "gpt-4.1"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    response_format: str | None = None  # "json_object" or None


class PromptConfig(BaseModel):
    """Prompt configuration for an agent."""

    system_prompt: str = ""
    user_prompt_template: str = ""
    version: str = "1.0.0"
    description: str = ""
    variables: list[str] = Field(
        default_factory=list,
        description="List of template variable names expected in the prompt",
    )


class AgentConfig(BaseModel):
    """
    Complete configuration for a single agent.

    This is the central configuration object that each agent uses.
    It combines prompt, model, and retry settings into one structure.
    """

    agent_name: str
    display_name: str = ""
    description: str = ""
    enabled: bool = True

    prompt: PromptConfig = Field(default_factory=PromptConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)

    # Tool configuration — which tools this agent can use
    tools: list[str] = Field(
        default_factory=list,
        description="List of tool names from the Tool Registry this agent can invoke",
    )

    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Configuration Manager
# =============================================================================


class AgentConfigManager:
    """
    Manages agent configurations.

    Loads configurations from a JSON config file and provides
    per-agent access. Supports runtime updates and version tracking.
    """

    def __init__(self, config_dir: str | Path | None = None) -> None:
        self._configs: dict[str, AgentConfig] = {}
        self._config_dir = Path(config_dir) if config_dir else self._default_config_dir()
        self._load_defaults()

    @staticmethod
    def _default_config_dir() -> Path:
        """Default config directory relative to the backend root."""
        return Path(__file__).parent.parent.parent / "config" / "agents"

    def _load_defaults(self) -> None:
        """Load default configurations for all agents."""
        settings = get_settings()

        default_agents = {
            "research": AgentConfig(
                agent_name="research",
                display_name="Research Intelligence",
                description="Gathers trending topics, industry news, and competitor insights",
                prompt=PromptConfig(
                    system_prompt="",  # To be configured
                    version="0.0.0",
                    description="Research Intelligence agent prompt — not yet implemented",
                ),
                model=ModelConfig(
                    provider=settings.default_llm_provider,
                    model=settings.default_llm_model,
                    temperature=0.3,  # Lower temp for factual research
                    max_tokens=settings.default_llm_max_tokens,
                ),
                tools=["web_search", "news_api", "google_trends", "linkedin", "reddit", "web_scraper"],
            ),
            "topic_prioritization": AgentConfig(
                agent_name="topic_prioritization",
                display_name="Topic Prioritization",
                description="Scores and ranks topics by relevance, trend potential, and brand fit",
                prompt=PromptConfig(
                    system_prompt="",
                    version="0.0.0",
                    description="Topic Prioritization agent prompt — not yet implemented",
                ),
                model=ModelConfig(
                    provider=settings.default_llm_provider,
                    model=settings.default_llm_model,
                    temperature=0.2, # Lower temperature for reasoning/scoring
                    max_tokens=8192, # Need higher tokens for batch-processing multiple topics
                    response_format="json_object",
                ),
                tools=[],
                metadata={
                    "strategic_profile": "Thought Leadership",
                    "profiles": {
                        "Thought Leadership": {
                            "opportunity": 0.20,
                            "business_alignment": 0.20,
                            "audience_intent": 0.15,
                            "strategic_value": 0.20,
                            "virality": 0.05,
                            "freshness": 0.15,
                            "confidence": 0.05,
                        },
                        "Lead Generation": {
                            "opportunity": 0.15,
                            "business_alignment": 0.30,
                            "audience_intent": 0.25,
                            "strategic_value": 0.10,
                            "virality": 0.05,
                            "freshness": 0.05,
                            "confidence": 0.10,
                        },
                        "Brand Awareness": {
                            "opportunity": 0.25,
                            "business_alignment": 0.15,
                            "audience_intent": 0.10,
                            "strategic_value": 0.10,
                            "virality": 0.25,
                            "freshness": 0.10,
                            "confidence": 0.05,
                        }
                    }
                }
            ),
            "content_strategist": AgentConfig(
                agent_name="content_strategist",
                display_name="Content Strategist",
                description="Creates content plans with angles, hooks, and platform-specific guidelines",
                prompt=PromptConfig(
                    system_prompt="",
                    version="0.0.0",
                    description="Content Strategist agent prompt — not yet implemented",
                ),
                model=ModelConfig(
                    provider=settings.default_llm_provider,
                    model=settings.default_llm_model,
                    temperature=0.6,
                    max_tokens=4096,
                ),
                tools=[],
            ),
            "content_writer": AgentConfig(
                agent_name="content_writer",
                display_name="Content Writer",
                description="Produces platform-ready content drafts for LinkedIn and Instagram",
                prompt=PromptConfig(
                    system_prompt="",
                    version="0.0.0",
                    description="Content Writer agent prompt — not yet implemented",
                ),
                model=ModelConfig(
                    provider=settings.default_llm_provider,
                    model=settings.default_llm_model,
                    temperature=0.8,  # Higher temp for creativity
                    max_tokens=4096,
                ),
                tools=[],
                metadata={
                    "max_concurrent_pipelines": 2
                }
            ),
            "chief_editor": AgentConfig(
                agent_name="chief_editor",
                display_name="Chief Editor",
                description="Reviews drafts for quality, brand voice, and strategic alignment",
                prompt=PromptConfig(
                    system_prompt="",
                    version="0.0.0",
                    description="Chief Editor agent prompt — not yet implemented",
                ),
                model=ModelConfig(
                    provider=settings.default_llm_provider,
                    model=settings.default_llm_model,
                    temperature=0.3,
                    max_tokens=4096,
                ),
                tools=[],
                metadata={
                    "max_concurrent_pipelines": 2,
                    "max_revision_cycles": 2
                }
            ),
            "cmo": AgentConfig(
                agent_name="cmo",
                display_name="Curato CMO",
                description="Final approval authority — approves or rejects content with feedback",
                prompt=PromptConfig(
                    system_prompt="",
                    version="0.0.0",
                    description="CMO agent prompt — not yet implemented",
                ),
                model=ModelConfig(
                    provider=settings.default_llm_provider,
                    model=settings.default_llm_model,
                    temperature=0.2,  # Very low temp for consistent decisions
                    max_tokens=2048,
                    response_format="json_object",
                ),
                tools=[],
            ),
        }

        self._configs = default_agents

        # Attempt to load overrides from config file
        self._load_from_file()

    def _load_from_file(self) -> None:
        """Load configuration overrides from JSON file if it exists."""
        config_file = self._config_dir / "agent_configs.json"
        if not config_file.exists():
            logger.info("No agent config file found, using defaults", path=str(config_file))
            return

        try:
            with open(config_file) as f:
                file_configs = json.load(f)

            for agent_name, config_data in file_configs.items():
                if agent_name in self._configs:
                    # Merge file config with defaults
                    existing = self._configs[agent_name].model_dump()
                    existing.update(config_data)
                    self._configs[agent_name] = AgentConfig(**existing)
                else:
                    self._configs[agent_name] = AgentConfig(**config_data)

            logger.info(
                "Loaded agent configs from file",
                path=str(config_file),
                agents=list(file_configs.keys()),
            )
        except Exception as e:
            logger.error("Failed to load agent configs from file", error=str(e))

    def get_config(self, agent_name: str) -> AgentConfig:
        """Get configuration for a specific agent."""
        if agent_name not in self._configs:
            logger.warning(
                "No config found for agent, using defaults",
                agent=agent_name,
            )
            return AgentConfig(agent_name=agent_name)
        return self._configs[agent_name]

    def update_config(self, agent_name: str, updates: dict[str, Any]) -> AgentConfig:
        """Update configuration for a specific agent at runtime."""
        current = self.get_config(agent_name)
        current_dict = current.model_dump()
        current_dict.update(updates)
        self._configs[agent_name] = AgentConfig(**current_dict)
        logger.info("Updated agent config", agent=agent_name, updates=list(updates.keys()))
        return self._configs[agent_name]

    def list_configs(self) -> dict[str, AgentConfig]:
        """List all agent configurations."""
        return self._configs.copy()

    def save_to_file(self) -> None:
        """Persist current configurations to the config file."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self._config_dir / "agent_configs.json"

        configs_dict = {
            name: config.model_dump() for name, config in self._configs.items()
        }

        with open(config_file, "w") as f:
            json.dump(configs_dict, f, indent=2, default=str)

        logger.info("Saved agent configs to file", path=str(config_file))


# ── Singleton ────────────────────────────────────────────────────────────────
_config_manager: AgentConfigManager | None = None


def get_agent_config_manager() -> AgentConfigManager:
    """Get or create the singleton AgentConfigManager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = AgentConfigManager()
    return _config_manager

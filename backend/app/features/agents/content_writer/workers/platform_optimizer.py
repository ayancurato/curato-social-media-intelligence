"""
Curato AI — Platform Optimizer Worker (Deterministic)
"""

from typing import Any
from app.features.agents.content_writer.utils.formatting import apply_platform_formatting


class PlatformOptimizerWorker:
    """
    Applies deterministic formatting rules to the draft based on the target platform.
    Does not use an LLM, reducing latency and cost.
    """
    
    @property
    def name(self) -> str:
        return "Platform Optimizer"

    def process(self, draft: str, platform: str) -> str:
        return apply_platform_formatting(draft, platform)

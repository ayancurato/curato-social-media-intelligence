"""
Curato AI — LLM Prompt Budget Guard
"""

import math
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptBudgetGuard:
    """
    Estimates input tokens before hitting the routing layer and
    gracefully truncates the prompt if it exceeds the model's budget threshold.
    """
    
    # Safe heuristic: 4 characters ~ 1 token for English text
    CHARS_PER_TOKEN = 4.0
    
    # We leave 15% of the context window as headroom for completion/system prompts
    BUDGET_THRESHOLD_PCT = 0.85

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return math.ceil(len(text) / cls.CHARS_PER_TOKEN)
        
    @classmethod
    def apply_budget(cls, prompt: str, context_window: int) -> str:
        """
        Check if prompt exceeds the budget threshold.
        If so, truncate it from the middle to preserve instructions at top and latest data at bottom.
        """
        estimated_tokens = cls.estimate_tokens(prompt)
        max_allowed_tokens = int(context_window * cls.BUDGET_THRESHOLD_PCT)
        
        if estimated_tokens <= max_allowed_tokens:
            return prompt
            
        logger.warning(
            "PromptBudgetGuard: Prompt exceeds budget, truncating.",
            estimated=estimated_tokens,
            allowed=max_allowed_tokens,
            context_window=context_window
        )
        
        # Calculate how many chars we can keep
        allowed_chars = int(max_allowed_tokens * cls.CHARS_PER_TOKEN)
        
        # Keep 40% of the beginning and 60% of the end
        keep_start = int(allowed_chars * 0.4)
        keep_end = allowed_chars - keep_start
        
        truncation_msg = "\n\n...[TRUNCATED BY BUDGET GUARD]...\n\n"
        
        # Make room for the truncation message
        keep_start -= len(truncation_msg) // 2
        keep_end -= len(truncation_msg) // 2
        
        truncated_prompt = prompt[:keep_start] + truncation_msg + prompt[-keep_end:]
        return truncated_prompt

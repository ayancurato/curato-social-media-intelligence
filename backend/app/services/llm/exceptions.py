"""
Curato AI — LLM Exceptions & Error Classification
"""

import re
from typing import Optional


class LLMTransientError(Exception):
    """Temporary errors like 503, connection timeouts, or temporary 429s."""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class LLMQuotaExhaustedError(Exception):
    """Hard quota exhaustion like Tokens per day, credits exhausted."""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class LLMFatalError(Exception):
    """Permanent errors like authentication failures or invalid requests."""
    pass


class AllProvidersExhaustedError(Exception):
    """Raised when all configured providers are unavailable or quota-exhausted."""
    pass


def classify_llm_error(e: Exception) -> Exception:
    """
    Parses a raw exception from an LLM provider SDK (OpenAI, Anthropic, etc.)
    and returns a structured exception type. Also extracts retry-after if present.
    """
    err_str = str(e).lower()
    
    # Try to extract retry-after
    retry_after: Optional[float] = None
    
    # Look for common retry-after patterns: "retry after X seconds", "Please try again in X.Ys"
    # Matches patterns like "Please try again in 86400s", "try again in 14m2s", etc.
    # We will do a basic float extraction for "retry after X" or "try again in X"
    retry_match = re.search(r'(?:retry after|try again in|wait)\s*([0-9.]+)\s*(s|sec|seconds)?', err_str)
    if retry_match:
        try:
            val = float(retry_match.group(1))
            retry_after = val
        except (ValueError, TypeError):
            pass

    # Some APIs format it as minutes or hours
    if not retry_after:
        min_match = re.search(r'(?:try again in|wait)\s*([0-9.]+)\s*(m|min|minutes)', err_str)
        if min_match:
            try:
                retry_after = float(min_match.group(1)) * 60
            except (ValueError, TypeError):
                pass
            
    # Look for headers dict string representation if present
    header_match = re.search(r"\'retry-after\':\s*\'([0-9.]+)\'", err_str)
    if header_match and not retry_after:
        try:
            retry_after = float(header_match.group(1))
        except (ValueError, TypeError):
            pass

    # Quota exhaustion keywords
    quota_keywords = [
        "tokens per day", "tokens per minute", "credits exhausted", 
        "billing", "out of credits", "quota exceeded", "rate limit reached for"
    ]
    for kw in quota_keywords:
        if kw in err_str:
            return LLMQuotaExhaustedError(str(e), retry_after=retry_after)

    # Transient keywords
    transient_keywords = [
        "429", "503", "502", "504", "timeout", "connection error", 
        "rate limit", "too many requests", "service unavailable",
        "connection refused", "connection reset"
    ]
    for kw in transient_keywords:
        if kw in err_str:
            return LLMTransientError(str(e), retry_after=retry_after)

    # Fatal keywords
    fatal_keywords = [
        "authentication", "401", "403", "invalid request", 
        "400", "validation", "malformed", "not found", "404"
    ]
    for kw in fatal_keywords:
        if kw in err_str:
            return LLMFatalError(str(e))

    # If it's something else but looks like a generic error, we default to transient
    # since we have a circuit breaker anyway.
    return LLMTransientError(str(e), retry_after=retry_after)

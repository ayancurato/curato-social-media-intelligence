"""
Curato AI — Content Fingerprinting Utilities
"""

import re
from typing import Any


def calculate_word_count(text: str) -> int:
    return len(re.findall(r'\b\w+\b', text))


def calculate_reading_time(word_count: int, wpm: int = 200) -> int:
    """Returns reading time in seconds."""
    if word_count == 0:
        return 0
    return max(1, int((word_count / wpm) * 60))


def calculate_sentence_count(text: str) -> int:
    # simple split by punctuation
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def generate_fingerprint(draft: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Generates a statistical fingerprint for the final draft.
    """
    word_count = calculate_word_count(draft)
    sentence_count = calculate_sentence_count(draft)
    
    reading_time_sec = calculate_reading_time(word_count)
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "reading_time_seconds": reading_time_sec,
        "average_words_per_sentence": round(word_count / max(1, sentence_count), 2),
        "hook_type": metadata.get("hook_type", "Unknown"),
        "cta_type": metadata.get("cta_type", "Unknown"),
        "platform": metadata.get("platform", "Unknown"),
        "tone": metadata.get("tone", "Unknown"),
        "entity_count": len(metadata.get("entities", [])),
    }

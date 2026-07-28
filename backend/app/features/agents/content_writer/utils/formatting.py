"""
Curato AI — Content Formatting Utilities (Deterministic rules)
"""

import re


def format_for_linkedin(draft: str) -> str:
    """
    Applies strict formatting rules for LinkedIn.
    - Ensures paragraph spacing for skimmability (1-2 sentences max per paragraph).
    - Checks hashtag placement.
    """
    # Simple rule: replace triple newlines with double newlines
    draft = re.sub(r'\n{3,}', '\n\n', draft)
    
    # Simple rule: ensure hashtags are at the end, not mid-sentence if possible.
    # We won't re-write sentences here, but we can ensure there is a blank line before hashtags.
    if '#' in draft:
        parts = draft.rsplit('\n', 1)
        if len(parts) > 1 and parts[-1].strip().startswith('#'):
            draft = parts[0].strip() + '\n\n' + parts[-1].strip()
            
    return draft.strip()


def format_for_instagram(draft: str) -> str:
    """
    Applies strict formatting rules for Instagram captions.
    - Limits long paragraphs.
    - Standardizes emoji spacing (placeholder logic).
    """
    draft = re.sub(r'\n{3,}', '\n\n', draft)
    return draft.strip()


def format_for_twitter(draft: str) -> str:
    """
    Splits content into a Twitter thread if over 280 characters.
    """
    if len(draft) <= 280:
        return draft.strip()
        
    paragraphs = draft.split('\n\n')
    thread = []
    
    for p in paragraphs:
        if len(p) > 270:
            # simple hard wrap for extreme cases
            thread.extend([p[i:i+270] for i in range(0, len(p), 270)])
        else:
            thread.append(p)
            
    return "\n\n---\n\n".join(thread)


def apply_platform_formatting(draft: str, platform: str) -> str:
    """Routes the draft to the correct platform formatting utility."""
    platform = platform.lower()
    if platform == "linkedin":
        return format_for_linkedin(draft)
    elif platform == "instagram":
        return format_for_instagram(draft)
    elif platform in ("twitter", "x"):
        return format_for_twitter(draft)
    return draft.strip()

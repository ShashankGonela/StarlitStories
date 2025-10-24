"""
Safety utilities for Story Teller Agent.

This module provides fast safety checks and content filtering for child-appropriate
storytelling. These checks complement the LLM-based StoryChecker node.
"""

import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


# Banned themes and keywords that are never appropriate for children 5-10
BANNED_THEMES = [
    # Violence & horror
    "murder", "killing", "blood", "gore", "torture", "massacre",
    "mutilation", "dismemberment", "slaughter", "violent death",
    
    # Adult content
    "sex", "sexual", "erotic", "pornography", "nudity", "intercourse",
    "reproduction", "genitals", "masturbation", "rape", "assault",
    
    # Substance abuse
    "drugs", "cocaine", "heroin", "meth", "marijuana", "weed",
    "cigarettes", "smoking", "drinking", "drunk", "alcoholic",
    "overdose", "addiction", "high on",
    
    # Disturbing content
    "suicide", "self-harm", "cutting", "depression", "trauma",
    "abuse", "molestation", "pedophile", "kidnapping",
    
    # Profanity & slurs (add more as needed)
    "damn", "hell", "shit", "fuck", "bitch", "bastard",
    
    # Weapons (context matters, but these are red flags)
    "gun", "rifle", "pistol", "grenade", "bomb", "explosive",
    "knife attack", "stabbing", "shooting",
    
    # Scary/horror
    "nightmare", "demon", "possessed", "haunted", "evil spirit",
    "terror", "horrifying", "gruesome", "macabre",
]


# Warning themes - may be okay in context but require extra scrutiny
WARNING_THEMES = [
    "death", "dying", "dead", "funeral", "cemetery", "grave",
    "monster", "scary", "frightened", "afraid", "fear",
    "fight", "battle", "combat", "war", "conflict",
    "sad", "crying", "tears", "lonely", "abandoned",
    "lost", "separated", "orphan", "homeless",
    "fire", "burn", "flames", "disaster", "catastrophe",
]


# Positive themes (encourage these)
POSITIVE_THEMES = [
    "friendship", "kindness", "courage", "bravery", "helping",
    "sharing", "caring", "love", "family", "honesty",
    "truth", "justice", "fairness", "cooperation", "teamwork",
    "adventure", "discovery", "learning", "growing", "magic",
    "wonder", "joy", "happiness", "laughter", "fun",
]


def is_theme_child_safe(theme: str, strict_mode: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Fast heuristic check if a theme is child-safe.
    
    Args:
        theme: The theme to check
        strict_mode: If True, reject warning themes too
        
    Returns:
        Tuple of (is_safe, reason)
        - is_safe: True if theme passes safety check
        - reason: Explanation if rejected, None if safe
    """
    if not theme:
        return False, "Empty theme provided"
    
    theme_lower = theme.lower().strip()
    
    # Check for banned content
    for banned in BANNED_THEMES:
        if banned in theme_lower:
            logger.warning(f"Rejected theme containing banned keyword: '{banned}'")
            return False, f"Theme contains inappropriate content: '{banned}'"
    
    # In strict mode, also check warning themes
    if strict_mode:
        for warning in WARNING_THEMES:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(warning) + r'\b'
            if re.search(pattern, theme_lower):
                logger.info(f"Theme contains warning keyword: '{warning}' (strict mode)")
                return False, f"Theme may not be appropriate: '{warning}'. Please choose a more positive theme."
    
    return True, None


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """
    Basic text sanitization to prevent prompt injection or oversized content.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        logger.warning(f"Text truncated from {len(text)} to {max_length} characters")
        text = text[:max_length]
    
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    return text.strip()


def check_content_safety(content: str) -> Tuple[bool, List[str]]:
    """
    Scan content for safety issues.
    
    This is a basic keyword-based check. The LLM StoryChecker provides
    more sophisticated contextual analysis.
    
    Args:
        content: Content to check
        
    Returns:
        Tuple of (is_safe, issues_found)
        - is_safe: True if no major issues detected
        - issues_found: List of issues (empty if safe)
    """
    if not content:
        return True, []
    
    content_lower = content.lower()
    issues = []
    
    # Check for banned keywords
    for banned in BANNED_THEMES:
        pattern = r'\b' + re.escape(banned) + r'\b'
        if re.search(pattern, content_lower):
            issues.append(f"Contains banned keyword: '{banned}'")
    
    is_safe = len(issues) == 0
    
    if not is_safe:
        logger.warning(f"Content safety check failed: {len(issues)} issues found")
    
    return is_safe, issues


def extract_age_appropriate_length(age_min: int = 5, age_max: int = 10, length_tier: str = "medium") -> int:
    """
    Get recommended word count for stories based on age range and length tier.
    
    Args:
        age_min: Minimum age (default 5)
        age_max: Maximum age (default 10)
        length_tier: "short", "medium", or "long"
        
    Returns:
        Recommended word count
    """
    # Base recommendations for ages 5-10
    word_counts = {
        "short": (200, 400),
        "medium": (400, 800),
        "long": (800, 1200),
    }
    
    tier = length_tier.lower()
    if tier not in word_counts:
        logger.warning(f"Unknown length tier '{tier}', defaulting to medium")
        tier = "medium"
    
    min_words, max_words = word_counts[tier]
    
    # Return midpoint
    return (min_words + max_words) // 2


def get_safe_alternatives(unsafe_theme: str) -> List[str]:
    """
    Suggest safe alternative themes when a request is rejected.
    
    Args:
        unsafe_theme: The rejected theme
        
    Returns:
        List of safe alternative suggestions
    """
    # Simple mapping of unsafe to safe alternatives
    alternatives = {
        "violence": ["courage", "bravery", "problem-solving"],
        "scary": ["adventure", "mystery", "discovery"],
        "death": ["saying goodbye", "remembering loved ones", "the circle of life"],
        "fighting": ["cooperation", "working together", "resolving conflicts"],
        "monsters": ["friendly creatures", "magical beings", "animal friends"],
    }
    
    # Try to find matching alternatives
    theme_lower = unsafe_theme.lower()
    for key, values in alternatives.items():
        if key in theme_lower:
            return values
    
    # Default safe suggestions
    return [
        "friendship and kindness",
        "helping others",
        "learning something new",
        "animal adventures",
        "magical discoveries",
    ]


def format_rejection_message(theme: str, reason: str) -> str:
    """
    Format a gentle rejection message for inappropriate requests.
    
    Args:
        theme: The rejected theme
        reason: Why it was rejected
        
    Returns:
        Formatted rejection message
    """
    alternatives = get_safe_alternatives(theme)
    alt_text = ", ".join(alternatives[:3])
    
    return (
        f"I'm sorry — I can't help with that story. "
        f"I can help make a safe, child-friendly story about {alt_text} instead. "
        f"Would you like that?"
    )


# Logging configuration for safety checks
def configure_safety_logging(log_level: str = "INFO"):
    """Configure logging for safety module."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

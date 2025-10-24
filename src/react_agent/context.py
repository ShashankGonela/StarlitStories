"""
Context and configuration for Story Teller Agent.

Defines model mappings, timeouts, and default state initialization.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


# Model mappings (maps node names to LLM provider/model strings)
MODEL_MAPPING = {
    "MainAgent": "google/gemini-2.5-flash",
    "StoryGenerator": "google/gemini-2.5-pro",
    "StoryChecker": "google/gemini-2.5-flash",
    "MoralSummarizer": "google/gemini-2.5-flash",
    "StoryRetriever": "google/gemini-2.5-pro",
    "Formatter": "google/gemini-2.5-flash",
}


# Node timeout settings (in seconds)
NODE_TIMEOUTS = {
    "MainAgent": 30,
    "StoryGenerator": 60,
    "StoryChecker": 30,
    "MoralSummarizer": 20,
    "StoryRetriever": 45,
    "Formatter": 20,
}


# Story generation settings
MAX_STORY_ITERATIONS = int(os.getenv("MAX_STORY_ITERATIONS", "3"))
DEFAULT_STORY_LENGTH = os.getenv("DEFAULT_STORY_LENGTH", "medium")
ENABLE_SAFETY_CHECKS = os.getenv("ENABLE_SAFETY_CHECKS", "true").lower() == "true"
STRICT_MODE = os.getenv("STRICT_MODE", "true").lower() == "true"


# LLM settings
DEFAULT_TEMPERATURE = {
    "MainAgent": 0.3,  # More deterministic for routing
    "StoryGenerator": 0.8,  # More creative for story generation
    "StoryChecker": 0.2,  # Very deterministic for validation
    "MoralSummarizer": 0.5,  # Balanced
    "StoryRetriever": 0.3,  # Deterministic for retrieval
    "Formatter": 0.1,  # Very deterministic for formatting
}


# Story length word count targets
LENGTH_WORD_COUNTS = {
    "short": {"min": 200, "max": 400, "target": 300},
    "medium": {"min": 400, "max": 800, "target": 600},
    "long": {"min": 800, "max": 1200, "target": 1000},
}


# State initialization
def get_initial_state() -> Dict[str, Any]:
    """
    Get the initial state for the LangGraph workflow.
    
    Returns:
        Dictionary with initial state values
    """
    return {
        "theme": "",
        "last_story_generated": None,
        "turn_count": 0,
        "feedback_history": [],
        "approved_story": None,
        "iteration_count": 0,
        "request_type": "new",  # "new", "modify", "retrieve"
        "length_tier": DEFAULT_STORY_LENGTH,
        "user_input": "",
        "final_output": "",
        "conversation_history": [],  # Track full conversation
    }


def get_model_for_node(node_name: str) -> str:
    """
    Get the LLM model string for a given node.
    
    Args:
        node_name: Name of the node (e.g., "StoryGenerator")
        
    Returns:
        Model string (e.g., "google/gemini-2.5-pro")
    """
    return MODEL_MAPPING.get(node_name, "google/gemini-2.5-flash")


def get_timeout_for_node(node_name: str) -> int:
    """
    Get the timeout in seconds for a given node.
    
    Args:
        node_name: Name of the node
        
    Returns:
        Timeout in seconds
    """
    return NODE_TIMEOUTS.get(node_name, 30)


def get_temperature_for_node(node_name: str) -> float:
    """
    Get the temperature setting for a given node.
    
    Args:
        node_name: Name of the node
        
    Returns:
        Temperature value (0.0 to 1.0)
    """
    return DEFAULT_TEMPERATURE.get(node_name, 0.7)


def get_length_targets(length_tier: str) -> Dict[str, int]:
    """
    Get word count targets for a length tier.
    
    Args:
        length_tier: "short", "medium", or "long"
        
    Returns:
        Dictionary with "min", "max", and "target" word counts
    """
    return LENGTH_WORD_COUNTS.get(
        length_tier.lower(),
        LENGTH_WORD_COUNTS["medium"]
    )


# Runtime configuration
class RuntimeConfig:
    """Runtime configuration for the agent."""
    
    def __init__(self):
        self.max_iterations = MAX_STORY_ITERATIONS
        self.enable_safety = ENABLE_SAFETY_CHECKS
        self.strict_mode = STRICT_MODE
        self.default_length = DEFAULT_STORY_LENGTH
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "max_iterations": self.max_iterations,
            "enable_safety": self.enable_safety,
            "strict_mode": self.strict_mode,
            "default_length": self.default_length,
        }


# Global config instance
runtime_config = RuntimeConfig()

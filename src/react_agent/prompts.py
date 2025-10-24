"""
Prompt loader utility for Story Teller Agent.

Loads prompt files from the prompts/ directory and provides templating support.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Path to prompts directory
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt file from the prompts directory.
    
    Args:
        prompt_name: Name of the prompt file (without .txt extension)
                    e.g., "main_agent_prompt", "story_generator_prompt"
    
    Returns:
        The prompt content as a string
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompt_path = PROMPTS_DIR / f"{prompt_name}.txt"
    
    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Loaded prompt: {prompt_name}")
        return content
    except Exception as e:
        logger.error(f"Error loading prompt {prompt_name}: {e}")
        raise


def format_prompt(prompt_template: str, **kwargs) -> str:
    """
    Format a prompt template with provided values.
    
    Args:
        prompt_template: The prompt template with {placeholders}
        **kwargs: Values to substitute into the template
        
    Returns:
        Formatted prompt string
    """
    try:
        return prompt_template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing template variable: {e}")
        raise ValueError(f"Missing required template variable: {e}")


class PromptManager:
    """
    Manages loading and caching of prompt templates.
    """
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompts into cache."""
        prompt_files = [
            "main_agent_prompt",
            "story_generator_prompt",
            "story_checker_prompt",
            "moral_summarizer_prompt",
            "story_retriever_prompt",
            "formatter_prompt",
        ]
        
        for prompt_name in prompt_files:
            try:
                self._cache[prompt_name] = load_prompt(prompt_name)
            except FileNotFoundError:
                logger.warning(f"Prompt file not found: {prompt_name}")
                self._cache[prompt_name] = ""
    
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a prompt, optionally formatted with values.
        
        Args:
            prompt_name: Name of the prompt (without .txt)
            **kwargs: Optional values to format into the prompt
            
        Returns:
            The prompt string (formatted if kwargs provided)
        """
        if prompt_name not in self._cache:
            self._cache[prompt_name] = load_prompt(prompt_name)
        
        prompt = self._cache[prompt_name]
        
        if kwargs:
            return format_prompt(prompt, **kwargs)
        
        return prompt
    
    def reload_prompt(self, prompt_name: str):
        """
        Reload a prompt from disk (useful during development).
        
        Args:
            prompt_name: Name of the prompt to reload
        """
        self._cache[prompt_name] = load_prompt(prompt_name)
        logger.info(f"Reloaded prompt: {prompt_name}")


# Global prompt manager instance
_prompt_manager = PromptManager()


def get_prompt(prompt_name: str, **kwargs) -> str:
    """
    Convenience function to get a prompt from the global manager.
    
    Args:
        prompt_name: Name of the prompt
        **kwargs: Optional template values
        
    Returns:
        The prompt string
    """
    return _prompt_manager.get_prompt(prompt_name, **kwargs)


def reload_prompt(prompt_name: str):
    """Reload a prompt from disk."""
    _prompt_manager.reload_prompt(prompt_name)


# Specific prompt getters for convenience
def get_main_agent_prompt() -> str:
    """Get the main agent system prompt."""
    return get_prompt("main_agent_prompt")


def get_story_generator_prompt(**kwargs) -> str:
    """Get the story generator prompt, optionally formatted."""
    return get_prompt("story_generator_prompt", **kwargs)


def get_story_checker_prompt(**kwargs) -> str:
    """Get the story checker prompt, optionally formatted."""
    return get_prompt("story_checker_prompt", **kwargs)


def get_moral_summarizer_prompt() -> str:
    """Get the moral summarizer prompt."""
    return get_prompt("moral_summarizer_prompt")


def get_story_retriever_prompt(**kwargs) -> str:
    """Get the story retriever prompt, optionally formatted."""
    return get_prompt("story_retriever_prompt", **kwargs)


def get_formatter_prompt(**kwargs) -> str:
    """Get the formatter prompt, optionally formatted."""
    return get_prompt("formatter_prompt", **kwargs)

"""
Utility functions for Story Teller Agent.

Helper functions for state management, formatting, and data processing.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from LLM response, handling common formatting issues.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Parsed JSON as dictionary, or None if parsing fails
    """
    if not response_text:
        return None
    
    # Try direct parsing first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    if "```json" in response_text:
        try:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Try to find JSON object in text
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    
    logger.error(f"Failed to parse JSON from response: {response_text[:200]}...")
    return None


def validate_story_structure(story_data: Dict[str, Any]) -> bool:
    """
    Validate that story data has required fields.
    
    Args:
        story_data: Story dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["title", "story"]
    
    if not isinstance(story_data, dict):
        logger.error("Story data is not a dictionary")
        return False
    
    for field in required_fields:
        if field not in story_data:
            logger.error(f"Missing required field: {field}")
            return False
        if not story_data[field] or not isinstance(story_data[field], str):
            logger.error(f"Invalid value for field: {field}")
            return False
    
    return True


def count_words(text: str) -> int:
    """
    Count words in a text string.
    
    Args:
        text: Text to count words in
        
    Returns:
        Number of words
    """
    if not text:
        return 0
    return len(text.split())


def format_state_summary(state: Dict[str, Any]) -> str:
    """
    Create a human-readable summary of the current state.
    
    Args:
        state: Current workflow state
        
    Returns:
        Formatted summary string
    """
    lines = [
        "=== Current State ===",
        f"Theme: {state.get('theme', 'Not set')}",
        f"Turn count: {state.get('turn_count', 0)}",
        f"Iteration count: {state.get('iteration_count', 0)}",
        f"Request type: {state.get('request_type', 'unknown')}",
        f"Length tier: {state.get('length_tier', 'medium')}",
    ]
    
    if state.get('last_story_generated'):
        story = state['last_story_generated']
        word_count = count_words(story.get('story', ''))
        lines.append(f"Last story: '{story.get('title', 'Untitled')}' ({word_count} words)")
    
    if state.get('approved_story'):
        lines.append("Status: Story approved")
    
    if state.get('feedback_history'):
        lines.append(f"Feedback items: {len(state['feedback_history'])}")
    
    return "\n".join(lines)


def add_feedback_to_history(
    state: Dict[str, Any],
    feedback: str,
    iteration: int
) -> Dict[str, Any]:
    """
    Add feedback to the state's feedback history.
    
    Args:
        state: Current state
        feedback: Feedback message to add
        iteration: Current iteration number
        
    Returns:
        Updated state
    """
    if "feedback_history" not in state:
        state["feedback_history"] = []
    
    state["feedback_history"].append({
        "iteration": iteration,
        "feedback": feedback,
        "timestamp": datetime.now().isoformat(),
    })
    
    return state


def should_continue_iteration(state: Dict[str, Any], max_iterations: int) -> bool:
    """
    Determine if we should continue iterating or stop.
    
    Args:
        state: Current state
        max_iterations: Maximum allowed iterations
        
    Returns:
        True if should continue, False if should stop
    """
    iteration_count = state.get("iteration_count", 0)
    
    if iteration_count >= max_iterations:
        logger.warning(f"Reached maximum iterations ({max_iterations})")
        return False
    
    # If story is approved, don't continue
    if state.get("approved_story"):
        return False
    
    return True


def increment_iteration(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Increment the iteration counter in state.
    
    Args:
        state: Current state
        
    Returns:
        Updated state
    """
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def reset_iteration_count(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reset the iteration counter to 0.
    
    Args:
        state: Current state
        
    Returns:
        Updated state
    """
    state["iteration_count"] = 0
    return state


def extract_theme_from_input(user_input: str) -> Optional[str]:
    """
    Extract theme from user input using simple heuristics.
    
    Args:
        user_input: User's input text
        
    Returns:
        Extracted theme or None
    """
    # Common patterns
    patterns = [
        "story about ",
        "tell me about ",
        "theme of ",
        "tale of ",
        "story on ",
    ]
    
    user_lower = user_input.lower()
    
    for pattern in patterns:
        if pattern in user_lower:
            start = user_lower.find(pattern) + len(pattern)
            # Take rest of sentence or up to punctuation
            remaining = user_input[start:].strip()
            if remaining:
                # Find first sentence-ending punctuation
                for punct in ['.', '!', '?']:
                    if punct in remaining:
                        remaining = remaining[:remaining.find(punct)]
                return remaining.strip()
    
    # If no pattern found, return whole input (let LLM handle it)
    return user_input.strip()


def classify_request_type(user_input: str) -> str:
    """
    Classify the type of user request.
    
    Args:
        user_input: User's input text
        
    Returns:
        Request type: "new_story", "modify_story", "retrieve_story", "conversational", "disallowed"
    """
    user_lower = user_input.lower()
    
    # Check for modification requests
    modify_keywords = ["change", "modify", "update", "edit", "revise", "improve", "make it"]
    if any(keyword in user_lower for keyword in modify_keywords):
        return "modify_story"
    
    # Check for retrieval of classic/popular stories
    retrieve_keywords = ["tell me", "classic", "traditional", "famous", "popular", "original"]
    story_names = ["cinderella", "snow white", "little red riding hood", "three little pigs",
                   "goldilocks", "hansel and gretel", "jack and the beanstalk"]
    if any(keyword in user_lower for keyword in retrieve_keywords) or \
       any(story in user_lower for story in story_names):
        return "retrieve_story"
    
    # Check for story creation requests
    create_keywords = ["story", "tale", "tell", "create", "write", "generate"]
    if any(keyword in user_lower for keyword in create_keywords):
        return "new_story"
    
    # Check for conversational
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon"]
    if any(greeting in user_lower for greeting in greetings) and len(user_input) < 50:
        return "conversational"
    
    # Default to conversational
    return "conversational"


def format_final_output(
    title: str,
    story: str,
    moral: str,
    formatted_output: Optional[str] = None
) -> str:
    """
    Format the final output for display.
    
    Args:
        title: Story title
        story: Story text
        moral: Moral lesson
        formatted_output: Pre-formatted output from Formatter node (if available)
        
    Returns:
        Formatted string ready for display
    """
    if formatted_output:
        return formatted_output
    
    # Fallback formatting if Formatter node fails
    return f"""
# {title}

{story}

---

**Moral:** {moral}

---

*Generated by Story Teller Agent*
"""


def log_node_execution(node_name: str, input_data: Any, output_data: Any):
    """
    Log node execution for debugging.
    
    Args:
        node_name: Name of the executed node
        input_data: Input to the node
        output_data: Output from the node
    """
    logger.info(f"=== Node: {node_name} ===")
    logger.debug(f"Input: {str(input_data)[:200]}...")
    logger.debug(f"Output: {str(output_data)[:200]}...")


def create_error_response(error_message: str, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_message: Error message to include
        state: Current state (optional)
        
    Returns:
        Error response dictionary
    """
    return {
        "error": True,
        "message": error_message,
        "state": state or {},
        "timestamp": datetime.now().isoformat(),
    }

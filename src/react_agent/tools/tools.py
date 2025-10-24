"""
Tools for Story Teller Agent.

Each tool wraps a node in the LangGraph workflow and handles LLM calls.
"""

import json
import logging
from typing import Dict, Any, Optional
from langsmith.run_helpers import traceable

from ..services.llm_client import LLMClient
from ..services.safety import (
    is_theme_child_safe,
    sanitize_text,
    check_content_safety,
    format_rejection_message,
)
from ..prompts import (
    get_main_agent_prompt,
    get_story_generator_prompt,
    get_story_checker_prompt,
    get_moral_summarizer_prompt,
    get_story_retriever_prompt,
    get_formatter_prompt,
)
from ..context import (
    get_model_for_node,
    get_temperature_for_node,
    get_length_targets,
    runtime_config,
)
from ..utils import (
    parse_json_response,
    validate_story_structure,
    classify_request_type,
    extract_theme_from_input,
)

logger = logging.getLogger(__name__)


@traceable(run_type="tool", name="MainAgent")
def main_agent_tool(
    input_text: str,
    state: Dict[str, Any],
    mock_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main agent tool - routes user requests and ensures child-safe storytelling.
    Uses full conversation history for context-aware routing.
    
    Args:
        input_text: User's input text
        state: Current workflow state
        mock_response: Optional mock response for testing
        
    Returns:
        Dictionary with:
            - route: Where to route ("story_generator", "story_retriever", "refuse", "respond")
            - theme: Extracted theme (if applicable)
            - request_type: Type of request
            - response: Response message (if applicable)
    """
    logger.info("MainAgent: Processing user input")
    
    # Sanitize input
    input_text = sanitize_text(input_text)
    
    # Build conversation history for LLM context
    conversation_history = state.get('conversation_history', [])
    history_text = ""
    
    if conversation_history:
        history_text = "\n\n=== CONVERSATION HISTORY ===\n"
        # Show last 5 exchanges for context (10 messages = 5 user + 5 agent)
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        for msg in recent_history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            history_text += f"{role.upper()}: {content}\n"
        history_text += "=== END HISTORY ===\n"
    
    # Build current state context
    last_story = state.get('last_story_generated')
    previous_title = last_story.get('title', 'None') if last_story else 'None'
    
    state_context = f"""
CURRENT STATE:
- Previous story title: {previous_title}
- Previous theme: {state.get('theme', 'None')}
- Turn count: {state.get('turn_count', 0)}
"""
    
    # Call LLM for sophisticated routing and safety assessment
    model = get_model_for_node("MainAgent")
    system_prompt = get_main_agent_prompt()
    
    user_prompt = f"""{history_text}
{state_context}

CURRENT USER INPUT: "{input_text}"

INSTRUCTIONS:
Analyze the FULL CONVERSATION HISTORY above to understand context.

CLASSIFICATION PRIORITY (check in this order):
1. FIRST: Is this a farewell (goodbye, goodnight, see you, bye), greeting (hello, hi), thank you, or acknowledgment?
   → If YES: classify as CONVERSATIONAL (even if story exists in history)
2. THEN: Is user asking to modify/change/adjust the PREVIOUS story (from history)?
   → If YES: classify as MODIFY_STORY
3. THEN: Is user asking for a completely NEW story with a different theme?
   → If YES: classify as NEW_STORY
4. Is user requesting a classic/well-known story by name?
   → If YES: classify as RETRIEVE_CLASSIC_STORY
5. Is content inappropriate for children 5-10?
   → If YES: classify as INAPPROPRIATE
6. Otherwise: classify as CONVERSATIONAL

Provide your analysis in this EXACT format:

DECISION: [appropriate/inappropriate]
REQUEST_TYPE: [conversational/new_story/modify_story/retrieve_classic_story/inappropriate]
THEME: [extracted theme or modification description]
RESPONSE: [your response to the user if conversational or inappropriate]

CRITICAL: 
- "Goodnight", "Goodbye", "See you later", "Thank you" are ALWAYS conversational, even after a story
- Look at conversation history! If a story was just generated and user says "make the swordfish win" or similar, this is MODIFY_STORY, not NEW_STORY!"""
    
    client = LLMClient()
    
    try:
        response = client.call_llm(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=get_temperature_for_node("MainAgent"),
            mock_response=mock_response,
        )
        
        # Parse structured response from LLM
        response_text = response["text"]
        logger.debug(f"MainAgent response: {response_text}")
        
        # Extract decision fields
        decision = "appropriate"
        request_type = "conversational"
        theme = ""
        llm_response = response_text
        
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip().lower()
            elif line.startswith("REQUEST_TYPE:"):
                request_type = line.split(":", 1)[1].strip().lower()
            elif line.startswith("THEME:"):
                theme = line.split(":", 1)[1].strip()
            elif line.startswith("RESPONSE:"):
                llm_response = line.split(":", 1)[1].strip()
        
        logger.info(f"Parsed - Decision: {decision}, RequestType: {request_type}, Theme: {theme}")
        
        # Determine routing based on LLM decision
        if decision == "inappropriate" or "inappropriate" in request_type:
            route = "refuse"
            response_out = llm_response
        elif request_type == "conversational":
            route = "respond"
            response_out = llm_response
        elif "modify" in request_type:
            route = "story_generator"
            request_type = "modify"
            response_out = None
        elif "retrieve" in request_type or "classic" in request_type:
            route = "story_retriever"
            response_out = None
        elif "new" in request_type or "story" in request_type:
            route = "story_generator"
            request_type = "new"
            response_out = None
        else:
            # Default to conversational response
            route = "respond"
            response_out = llm_response
        
        return {
            "route": route,
            "theme": theme if theme else state.get("theme", ""),
            "request_type": request_type,
            "response": response_out,
        }
        
    except Exception as e:
        logger.error(f"MainAgent error: {e}")
        return {
            "route": "error",
            "theme": "",
            "request_type": "error",
            "response": "I'm sorry, I encountered an error. Please try again.",
        }


@traceable(run_type="tool", name="StoryGenerator")
def story_generator_tool(
    theme: str,
    previous_story: Optional[Dict[str, Any]] = None,
    feedback: Optional[str] = None,
    request_type: str = "new",
    length_tier: str = "medium",
    mock_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Story generator tool - creates or modifies stories.
    
    Args:
        theme: Theme for the story
        previous_story: Previous story (for modifications)
        feedback: Feedback from StoryChecker
        request_type: "new" or "modify"
        length_tier: "short", "medium", or "long"
        mock_response: Optional mock response for testing
        
    Returns:
        Dictionary with:
            - title: Story title
            - story: Story text
            - notes: Optional notes
            - success: Whether generation succeeded
    """
    logger.info(f"StoryGenerator: Generating {request_type} story for theme '{theme}'")
    
    model = get_model_for_node("StoryGenerator")
    system_prompt = get_story_generator_prompt(
        theme=theme,
        previous_story=previous_story.get("story", "") if previous_story else "none",
        feedback=feedback or "none",
        request_type=request_type,
        length_tier=length_tier
    )
    
    length_info = get_length_targets(length_tier)
    
    user_prompt = f"""Generate a story with the following requirements:
- Theme: {theme}
- Target length: {length_tier} ({length_info['min']}-{length_info['max']} words)
- Request type: {request_type}
"""
    
    if previous_story:
        user_prompt += f"\n- Previous story title: {previous_story.get('title', 'Unknown')}"
    
    if feedback:
        user_prompt += f"\n- Feedback to incorporate: {feedback}"
    
    user_prompt += "\n\nProvide output as valid JSON with keys: title, story, notes"
    
    client = LLMClient()
    
    try:
        response = client.call_llm(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=get_temperature_for_node("StoryGenerator"),
            response_format="json",
            mock_response=mock_response,
        )
        
        # Parse JSON response
        story_data = parse_json_response(response["text"])
        
        if not story_data or not validate_story_structure(story_data):
            logger.error("Invalid story structure from generator")
            return {
                "title": "Error",
                "story": "Failed to generate story",
                "notes": "JSON parsing failed",
                "success": False,
            }
        
        # Add success flag
        story_data["success"] = True
        
        logger.info(f"Generated story: '{story_data.get('title', 'Untitled')}'")
        return story_data
        
    except Exception as e:
        logger.error(f"StoryGenerator error: {e}")
        return {
            "title": "Error",
            "story": f"Failed to generate story: {str(e)}",
            "notes": "",
            "success": False,
        }


@traceable(run_type="tool", name="StoryChecker")
def story_checker_tool(
    story_text: str,
    story_title: str,
    theme: str,
    mock_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Story checker tool - validates story appropriateness and theme adherence.
    
    Args:
        story_text: The story text to check
        story_title: The story title
        theme: Expected theme
        mock_response: Optional mock response for testing
        
    Returns:
        Dictionary with:
            - approved: Boolean indicating if story is approved
            - score: Float score 0.0-1.0
            - reasons: List of reasons for decision
            - feedback_for_generator: Feedback for improvements (if not approved)
    """
    logger.info(f"StoryChecker: Checking story '{story_title}'")
    
    # Fast content safety check first
    if runtime_config.enable_safety:
        is_safe, issues = check_content_safety(story_text)
        if not is_safe:
            logger.warning(f"Story failed safety check: {issues}")
            return {
                "approved": False,
                "score": 0.0,
                "reasons": issues,
                "feedback_for_generator": f"Remove inappropriate content: {', '.join(issues)}",
            }
    
    model = get_model_for_node("StoryChecker")
    system_prompt = get_story_checker_prompt()
    
    user_prompt = f"""Check this story for appropriateness and theme adherence:

Title: {story_title}
Expected theme: {theme}

Story:
{story_text}

Provide your analysis as strict JSON with keys: approved, score, reasons, feedback_for_generator"""
    
    client = LLMClient()
    
    try:
        response = client.call_llm(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=get_temperature_for_node("StoryChecker"),
            response_format="json",
            mock_response=mock_response,
        )
        
        # Parse JSON response
        check_data = parse_json_response(response["text"])
        
        if not check_data:
            logger.error("Failed to parse StoryChecker response")
            # Default to not approved for safety
            return {
                "approved": False,
                "score": 0.0,
                "reasons": ["Failed to validate story"],
                "feedback_for_generator": "Unable to validate. Please regenerate.",
            }
        
        # Ensure required fields
        check_data.setdefault("approved", False)
        check_data.setdefault("score", 0.0)
        check_data.setdefault("reasons", [])
        check_data.setdefault("feedback_for_generator", "")
        
        logger.info(f"Story check result: {'APPROVED' if check_data['approved'] else 'NOT APPROVED'} (score: {check_data['score']})")
        return check_data
        
    except Exception as e:
        logger.error(f"StoryChecker error: {e}")
        # Default to not approved for safety
        return {
            "approved": False,
            "score": 0.0,
            "reasons": [f"Error during validation: {str(e)}"],
            "feedback_for_generator": "Validation error. Please regenerate.",
        }


@traceable(run_type="tool", name="MoralSummarizer")
def moral_summarizer_tool(
    story_text: str,
    story_title: str,
    mock_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Moral summarizer tool - extracts and summarizes the moral lesson.
    
    Args:
        story_text: The approved story text
        story_title: The story title
        mock_response: Optional mock response for testing
        
    Returns:
        Dictionary with:
            - moral: The moral lesson text
            - success: Whether summarization succeeded
    """
    logger.info(f"MoralSummarizer: Extracting moral from '{story_title}'")
    
    model = get_model_for_node("MoralSummarizer")
    system_prompt = get_moral_summarizer_prompt()
    
    user_prompt = f"""Extract the moral lesson from this story:

Title: {story_title}

Story:
{story_text}

Provide a clear, child-friendly moral summary (1-3 sentences)."""
    
    client = LLMClient()
    
    try:
        response = client.call_llm(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=get_temperature_for_node("MoralSummarizer"),
            mock_response=mock_response,
        )
        
        moral = response["text"].strip()
        
        logger.info("Extracted moral successfully")
        return {
            "moral": moral,
            "success": True,
        }
        
    except Exception as e:
        logger.error(f"MoralSummarizer error: {e}")
        return {
            "moral": "This story teaches us important lessons about life.",
            "success": False,
        }

@traceable(run_type="tool", name="StoryRetriever")
def story_retriever_tool(
    query: str,
    mock_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Story retriever tool - retrieves canonical versions of popular/classic stories.
    
    Args:
        query: Story name or description
        mock_response: Optional mock response for testing
        
    Returns:
        Dictionary with:
            - title: Story title
            - story: Story text
            - provenance: Source information
            - found: Whether story was found
            - reason: Reason if not found
    """
    logger.info(f"StoryRetriever: Retrieving story for query '{query}'")
    
    model = get_model_for_node("StoryRetriever")
    system_prompt = get_story_retriever_prompt()
    
    user_prompt = f"""Retrieve the canonical, child-appropriate version of this story:

Query: {query}

Provide output as JSON with keys: title, story, provenance, found, reason (if not found)"""
    
    client = LLMClient()
    
    try:
        response = client.call_llm(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=get_temperature_for_node("StoryRetriever"),
            response_format="json",
            mock_response=mock_response,
        )
        
        # Parse JSON response
        retrieval_data = parse_json_response(response["text"])
        
        if not retrieval_data:
            logger.error("Failed to parse StoryRetriever response")
            return {
                "title": "",
                "story": "",
                "provenance": "",
                "found": False,
                "reason": "Failed to parse retrieval response",
            }
        
        # Ensure required fields
        retrieval_data.setdefault("found", False)
        retrieval_data.setdefault("title", "")
        retrieval_data.setdefault("story", "")
        retrieval_data.setdefault("provenance", "")
        retrieval_data.setdefault("reason", "")
        
        if retrieval_data["found"]:
            logger.info(f"Retrieved story: '{retrieval_data['title']}'")
        else:
            logger.info(f"Story not found: {retrieval_data.get('reason', 'Unknown reason')}")
        
        return retrieval_data
        
    except Exception as e:
        logger.error(f"StoryRetriever error: {e}")
        return {
            "title": "",
            "story": "",
            "provenance": "",
            "found": False,
            "reason": f"Error during retrieval: {str(e)}",
        }

@traceable(run_type="tool", name="Formatter")
def formatter_tool(
    story_title: str,
    story_text: str,
    moral: str,
    mock_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Formatter tool - formats the final story output for display.
    
    Args:
        story_title: The story title
        story_text: The story text
        moral: The moral lesson
        mock_response: Optional mock response for testing
        
    Returns:
        Dictionary with:
            - formatted_output: Formatted markdown output
            - success: Whether formatting succeeded
    """
    logger.info(f"Formatter: Formatting story '{story_title}'")
    
    model = get_model_for_node("Formatter")
    system_prompt = get_formatter_prompt()
    
    user_prompt = f"""Format this story for display:

Title: {story_title}

Story:
{story_text}

Moral: {moral}

Produce a neat markdown-formatted output."""
    
    client = LLMClient()
    
    try:
        response = client.call_llm(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=get_temperature_for_node("Formatter"),
            mock_response=mock_response,
        )
        
        formatted = response["text"].strip()
        
        logger.info("Formatted output successfully")
        return {
            "formatted_output": formatted,
            "success": True,
        }
        
    except Exception as e:
        logger.error(f"Formatter error: {e}")
        # Fallback formatting
        fallback = f"""# {story_title}

{story_text}

---

**Moral:** {moral}

---

*Generated by Story Teller Agent*
"""
        return {
            "formatted_output": fallback,
            "success": False,
        }

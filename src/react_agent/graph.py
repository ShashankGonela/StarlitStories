"""
LangGraph workflow definition for Story Teller Agent.

Defines the graph structure, nodes, edges, and state management for the storytelling workflow.
"""

import logging
from typing import Dict, Any, Literal, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .tools.tools import (
    main_agent_tool,
    story_generator_tool,
    story_checker_tool,
    moral_summarizer_tool,
    story_retriever_tool,
    formatter_tool,
)
from .context import get_initial_state, runtime_config
from .utils import (
    add_feedback_to_history,
    should_continue_iteration,
    increment_iteration,
    reset_iteration_count,
    format_state_summary,
    log_node_execution,
)

logger = logging.getLogger(__name__)


# State schema
class AgentState(TypedDict, total=False):
    """State schema for the Story Teller agent."""
    theme: str
    last_story_generated: Dict[str, Any]
    turn_count: int
    feedback_history: list
    approved_story: Dict[str, Any]
    iteration_count: int
    request_type: str
    length_tier: str
    user_input: str
    final_output: str
    route: str
    current_moral: str
    conversation_history: list  # List of {"role": "user"/"agent", "content": str}


# Node functions
def main_agent_node(state: AgentState) -> AgentState:
    """
    Main agent node - routes user requests.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info("Executing MainAgent node")
    
    user_input = state.get("user_input", "")
    
    result = main_agent_tool(
        input_text=user_input,
        state=state
    )
    
    # Update state with routing decision
    state["route"] = result["route"]
    state["theme"] = result["theme"]
    state["request_type"] = result.get("request_type", "new")
    
    if result.get("response"):
        state["final_output"] = result["response"]
    
    # Add user input to conversation history
    if "conversation_history" not in state:
        state["conversation_history"] = []
    
    state["conversation_history"].append({
        "role": "user",
        "content": user_input
    })
    
    state["turn_count"] = state.get("turn_count", 0) + 1
    
    log_node_execution("MainAgent", state.get("user_input"), result)
    return state


def story_generator_node(state: AgentState) -> AgentState:
    """
    Story generator node - creates or modifies stories.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info("Executing StoryGenerator node")
    
    # Get feedback from last check if available
    feedback = None
    if state.get("feedback_history"):
        feedback = state["feedback_history"][-1].get("feedback", "")
    
    result = story_generator_tool(
        theme=state.get("theme", ""),
        previous_story=state.get("last_story_generated"),
        feedback=feedback,
        request_type=state.get("request_type", "new"),
        length_tier=state.get("length_tier", "medium")
    )
    
    if result.get("success"):
        state["last_story_generated"] = result
    
    log_node_execution("StoryGenerator", state.get("theme"), result)
    return state


def story_checker_node(state: AgentState) -> AgentState:
    """
    Story checker node - validates story appropriateness.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info("Executing StoryChecker node")
    
    story = state.get("last_story_generated", {})
    
    if not story:
        logger.error("No story to check")
        state["route"] = "error"
        return state
    
    result = story_checker_tool(
        story_text=story.get("story", ""),
        story_title=story.get("title", ""),
        theme=state.get("theme", "")
    )
    
    if result.get("approved"):
        # Story approved - save it
        state["approved_story"] = story
        state["route"] = "approved"
        reset_iteration_count(state)
    else:
        # Story not approved - need to iterate
        increment_iteration(state)
        
        # Add feedback to history
        add_feedback_to_history(
            state,
            result.get("feedback_for_generator", ""),
            state.get("iteration_count", 0)
        )
        
        # Check if we should continue iterating
        if should_continue_iteration(state, runtime_config.max_iterations):
            state["route"] = "iterate"
        else:
            logger.warning("Max iterations reached - using best available story")
            # Use the story anyway since we hit max iterations
            state["approved_story"] = story
            state["route"] = "approved"
    
    log_node_execution("StoryChecker", story.get("title"), result)
    return state


def moral_summarizer_node(state: AgentState) -> AgentState:
    """
    Moral summarizer node - extracts moral lesson.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info("Executing MoralSummarizer node")
    
    story = state.get("approved_story", {})
    
    result = moral_summarizer_tool(
        story_text=story.get("story", ""),
        story_title=story.get("title", "")
    )
    
    state["current_moral"] = result.get("moral", "")
    
    log_node_execution("MoralSummarizer", story.get("title"), result)
    return state


def story_retriever_node(state: AgentState) -> AgentState:
    """
    Story retriever node - retrieves popular/classic stories.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info("Executing StoryRetriever node")
    
    query = state.get("theme", state.get("user_input", ""))
    
    result = story_retriever_tool(query=query)
    
    if result.get("found"):
        # Retrieved story successfully
        state["last_story_generated"] = {
            "title": result["title"],
            "story": result["story"],
            "notes": result.get("provenance", ""),
        }
        state["route"] = "check"
    else:
        # Story not found - route to generator to create original
        logger.info(f"Story not found, routing to generator: {result.get('reason')}")
        state["route"] = "generate"
        state["request_type"] = "new"
    
    log_node_execution("StoryRetriever", query, result)
    return state


def formatter_node(state: AgentState) -> AgentState:
    """
    Formatter node - formats final output.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    logger.info("Executing Formatter node")
    
    story = state.get("approved_story", {})
    moral = state.get("current_moral", "")
    
    result = formatter_tool(
        story_title=story.get("title", ""),
        story_text=story.get("story", ""),
        moral=moral
    )
    
    formatted_output = result.get("formatted_output", "")
    state["final_output"] = formatted_output
    
    # Add agent's story response to conversation history
    if "conversation_history" not in state:
        state["conversation_history"] = []
    
    state["conversation_history"].append({
        "role": "agent",
        "content": f"Story: {story.get('title', 'Untitled')}"
    })
    
    log_node_execution("Formatter", story.get("title"), result)
    return state


# Routing functions
def route_from_main_agent(state: AgentState) -> Literal["generate", "retrieve", "refuse", "respond", "error"]:
    """
    Determine routing from MainAgent.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    route = state.get("route", "respond")
    
    if route == "story_generator":
        return "generate"
    elif route == "story_retriever":
        return "retrieve"
    elif route == "refuse":
        return "respond"
    elif route == "error":
        return "error"
    else:
        return "respond"


def route_from_retriever(state: AgentState) -> Literal["check", "generate"]:
    """
    Determine routing from StoryRetriever.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    route = state.get("route", "check")
    
    if route == "generate":
        return "generate"
    else:
        return "check"


def route_from_checker(state: AgentState) -> Literal["iterate", "summarize"]:
    """
    Determine routing from StoryChecker.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    route = state.get("route", "approved")
    
    if route == "iterate":
        return "iterate"
    else:
        return "summarize"


# Build the graph
def create_graph() -> StateGraph:
    """
    Create the LangGraph workflow.
    
    Returns:
        Configured StateGraph
    """
    # Create workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("main_agent", main_agent_node)
    workflow.add_node("generate", story_generator_node)
    workflow.add_node("retrieve", story_retriever_node)
    workflow.add_node("check", story_checker_node)
    workflow.add_node("summarize", moral_summarizer_node)
    workflow.add_node("format", formatter_node)
    
    # Set entry point
    workflow.set_entry_point("main_agent")
    
    # Add conditional edges from main_agent
    workflow.add_conditional_edges(
        "main_agent",
        route_from_main_agent,
        {
            "generate": "generate",
            "retrieve": "retrieve",
            "respond": END,
            "refuse": END,
            "error": END,
        }
    )
    
    # Add edges from generator to checker
    workflow.add_edge("generate", "check")
    
    # Add conditional edges from retriever
    workflow.add_conditional_edges(
        "retrieve",
        route_from_retriever,
        {
            "check": "check",
            "generate": "generate",
        }
    )
    
    # Add conditional edges from checker
    workflow.add_conditional_edges(
        "check",
        route_from_checker,
        {
            "iterate": "generate",  # Loop back to generator
            "summarize": "summarize",
        }
    )
    
    # Add edges from summarizer to formatter to end
    workflow.add_edge("summarize", "format")
    workflow.add_edge("format", END)
    
    return workflow


def compile_graph():
    """
    Compile the graph with memory.
    
    Returns:
        Compiled graph ready for execution
    """
    workflow = create_graph()
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Example execution functions
def run_example_session():
    """
    Run example sessions to demonstrate the workflow.
    """
    logger.info("Running example sessions")
    
    graph = compile_graph()
    
    # Example 1: New story request
    print("\n" + "=" * 60)
    print("EXAMPLE 1: New Story Request")
    print("=" * 60)
    
    initial_state = get_initial_state()
    initial_state["user_input"] = "Tell me a story about a brave little mouse who helps his friends"
    initial_state["length_tier"] = "medium"
    
    config = {"configurable": {"thread_id": "example_1"}}
    
    try:
        final_state = graph.invoke(initial_state, config)
        print("\nFinal Output:")
        print(final_state.get("final_output", "No output generated"))
        print("\nState Summary:")
        print(format_state_summary(final_state))
    except Exception as e:
        logger.error(f"Example 1 failed: {e}")
        print(f"Error: {e}")
    
    # Example 2: Popular story request
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Popular Story Request")
    print("=" * 60)
    
    initial_state = get_initial_state()
    initial_state["user_input"] = "Tell me the story of The Three Little Pigs"
    initial_state["length_tier"] = "medium"
    
    config = {"configurable": {"thread_id": "example_2"}}
    
    try:
        final_state = graph.invoke(initial_state, config)
        print("\nFinal Output:")
        print(final_state.get("final_output", "No output generated"))
        print("\nState Summary:")
        print(format_state_summary(final_state))
    except Exception as e:
        logger.error(f"Example 2 failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run examples
    run_example_session()

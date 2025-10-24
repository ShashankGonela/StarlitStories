"""
Main entry point for Story Teller Agent.

Provides CLI interface and example execution modes.
"""

import sys
import argparse
import logging
from typing import Optional

from .graph import compile_graph, run_example_session
from .context import get_initial_state, runtime_config
from .utils import format_state_summary

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO"):
    """
    Configure logging for the application.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def run_interactive_mode():
    """
    Run the agent in interactive CLI mode.
    """
    print("=" * 70)
    print("Story Teller Agent - Interactive Mode")
    print("=" * 70)
    print("\nWelcome! I'm your Story Teller agent.")
    print("I create safe, child-friendly stories for ages 5-10.")
    print("\nCommands:")
    print("  - Type your story request (e.g., 'Tell me a story about friendship')")
    print("  - Type 'exit' or 'quit' to leave")
    print("  - Type 'help' for more information")
    print("=" * 70)
    print()
    
    graph = compile_graph()
    session_id = "interactive_session"
    
    # Initialize state once for the entire session
    session_state = get_initial_state()
    config = {"configurable": {"thread_id": session_id}}
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nGoodbye! Happy storytelling!")
                break
            
            if user_input.lower() == "help":
                print("\nHow to use:")
                print("  - Request a new story: 'Tell me a story about [theme]'")
                print("  - Request a classic story: 'Tell me the story of [story name]'")
                print("  - Modify a story: 'Change the story to be more [description]'")
                print("\nExamples:")
                print("  - 'Tell me a story about a brave little mouse'")
                print("  - 'Tell me the story of The Three Little Pigs'")
                print("  - 'Make it shorter and funnier'")
                continue
            
            # Update state with new user input (preserve previous state)
            session_state["user_input"] = user_input
            session_state["length_tier"] = runtime_config.default_length
            
            print("\nAgent: Let me work on that...\n")
            
            # Execute graph with maintained state
            final_state = graph.invoke(session_state, config)
            
            # Update session state from final state
            session_state = final_state
            
            # Display output
            output = final_state.get("final_output", "")
            
            # If no final_output, the story was generated but not in final_output yet
            # Check if we have an approved story to show
            if not output and final_state.get("approved_story"):
                # Story was generated but not formatted yet - shouldn't happen but handle it
                story = final_state["approved_story"]
                output = f"\n# {story.get('title', 'Story')}\n\n{story.get('story', '')}\n"
            
            if not output:
                output = "I couldn't generate a response. Please try again."
            
            print(f"Agent: {output}")
            
            # Optionally show state summary in debug mode
            if logger.isEnabledFor(logging.DEBUG):
                print("\n" + "=" * 70)
                print(format_state_summary(final_state))
                print("=" * 70)
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}", exc_info=True)
            print(f"\nAgent: I'm sorry, I encountered an error: {e}")
            print("Please try again with a different request.")


def run_single_request(request: str, length: str = "medium") -> Optional[str]:
    """
    Run a single request and return the output.
    
    Args:
        request: User's story request
        length: Story length tier ("short", "medium", "long")
        
    Returns:
        Final output string or None if failed
    """
    logger.info(f"Processing single request: {request}")
    
    graph = compile_graph()
    
    state = get_initial_state()
    state["user_input"] = request
    state["length_tier"] = length
    
    config = {"configurable": {"thread_id": "single_request"}}
    
    try:
        final_state = graph.invoke(state, config)
        return final_state.get("final_output")
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return None


def run_server_mode(host: str = "localhost", port: int = 8000):
    """
    Run a simple HTTP server for the agent.
    
    NOTE: This is a placeholder. For production, use LangGraph Cloud or
    implement with FastAPI/Flask.
    
    Args:
        host: Server host
        port: Server port
    """
    print(f"Starting Story Teller Agent server on {host}:{port}")
    print("\nNOTE: Server mode is not fully implemented in this version.")
    print("For production deployment, consider:")
    print("  - LangGraph Cloud (https://langchain-ai.github.io/langgraph/cloud/)")
    print("  - FastAPI integration")
    print("  - Flask integration")
    print("\nFor now, use --interactive mode for testing.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Story Teller Agent - A child-safe storytelling agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in interactive mode
  python -m react_agent.main --interactive
  
  # Run example scenarios
  python -m react_agent.main --example
  
  # Process a single request
  python -m react_agent.main --request "Tell me a story about friendship"
  
  # Start server (placeholder)
  python -m react_agent.main --serve
        """
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive CLI mode"
    )
    
    parser.add_argument(
        "--example",
        action="store_true",
        help="Run example scenarios"
    )
    
    parser.add_argument(
        "--request",
        type=str,
        help="Process a single request"
    )
    
    parser.add_argument(
        "--length",
        type=str,
        default="medium",
        choices=["short", "medium", "long"],
        help="Story length (for --request mode)"
    )
    
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start HTTP server (placeholder)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Server host (for --serve mode)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (for --serve mode)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Execute based on mode
    if args.interactive:
        run_interactive_mode()
    elif args.example:
        run_example_session()
    elif args.request:
        output = run_single_request(args.request, args.length)
        if output:
            print("\n" + "=" * 70)
            print("Story Teller Agent Output")
            print("=" * 70)
            print(output)
            print("=" * 70)
        else:
            print("Failed to generate output")
            sys.exit(1)
    elif args.serve:
        run_server_mode(args.host, args.port)
    else:
        parser.print_help()
        print("\nNo mode specified. Use --help for options.")
        sys.exit(1)


if __name__ == "__main__":
    main()

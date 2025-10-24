"""
FastAPI server for Starlit Stories - Story Teller Agent

This server provides a REST API endpoint for generating stories using the LangGraph agent.
"""

import logging
import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langsmith import Client
from langsmith.run_helpers import traceable

from react_agent.graph import compile_graph
from react_agent.context import get_initial_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize LangSmith tracing
try:
    langsmith_client = Client()
    project_name = os.getenv("LANGCHAIN_PROJECT", "Starlit Stories")
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    if tracing_enabled:
        logger.info(f"✅ LangSmith tracing enabled for project: {project_name}")
    else:
        logger.info("ℹ️ LangSmith tracing is disabled (set LANGCHAIN_TRACING_V2=true to enable)")
except Exception as e:
    logger.warning(f"⚠️ LangSmith client initialization failed: {e}")
    langsmith_client = None

# Initialize FastAPI app
app = FastAPI(
    title="Starlit Stories API",
    description="AI-powered bedtime story generator for children ages 5-10",
    version="1.0.0"
)

# Configure CORS - allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class StoryRequest(BaseModel):
    """Request model for story generation."""
    user_input: str = Field(..., min_length=1, max_length=500, description="User's story request")
    length_tier: str = Field(default="medium", description="Story length: short, medium, or long")
    thread_id: str | None = Field(default=None, description="Optional thread ID to maintain conversation history")

class StoryResponse(BaseModel):
    """Response model for generated stories."""
    success: bool = Field(..., description="Whether story generation succeeded")
    story: str = Field(default="", description="The generated story")
    title: str = Field(default="", description="Story title")
    moral: str = Field(default="", description="Moral summary of the story")
    error: str = Field(default="", description="Error message if generation failed")
    thread_id: str = Field(..., description="Thread ID for maintaining conversation history")

# Initialize the LangGraph workflow
graph = compile_graph()
logger.info("LangGraph workflow compiled successfully")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Starlit Stories API is running",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": "Starlit Stories API",
        "graph_compiled": graph is not None
    }

@app.post("/generate_story", response_model=StoryResponse)
@traceable(run_type="chain", name="GenerateStoryAPI")
async def generate_story(request: StoryRequest) -> StoryResponse:
    """
    Generate a story based on user input.
    
    Args:
        request: StoryRequest containing user_input and optional length_tier
        
    Returns:
        StoryResponse with generated story, title, and moral
        
    Raises:
        HTTPException: If story generation fails
    """
    logger.info(f"Received story request: {request.user_input[:50]}...")
    
    try:
        # Use provided thread_id or generate a new one
        import uuid
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        logger.info(f"Invoking graph with thread_id: {thread_id}")
        
        # Try to get existing state from checkpointer
        try:
            existing_state = graph.get_state(config)
            if existing_state and existing_state.values:
                # Update existing state with new inputs
                state = existing_state.values
                state["user_input"] = request.user_input
                state["length_tier"] = request.length_tier
                logger.info(f"Loaded existing state with {len(state.get('conversation_history', []))} messages in history")
            else:
                # No existing state, create fresh one
                state = get_initial_state()
                state["user_input"] = request.user_input
                state["length_tier"] = request.length_tier
                logger.info("No existing state found, starting fresh conversation")
        except Exception as e:
            # Fallback to fresh state if retrieval fails
            logger.warning(f"Failed to retrieve existing state: {e}, starting fresh")
            state = get_initial_state()
            state["user_input"] = request.user_input
            state["length_tier"] = request.length_tier
        
        # Execute the LangGraph workflow
        final_state = graph.invoke(state, config)
        
        logger.info(f"Graph execution complete. Route: {final_state.get('route', 'unknown')}")
        
        # Extract story, title, and moral from final state
        final_output = final_state.get("final_output", "")
        approved_story = final_state.get("approved_story", {})
        route = final_state.get("route", "unknown")
        
        # Check route to determine response type
        # Route "approved" means a story was generated
        # Route "respond" means conversational response
        # Route "refuse" means inappropriate request
        if route == "approved" and approved_story:
            story_text = approved_story.get("story", "")
            story_title = approved_story.get("title", "Untitled Story")
            moral = final_state.get("current_moral", "")
            
            logger.info(f"Story generated successfully: {story_title}")
            
            return StoryResponse(
                success=True,
                story=story_text,
                title=story_title,
                moral=moral,
                thread_id=thread_id
            )
        
        # Conversational response (greetings, farewells, etc.)
        elif route == "respond" and final_output:
            logger.info(f"Returning conversational response: {final_output[:50]}...")
            return StoryResponse(
                success=True,
                story=final_output,
                title="",  # Empty title indicates conversational response
                moral="",
                thread_id=thread_id
            )
        
        # Refusal response (inappropriate request)
        elif route == "refuse" and final_output:
            logger.info(f"Refusing inappropriate request: {final_output[:50]}...")
            return StoryResponse(
                success=True,
                story=final_output,
                title="",  # Empty title indicates refusal/conversational
                moral="",
                thread_id=thread_id
            )
        
        # Fallback: if we have approved story but route is unclear
        elif approved_story:
            story_text = approved_story.get("story", "")
            story_title = approved_story.get("title", "Untitled Story")
            moral = final_state.get("current_moral", "")
            
            logger.info(f"Story generated successfully: {story_title}")
            
            return StoryResponse(
                success=True,
                story=story_text,
                title=story_title,
                moral=moral,
                thread_id=thread_id
            )
        
        # Fallback: final output without approved story
        elif final_output:
            logger.info("Returning conversational response (fallback)")
            return StoryResponse(
                success=True,
                story=final_output,
                title="",
                moral="",
                thread_id=thread_id
            )
        
        # If neither, something went wrong
        else:
            logger.warning("Story generation produced no output")
            return StoryResponse(
                success=False,
                error="Story generation did not produce output. Please try a different request.",
                thread_id=thread_id
            )
            
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate story: {str(e)}"
        )

@app.get("/examples")
async def get_examples():
    """Get example story prompts."""
    return {
        "examples": [
            "Tell me a story about a brave little mouse",
            "I want to hear about a friendly dragon who loves to bake",
            "Create a story about a curious star exploring the night sky",
            "Tell me about a magical forest where animals can talk",
            "Story about a kind mermaid who helps lost sailors"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Starlit Stories API server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

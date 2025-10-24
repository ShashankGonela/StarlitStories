"""
LLM Client abstraction layer for Story Teller Agent.

This module provides a pluggable interface for calling different LLM providers.
Currently supports Google Gemini, with placeholders for OpenAI and Anthropic.

Developer Note: Replace the TODO sections with actual provider SDK calls.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langsmith.run_helpers import traceable

load_dotenv()
logger = logging.getLogger(__name__)


class LLMClient:
    """
    Abstraction layer for LLM provider calls.
    
    Supports multiple providers through environment configuration.
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            provider: LLM provider name ('gemini', 'openai', 'anthropic')
                     If None, reads from LANGGRAPH_RUNTIME_PROVIDER env var
        """
        self.provider = provider or os.getenv("LANGGRAPH_RUNTIME_PROVIDER", "gemini")
        self.api_keys = self._load_api_keys()
        self._validate_configuration()
        logger.info(f"Initialized LLMClient with provider: {self.provider}")

    def _load_api_keys(self) -> Dict[str, Optional[str]]:
        """Load API keys from environment."""
        return {
            "gemini": os.getenv("GEMINI_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        }

    def _validate_configuration(self):
        """Validate that the configured provider has an API key."""
        api_key = self.api_keys.get(self.provider)
        if not api_key or api_key == f"your_{self.provider}_api_key_here":
            logger.warning(
                f"No valid API key found for provider '{self.provider}'. "
                f"Set {self.provider.upper()}_API_KEY in your .env file."
            )

    @traceable(run_type="llm", name="LLM_Call")
    def call_llm(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
        mock_response: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call the configured LLM provider.

        Args:
            model: Model identifier (e.g., "google/gemini-2.5-flash")
            system_prompt: System/instruction prompt
            user_prompt: User input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            response_format: Expected format ("json" or None)
            mock_response: If provided, return this instead of calling API (for testing)

        Returns:
            Dict with keys:
                - text: Response text
                - raw: Raw response object
                - model: Model used
                - tokens: Token usage info (if available)

        Raises:
            ValueError: If provider is not configured or unsupported
            Exception: If API call fails
        """
        if mock_response:
            logger.info("Using mock response (testing mode)")
            return {
                "text": mock_response,
                "raw": {"mock": True},
                "model": model,
                "tokens": {"prompt": 0, "completion": 0, "total": 0},
            }

        logger.info(f"Calling {self.provider} with model {model}")
        
        # Route to appropriate provider
        if self.provider == "gemini":
            return self._call_gemini(model, system_prompt, user_prompt, temperature, max_tokens)
        elif self.provider == "openai":
            return self._call_openai(model, system_prompt, user_prompt, temperature, max_tokens, response_format)
        elif self.provider == "anthropic":
            return self._call_anthropic(model, system_prompt, user_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_gemini(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: Optional[int],
    ) -> Dict[str, Any]:
        """
        Call Google Gemini API.
        
        TODO: Implement actual Gemini API call. Example:
        """
        import google.generativeai as genai
        genai.configure(api_key=self.api_keys['gemini'])
        
        # Extract model name from format "google/gemini-2.5-flash"
        model_name = model.split('/')[-1] if '/' in model else model
        
        client = genai.GenerativeModel(model_name)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = client.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        return {
            "text": response.text,
            "raw": response,
            "model": model,
            "tokens": {
                "prompt": response.usage_metadata.prompt_token_count,
                "completion": response.usage_metadata.candidates_token_count,
                "total": response.usage_metadata.total_token_count,
            }
        }
        
        api_key = self.api_keys.get("gemini")
        if not api_key or api_key.startswith("your_"):
            raise ValueError(
                "Gemini API key not configured. Set GEMINI_API_KEY in .env file.\n"
                "Get your key from: https://makersuite.google.com/app/apikey"
            )
        
        # Placeholder implementation
        logger.error("Gemini provider not fully implemented. Add google-generativeai SDK.")
        raise NotImplementedError(
            "Gemini API call not implemented. Install 'google-generativeai' and "
            "uncomment the implementation code in llm_client.py"
        )

    def _call_openai(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: Optional[int],
        response_format: Optional[str],
    ) -> Dict[str, Any]:
        """
        Call OpenAI API.
        
        TODO: Implement actual OpenAI API call. Example:
        
        from openai import OpenAI
        client = OpenAI(api_key=self.api_keys['openai'])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs = {
            "model": model.split('/')[-1],
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
            
        response = client.chat.completions.create(**kwargs)
        
        return {
            "text": response.choices[0].message.content,
            "raw": response,
            "model": model,
            "tokens": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens,
            }
        }
        """
        api_key = self.api_keys.get("openai")
        if not api_key or api_key.startswith("your_"):
            raise ValueError(
                "OpenAI API key not configured. Set OPENAI_API_KEY in .env file."
            )
        
        logger.error("OpenAI provider not fully implemented. Add openai SDK.")
        raise NotImplementedError(
            "OpenAI API call not implemented. Install 'openai' and "
            "uncomment the implementation code in llm_client.py"
        )

    def _call_anthropic(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: Optional[int],
    ) -> Dict[str, Any]:
        """
        Call Anthropic Claude API.
        
        TODO: Implement actual Anthropic API call. Example:
        
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_keys['anthropic'])
        
        response = client.messages.create(
            model=model.split('/')[-1],
            max_tokens=max_tokens or 4096,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {
            "text": response.content[0].text,
            "raw": response,
            "model": model,
            "tokens": {
                "prompt": response.usage.input_tokens,
                "completion": response.usage.output_tokens,
                "total": response.usage.input_tokens + response.usage.output_tokens,
            }
        }
        """
        api_key = self.api_keys.get("anthropic")
        if not api_key or api_key.startswith("your_"):
            raise ValueError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env file."
            )
        
        logger.error("Anthropic provider not fully implemented. Add anthropic SDK.")
        raise NotImplementedError(
            "Anthropic API call not implemented. Install 'anthropic' and "
            "uncomment the implementation code in llm_client.py"
        )


# Convenience function for quick calls
def call_llm(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[str] = None,
    mock_response: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to call LLM without managing client instance.
    
    See LLMClient.call_llm() for full documentation.
    """
    client = LLMClient()
    return client.call_llm(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        mock_response=mock_response,
    )

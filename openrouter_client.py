"""
OpenRouter API Client for AI Research
This module provides a client for interacting with OpenRouter's API using various AI models.
"""

from openai import OpenAI
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class OpenRouterClient:
    """
    A client for interacting with OpenRouter's API.
    Supports text and image analysis using various AI models.
    """
    
    def __init__(self, api_key: Optional[str] = None, site_url: Optional[str] = None, site_name: Optional[str] = None):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. If None, will try to get from OPENROUTER_API_KEY env var
            site_url: Your site URL for rankings on openrouter.ai (optional)
            site_name: Your site name for rankings on openrouter.ai (optional)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.")
        
        self.site_url = site_url or os.getenv("YOUR_SITE_URL")
        self.site_name = site_name or os.getenv("YOUR_SITE_NAME")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        
        # Cost tracking
        self.total_cost = 0.0
        self.request_count = 0
    
    def _extract_cost_info(self, response) -> Tuple[float, Dict[str, Any]]:
        """
        Extract cost information from OpenRouter API response.
        
        Args:
            response: The API response object
            
        Returns:
            Tuple of (cost, usage_info)
        """
        cost = 0.0
        usage_info = {}
        
        try:
            # Check for usage information in the response
            if hasattr(response, 'usage') and response.usage:
                usage_info = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            
            # Check for cost information in extra_body or response headers
            if hasattr(response, 'extra_body') and response.extra_body:
                cost_data = response.extra_body.get('cost', {})
                if cost_data:
                    cost = float(cost_data.get('total', 0.0))
                    usage_info['cost'] = cost
            
            # Alternative: check response headers for cost info
            if hasattr(response, 'response_headers'):
                cost_header = response.response_headers.get('x-cost')
                if cost_header:
                    cost = float(cost_header)
                    usage_info['cost'] = cost
                    
        except (AttributeError, ValueError, TypeError) as e:
            # If cost extraction fails, we'll estimate based on tokens
            pass
        
        return cost, usage_info
    
    def _estimate_cost(self, model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> float:
        """
        Estimate cost based on model and token usage.
        This is a fallback when exact cost isn't available.
        
        Args:
            model: The model name
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        # Approximate pricing per 1K tokens (as of 2024)
        pricing = {
            "x-ai/grok-4-fast": {"input": 0.001, "output": 0.003},
            "x-ai/grok-4": {"input": 0.002, "output": 0.006},
            "anthropic/claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
            "anthropic/claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "openai/gpt-4o": {"input": 0.005, "output": 0.015},
            "openai/gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "google/gemini-pro": {"input": 0.0005, "output": 0.0015},
            "meta-llama/llama-3.1-8b-instruct": {"input": 0.0002, "output": 0.0002},
            "meta-llama/llama-3.1-70b-instruct": {"input": 0.0009, "output": 0.0009},
        }
        
        model_pricing = pricing.get(model, {"input": 0.001, "output": 0.003})  # Default fallback
        
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get a summary of costs and usage.
        
        Returns:
            Dictionary with cost summary information
        """
        return {
            'total_cost': self.total_cost,
            'request_count': self.request_count,
            'average_cost_per_request': self.total_cost / max(self.request_count, 1)
        }
    
    def analyze_image(self, image_url: str, prompt: str = "What is in this image?", model: str = "x-ai/grok-4-fast") -> str:
        """
        Analyze an image using the specified AI model.
        
        Args:
            image_url: URL of the image to analyze
            prompt: The prompt/question to ask about the image
            model: The AI model to use for analysis
            
        Returns:
            The AI's response as a string
        """
        extra_headers = {}
        if self.site_url:
            extra_headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            extra_headers["X-Title"] = self.site_name
        
        completion = self.client.chat.completions.create(
            extra_headers=extra_headers,
            extra_body={},
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
        )
        
        # Track cost
        cost, usage_info = self._extract_cost_info(completion)
        if cost == 0.0 and usage_info:
            # Estimate cost if not provided
            cost = self._estimate_cost(
                model, 
                usage_info.get('prompt_tokens', 0), 
                usage_info.get('completion_tokens', 0)
            )
        
        self.total_cost += cost
        self.request_count += 1
        
        # Store cost info in the response for later access
        completion.cost_info = {
            'cost': cost,
            'usage': usage_info,
            'model': model
        }
        
        return completion.choices[0].message.content
    
    def chat_completion(self, messages: List[Dict[str, Any]], model: str = "x-ai/grok-4-fast") -> str:
        """
        Send a chat completion request to the AI model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The AI model to use
            
        Returns:
            The AI's response as a string
        """
        extra_headers = {}
        if self.site_url:
            extra_headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            extra_headers["X-Title"] = self.site_name
        
        completion = self.client.chat.completions.create(
            extra_headers=extra_headers,
            extra_body={},
            model=model,
            messages=messages
        )
        
        # Track cost
        cost, usage_info = self._extract_cost_info(completion)
        if cost == 0.0 and usage_info:
            # Estimate cost if not provided
            cost = self._estimate_cost(
                model, 
                usage_info.get('prompt_tokens', 0), 
                usage_info.get('completion_tokens', 0)
            )
        
        self.total_cost += cost
        self.request_count += 1
        
        # Store cost info in the response for later access
        completion.cost_info = {
            'cost': cost,
            'usage': usage_info,
            'model': model
        }
        
        return completion.choices[0].message.content
    
    def research_query(self, query: str, model: str = "x-ai/grok-4-fast") -> str:
        """
        Send a research query to the AI model.
        
        Args:
            query: The research question or topic
            model: The AI model to use
            
        Returns:
            The AI's response as a string
        """
        messages = [
            {
                "role": "system",
                "content": "You are an AI research assistant. Provide detailed, accurate, and well-structured responses to research queries."
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        return self.chat_completion(messages, model)
    
    def chat_completion_stream(self, messages: List[Dict[str, Any]], model: str = "x-ai/grok-4-fast"):
        """
        Send a streaming chat completion request to the AI model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The AI model to use
            
        Yields:
            Chunks of the AI's response as they arrive
        """
        extra_headers = {}
        if self.site_url:
            extra_headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            extra_headers["X-Title"] = self.site_name
        
        stream = self.client.chat.completions.create(
            extra_headers=extra_headers,
            extra_body={},
            model=model,
            messages=messages,
            stream=True
        )
        
        # Track tokens for cost estimation
        prompt_tokens = 0
        completion_tokens = 0
        full_response = ""
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                completion_tokens += len(content.split())  # Rough token estimation
                yield content
            
            # Check for usage info in the last chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens or 0
                completion_tokens = chunk.usage.completion_tokens or 0
        
        # Estimate and track cost for streaming
        cost = self._estimate_cost(model, prompt_tokens, completion_tokens)
        self.total_cost += cost
        self.request_count += 1
        
        # Store cost info for later access
        stream.cost_info = {
            'cost': cost,
            'usage': {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens
            },
            'model': model
        }
    
    def analyze_image_stream(self, image_url: str, prompt: str = "What is in this image?", model: str = "x-ai/grok-4-fast"):
        """
        Analyze an image using the specified AI model with streaming output.
        
        Args:
            image_url: URL of the image to analyze
            prompt: The prompt/question to ask about the image
            model: The AI model to use for analysis
            
        Yields:
            Chunks of the AI's response as they arrive
        """
        extra_headers = {}
        if self.site_url:
            extra_headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            extra_headers["X-Title"] = self.site_name
        
        stream = self.client.chat.completions.create(
            extra_headers=extra_headers,
            extra_body={},
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            stream=True
        )
        
        # Track tokens for cost estimation
        prompt_tokens = 0
        completion_tokens = 0
        full_response = ""
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                completion_tokens += len(content.split())  # Rough token estimation
                yield content
            
            # Check for usage info in the last chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens or 0
                completion_tokens = chunk.usage.completion_tokens or 0
        
        # Estimate and track cost for streaming
        cost = self._estimate_cost(model, prompt_tokens, completion_tokens)
        self.total_cost += cost
        self.request_count += 1
        
        # Store cost info for later access
        stream.cost_info = {
            'cost': cost,
            'usage': {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens
            },
            'model': model
        }
    
    def research_query_stream(self, query: str, model: str = "x-ai/grok-4-fast"):
        """
        Send a streaming research query to the AI model.
        
        Args:
            query: The research question or topic
            model: The AI model to use
            
        Yields:
            Chunks of the AI's response as they arrive
        """
        messages = [
            {
                "role": "system",
                "content": "You are an AI research assistant. Provide detailed, accurate, and well-structured responses to research queries."
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        for chunk in self.chat_completion_stream(messages, model):
            yield chunk


# Example usage function
def example_usage():
    """
    Example of how to use the OpenRouterClient
    """
    try:
        # Initialize the client
        client = OpenRouterClient()
        
        # Example 1: Analyze an image
        image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
        result = client.analyze_image(image_url)
        print("Image Analysis Result:")
        print(result)
        print("\n" + "="*50 + "\n")
        
        # Example 2: Research query
        research_result = client.research_query("What are the latest developments in AI research?")
        print("Research Query Result:")
        print(research_result)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set your OPENROUTER_API_KEY environment variable")


if __name__ == "__main__":
    example_usage()

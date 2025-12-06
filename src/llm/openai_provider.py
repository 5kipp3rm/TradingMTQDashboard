"""
OpenAI Provider for GPT models
"""
from typing import List, Dict, Any, Optional
import os

try:
    from openai import OpenAI
    OPENAI_INSTALLED = True
except ImportError:
    OPENAI_INSTALLED = False

from .base import BaseLLMProvider, LLMMessage, LLMResponse, MessageRole

try:
    from src.utils.config_loader import get_openai_key, get_openai_model
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    CONFIG_LOADER_AVAILABLE = False


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI GPT provider
    
    Supported models:
    - gpt-4o (most capable, 128K context)
    - gpt-4o-mini (fast & economical, recommended)
    - gpt-3.5-turbo (legacy)
    """
    
    def __init__(self, model: str = "gpt-4o-mini", 
                 api_key: Optional[str] = None, 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize OpenAI provider
        
        Args:
            model: Model name (default from config if available)
            api_key: OpenAI API key (checks: 1. parameter, 2. env var, 3. config file)
            config: Additional configuration
        """
        if not OPENAI_INSTALLED:
            raise ImportError("OpenAI library required. Install with: pip install openai")
        
        super().__init__(model, api_key, config)
        
        # Try to get API key in priority order:
        # 1. Passed as parameter
        # 2. Environment variable
        # 3. Config file
        if not self.api_key:
            self.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.api_key and CONFIG_LOADER_AVAILABLE:
            self.api_key = get_openai_key()
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set via:\n"
                "  1. Pass api_key parameter, OR\n"
                "  2. Set OPENAI_API_KEY env var, OR\n"
                "  3. Add to config/api_keys.yaml"
            )
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Default parameters
        self.default_params = {
            'temperature': 0.7,
            'max_tokens': 1000,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
        }
        self.default_params.update(config or {})
    
    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send chat messages to GPT"""
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
        
        # Merge parameters
        params = {**self.default_params, **kwargs}
        
        # Call API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            **params
        )
        
        # Extract response
        choice = response.choices[0]
        
        return LLMResponse(
            content=choice.message.content,
            role=MessageRole.ASSISTANT,
            finish_reason=choice.finish_reason,
            usage={
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            metadata={'model': self.model}
        )
    
    def chat_completion(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Simple chat completion"""
        messages = []
        
        if system_prompt:
            messages.append(LLMMessage(role=MessageRole.SYSTEM, content=system_prompt))
        
        messages.append(LLMMessage(role=MessageRole.USER, content=prompt))
        
        response = self.chat(messages, **kwargs)
        return response.content

"""
Anthropic Provider for Claude models
"""
from typing import List, Dict, Any, Optional
import os

try:
    from anthropic import Anthropic
    ANTHROPIC_INSTALLED = True
except ImportError:
    ANTHROPIC_INSTALLED = False

from .base import BaseLLMProvider, LLMMessage, LLMResponse, MessageRole

try:
    from src.utils.config_loader import get_anthropic_key, get_anthropic_model
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    CONFIG_LOADER_AVAILABLE = False


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude provider
    
    Supported models:
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229
    - claude-3-haiku-20240307
    """
    
    def __init__(self, model: str = "claude-3-sonnet-20240229",
                 api_key: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize Anthropic provider
        
        Args:
            model: Model name
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            config: Additional configuration
        """
        if not ANTHROPIC_INSTALLED:
            raise ImportError("Anthropic library required. Install with: pip install anthropic")
        
        super().__init__(model, api_key, config)
        
        # Try to get API key in priority order:
        # 1. Passed as parameter
        # 2. Environment variable
        # 3. Config file
        if not self.api_key:
            self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key and CONFIG_LOADER_AVAILABLE:
            self.api_key = get_anthropic_key()
        
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set via:\n"
                "  1. Pass api_key parameter, OR\n"
                "  2. Set ANTHROPIC_API_KEY env var, OR\n"
                "  3. Add to config/api_keys.yaml"
            )
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)
        
        # Default parameters
        self.default_params = {
            'max_tokens': 1000,
            'temperature': 0.7,
        }
        self.default_params.update(config or {})
    
    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send chat messages to Claude"""
        # Separate system message from conversation
        system_msg = None
        conversation = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_msg = msg.content
            else:
                conversation.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        # Merge parameters
        params = {**self.default_params, **kwargs}
        
        # Call API
        if system_msg:
            response = self.client.messages.create(
                model=self.model,
                system=system_msg,
                messages=conversation,
                **params
            )
        else:
            response = self.client.messages.create(
                model=self.model,
                messages=conversation,
                **params
            )
        
        # Extract response
        content = response.content[0].text
        
        return LLMResponse(
            content=content,
            role=MessageRole.ASSISTANT,
            finish_reason=response.stop_reason,
            usage={
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
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

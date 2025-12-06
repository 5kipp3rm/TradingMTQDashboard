"""
Base classes for LLM integration
Provides abstract interface for multiple LLM providers (OpenAI, Anthropic, etc.)
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json


class MessageRole(Enum):
    """Message roles in conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """Single message in conversation"""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    role: MessageRole = MessageRole.ASSISTANT
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None  # tokens used
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers
    
    Supports multiple providers:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Local models (via Ollama, LM Studio)
    """
    
    def __init__(self, model: str, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM provider
        
        Args:
            model: Model name (e.g., 'gpt-4', 'claude-3-opus')
            api_key: API key for provider
            config: Additional configuration
        """
        self.model = model
        self.api_key = api_key
        self.config = config or {}
        self.conversation_history: List[LLMMessage] = []
    
    @abstractmethod
    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """
        Send chat messages and get response
        
        Args:
            messages: Conversation messages
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with completion
        """
        pass
    
    @abstractmethod
    def chat_completion(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Simple chat completion (single turn)
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            **kwargs: Additional parameters
            
        Returns:
            Response text
        """
        pass
    
    def add_message(self, role: MessageRole, content: str) -> None:
        """Add message to conversation history"""
        self.conversation_history.append(
            LLMMessage(role=role, content=content)
        )
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[LLMMessage]:
        """Get conversation history"""
        return self.conversation_history
    
    def extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from LLM response
        Handles markdown code blocks and plain JSON
        """
        # Try to find JSON in markdown code block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None


class LLMFactory:
    """Factory for creating LLM provider instances"""
    
    @staticmethod
    def create(provider: str, model: str, api_key: Optional[str] = None, 
               config: Optional[Dict[str, Any]] = None) -> BaseLLMProvider:
        """
        Create LLM provider instance
        
        Args:
            provider: Provider name ('openai', 'anthropic', 'local')
            model: Model name
            api_key: API key
            config: Additional config
            
        Returns:
            BaseLLMProvider instance
        """
        provider = provider.lower()
        
        if provider == 'openai':
            from .openai_provider import OpenAIProvider
            return OpenAIProvider(model, api_key, config)
        
        elif provider == 'anthropic':
            from .anthropic_provider import AnthropicProvider
            return AnthropicProvider(model, api_key, config)
        
        else:
            raise ValueError(f"Unknown provider: {provider}")

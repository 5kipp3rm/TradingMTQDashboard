"""
LLM Integration Module for TradingMTQ
Provides AI-powered market analysis, sentiment analysis, and natural language interfaces
"""

from .base import BaseLLMProvider, LLMMessage, LLMResponse, MessageRole
from .sentiment import SentimentAnalyzer, SentimentResult
from .market_analyst import MarketAnalyst

# Optional provider imports
try:
    from .openai_provider import OpenAIProvider
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAIProvider = None

try:
    from .anthropic_provider import AnthropicProvider
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AnthropicProvider = None

__all__ = [
    'BaseLLMProvider',
    'LLMMessage',
    'LLMResponse',
    'MessageRole',
    'SentimentAnalyzer',
    'SentimentResult',
    'MarketAnalyst',
    'OpenAIProvider',
    'AnthropicProvider',
    'OPENAI_AVAILABLE',
    'ANTHROPIC_AVAILABLE',
]

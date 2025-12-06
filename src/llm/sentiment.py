"""
Sentiment Analysis using LLMs
Analyzes market news, social media, and reports to generate trading signals
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json

from .base import BaseLLMProvider, MessageRole


class Sentiment(Enum):
    """Sentiment classification"""
    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    sentiment: Sentiment
    confidence: float  # 0.0 to 1.0
    reasoning: str
    key_factors: List[str]
    trading_signal: Optional[str] = None  # BUY, SELL, HOLD
    metadata: Optional[Dict[str, Any]] = None


class SentimentAnalyzer:
    """
    Analyzes market sentiment using LLM
    
    Can analyze:
    - News articles
    - Social media posts
    - Market reports
    - Economic data releases
    """
    
    def __init__(self, llm_provider: BaseLLMProvider):
        """
        Initialize sentiment analyzer
        
        Args:
            llm_provider: LLM provider instance (OpenAI, Anthropic, etc.)
        """
        self.llm = llm_provider
        
        self.system_prompt = """You are an expert financial analyst specializing in market sentiment analysis.
Analyze the provided text and determine the market sentiment for the specified instrument.

Consider:
- Market-moving events and their potential impact
- Tone and language used in the text
- Economic indicators mentioned
- Expert opinions and forecasts
- Technical vs fundamental factors

Respond ONLY with valid JSON in this exact format:
{
    "sentiment": -2 to 2 (very bearish=-2, bearish=-1, neutral=0, bullish=1, very bullish=2),
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of the sentiment",
    "key_factors": ["factor1", "factor2", "factor3"],
    "trading_signal": "BUY" or "SELL" or "HOLD"
}"""
    
    def analyze_text(self, text: str, symbol: str = "market") -> SentimentResult:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze (news, report, etc.)
            symbol: Trading symbol context (e.g., "EURUSD")
            
        Returns:
            SentimentResult with analysis
        """
        prompt = f"""Analyze the market sentiment for {symbol} based on the following text:

{text}

Provide your analysis in JSON format as specified."""
        
        try:
            # Get LLM response
            response = self.llm.chat_completion(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=500
            )
            
            # Parse JSON
            result = self.llm.extract_json(response)
            
            if not result:
                raise ValueError("Failed to parse JSON response")
            
            # Convert to SentimentResult
            sentiment_value = result.get('sentiment', 0)
            sentiment = Sentiment(sentiment_value)
            
            return SentimentResult(
                sentiment=sentiment,
                confidence=result.get('confidence', 0.5),
                reasoning=result.get('reasoning', ''),
                key_factors=result.get('key_factors', []),
                trading_signal=result.get('trading_signal'),
                metadata={'symbol': symbol, 'raw_response': response}
            )
        
        except Exception as e:
            # Fallback to neutral sentiment on error
            return SentimentResult(
                sentiment=Sentiment.NEUTRAL,
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                key_factors=[],
                trading_signal="HOLD",
                metadata={'error': str(e)}
            )
    
    def analyze_multiple(self, texts: List[str], symbol: str = "market") -> SentimentResult:
        """
        Analyze multiple texts and aggregate sentiment
        
        Args:
            texts: List of texts to analyze
            symbol: Trading symbol
            
        Returns:
            Aggregated SentimentResult
        """
        if not texts:
            return SentimentResult(
                sentiment=Sentiment.NEUTRAL,
                confidence=0.0,
                reasoning="No texts provided",
                key_factors=[],
                trading_signal="HOLD"
            )
        
        # Analyze each text
        results = [self.analyze_text(text, symbol) for text in texts]
        
        # Aggregate sentiments
        avg_sentiment = sum(r.sentiment.value for r in results) / len(results)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        # Determine overall sentiment
        if avg_sentiment >= 1.5:
            overall_sentiment = Sentiment.VERY_BULLISH
        elif avg_sentiment >= 0.5:
            overall_sentiment = Sentiment.BULLISH
        elif avg_sentiment <= -1.5:
            overall_sentiment = Sentiment.VERY_BEARISH
        elif avg_sentiment <= -0.5:
            overall_sentiment = Sentiment.BEARISH
        else:
            overall_sentiment = Sentiment.NEUTRAL
        
        # Aggregate key factors
        all_factors = []
        for r in results:
            all_factors.extend(r.key_factors)
        
        # Determine trading signal
        if overall_sentiment.value >= 1:
            signal = "BUY"
        elif overall_sentiment.value <= -1:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        return SentimentResult(
            sentiment=overall_sentiment,
            confidence=avg_confidence,
            reasoning=f"Aggregated from {len(texts)} sources",
            key_factors=list(set(all_factors))[:5],  # Top 5 unique factors
            trading_signal=signal,
            metadata={'num_sources': len(texts)}
        )

"""
AI Market Analyst
Generates comprehensive market analysis reports using LLM
"""
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

from .base import BaseLLMProvider


class MarketAnalyst:
    """
    AI-powered market analyst
    
    Generates:
    - Market analysis reports
    - Trade recommendations
    - Risk assessments
    - Technical + fundamental insights
    """
    
    def __init__(self, llm_provider: BaseLLMProvider):
        """
        Initialize market analyst
        
        Args:
            llm_provider: LLM provider instance
        """
        self.llm = llm_provider
        
        self.system_prompt = """You are a professional forex market analyst with expertise in:
- Technical analysis (indicators, patterns, trends)
- Fundamental analysis (economic data, central bank policy)
- Risk management and position sizing
- Multi-timeframe analysis

Provide clear, actionable analysis that traders can use to make informed decisions.
Always include both bullish and bearish scenarios, key support/resistance levels, and risk factors."""
    
    def analyze_market(self, symbol: str, bars: pd.DataFrame, 
                      additional_context: Optional[str] = None) -> str:
        """
        Generate comprehensive market analysis
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            bars: Recent OHLC data
            additional_context: Optional additional information
            
        Returns:
            Markdown-formatted analysis report
        """
        # Prepare market data summary
        latest = bars.iloc[-1]
        prev = bars.iloc[-2]
        
        price_change = ((latest['close'] - prev['close']) / prev['close']) * 100
        high_5d = bars['high'].tail(5).max()
        low_5d = bars['low'].tail(5).min()
        
        data_summary = f"""Current Market Data for {symbol}:
- Current Price: {latest['close']:.5f}
- 24h Change: {price_change:+.2f}%
- 5-Day High: {high_5d:.5f}
- 5-Day Low: {low_5d:.5f}
- Volume: {latest['volume']}
- Timestamp: {latest.get('timestamp', datetime.now())}
"""
        
        if additional_context:
            data_summary += f"\nAdditional Context:\n{additional_context}"
        
        prompt = f"""{data_summary}

Please provide a comprehensive market analysis for {symbol} including:

1. **Current Market Condition**
   - Overall trend and momentum
   - Key price levels (support/resistance)
   
2. **Technical Analysis**
   - Important indicators and signals
   - Chart patterns if any
   
3. **Trade Setup**
   - Recommended direction (LONG/SHORT/WAIT)
   - Entry price
   - Stop loss level
   - Take profit targets
   - Position size suggestion
   
4. **Risk Factors**
   - Key risks to watch
   - Upcoming events that may impact price
   
5. **Confidence Level**
   - Your confidence in this analysis (0-100%)

Format your response in clear markdown."""
        
        response = self.llm.chat_completion(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.5,
            max_tokens=1500
        )
        
        return response
    
    def explain_trade(self, symbol: str, signal_type: str, price: float,
                     stop_loss: float, take_profit: float) -> str:
        """
        Generate natural language explanation of a trade
        
        Args:
            symbol: Trading symbol
            signal_type: BUY or SELL
            price: Entry price
            stop_loss: SL price
            take_profit: TP price
            
        Returns:
            Human-readable trade explanation
        """
        sl_distance = abs(price - stop_loss)
        tp_distance = abs(take_profit - price)
        risk_reward = tp_distance / sl_distance if sl_distance > 0 else 0
        
        prompt = f"""Explain this forex trade in simple terms that a beginner trader would understand:

**Trade Details:**
- Symbol: {symbol}
- Direction: {signal_type}
- Entry Price: {price:.5f}
- Stop Loss: {stop_loss:.5f}
- Take Profit: {take_profit:.5f}
- Risk/Reward Ratio: {risk_reward:.2f}

Provide a brief, clear explanation of:
1. What this trade is doing
2. Why the stop loss and take profit are positioned there
3. What the risk/reward ratio means for this trade
4. One key thing to watch while the trade is active

Keep it concise (3-4 sentences)."""
        
        response = self.llm.chat_completion(
            prompt=prompt,
            system_prompt="You are a patient trading educator. Explain trades clearly and simply.",
            temperature=0.7,
            max_tokens=300
        )
        
        return response
    
    def generate_daily_summary(self, trades_executed: int, win_rate: float,
                              total_pnl: float, open_positions: int) -> str:
        """
        Generate end-of-day trading summary
        
        Args:
            trades_executed: Number of trades today
            win_rate: Win rate percentage
            total_pnl: Total profit/loss
            open_positions: Number of open positions
            
        Returns:
            Daily summary report
        """
        prompt = f"""Generate a brief daily trading summary based on these statistics:

**Today's Performance:**
- Trades Executed: {trades_executed}
- Win Rate: {win_rate:.1f}%
- Total P/L: ${total_pnl:.2f}
- Open Positions: {open_positions}

Provide:
1. Brief performance assessment (1-2 sentences)
2. One strength observed today
3. One area for improvement
4. Outlook for tomorrow (bullish/bearish/cautious)

Keep it professional but encouraging. Format in markdown."""
        
        response = self.llm.chat_completion(
            prompt=prompt,
            system_prompt="You are a trading performance analyst. Provide constructive feedback.",
            temperature=0.6,
            max_tokens=400
        )
        
        return response

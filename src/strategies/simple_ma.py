"""
Simple Moving Average Crossover Strategy
Buy when fast MA crosses above slow MA
Sell when fast MA crosses below slow MA
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType
from ..connectors.base import OHLCBar


class SimpleMovingAverageStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy
    
    Parameters:
        fast_period: Fast MA period (default: 10)
        slow_period: Slow MA period (default: 20)
        sl_pips: Stop loss in pips (default: 20)
        tp_pips: Take profit in pips (default: 40)
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize strategy"""
        default_params = {
            'fast_period': 10,
            'slow_period': 20,
            'sl_pips': 20,
            'tp_pips': 40,
        }
        if params:
            default_params.update(params)
        
        super().__init__("Simple MA Crossover", default_params)
        
        self.last_signal = None
        self.last_fast_ma = None
        self.last_slow_ma = None
    
    def calculate_sma(self, bars: List[OHLCBar], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(bars) < period:
            return 0.0
        
        closes = [bar.close for bar in bars[-period:]]
        return sum(closes) / period
    
    def analyze(self, symbol: str, timeframe: str, bars: List[OHLCBar]) -> Signal:
        """
        Analyze market data and generate signal
        
        Strategy logic:
        - BUY: Fast MA crosses above Slow MA (bullish crossover)
        - SELL: Fast MA crosses below Slow MA (bearish crossover)
        - HOLD: No crossover detected
        """
        if not self.enabled:
            return Signal(
                type=SignalType.HOLD,
                symbol=symbol,
                timestamp=datetime.now(),
                price=bars[-1].close,
                confidence=0.0,
                reason="Strategy disabled"
            )
        
        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']
        
        # Need enough bars for calculation
        if len(bars) < slow_period:
            return Signal(
                type=SignalType.HOLD,
                symbol=symbol,
                timestamp=bars[-1].time,
                price=bars[-1].close,
                confidence=0.0,
                reason=f"Insufficient data (need {slow_period} bars)"
            )
        
        # Calculate MAs
        fast_ma = self.calculate_sma(bars, fast_period)
        slow_ma = self.calculate_sma(bars, slow_period)
        
        current_price = bars[-1].close
        pip_value = 0.0001  # For most forex pairs
        
        # Detect crossover
        signal_type = SignalType.HOLD
        reason = "No crossover"
        confidence = 0.0
        
        if self.last_fast_ma is not None and self.last_slow_ma is not None:
            # Bullish crossover: Fast MA crosses above Slow MA
            if self.last_fast_ma <= self.last_slow_ma and fast_ma > slow_ma:
                signal_type = SignalType.BUY
                reason = f"Bullish crossover (Fast MA {fast_ma:.5f} > Slow MA {slow_ma:.5f})"
                confidence = min((fast_ma - slow_ma) / slow_ma * 100, 1.0)
            
            # Bearish crossover: Fast MA crosses below Slow MA
            elif self.last_fast_ma >= self.last_slow_ma and fast_ma < slow_ma:
                signal_type = SignalType.SELL
                reason = f"Bearish crossover (Fast MA {fast_ma:.5f} < Slow MA {slow_ma:.5f})"
                confidence = min((slow_ma - fast_ma) / slow_ma * 100, 1.0)
        
        # Store current MAs for next iteration
        self.last_fast_ma = fast_ma
        self.last_slow_ma = slow_ma
        
        # Calculate SL/TP
        sl = None
        tp = None
        
        if signal_type == SignalType.BUY:
            sl = current_price - (self.params['sl_pips'] * pip_value)
            tp = current_price + (self.params['tp_pips'] * pip_value)
        elif signal_type == SignalType.SELL:
            sl = current_price + (self.params['sl_pips'] * pip_value)
            tp = current_price - (self.params['tp_pips'] * pip_value)
        
        signal = Signal(
            type=signal_type,
            symbol=symbol,
            timestamp=bars[-1].time,
            price=current_price,
            confidence=confidence,
            stop_loss=sl,
            take_profit=tp,
            reason=reason,
            metadata={
                'fast_ma': fast_ma,
                'slow_ma': slow_ma,
                'fast_period': fast_period,
                'slow_period': slow_period,
            }
        )
        
        self.last_signal = signal
        return signal

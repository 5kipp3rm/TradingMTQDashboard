"""
RSI Strategy
Mean reversion strategy based on RSI oversold/overbought levels
"""
from typing import List, Optional
import numpy as np
from .base import BaseStrategy, Signal, SignalType
from ..connectors.base import OHLCBar
from ..indicators.momentum import RSI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RSIStrategy(BaseStrategy):
    """
    RSI Mean Reversion Strategy
    
    Entry Signals:
    - BUY: RSI crosses above oversold level (default 30)
    - SELL: RSI crosses below overbought level (default 70)
    
    Exit Signals:
    - Take profit when RSI reaches opposite extreme
    - Stop loss based on ATR
    """
    
    def __init__(self, symbol: str, timeframe: str = 'M5',
                 rsi_period: int = 14, oversold: float = 30, overbought: float = 70,
                 sl_atr_multiplier: float = 2.0, tp_rsi_target: float = 50):
        """
        Initialize RSI strategy
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            rsi_period: RSI calculation period
            oversold: Oversold threshold (buy signal)
            overbought: Overbought threshold (sell signal)
            sl_atr_multiplier: Stop loss as multiple of ATR
            tp_rsi_target: Take profit when RSI reaches this level
        """
        super().__init__(
            name=f"RSI_{rsi_period}_{oversold}_{overbought}"
        )
        
        self.symbol = symbol
        self.timeframe = timeframe
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.sl_atr_multiplier = sl_atr_multiplier
        self.tp_rsi_target = tp_rsi_target
        
        self.rsi_indicator = RSI(period=rsi_period, overbought=overbought, oversold=oversold)
    
    def analyze(self, bars: List[OHLCBar]) -> Optional[Signal]:
        """
        Analyze bars and generate trading signal
        
        Args:
            bars: List of OHLC bars
            
        Returns:
            Signal or None
        """
        if not self.enabled:
            return None
        
        if len(bars) < self.rsi_period + 1:
            logger.debug(f"[{self.name}] Insufficient data: {len(bars)} bars")
            return None
        
        # Extract close prices
        closes = np.array([bar.close for bar in bars])
        
        # Calculate RSI
        rsi_result = self.rsi_indicator.calculate(closes)
        rsi_values = rsi_result.values
        rsi_signals = rsi_result.signals
        
        # Check latest signal
        current_rsi = rsi_values[-1]
        if np.isnan(current_rsi):
            return None
        
        # Get signal from indicator
        latest_signal = rsi_signals[-1]
        
        if latest_signal == 0:
            return None
        
        current_price = bars[-1].close
        
        # Calculate ATR for stop loss
        highs = np.array([bar.high for bar in bars])
        lows = np.array([bar.low for bar in bars])
        
        # Simple ATR calculation
        tr = []
        for i in range(1, len(bars)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr.append(max(hl, hc, lc))
        
        atr = np.mean(tr[-14:]) if len(tr) >= 14 else (current_price * 0.001)  # Default to 0.1%
        
        # Generate signal
        if latest_signal == 1:  # Bullish - RSI crossed above oversold
            sl = current_price - (self.sl_atr_multiplier * atr)
            tp = current_price + (self.sl_atr_multiplier * atr * 1.5)  # 1.5:1 R:R
            
            return Signal(
                type=SignalType.BUY,
                symbol=self.symbol,
                timestamp=bars[-1].time,
                price=current_price,
                stop_loss=sl,
                take_profit=tp,
                confidence=self._calculate_confidence(current_rsi, "BUY"),
                reason=f"RSI crossed above {self.oversold} (current: {current_rsi:.1f})"
            )
        
        elif latest_signal == -1:  # Bearish - RSI crossed below overbought
            sl = current_price + (self.sl_atr_multiplier * atr)
            tp = current_price - (self.sl_atr_multiplier * atr * 1.5)  # 1.5:1 R:R
            
            return Signal(
                type=SignalType.SELL,
                symbol=self.symbol,
                timestamp=bars[-1].time,
                price=current_price,
                stop_loss=sl,
                take_profit=tp,
                confidence=self._calculate_confidence(current_rsi, "SELL"),
                reason=f"RSI crossed below {self.overbought} (current: {current_rsi:.1f})"
            )
        
        return None
    
    def _calculate_confidence(self, rsi: float, direction: str) -> float:
        """
        Calculate signal confidence based on RSI distance from extreme
        
        Args:
            rsi: Current RSI value
            direction: "BUY" or "SELL"
            
        Returns:
            Confidence score 0-1
        """
        if direction == "BUY":
            # More confident when RSI is deeper in oversold
            distance = max(0, self.oversold - rsi)
            max_distance = self.oversold
            confidence = 0.5 + (distance / max_distance * 0.5)
        else:  # SELL
            # More confident when RSI is deeper in overbought
            distance = max(0, rsi - self.overbought)
            max_distance = 100 - self.overbought
            confidence = 0.5 + (distance / max_distance * 0.5)
        
        return min(1.0, max(0.5, confidence))

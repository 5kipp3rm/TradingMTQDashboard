"""
MACD Strategy
Trend-following strategy based on MACD crossovers
"""
from typing import List, Optional
import numpy as np
from .base import BaseStrategy, Signal, SignalType
from ..connectors.base import OHLCBar
from ..indicators.trend import MACD
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MACDStrategy(BaseStrategy):
    """
    MACD Crossover Strategy
    
    Entry Signals:
    - BUY: MACD histogram crosses above zero (bullish momentum)
    - SELL: MACD histogram crosses below zero (bearish momentum)
    
    Additional confirmation: Check if MACD line is above/below signal line
    """
    
    def __init__(self, symbol: str, timeframe: str = 'M5',
                 fast_period: int = 12, slow_period: int = 26, signal_period: int = 9,
                 sl_pips: int = 20, tp_pips: int = 40):
        """
        Initialize MACD strategy
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            sl_pips: Stop loss in pips
            tp_pips: Take profit in pips
        """
        super().__init__(
            name=f"MACD_{fast_period}_{slow_period}_{signal_period}"
        )
        
        self.symbol = symbol
        self.timeframe = timeframe
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.sl_pips = sl_pips
        self.tp_pips = tp_pips
        
        self.macd_indicator = MACD(fast_period, slow_period, signal_period)
    
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
        
        min_bars = self.slow_period + self.signal_period + 5
        if len(bars) < min_bars:
            logger.debug(f"[{self.name}] Insufficient data: {len(bars)} bars")
            return None
        
        # Extract close prices
        closes = np.array([bar.close for bar in bars])
        
        # Calculate MACD
        macd_result = self.macd_indicator.calculate(closes)
        macd_line = macd_result.values
        signals = macd_result.signals
        histogram = macd_result.metadata['histogram']
        signal_line = macd_result.metadata['signal_line']
        
        # Check latest signal
        latest_signal = signals[-1]
        
        if latest_signal == 0:
            return None
        
        current_price = bars[-1].close
        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        current_histogram = histogram[-1]
        
        if np.isnan(current_histogram):
            return None
        
        # Calculate SL/TP
        pip_value = 0.0001 if 'JPY' not in self.symbol else 0.01
        
        # Generate signal
        if latest_signal == 1:  # Bullish crossover
            sl = current_price - (self.sl_pips * pip_value)
            tp = current_price + (self.tp_pips * pip_value)
            
            # Calculate confidence based on histogram strength
            confidence = self._calculate_confidence(current_histogram, histogram[-5:], "BUY")
            
            return Signal(
                type=SignalType.BUY,
                symbol=self.symbol,
                timestamp=bars[-1].time,
                price=current_price,
                stop_loss=sl,
                take_profit=tp,
                confidence=confidence,
                reason=f"MACD bullish crossover (Histogram: {current_histogram:.5f})"
            )
        
        elif latest_signal == -1:  # Bearish crossover
            sl = current_price + (self.sl_pips * pip_value)
            tp = current_price - (self.tp_pips * pip_value)
            
            # Calculate confidence based on histogram strength
            confidence = self._calculate_confidence(current_histogram, histogram[-5:], "SELL")
            
            return Signal(
                type=SignalType.SELL,
                symbol=self.symbol,
                timestamp=bars[-1].time,
                price=current_price,
                stop_loss=sl,
                take_profit=tp,
                confidence=confidence,
                reason=f"MACD bearish crossover (Histogram: {current_histogram:.5f})"
            )
        
        return None
    
    def _calculate_confidence(self, current_hist: float, recent_hist: np.ndarray, direction: str) -> float:
        """
        Calculate confidence based on histogram strength and momentum
        
        Args:
            current_hist: Current histogram value
            recent_hist: Recent histogram values
            direction: "BUY" or "SELL"
            
        Returns:
            Confidence score 0-1
        """
        # Filter out NaN values
        recent_hist = recent_hist[~np.isnan(recent_hist)]
        
        if len(recent_hist) < 2:
            return 0.6
        
        # Check momentum (is histogram accelerating?)
        momentum = current_hist - recent_hist[-2]
        
        if direction == "BUY":
            # Higher confidence if momentum is strongly positive
            strength = abs(current_hist)
            momentum_factor = 1.0 if momentum > 0 else 0.8
        else:  # SELL
            # Higher confidence if momentum is strongly negative
            strength = abs(current_hist)
            momentum_factor = 1.0 if momentum < 0 else 0.8
        
        # Base confidence from strength
        base_confidence = min(0.9, 0.6 + (strength * 1000))  # Scale factor
        
        return base_confidence * momentum_factor

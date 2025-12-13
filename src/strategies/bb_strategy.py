"""
Bollinger Bands Strategy
Mean reversion strategy using Bollinger Bands
"""
from typing import List, Optional
import numpy as np
from .base import BaseStrategy, Signal, SignalType
from ..connectors.base import OHLCBar
from ..indicators.volatility import BollingerBands
from ..indicators.momentum import RSI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands Mean Reversion Strategy
    
    Entry Signals:
    - BUY: Price touches or crosses below lower band + RSI oversold confirmation
    - SELL: Price touches or crosses above upper band + RSI overbought confirmation
    
    Uses RSI as confirmation to avoid false signals
    """
    
    def __init__(self, symbol: str, timeframe: str = 'M5',
                 bb_period: int = 20, bb_std: float = 2.0,
                 rsi_period: int = 14, rsi_oversold: float = 35, rsi_overbought: float = 65,
                 sl_multiplier: float = 1.5, tp_multiplier: float = 2.5):
        """
        Initialize Bollinger Bands strategy
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            bb_period: Bollinger Bands period
            bb_std: Number of standard deviations
            rsi_period: RSI period for confirmation
            rsi_oversold: RSI oversold level
            rsi_overbought: RSI overbought level
            sl_multiplier: Stop loss as multiplier of band width
            tp_multiplier: Take profit as multiplier of band width
        """
        super().__init__(
            name=f"BB_{bb_period}_{bb_std}_RSI_{rsi_period}"
        )
        
        self.symbol = symbol
        self.timeframe = timeframe
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.sl_multiplier = sl_multiplier
        self.tp_multiplier = tp_multiplier
        
        self.bb_indicator = BollingerBands(period=bb_period, std_dev=bb_std)
        self.rsi_indicator = RSI(period=rsi_period, overbought=rsi_overbought, oversold=rsi_oversold)
    
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
        
        min_bars = max(self.bb_period, self.rsi_period) + 5
        if len(bars) < min_bars:
            logger.debug(f"[{self.name}] Insufficient data: {len(bars)} bars")
            return None
        
        # Extract close prices
        closes = np.array([bar.close for bar in bars])
        
        # Calculate Bollinger Bands
        bb_result = self.bb_indicator.calculate(closes)
        middle_band = bb_result.values
        upper_band = bb_result.metadata['upper_band']
        lower_band = bb_result.metadata['lower_band']
        
        # Calculate RSI for confirmation
        rsi_result = self.rsi_indicator.calculate(closes)
        rsi_values = rsi_result.values
        
        # Get current values
        current_price = bars[-1].close
        current_middle = middle_band[-1]
        current_upper = upper_band[-1]
        current_lower = lower_band[-1]
        current_rsi = rsi_values[-1]
        
        prev_price = bars[-2].close
        prev_lower = lower_band[-2]
        prev_upper = upper_band[-2]
        
        if np.isnan(current_middle) or np.isnan(current_rsi):
            return None
        
        # Calculate band width for SL/TP
        band_width = current_upper - current_lower
        
        # Check for signals
        signal = None
        
        # BUY: Price touches lower band and RSI is oversold
        if (prev_price > prev_lower and current_price <= current_lower) and current_rsi < self.rsi_oversold:
            sl = current_price - (band_width * self.sl_multiplier * 0.5)
            tp = current_middle + (band_width * 0.3)  # Target middle band
            
            confidence = self._calculate_confidence(current_price, current_lower, current_middle, current_rsi, "BUY")
            
            signal = Signal(
                type=SignalType.BUY,
                symbol=self.symbol,
                timestamp=bars[-1].time,
                price=current_price,
                stop_loss=sl,
                take_profit=tp,
                confidence=confidence,
                reason=f"Price touched lower BB ({current_price:.5f}) + RSI oversold ({current_rsi:.1f})"
            )
        
        # SELL: Price touches upper band and RSI is overbought
        elif (prev_price < prev_upper and current_price >= current_upper) and current_rsi > self.rsi_overbought:
            sl = current_price + (band_width * self.sl_multiplier * 0.5)
            tp = current_middle - (band_width * 0.3)  # Target middle band
            
            confidence = self._calculate_confidence(current_price, current_upper, current_middle, current_rsi, "SELL")
            
            signal = Signal(
                type=SignalType.SELL,
                symbol=self.symbol,
                timestamp=bars[-1].time,
                price=current_price,
                stop_loss=sl,
                take_profit=tp,
                confidence=confidence,
                reason=f"Price touched upper BB ({current_price:.5f}) + RSI overbought ({current_rsi:.1f})"
            )
        
        return signal
    
    def _calculate_confidence(self, price: float, band: float, middle: float, rsi: float, direction: str) -> float:
        """
        Calculate confidence based on:
        - How far price penetrated the band
        - RSI extremity
        - Distance to middle band (mean reversion potential)
        
        Args:
            price: Current price
            band: Band level (upper or lower)
            middle: Middle band level
            rsi: Current RSI
            direction: "BUY" or "SELL"
            
        Returns:
            Confidence score 0-1
        """
        # Distance beyond band (penetration)
        if direction == "BUY":
            penetration = max(0, (band - price) / price)
            rsi_extreme = max(0, self.rsi_oversold - rsi) / self.rsi_oversold
        else:  # SELL
            penetration = max(0, (price - band) / price)
            rsi_extreme = max(0, rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
        
        # Mean reversion potential (distance to middle)
        reversion_potential = abs(price - middle) / price
        
        # Combine factors
        confidence = 0.5 + (penetration * 100) + (rsi_extreme * 0.3) + (reversion_potential * 50)
        
        return min(0.95, max(0.6, confidence))

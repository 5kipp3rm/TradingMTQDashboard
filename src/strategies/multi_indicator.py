"""
Multi-Indicator Strategy
Combines multiple indicators for confirmation
"""
from typing import List, Optional
import numpy as np
from .base import BaseStrategy, Signal, SignalType
from ..connectors.base import OHLCBar
from ..indicators.trend import MACD, EMA
from ..indicators.momentum import RSI, Stochastic
from ..indicators.volatility import BollingerBands
import logging

logger = logging.getLogger(__name__)


class MultiIndicatorStrategy(BaseStrategy):
    """
    Multi-Indicator Confirmation Strategy
    
    Requires agreement from multiple indicators before generating signal:
    - MACD: Trend direction
    - RSI: Momentum confirmation
    - Stochastic: Overbought/oversold
    - EMA: Trend filter
    
    More conservative but higher probability trades
    """
    
    def __init__(self, symbol: str, timeframe: str = 'M5',
                 ema_period: int = 50, min_confirmations: int = 3,
                 sl_pips: int = 25, tp_pips: int = 50):
        """
        Initialize Multi-Indicator strategy
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            ema_period: EMA period for trend filter
            min_confirmations: Minimum number of indicator confirmations needed
            sl_pips: Stop loss in pips
            tp_pips: Take profit in pips
        """
        super().__init__(
            name=f"MultiIndicator_{min_confirmations}conf",
            symbol=symbol,
            timeframe=timeframe
        )
        
        self.ema_period = ema_period
        self.min_confirmations = min_confirmations
        self.sl_pips = sl_pips
        self.tp_pips = tp_pips
        
        # Initialize indicators
        self.macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        self.rsi = RSI(period=14, overbought=70, oversold=30)
        self.stoch = Stochastic(k_period=14, d_period=3, smooth=3)
        self.ema = EMA(period=ema_period)
        self.bb = BollingerBands(period=20, std_dev=2.0)
    
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
        
        if len(bars) < self.ema_period + 30:
            logger.debug(f"[{self.name}] Insufficient data: {len(bars)} bars")
            return None
        
        # Extract price data
        closes = np.array([bar.close for bar in bars])
        highs = np.array([bar.high for bar in bars])
        lows = np.array([bar.low for bar in bars])
        
        # Calculate all indicators
        macd_result = self.macd.calculate(closes)
        rsi_result = self.rsi.calculate(closes)
        stoch_result = self.stoch.calculate(closes, highs, lows)
        ema_result = self.ema.calculate(closes)
        bb_result = self.bb.calculate(closes)
        
        # Get current values
        current_price = bars[-1].close
        current_ema = ema_result.values[-1]
        current_rsi = rsi_result.values[-1]
        current_stoch_k = stoch_result.values[-1]
        current_macd_hist = macd_result.metadata['histogram'][-1]
        current_bb_upper = bb_result.metadata['upper_band'][-1]
        current_bb_lower = bb_result.metadata['lower_band'][-1]
        
        # Check if we have valid data
        if any(np.isnan(v) for v in [current_ema, current_rsi, current_stoch_k, current_macd_hist]):
            return None
        
        # Count bullish and bearish confirmations
        bullish_signals = 0
        bearish_signals = 0
        confirmations = []
        
        # 1. MACD Histogram
        if current_macd_hist > 0:
            bullish_signals += 1
            confirmations.append("MACD bullish")
        elif current_macd_hist < 0:
            bearish_signals += 1
            confirmations.append("MACD bearish")
        
        # 2. RSI
        if current_rsi < 40:  # Oversold area
            bullish_signals += 1
            confirmations.append(f"RSI oversold ({current_rsi:.1f})")
        elif current_rsi > 60:  # Overbought area
            bearish_signals += 1
            confirmations.append(f"RSI overbought ({current_rsi:.1f})")
        
        # 3. Stochastic
        if current_stoch_k < 20:  # Oversold
            bullish_signals += 1
            confirmations.append(f"Stoch oversold ({current_stoch_k:.1f})")
        elif current_stoch_k > 80:  # Overbought
            bearish_signals += 1
            confirmations.append(f"Stoch overbought ({current_stoch_k:.1f})")
        
        # 4. EMA Trend Filter
        if current_price > current_ema:
            bullish_signals += 1
            confirmations.append("Price > EMA (uptrend)")
        elif current_price < current_ema:
            bearish_signals += 1
            confirmations.append("Price < EMA (downtrend)")
        
        # 5. Bollinger Bands
        if current_price <= current_bb_lower:
            bullish_signals += 1
            confirmations.append("Price at lower BB")
        elif current_price >= current_bb_upper:
            bearish_signals += 1
            confirmations.append("Price at upper BB")
        
        # Calculate pip value
        pip_value = 0.0001 if 'JPY' not in self.symbol else 0.01
        
        # Generate signal if we have enough confirmations
        if bullish_signals >= self.min_confirmations and bullish_signals > bearish_signals:
            sl = current_price - (self.sl_pips * pip_value)
            tp = current_price + (self.tp_pips * pip_value)
            
            confidence = min(0.95, 0.5 + (bullish_signals * 0.1))
            reason = f"{bullish_signals} bullish signals: " + ", ".join(confirmations[:3])
            
            return Signal(
                signal_type=SignalType.BUY,
                symbol=self.symbol,
                price=current_price,
                sl=sl,
                tp=tp,
                confidence=confidence,
                reason=reason
            )
        
        elif bearish_signals >= self.min_confirmations and bearish_signals > bullish_signals:
            sl = current_price + (self.sl_pips * pip_value)
            tp = current_price - (self.tp_pips * pip_value)
            
            confidence = min(0.95, 0.5 + (bearish_signals * 0.1))
            reason = f"{bearish_signals} bearish signals: " + ", ".join(confirmations[:3])
            
            return Signal(
                signal_type=SignalType.SELL,
                symbol=self.symbol,
                price=current_price,
                sl=sl,
                tp=tp,
                confidence=confidence,
                reason=reason
            )
        
        return None

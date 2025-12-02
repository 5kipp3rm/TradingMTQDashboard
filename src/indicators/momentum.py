"""
Momentum Indicators
RSI, Stochastic, etc.
"""
import numpy as np
from .base import BaseIndicator, IndicatorResult


class RSI(BaseIndicator):
    """Relative Strength Index"""
    
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        """
        Initialize RSI
        
        Args:
            period: Number of periods for RSI
            overbought: Overbought threshold (default 70)
            oversold: Oversold threshold (default 30)
        """
        super().__init__(f"RSI_{period}")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate(self, data: np.ndarray, **kwargs) -> IndicatorResult:
        """
        Calculate RSI
        
        Args:
            data: Close prices
            
        Returns:
            IndicatorResult with RSI values and signals
        """
        if not self.validate_data(data, self.period + 1):
            return IndicatorResult(values=np.array([]))
        
        # Calculate price changes
        deltas = np.diff(data)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate initial averages using SMA
        avg_gain = np.zeros(len(gains))
        avg_loss = np.zeros(len(losses))
        
        # Initial average
        avg_gain[self.period - 1] = np.mean(gains[:self.period])
        avg_loss[self.period - 1] = np.mean(losses[:self.period])
        
        # Calculate smoothed averages (Wilder's smoothing)
        for i in range(self.period, len(gains)):
            avg_gain[i] = (avg_gain[i - 1] * (self.period - 1) + gains[i]) / self.period
            avg_loss[i] = (avg_loss[i - 1] * (self.period - 1) + losses[i]) / self.period
        
        # Calculate RS and RSI
        rs = np.zeros_like(avg_gain)
        rsi = np.zeros_like(avg_gain)
        
        for i in range(len(rs)):
            if avg_loss[i] != 0:
                rs[i] = avg_gain[i] / avg_loss[i]
                rsi[i] = 100 - (100 / (1 + rs[i]))
            else:
                rsi[i] = 100 if avg_gain[i] > 0 else 50
        
        # Pad to match input length
        rsi_padded = np.full(len(data), np.nan)
        rsi_padded[self.period:] = rsi[self.period - 1:]
        
        # Generate signals
        signals = np.zeros_like(rsi_padded)
        for i in range(1, len(rsi_padded)):
            if not np.isnan(rsi_padded[i]) and not np.isnan(rsi_padded[i-1]):
                # Oversold to neutral (bullish)
                if rsi_padded[i-1] <= self.oversold and rsi_padded[i] > self.oversold:
                    signals[i] = 1
                # Overbought to neutral (bearish)
                elif rsi_padded[i-1] >= self.overbought and rsi_padded[i] < self.overbought:
                    signals[i] = -1
        
        return IndicatorResult(
            values=rsi_padded,
            signals=signals,
            metadata={
                'overbought': self.overbought,
                'oversold': self.oversold
            }
        )


class Stochastic(BaseIndicator):
    """Stochastic Oscillator"""
    
    def __init__(self, k_period: int = 14, d_period: int = 3, smooth: int = 3):
        """
        Initialize Stochastic
        
        Args:
            k_period: %K period
            d_period: %D period (SMA of %K)
            smooth: Smoothing period for %K
        """
        super().__init__(f"STOCH_{k_period}_{d_period}_{smooth}")
        self.k_period = k_period
        self.d_period = d_period
        self.smooth = smooth
    
    def calculate(self, data: np.ndarray, high: np.ndarray = None, 
                  low: np.ndarray = None, **kwargs) -> IndicatorResult:
        """
        Calculate Stochastic Oscillator
        
        Args:
            data: Close prices
            high: High prices (if None, use close)
            low: Low prices (if None, use close)
            
        Returns:
            IndicatorResult with %K, %D values and signals
        """
        if not self.validate_data(data, self.k_period + self.d_period):
            return IndicatorResult(values=np.array([]))
        
        # Use close prices if high/low not provided
        if high is None:
            high = data
        if low is None:
            low = data
        
        # Calculate %K
        k_values = np.full(len(data), np.nan)
        
        for i in range(self.k_period - 1, len(data)):
            period_high = np.max(high[i - self.k_period + 1:i + 1])
            period_low = np.min(low[i - self.k_period + 1:i + 1])
            
            if period_high != period_low:
                k_values[i] = 100 * (data[i] - period_low) / (period_high - period_low)
            else:
                k_values[i] = 50
        
        # Smooth %K if smooth > 1
        if self.smooth > 1:
            k_smoothed = np.full_like(k_values, np.nan)
            for i in range(self.k_period + self.smooth - 2, len(k_values)):
                k_smoothed[i] = np.nanmean(k_values[i - self.smooth + 1:i + 1])
            k_values = k_smoothed
        
        # Calculate %D (SMA of %K)
        d_values = np.full_like(k_values, np.nan)
        for i in range(self.k_period + self.d_period - 2, len(k_values)):
            d_values[i] = np.nanmean(k_values[i - self.d_period + 1:i + 1])
        
        # Generate signals (1 = bullish crossover, -1 = bearish crossover)
        signals = np.zeros_like(k_values)
        for i in range(1, len(k_values)):
            if not np.isnan(k_values[i]) and not np.isnan(d_values[i]):
                # Bullish crossover: %K crosses above %D
                if k_values[i-1] <= d_values[i-1] and k_values[i] > d_values[i]:
                    signals[i] = 1
                # Bearish crossover: %K crosses below %D
                elif k_values[i-1] >= d_values[i-1] and k_values[i] < d_values[i]:
                    signals[i] = -1
        
        return IndicatorResult(
            values=k_values,
            signals=signals,
            metadata={'d_values': d_values}
        )

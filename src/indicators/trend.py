"""
Trend Indicators
SMA, EMA, MACD, etc.
"""
import numpy as np
from typing import Optional
from .base import BaseIndicator, IndicatorResult


class SMA(BaseIndicator):
    """Simple Moving Average"""
    
    def __init__(self, period: int = 20):
        """
        Initialize SMA
        
        Args:
            period: Number of periods for average
        """
        super().__init__(f"SMA_{period}")
        self.period = period
    
    def calculate(self, data: np.ndarray, **kwargs) -> IndicatorResult:
        """
        Calculate Simple Moving Average
        
        Args:
            data: Close prices
            
        Returns:
            IndicatorResult with SMA values
        """
        if not self.validate_data(data, self.period):
            return IndicatorResult(values=np.array([]))
        
        # Calculate SMA using convolution for efficiency
        sma = np.convolve(data, np.ones(self.period), 'valid') / self.period
        
        # Pad with NaN to match input length
        padded = np.full(len(data), np.nan)
        padded[self.period - 1:] = sma
        
        return IndicatorResult(values=padded)


class EMA(BaseIndicator):
    """Exponential Moving Average"""
    
    def __init__(self, period: int = 20):
        """
        Initialize EMA
        
        Args:
            period: Number of periods for average
        """
        super().__init__(f"EMA_{period}")
        self.period = period
        self.alpha = 2 / (period + 1)
    
    def calculate(self, data: np.ndarray, **kwargs) -> IndicatorResult:
        """
        Calculate Exponential Moving Average
        
        Args:
            data: Close prices
            
        Returns:
            IndicatorResult with EMA values
        """
        if not self.validate_data(data, self.period):
            return IndicatorResult(values=np.array([]))
        
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = self.alpha * data[i] + (1 - self.alpha) * ema[i - 1]
        
        # Set initial values to NaN
        ema[:self.period - 1] = np.nan
        
        return IndicatorResult(values=ema)


class MACD(BaseIndicator):
    """Moving Average Convergence Divergence"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        Initialize MACD
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
        """
        super().__init__(f"MACD_{fast_period}_{slow_period}_{signal_period}")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        self.fast_ema = EMA(fast_period)
        self.slow_ema = EMA(slow_period)
        self.signal_ema = EMA(signal_period)
    
    def calculate(self, data: np.ndarray, **kwargs) -> IndicatorResult:
        """
        Calculate MACD, Signal, and Histogram
        
        Args:
            data: Close prices
            
        Returns:
            IndicatorResult with MACD line, signal line, and histogram
        """
        if not self.validate_data(data, self.slow_period + self.signal_period):
            return IndicatorResult(values=np.array([]))
        
        # Calculate fast and slow EMAs
        fast = self.fast_ema.calculate(data).values
        slow = self.slow_ema.calculate(data).values
        
        # MACD line = fast EMA - slow EMA
        macd_line = fast - slow
        
        # Signal line = EMA of MACD line
        # Remove NaN values for signal calculation
        valid_idx = ~np.isnan(macd_line)
        signal_line = np.full_like(macd_line, np.nan)
        
        if np.sum(valid_idx) >= self.signal_period:
            valid_macd = macd_line[valid_idx]
            signal_values = self.signal_ema.calculate(valid_macd).values
            signal_line[valid_idx] = signal_values
        
        # Histogram = MACD - Signal
        histogram = macd_line - signal_line
        
        # Generate signals (1 = bullish crossover, -1 = bearish crossover)
        signals = np.zeros_like(histogram)
        for i in range(1, len(histogram)):
            if not np.isnan(histogram[i]) and not np.isnan(histogram[i-1]):
                # Bullish crossover: histogram crosses above zero
                if histogram[i-1] <= 0 and histogram[i] > 0:
                    signals[i] = 1
                # Bearish crossover: histogram crosses below zero
                elif histogram[i-1] >= 0 and histogram[i] < 0:
                    signals[i] = -1
        
        return IndicatorResult(
            values=macd_line,
            signals=signals,
            metadata={
                'signal_line': signal_line,
                'histogram': histogram
            }
        )

"""
Volatility Indicators
Bollinger Bands, ATR, etc.
"""
import numpy as np
from .base import BaseIndicator, IndicatorResult
from .trend import SMA


class BollingerBands(BaseIndicator):
    """Bollinger Bands"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        Initialize Bollinger Bands
        
        Args:
            period: Period for moving average
            std_dev: Number of standard deviations
        """
        super().__init__(f"BB_{period}_{std_dev}")
        self.period = period
        self.std_dev = std_dev
        self.sma = SMA(period)
    
    def calculate(self, data: np.ndarray, **kwargs) -> IndicatorResult:
        """
        Calculate Bollinger Bands
        
        Args:
            data: Close prices
            
        Returns:
            IndicatorResult with middle, upper, and lower bands
        """
        if not self.validate_data(data, self.period):
            return IndicatorResult(values=np.array([]))
        
        # Calculate middle band (SMA)
        middle_band = self.sma.calculate(data).values
        
        # Calculate standard deviation
        std = np.full(len(data), np.nan)
        for i in range(self.period - 1, len(data)):
            std[i] = np.std(data[i - self.period + 1:i + 1])
        
        # Calculate upper and lower bands
        upper_band = middle_band + (self.std_dev * std)
        lower_band = middle_band - (self.std_dev * std)
        
        # Calculate bandwidth for reference
        bandwidth = (upper_band - lower_band) / middle_band * 100
        
        # Generate signals
        signals = np.zeros_like(data)
        for i in range(1, len(data)):
            if not np.isnan(upper_band[i]) and not np.isnan(lower_band[i]):
                # Price touches lower band (potential buy)
                if data[i-1] > lower_band[i-1] and data[i] <= lower_band[i]:
                    signals[i] = 1
                # Price touches upper band (potential sell)
                elif data[i-1] < upper_band[i-1] and data[i] >= upper_band[i]:
                    signals[i] = -1
        
        return IndicatorResult(
            values=middle_band,
            signals=signals,
            metadata={
                'upper_band': upper_band,
                'lower_band': lower_band,
                'bandwidth': bandwidth
            }
        )


class ATR(BaseIndicator):
    """Average True Range"""
    
    def __init__(self, period: int = 14):
        """
        Initialize ATR
        
        Args:
            period: Number of periods for averaging
        """
        super().__init__(f"ATR_{period}")
        self.period = period
    
    def calculate(self, data: np.ndarray, high: np.ndarray = None,
                  low: np.ndarray = None, **kwargs) -> IndicatorResult:
        """
        Calculate Average True Range
        
        Args:
            data: Close prices
            high: High prices (if None, use close)
            low: Low prices (if None, use close)
            
        Returns:
            IndicatorResult with ATR values
        """
        if not self.validate_data(data, self.period + 1):
            return IndicatorResult(values=np.array([]))
        
        # Use close prices if high/low not provided
        if high is None:
            high = data
        if low is None:
            low = data
        
        # Calculate True Range
        tr = np.zeros(len(data))
        
        for i in range(1, len(data)):
            high_low = high[i] - low[i]
            high_close = abs(high[i] - data[i - 1])
            low_close = abs(low[i] - data[i - 1])
            tr[i] = max(high_low, high_close, low_close)
        
        # Calculate ATR using Wilder's smoothing
        atr = np.full(len(data), np.nan)
        atr[self.period] = np.mean(tr[1:self.period + 1])
        
        for i in range(self.period + 1, len(data)):
            atr[i] = (atr[i - 1] * (self.period - 1) + tr[i]) / self.period
        
        return IndicatorResult(
            values=atr,
            metadata={'true_range': tr}
        )

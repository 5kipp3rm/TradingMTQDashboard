"""
Volume Indicators
OBV, VWAP, etc.
"""
import numpy as np
from .base import BaseIndicator, IndicatorResult


class OBV(BaseIndicator):
    """On-Balance Volume"""
    
    def __init__(self):
        """Initialize OBV"""
        super().__init__("OBV")
    
    def calculate(self, data: np.ndarray, volume: np.ndarray = None, **kwargs) -> IndicatorResult:
        """
        Calculate On-Balance Volume
        
        Args:
            data: Close prices
            volume: Volume data
            
        Returns:
            IndicatorResult with OBV values
        """
        if volume is None:
            # Use dummy volume if not provided
            volume = np.ones_like(data)
        
        if not self.validate_data(data, 2):
            return IndicatorResult(values=np.array([]))
        
        obv = np.zeros(len(data))
        
        for i in range(1, len(data)):
            if data[i] > data[i - 1]:
                obv[i] = obv[i - 1] + volume[i]
            elif data[i] < data[i - 1]:
                obv[i] = obv[i - 1] - volume[i]
            else:
                obv[i] = obv[i - 1]
        
        # Generate trend signals
        signals = np.zeros_like(obv)
        for i in range(2, len(obv)):
            # OBV rising while price rising (bullish confirmation)
            if obv[i] > obv[i-1] and data[i] > data[i-1]:
                signals[i] = 1
            # OBV falling while price falling (bearish confirmation)
            elif obv[i] < obv[i-1] and data[i] < data[i-1]:
                signals[i] = -1
        
        return IndicatorResult(values=obv, signals=signals)


class VWAP(BaseIndicator):
    """Volume Weighted Average Price"""
    
    def __init__(self):
        """Initialize VWAP"""
        super().__init__("VWAP")
    
    def calculate(self, data: np.ndarray, volume: np.ndarray = None,
                  high: np.ndarray = None, low: np.ndarray = None, **kwargs) -> IndicatorResult:
        """
        Calculate VWAP
        
        Args:
            data: Close prices
            volume: Volume data
            high: High prices (if None, use close)
            low: Low prices (if None, use close)
            
        Returns:
            IndicatorResult with VWAP values
        """
        if volume is None:
            volume = np.ones_like(data)
        
        if not self.validate_data(data, 1):
            return IndicatorResult(values=np.array([]))
        
        # Use close if high/low not provided
        if high is None:
            high = data
        if low is None:
            low = data
        
        # Calculate typical price
        typical_price = (high + low + data) / 3
        
        # Calculate VWAP (cumulative)
        vwap = np.zeros(len(data))
        cum_vol = 0
        cum_tp_vol = 0
        
        for i in range(len(data)):
            cum_tp_vol += typical_price[i] * volume[i]
            cum_vol += volume[i]
            
            if cum_vol > 0:
                vwap[i] = cum_tp_vol / cum_vol
        
        # Generate signals
        signals = np.zeros_like(vwap)
        for i in range(1, len(data)):
            # Price crosses above VWAP (bullish)
            if data[i-1] <= vwap[i-1] and data[i] > vwap[i]:
                signals[i] = 1
            # Price crosses below VWAP (bearish)
            elif data[i-1] >= vwap[i-1] and data[i] < vwap[i]:
                signals[i] = -1
        
        return IndicatorResult(values=vwap, signals=signals)

"""
Base Strategy Class
Abstract base for all trading strategies
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    CLOSE_BUY = "CLOSE_BUY"
    CLOSE_SELL = "CLOSE_SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    """Trading signal"""
    type: SignalType
    symbol: str
    timestamp: datetime
    price: float
    confidence: float  # 0.0 to 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies
    All strategies must implement the analyze() method
    """
    
    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy
        
        Args:
            name: Strategy name
            params: Strategy parameters
        """
        self.name = name
        self.params = params or {}
        self.enabled = True
    
    @abstractmethod
    def analyze(self, symbol: str, timeframe: str, bars: list) -> Signal:
        """
        Analyze market data and generate trading signal
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Timeframe (e.g., "M5", "H1")
            bars: List of OHLC bars
            
        Returns:
            Signal object with trading decision
        """
        pass
    
    def get_name(self) -> str:
        """Get strategy name"""
        return self.name
    
    def get_params(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return self.params
    
    def set_param(self, key: str, value: Any):
        """Set strategy parameter"""
        self.params[key] = value
    
    def enable(self):
        """Enable strategy"""
        self.enabled = True
    
    def disable(self):
        """Disable strategy"""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if strategy is enabled"""
        return self.enabled

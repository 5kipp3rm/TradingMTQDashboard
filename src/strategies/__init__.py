"""
Trading Strategies Package
"""
from .base import BaseStrategy, Signal, SignalType
from .simple_ma import SimpleMovingAverageStrategy

__all__ = [
    'BaseStrategy',
    'Signal',
    'SignalType',
    'SimpleMovingAverageStrategy',
]

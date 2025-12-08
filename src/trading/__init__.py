"""
Trading package - High-level trading logic
"""
from .controller import TradingController
from .currency_trader import CurrencyTrader, CurrencyTraderConfig
from .orchestrator import MultiCurrencyOrchestrator
from .intelligent_position_manager import IntelligentPositionManager, PositionDecision


__all__ = [
    'TradingController',
    'CurrencyTrader',
    'CurrencyTraderConfig',
    'MultiCurrencyOrchestrator',
    'IntelligentPositionManager',
    'PositionDecision'
]

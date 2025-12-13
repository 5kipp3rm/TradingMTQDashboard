"""
CLI Module for TradingMTQ
Provides command-line interface for trading operations
"""

try:
    from .app import cli
    __all__ = ['cli']
except ImportError as e:
    # Fallback if Click is not installed
    def cli():
        print("Error: Click library not installed.")
        print("Install with: pip install click")
        import sys
        sys.exit(1)
    __all__ = ['cli']

"""
Trading Control Interfaces

Abstract interfaces for trading control components.
"""

from abc import ABC, abstractmethod
from src.services.trading_control.models import AutoTradingStatus


class IAutoTradingChecker(ABC):
    """
    Interface for AutoTrading status checking (Strategy Pattern)

    Different implementations can check AutoTrading status in different ways:
    - WorkerBasedChecker: Ask worker via command
    - DirectMT5Checker: Check MT5 terminal directly
    - CachedChecker: Add caching layer (Decorator)

    SOLID: Open/Closed - easy to add new checker implementations
    """

    @abstractmethod
    def check_autotrading(self, account_id: str) -> AutoTradingStatus:
        """
        Check if AutoTrading is enabled for account

        Args:
            account_id: Account to check

        Returns:
            AutoTradingStatus with current status

        Raises:
            ValueError: If account not found
            RuntimeError: If check fails
        """
        pass

"""
AutoTrading Checkers - Strategy and Decorator Patterns

Implements AutoTrading status checking with caching.

Design Patterns:
- Strategy Pattern: Different checking implementations
- Decorator Pattern: Caching layer wraps base checker
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from src.services.trading_control.interfaces import IAutoTradingChecker
from src.services.trading_control.models import AutoTradingStatus
from src.workers.pool import WorkerPoolManager
from src.workers.commands import HealthCheckCommand


logger = logging.getLogger(__name__)


class WorkerBasedAutoTradingChecker(IAutoTradingChecker):
    """
    AutoTrading checker using worker pool

    Checks AutoTrading status by querying the MT5 worker.

    SOLID: Single Responsibility - only checks AutoTrading status
    """

    def __init__(self, worker_pool: WorkerPoolManager):
        """
        Initialize worker-based checker

        Args:
            worker_pool: Worker pool manager (injected dependency)
        """
        self.worker_pool = worker_pool
        logger.info("Initialized WorkerBasedAutoTradingChecker")

    def check_autotrading(self, account_id: str) -> AutoTradingStatus:
        """
        Check AutoTrading status via worker

        Args:
            account_id: Account to check

        Returns:
            AutoTradingStatus

        Raises:
            ValueError: If account not found
            RuntimeError: If check fails
        """
        logger.debug(f"Checking AutoTrading for account {account_id}")

        # Check if worker exists
        if not self.worker_pool.has_worker_for_account(account_id):
            raise ValueError(f"No worker found for account {account_id}")

        try:
            # Execute health check command which includes AutoTrading status
            # In a full implementation, there would be a dedicated command for this
            result = self.worker_pool.execute_command_on_account(
                account_id,
                HealthCheckCommand(),
                timeout=5.0
            )

            if not result.get("success"):
                error_msg = result.get("error", "Unknown error")
                logger.error(f"AutoTrading check failed for account {account_id}: {error_msg}")

                return AutoTradingStatus(
                    enabled=False,
                    account_id=account_id,
                    checked_at=datetime.utcnow(),
                    error=error_msg,
                    instructions=AutoTradingStatus.get_enable_instructions()
                )

            # In full implementation, health check would return autotrading_enabled field
            # For now, we'll assume it's enabled if worker is healthy
            health_data = result.get("result", {})
            is_healthy = health_data.get("healthy", False)

            # Simulate AutoTrading check
            # In real implementation, this would check mt5.terminal_info().trade_expert_enabled
            autotrading_enabled = is_healthy  # Placeholder logic

            if not autotrading_enabled:
                return AutoTradingStatus(
                    enabled=False,
                    account_id=account_id,
                    checked_at=datetime.utcnow(),
                    instructions=AutoTradingStatus.get_enable_instructions()
                )

            return AutoTradingStatus(
                enabled=True,
                account_id=account_id,
                checked_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error checking AutoTrading for account {account_id}: {e}", exc_info=True)
            raise RuntimeError(f"AutoTrading check failed: {str(e)}")


class CachedAutoTradingChecker(IAutoTradingChecker):
    """
    Caching decorator for AutoTrading checker

    Design Pattern: Decorator Pattern
    - Wraps another IAutoTradingChecker
    - Adds caching layer transparently
    - Reduces load on MT5 terminal

    SOLID: Open/Closed - extends behavior without modifying base checker
    """

    def __init__(
        self,
        base_checker: IAutoTradingChecker,
        cache_ttl_seconds: int = 30
    ):
        """
        Initialize caching decorator

        Args:
            base_checker: Base checker to wrap (injected dependency)
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.base_checker = base_checker
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._cache: Dict[str, tuple[AutoTradingStatus, datetime]] = {}

        logger.info(
            f"Initialized CachedAutoTradingChecker "
            f"(wrapping {base_checker.__class__.__name__}, TTL={cache_ttl_seconds}s)"
        )

    def check_autotrading(self, account_id: str) -> AutoTradingStatus:
        """
        Check AutoTrading status with caching

        Args:
            account_id: Account to check

        Returns:
            AutoTradingStatus (may be from cache)

        Raises:
            ValueError: If account not found
            RuntimeError: If check fails
        """
        # Check cache
        if account_id in self._cache:
            cached_status, cached_at = self._cache[account_id]

            # Check if cache is still valid
            if datetime.utcnow() - cached_at < self.cache_ttl:
                logger.debug(f"Returning cached AutoTrading status for account {account_id}")
                return cached_status

            # Cache expired
            logger.debug(f"Cache expired for account {account_id}")

        # Cache miss or expired - query base checker
        logger.debug(f"Querying base checker for account {account_id}")
        status = self.base_checker.check_autotrading(account_id)

        # Update cache
        self._cache[account_id] = (status, datetime.utcnow())

        return status

    def clear_cache(self, account_id: Optional[str] = None) -> None:
        """
        Clear cache for account or all accounts

        Args:
            account_id: Account to clear (None = clear all)
        """
        if account_id:
            if account_id in self._cache:
                del self._cache[account_id]
                logger.debug(f"Cleared cache for account {account_id}")
        else:
            self._cache.clear()
            logger.debug("Cleared all AutoTrading cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        return {
            "cached_accounts": len(self._cache),
            "ttl_seconds": int(self.cache_ttl.total_seconds()),
        }

"""
Trading Control Factory - Dependency Injection

Provides factory methods and dependency injection for trading control service.

Design Pattern: Factory Pattern + Dependency Injection
"""

from typing import Optional
import logging

from src.services.trading_control.service import TradingControlService
from src.services.trading_control.checker import (
    WorkerBasedAutoTradingChecker,
    CachedAutoTradingChecker,
)
from src.services.trading_control.interfaces import IAutoTradingChecker
from src.workers.pool import WorkerPoolManager


logger = logging.getLogger(__name__)


# Singleton instances
_worker_pool_instance: Optional[WorkerPoolManager] = None
_trading_control_service_instance: Optional[TradingControlService] = None


def get_worker_pool_manager() -> WorkerPoolManager:
    """
    Get or create WorkerPoolManager singleton

    Returns:
        WorkerPoolManager instance
    """
    global _worker_pool_instance

    if _worker_pool_instance is None:
        _worker_pool_instance = WorkerPoolManager(max_workers=10)
        logger.info("Created new WorkerPoolManager singleton")

    return _worker_pool_instance


def create_autotrading_checker(
    worker_pool: WorkerPoolManager,
    enable_caching: bool = True,
    cache_ttl_seconds: int = 30
) -> IAutoTradingChecker:
    """
    Create AutoTrading checker

    Args:
        worker_pool: Worker pool manager
        enable_caching: If True, wrap with caching decorator
        cache_ttl_seconds: Cache TTL in seconds

    Returns:
        IAutoTradingChecker implementation
    """
    # Create base checker
    base_checker = WorkerBasedAutoTradingChecker(worker_pool)

    # Wrap with caching if requested
    if enable_caching:
        return CachedAutoTradingChecker(
            base_checker=base_checker,
            cache_ttl_seconds=cache_ttl_seconds
        )

    return base_checker


def get_trading_control_service(
    worker_pool: Optional[WorkerPoolManager] = None,
    autotrading_checker: Optional[IAutoTradingChecker] = None,
    enable_caching: bool = True,
    cache_ttl_seconds: int = 30,
    singleton: bool = True
) -> TradingControlService:
    """
    Get or create TradingControlService

    Args:
        worker_pool: Worker pool manager (optional, will create if None)
        autotrading_checker: AutoTrading checker (optional, will create if None)
        enable_caching: Enable AutoTrading status caching
        cache_ttl_seconds: Cache TTL in seconds
        singleton: If True, return singleton instance

    Returns:
        TradingControlService instance
    """
    global _trading_control_service_instance

    # Return singleton if exists and requested
    if singleton and _trading_control_service_instance is not None:
        return _trading_control_service_instance

    # Create worker pool if not provided
    if worker_pool is None:
        worker_pool = get_worker_pool_manager()

    # Create AutoTrading checker if not provided
    if autotrading_checker is None:
        autotrading_checker = create_autotrading_checker(
            worker_pool=worker_pool,
            enable_caching=enable_caching,
            cache_ttl_seconds=cache_ttl_seconds
        )

    # Create service
    service = TradingControlService(
        worker_pool=worker_pool,
        autotrading_checker=autotrading_checker
    )

    # Store as singleton if requested
    if singleton:
        _trading_control_service_instance = service
        logger.info("Created TradingControlService singleton")

    return service


def reset_trading_control_service() -> None:
    """
    Reset singleton instances (useful for testing)
    """
    global _trading_control_service_instance, _worker_pool_instance

    _trading_control_service_instance = None
    _worker_pool_instance = None

    logger.debug("Reset trading control service singletons")

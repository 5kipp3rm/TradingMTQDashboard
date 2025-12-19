"""
Tests for Trading Control Factory (Dependency Injection)

Tests factory methods and singleton management.
"""

import pytest
from unittest.mock import Mock, patch

from src.services.trading_control.factory import (
    get_worker_pool_manager,
    create_autotrading_checker,
    get_trading_control_service,
    reset_trading_control_service,
)
from src.services.trading_control.service import TradingControlService
from src.services.trading_control.checker import (
    WorkerBasedAutoTradingChecker,
    CachedAutoTradingChecker,
)
from src.workers.pool import WorkerPoolManager


class TestGetWorkerPoolManager:
    """Test get_worker_pool_manager factory function"""

    def test_creates_singleton(self):
        """Test creates singleton instance"""
        reset_trading_control_service()  # Clean state

        pool1 = get_worker_pool_manager()
        pool2 = get_worker_pool_manager()

        assert pool1 is pool2
        assert isinstance(pool1, WorkerPoolManager)

    def test_singleton_persists_across_calls(self):
        """Test singleton persists across multiple calls"""
        reset_trading_control_service()  # Clean state

        instances = [get_worker_pool_manager() for _ in range(5)]

        # All should be same instance
        assert all(inst is instances[0] for inst in instances)

    def test_creates_pool_with_default_max_workers(self):
        """Test pool created with default max_workers"""
        reset_trading_control_service()  # Clean state

        pool = get_worker_pool_manager()

        assert pool.max_workers == 10


class TestCreateAutoTradingChecker:
    """Test create_autotrading_checker factory function"""

    def test_creates_base_checker_without_caching(self):
        """Test creates base checker when caching disabled"""
        mock_pool = Mock(spec=WorkerPoolManager)

        checker = create_autotrading_checker(
            worker_pool=mock_pool, enable_caching=False
        )

        assert isinstance(checker, WorkerBasedAutoTradingChecker)
        assert checker.worker_pool is mock_pool

    def test_creates_cached_checker_with_caching(self):
        """Test creates cached checker when caching enabled"""
        mock_pool = Mock(spec=WorkerPoolManager)

        checker = create_autotrading_checker(
            worker_pool=mock_pool, enable_caching=True, cache_ttl_seconds=60
        )

        assert isinstance(checker, CachedAutoTradingChecker)
        assert isinstance(checker.base_checker, WorkerBasedAutoTradingChecker)
        assert checker.cache_ttl.total_seconds() == 60

    def test_creates_cached_checker_with_default_ttl(self):
        """Test creates cached checker with default TTL"""
        mock_pool = Mock(spec=WorkerPoolManager)

        checker = create_autotrading_checker(worker_pool=mock_pool, enable_caching=True)

        assert isinstance(checker, CachedAutoTradingChecker)
        assert checker.cache_ttl.total_seconds() == 30

    def test_checker_wraps_same_pool(self):
        """Test decorator wraps checker with same pool reference"""
        mock_pool = Mock(spec=WorkerPoolManager)

        checker = create_autotrading_checker(worker_pool=mock_pool, enable_caching=True)

        # Unwrap decorator to check base checker
        assert checker.base_checker.worker_pool is mock_pool


class TestGetTradingControlService:
    """Test get_trading_control_service factory function"""

    def test_creates_singleton_by_default(self):
        """Test creates singleton service by default"""
        reset_trading_control_service()  # Clean state

        service1 = get_trading_control_service()
        service2 = get_trading_control_service()

        assert service1 is service2
        assert isinstance(service1, TradingControlService)

    def test_creates_new_instance_when_singleton_false(self):
        """Test creates new instance when singleton=False"""
        reset_trading_control_service()  # Clean state

        service1 = get_trading_control_service(singleton=False)
        service2 = get_trading_control_service(singleton=False)

        assert service1 is not service2
        assert isinstance(service1, TradingControlService)
        assert isinstance(service2, TradingControlService)

    def test_creates_service_with_default_dependencies(self):
        """Test creates service with default dependencies"""
        reset_trading_control_service()  # Clean state

        service = get_trading_control_service()

        assert isinstance(service.worker_pool, WorkerPoolManager)
        assert isinstance(service.autotrading_checker, CachedAutoTradingChecker)

    def test_creates_service_with_custom_worker_pool(self):
        """Test creates service with custom worker pool"""
        reset_trading_control_service()  # Clean state
        mock_pool = Mock(spec=WorkerPoolManager)

        service = get_trading_control_service(worker_pool=mock_pool, singleton=False)

        assert service.worker_pool is mock_pool

    def test_creates_service_with_custom_checker(self):
        """Test creates service with custom checker"""
        reset_trading_control_service()  # Clean state
        mock_pool = Mock(spec=WorkerPoolManager)
        mock_checker = Mock()

        service = get_trading_control_service(
            worker_pool=mock_pool, autotrading_checker=mock_checker, singleton=False
        )

        assert service.autotrading_checker is mock_checker

    def test_creates_service_with_caching_enabled(self):
        """Test creates service with caching enabled"""
        reset_trading_control_service()  # Clean state

        service = get_trading_control_service(enable_caching=True, singleton=False)

        assert isinstance(service.autotrading_checker, CachedAutoTradingChecker)

    def test_creates_service_with_caching_disabled(self):
        """Test creates service with caching disabled"""
        reset_trading_control_service()  # Clean state

        service = get_trading_control_service(enable_caching=False, singleton=False)

        assert isinstance(service.autotrading_checker, WorkerBasedAutoTradingChecker)

    def test_creates_service_with_custom_cache_ttl(self):
        """Test creates service with custom cache TTL"""
        reset_trading_control_service()  # Clean state

        service = get_trading_control_service(
            enable_caching=True, cache_ttl_seconds=120, singleton=False
        )

        assert isinstance(service.autotrading_checker, CachedAutoTradingChecker)
        assert service.autotrading_checker.cache_ttl.total_seconds() == 120

    def test_singleton_uses_same_worker_pool(self):
        """Test singleton service uses same worker pool instance"""
        reset_trading_control_service()  # Clean state

        service1 = get_trading_control_service()
        service2 = get_trading_control_service()

        assert service1.worker_pool is service2.worker_pool

    def test_dependency_injection_chain(self):
        """Test full dependency injection chain"""
        reset_trading_control_service()  # Clean state

        # Create service with defaults
        service = get_trading_control_service(singleton=False)

        # Verify full chain: Service -> CachedChecker -> BaseChecker -> WorkerPool
        assert isinstance(service, TradingControlService)
        assert isinstance(service.autotrading_checker, CachedAutoTradingChecker)
        assert isinstance(
            service.autotrading_checker.base_checker, WorkerBasedAutoTradingChecker
        )
        assert isinstance(service.worker_pool, WorkerPoolManager)

        # Verify same worker pool throughout chain
        base_checker = service.autotrading_checker.base_checker
        assert base_checker.worker_pool is service.worker_pool


class TestResetTradingControlService:
    """Test reset_trading_control_service function"""

    def test_resets_singletons(self):
        """Test resets singleton instances"""
        # Create singletons
        service1 = get_trading_control_service()
        pool1 = get_worker_pool_manager()

        # Reset
        reset_trading_control_service()

        # Create new instances
        service2 = get_trading_control_service()
        pool2 = get_worker_pool_manager()

        # Should be different instances after reset
        assert service1 is not service2
        assert pool1 is not pool2

    def test_allows_fresh_start(self):
        """Test allows fresh start after reset"""
        reset_trading_control_service()

        # Create custom instance
        mock_pool = Mock(spec=WorkerPoolManager)
        service1 = get_trading_control_service(worker_pool=mock_pool)

        # Reset
        reset_trading_control_service()

        # Create new default instance
        service2 = get_trading_control_service()

        # Should have default dependencies, not custom ones
        assert service2.worker_pool is not mock_pool
        assert isinstance(service2.worker_pool, WorkerPoolManager)


class TestFactoryIntegration:
    """Test factory integration scenarios"""

    def test_multiple_services_same_pool(self):
        """Test multiple services can share same pool"""
        reset_trading_control_service()
        pool = get_worker_pool_manager()

        service1 = get_trading_control_service(worker_pool=pool, singleton=False)
        service2 = get_trading_control_service(worker_pool=pool, singleton=False)

        assert service1.worker_pool is pool
        assert service2.worker_pool is pool
        assert service1.worker_pool is service2.worker_pool

    def test_factory_pattern_flexibility(self):
        """Test factory allows flexible configuration"""
        reset_trading_control_service()

        # Configuration 1: Default with caching
        service1 = get_trading_control_service(enable_caching=True, singleton=False)

        # Configuration 2: No caching
        service2 = get_trading_control_service(enable_caching=False, singleton=False)

        # Configuration 3: Custom TTL
        service3 = get_trading_control_service(
            enable_caching=True, cache_ttl_seconds=120, singleton=False
        )

        # All different configurations
        assert isinstance(service1.autotrading_checker, CachedAutoTradingChecker)
        assert isinstance(service2.autotrading_checker, WorkerBasedAutoTradingChecker)
        assert isinstance(service3.autotrading_checker, CachedAutoTradingChecker)
        assert service3.autotrading_checker.cache_ttl.total_seconds() == 120

    def test_singleton_behavior_consistent(self):
        """Test singleton behavior is consistent across factory calls"""
        reset_trading_control_service()

        # Multiple calls should return same instance
        instances = [get_trading_control_service() for _ in range(10)]

        # All should be same instance
        assert all(inst is instances[0] for inst in instances)

        # All should share same worker pool
        pools = [inst.worker_pool for inst in instances]
        assert all(pool is pools[0] for pool in pools)

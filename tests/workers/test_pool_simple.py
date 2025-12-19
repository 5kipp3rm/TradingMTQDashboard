"""
Simplified unit tests for WorkerPoolManager

Tests key functionality without complex mocking.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.workers.pool import WorkerPoolManager
from src.workers.commands import GetAccountInfoCommand, HealthCheckCommand


class TestWorkerPoolManagerSimple:
    """Simplified tests for WorkerPoolManager"""

    def test_init(self):
        """Test initialization"""
        pool = WorkerPoolManager(max_workers=5)
        assert pool.max_workers == 5
        assert pool.get_worker_count() == 0

    def test_max_workers_enforced(self):
        """Test max workers limit"""
        pool = WorkerPoolManager(max_workers=1)

        # Mock the internals to avoid actual worker creation
        pool._workers = {"worker-1": Mock()}
        pool._account_to_worker = {"account-001": "worker-1"}

        # Should fail since we're at max
        with pytest.raises(ValueError, match="Maximum workers limit reached"):
            pool.start_worker("account-002", 2, "p", "s", auto_connect=False)

    def test_duplicate_account_rejected(self):
        """Test duplicate account is rejected"""
        pool = WorkerPoolManager()

        # Simulate existing worker
        pool._account_to_worker = {"account-001": "worker-1"}

        with pytest.raises(RuntimeError, match="Worker already exists for account"):
            pool.start_worker("account-001", 1, "p", "s", auto_connect=False)

    def test_stop_worker_not_found(self):
        """Test stopping non-existent worker raises error"""
        pool = WorkerPoolManager()

        with pytest.raises(KeyError, match="Worker not found"):
            pool.stop_worker("non-existent-worker")

    def test_execute_command_account_not_found(self):
        """Test executing command on non-existent account"""
        pool = WorkerPoolManager()
        cmd = GetAccountInfoCommand()

        with pytest.raises(KeyError, match="No worker found for account"):
            pool.execute_command_on_account("non-existent", cmd)

    def test_get_worker_not_found(self):
        """Test getting non-existent worker"""
        pool = WorkerPoolManager()

        with pytest.raises(KeyError, match="Worker not found"):
            pool.get_worker("non-existent")

    def test_get_worker_by_account_not_found(self):
        """Test getting worker by non-existent account"""
        pool = WorkerPoolManager()

        with pytest.raises(KeyError, match="No worker found for account"):
            pool.get_worker_by_account("non-existent")

    def test_has_worker_for_account(self):
        """Test checking if worker exists for account"""
        pool = WorkerPoolManager()

        assert not pool.has_worker_for_account("account-001")

        # Simulate adding worker
        pool._account_to_worker["account-001"] = "worker-1"

        assert pool.has_worker_for_account("account-001")

    def test_get_account_worker_id(self):
        """Test getting worker ID for account"""
        pool = WorkerPoolManager()

        # No worker
        assert pool.get_account_worker_id("account-001") is None

        # Add worker
        pool._account_to_worker["account-001"] = "worker-123"

        assert pool.get_account_worker_id("account-001") == "worker-123"

    def test_get_worker_count(self):
        """Test getting worker count"""
        pool = WorkerPoolManager()

        assert pool.get_worker_count() == 0

        # Add mock workers
        pool._workers = {"w1": Mock(), "w2": Mock()}

        assert pool.get_worker_count() == 2

    def test_list_workers_empty(self):
        """Test listing workers when empty"""
        pool = WorkerPoolManager()

        workers = pool.list_workers()

        assert workers == []

    def test_list_workers_with_workers(self):
        """Test listing workers"""
        pool = WorkerPoolManager()

        # Add mock workers with get_info method
        mock_handle1 = Mock()
        mock_handle1.get_info.return_value = {"worker_id": "w1", "account_id": "a1"}

        mock_handle2 = Mock()
        mock_handle2.get_info.return_value = {"worker_id": "w2", "account_id": "a2"}

        pool._workers = {"w1": mock_handle1, "w2": mock_handle2}

        workers = pool.list_workers()

        assert len(workers) == 2
        assert any(w["worker_id"] == "w1" for w in workers)
        assert any(w["worker_id"] == "w2" for w in workers)

    def test_observer_add_remove(self):
        """Test adding and removing observers"""
        from src.workers.interfaces import IWorkerObserver

        pool = WorkerPoolManager()
        observer = Mock(spec=IWorkerObserver)

        # Add observer
        pool.add_observer(observer)
        assert observer in pool._observers

        # Add same observer again (should not duplicate)
        pool.add_observer(observer)
        assert pool._observers.count(observer) == 1

        # Remove observer
        pool.remove_observer(observer)
        assert observer not in pool._observers

        # Remove again (should not error)
        pool.remove_observer(observer)

    def test_check_worker_health_not_found(self):
        """Test health check for non-existent worker"""
        pool = WorkerPoolManager()

        with pytest.raises(KeyError, match="Worker not found"):
            pool.check_worker_health("non-existent")

    def test_check_worker_health_process_dead(self):
        """Test health check when process is dead"""
        pool = WorkerPoolManager()

        # Create mock handle with dead worker
        mock_handle = Mock()
        mock_handle.is_alive.return_value = False
        mock_handle.worker_id = "test-worker"

        pool._workers["test-worker"] = mock_handle

        health = pool.check_worker_health("test-worker")

        assert health["healthy"] is False
        assert "not alive" in health["reason"]

    def test_check_all_workers_health(self):
        """Test checking health of all workers"""
        pool = WorkerPoolManager()

        # Create mock handles
        mock_handle1 = Mock()
        mock_handle1.is_alive.return_value = False
        pool._workers["w1"] = mock_handle1

        mock_handle2 = Mock()
        mock_handle2.is_alive.return_value = False
        pool._workers["w2"] = mock_handle2

        health_results = pool.check_all_workers_health()

        assert len(health_results) == 2
        assert "w1" in health_results
        assert "w2" in health_results
        assert health_results["w1"]["healthy"] is False
        assert health_results["w2"]["healthy"] is False

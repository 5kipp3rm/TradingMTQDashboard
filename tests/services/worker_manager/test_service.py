"""
Tests for WorkerManagerService

Tests service layer coordination between config and worker pool with mocking.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.services.worker_manager.service import WorkerManagerService
from src.services.worker_manager.models import (
    WorkerInfo,
    WorkerLifecycleStatus,
    ValidationResult,
)
from src.config.v2.models import AccountConfig, RiskConfig, CurrencyConfiguration


@pytest.fixture
def mock_config_service():
    """Create mock configuration service"""
    mock = Mock()
    mock.list_accounts.return_value = ["account-001", "account-002"]
    return mock


@pytest.fixture
def mock_worker_pool():
    """Create mock worker pool"""
    mock = Mock()
    mock.start_worker.return_value = "worker-123"
    mock.has_worker_for_account.return_value = False
    mock._account_to_worker = {}
    return mock


@pytest.fixture
def mock_validator():
    """Create mock validator"""
    mock = Mock()
    mock.validate.return_value = ValidationResult(
        valid=True,
        account_id="test-account",
    )
    return mock


@pytest.fixture
def valid_account_config():
    """Create valid account configuration"""
    return AccountConfig(
        account_id="account-001",
        currencies=[
            CurrencyConfiguration(
                symbol="EURUSD",
                enabled=True,
                risk=RiskConfig(risk_percent=1.0, max_positions=3),
                strategy=Mock(),
                position_management=Mock(),
            )
        ],
        default_risk=RiskConfig(
            risk_percent=1.0,
            max_positions=5,
        ),
    )


@pytest.fixture
def service(mock_config_service, mock_worker_pool, mock_validator):
    """Create service instance with mocks"""
    return WorkerManagerService(
        config_service=mock_config_service,
        worker_pool=mock_worker_pool,
        validator=mock_validator,
    )


class TestWorkerManagerServiceInitialization:
    """Test service initialization"""

    def test_service_initialization(self, mock_config_service, mock_worker_pool, mock_validator):
        """Service should initialize with dependencies"""
        service = WorkerManagerService(
            config_service=mock_config_service,
            worker_pool=mock_worker_pool,
            validator=mock_validator,
        )

        assert service.config_service == mock_config_service
        assert service.worker_pool == mock_worker_pool
        assert service.validator == mock_validator
        assert isinstance(service._worker_info, dict)

    def test_service_creates_validator_if_none(self, mock_config_service, mock_worker_pool):
        """Service should create validator if not provided"""
        service = WorkerManagerService(
            config_service=mock_config_service,
            worker_pool=mock_worker_pool,
            validator=None,
        )

        assert service.validator is not None


class TestStartWorkerFromConfig:
    """Test start_worker_from_config method"""

    def test_start_worker_loads_config(self, service, mock_config_service, valid_account_config):
        """Should load configuration from config service"""
        mock_config_service.load_account_config.return_value = valid_account_config

        service.start_worker_from_config("account-001")

        mock_config_service.load_account_config.assert_called_once_with(
            account_id="account-001",
            apply_defaults=True,
        )

    def test_start_worker_validates_config(self, service, mock_config_service, mock_validator, valid_account_config):
        """Should validate configuration before starting"""
        mock_config_service.load_account_config.return_value = valid_account_config

        service.start_worker_from_config("account-001")

        mock_validator.validate.assert_called_once_with(valid_account_config)

    def test_start_worker_creates_worker(self, service, mock_config_service, mock_worker_pool, valid_account_config):
        """Should create worker via pool"""
        mock_config_service.load_account_config.return_value = valid_account_config

        result = service.start_worker_from_config("account-001")

        mock_worker_pool.start_worker.assert_called_once()
        assert isinstance(result, WorkerInfo)
        assert result.account_id == "account-001"
        assert result.status == WorkerLifecycleStatus.RUNNING

    def test_start_worker_tracks_worker_info(self, service, mock_config_service, valid_account_config):
        """Should track worker info after starting"""
        mock_config_service.load_account_config.return_value = valid_account_config

        result = service.start_worker_from_config("account-001")

        assert "account-001" in service._worker_info
        assert service._worker_info["account-001"] == result

    def test_start_worker_fails_on_invalid_config(self, service, mock_config_service, mock_validator, valid_account_config):
        """Should raise error on invalid configuration"""
        mock_config_service.load_account_config.return_value = valid_account_config
        mock_validator.validate.return_value = ValidationResult(
            valid=False,
            account_id="account-001",
            errors=("Test error",),
        )

        with pytest.raises(ValueError, match="validation failed"):
            service.start_worker_from_config("account-001")

    def test_start_worker_skip_validation_when_disabled(self, service, mock_config_service, mock_validator, valid_account_config):
        """Should skip validation when validate=False"""
        mock_config_service.load_account_config.return_value = valid_account_config

        service.start_worker_from_config("account-001", validate=False)

        mock_validator.validate.assert_not_called()


class TestStopWorker:
    """Test stop_worker method"""

    def test_stop_worker_checks_existence(self, service, mock_worker_pool):
        """Should check if worker exists before stopping"""
        mock_worker_pool.has_worker_for_account.return_value = False

        with pytest.raises(ValueError, match="No worker found"):
            service.stop_worker("account-001")

    def test_stop_worker_calls_pool(self, service, mock_worker_pool):
        """Should call worker pool to stop worker"""
        mock_worker_pool.has_worker_for_account.return_value = True
        mock_worker_pool._account_to_worker = {"account-001": "worker-123"}

        service.stop_worker("account-001")

        mock_worker_pool.stop_worker.assert_called_once_with("worker-123", timeout=None)

    def test_stop_worker_updates_info(self, service, mock_worker_pool):
        """Should update worker info after stopping"""
        mock_worker_pool.has_worker_for_account.return_value = True
        mock_worker_pool._account_to_worker = {"account-001": "worker-123"}

        # Add initial worker info
        service._worker_info["account-001"] = WorkerInfo(
            worker_id="worker-123",
            account_id="account-001",
            status=WorkerLifecycleStatus.RUNNING,
            created_at=datetime.utcnow(),
        )

        service.stop_worker("account-001")

        assert service._worker_info["account-001"].status == WorkerLifecycleStatus.STOPPED
        assert service._worker_info["account-001"].stopped_at is not None


class TestBatchOperations:
    """Test batch operation methods"""

    def test_start_all_enabled_workers_lists_accounts(self, service, mock_config_service):
        """Should list all accounts from config service"""
        mock_config_service.list_accounts.return_value = []

        service.start_all_enabled_workers()

        mock_config_service.list_accounts.assert_called_once()

    def test_start_all_enabled_workers_starts_each(self, service, mock_config_service, valid_account_config):
        """Should start worker for each account"""
        mock_config_service.list_accounts.return_value = ["account-001", "account-002"]
        mock_config_service.load_account_config.return_value = valid_account_config

        result = service.start_all_enabled_workers()

        assert len(result) == 2
        assert "account-001" in result
        assert "account-002" in result

    def test_start_all_enabled_workers_skips_disabled(self, service, mock_config_service):
        """Should skip disabled accounts"""
        mock_config_service.list_accounts.return_value = ["account-001"]

        disabled_config = Mock()
        disabled_config.account_id = "account-001"
        disabled_config.enabled = False
        mock_config_service.load_account_config.return_value = disabled_config

        result = service.start_all_enabled_workers()

        assert len(result) == 0

    def test_start_all_enabled_workers_handles_errors(self, service, mock_config_service):
        """Should handle errors gracefully and continue"""
        mock_config_service.list_accounts.return_value = ["account-001", "account-002"]
        mock_config_service.load_account_config.side_effect = [
            Exception("Config error"),
            Mock(account_id="account-002", currencies=[Mock(symbol="EURUSD")]),
        ]

        result = service.start_all_enabled_workers(validate=False)

        # Should skip failed account and continue with next
        assert "account-001" not in result

    def test_stop_all_workers_stops_each(self, service, mock_worker_pool):
        """Should stop all tracked workers"""
        service._worker_info = {
            "account-001": WorkerInfo(
                worker_id="worker-1",
                account_id="account-001",
                status=WorkerLifecycleStatus.RUNNING,
                created_at=datetime.utcnow(),
            ),
            "account-002": WorkerInfo(
                worker_id="worker-2",
                account_id="account-002",
                status=WorkerLifecycleStatus.RUNNING,
                created_at=datetime.utcnow(),
            ),
        }
        mock_worker_pool.has_worker_for_account.return_value = True
        mock_worker_pool._account_to_worker = {
            "account-001": "worker-1",
            "account-002": "worker-2",
        }

        count = service.stop_all_workers()

        assert count == 2

    def test_validate_all_configs_validates_each(self, service, mock_config_service, mock_validator, valid_account_config):
        """Should validate all account configurations"""
        mock_config_service.list_accounts.return_value = ["account-001", "account-002"]
        mock_config_service.load_account_config.return_value = valid_account_config

        results = service.validate_all_configs()

        assert len(results) == 2
        assert mock_validator.validate.call_count == 2


class TestWorkerInformation:
    """Test worker information methods"""

    def test_get_worker_info_returns_info(self, service):
        """Should return worker info if exists"""
        info = WorkerInfo(
            worker_id="worker-123",
            account_id="account-001",
            status=WorkerLifecycleStatus.RUNNING,
            created_at=datetime.utcnow(),
        )
        service._worker_info["account-001"] = info

        result = service.get_worker_info("account-001")

        assert result == info

    def test_get_worker_info_returns_none(self, service):
        """Should return None if worker not found"""
        result = service.get_worker_info("nonexistent")

        assert result is None

    def test_list_workers_returns_all(self, service):
        """Should return list of all workers"""
        info1 = WorkerInfo(
            worker_id="worker-1",
            account_id="account-001",
            status=WorkerLifecycleStatus.RUNNING,
            created_at=datetime.utcnow(),
        )
        info2 = WorkerInfo(
            worker_id="worker-2",
            account_id="account-002",
            status=WorkerLifecycleStatus.RUNNING,
            created_at=datetime.utcnow(),
        )
        service._worker_info = {"account-001": info1, "account-002": info2}

        result = service.list_workers()

        assert len(result) == 2
        assert info1 in result
        assert info2 in result

    def test_is_worker_running_checks_pool(self, service, mock_worker_pool):
        """Should check worker pool for running status"""
        mock_worker_pool.has_worker_for_account.return_value = True

        result = service.is_worker_running("account-001")

        assert result is True
        mock_worker_pool.has_worker_for_account.assert_called_once_with("account-001")


class TestConfigValidation:
    """Test configuration validation"""

    def test_validate_config_loads_and_validates(self, service, mock_config_service, mock_validator, valid_account_config):
        """Should load config and validate"""
        mock_config_service.load_account_config.return_value = valid_account_config

        result = service.validate_config("account-001")

        mock_config_service.load_account_config.assert_called_once_with("account-001")
        mock_validator.validate.assert_called_once_with(valid_account_config)
        assert isinstance(result, ValidationResult)

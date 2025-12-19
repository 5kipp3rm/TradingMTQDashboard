"""
Tests for Worker Manager Models

Tests value objects and enums used in worker management.
"""

import pytest
from datetime import datetime
from src.services.worker_manager.models import (
    WorkerLifecycleStatus,
    WorkerCreationRequest,
    WorkerInfo,
    ValidationResult,
)


class TestWorkerLifecycleStatus:
    """Test WorkerLifecycleStatus enum"""

    def test_lifecycle_status_values(self):
        """All lifecycle statuses should be available"""
        assert WorkerLifecycleStatus.CREATED == "created"
        assert WorkerLifecycleStatus.STARTING == "starting"
        assert WorkerLifecycleStatus.RUNNING == "running"
        assert WorkerLifecycleStatus.STOPPING == "stopping"
        assert WorkerLifecycleStatus.STOPPED == "stopped"
        assert WorkerLifecycleStatus.FAILED == "failed"
        assert WorkerLifecycleStatus.RESTARTING == "restarting"

    def test_lifecycle_status_is_string(self):
        """Lifecycle status should be string enum"""
        status = WorkerLifecycleStatus.RUNNING
        assert isinstance(status.value, str)
        assert status.value == "running"


class TestWorkerCreationRequest:
    """Test WorkerCreationRequest value object"""

    def test_creation_request_immutable(self):
        """WorkerCreationRequest should be immutable (frozen dataclass)"""
        request = WorkerCreationRequest(
            account_id="test-001",
            login=12345678,
            password="test_pass",
            server="MetaQuotes-Demo",
        )

        with pytest.raises(AttributeError):
            request.account_id = "modified"

    def test_creation_request_required_fields(self):
        """WorkerCreationRequest should require all fields"""
        request = WorkerCreationRequest(
            account_id="test-001",
            login=12345678,
            password="test_pass",
            server="MetaQuotes-Demo",
        )

        assert request.account_id == "test-001"
        assert request.login == 12345678
        assert request.password == "test_pass"
        assert request.server == "MetaQuotes-Demo"

    def test_creation_request_default_values(self):
        """WorkerCreationRequest should have default values"""
        request = WorkerCreationRequest(
            account_id="test-001",
            login=12345678,
            password="test_pass",
            server="MetaQuotes-Demo",
        )

        assert request.timeout == 60000
        assert request.portable is False
        assert request.auto_connect is True

    def test_creation_request_custom_values(self):
        """WorkerCreationRequest should accept custom values"""
        request = WorkerCreationRequest(
            account_id="test-001",
            login=12345678,
            password="test_pass",
            server="MetaQuotes-Demo",
            timeout=120000,
            portable=True,
            auto_connect=False,
        )

        assert request.timeout == 120000
        assert request.portable is True
        assert request.auto_connect is False

    def test_creation_request_to_dict(self):
        """WorkerCreationRequest should convert to dictionary"""
        request = WorkerCreationRequest(
            account_id="test-001",
            login=12345678,
            password="test_pass",
            server="MetaQuotes-Demo",
        )

        result = request.to_dict()

        assert result["account_id"] == "test-001"
        assert result["login"] == 12345678
        assert result["password"] == "***"  # Password should be masked
        assert result["server"] == "MetaQuotes-Demo"
        assert result["timeout"] == 60000
        assert result["portable"] is False
        assert result["auto_connect"] is True


class TestWorkerInfo:
    """Test WorkerInfo value object"""

    def test_worker_info_immutable(self):
        """WorkerInfo should be immutable (frozen dataclass)"""
        now = datetime.utcnow()
        info = WorkerInfo(
            worker_id="worker-123",
            account_id="test-001",
            status=WorkerLifecycleStatus.RUNNING,
            created_at=now,
        )

        with pytest.raises(AttributeError):
            info.worker_id = "modified"

    def test_worker_info_required_fields(self):
        """WorkerInfo should require key fields"""
        now = datetime.utcnow()
        info = WorkerInfo(
            worker_id="worker-123",
            account_id="test-001",
            status=WorkerLifecycleStatus.RUNNING,
            created_at=now,
        )

        assert info.worker_id == "worker-123"
        assert info.account_id == "test-001"
        assert info.status == WorkerLifecycleStatus.RUNNING
        assert info.created_at == now

    def test_worker_info_optional_fields(self):
        """WorkerInfo should have optional timestamp fields"""
        now = datetime.utcnow()
        start_time = datetime.utcnow()
        stop_time = datetime.utcnow()

        info = WorkerInfo(
            worker_id="worker-123",
            account_id="test-001",
            status=WorkerLifecycleStatus.STOPPED,
            created_at=now,
            started_at=start_time,
            stopped_at=stop_time,
            error="Test error",
            metadata={"key": "value"},
        )

        assert info.started_at == start_time
        assert info.stopped_at == stop_time
        assert info.error == "Test error"
        assert info.metadata == {"key": "value"}

    def test_worker_info_to_dict(self):
        """WorkerInfo should convert to dictionary"""
        now = datetime.utcnow()
        info = WorkerInfo(
            worker_id="worker-123",
            account_id="test-001",
            status=WorkerLifecycleStatus.RUNNING,
            created_at=now,
        )

        result = info.to_dict()

        assert result["worker_id"] == "worker-123"
        assert result["account_id"] == "test-001"
        assert result["status"] == "running"
        assert result["created_at"] == now.isoformat()
        assert result["started_at"] is None
        assert result["stopped_at"] is None
        assert result["error"] is None
        assert result["metadata"] == {}

    def test_worker_info_to_dict_with_all_fields(self):
        """WorkerInfo to_dict should handle all fields"""
        now = datetime.utcnow()
        start_time = datetime.utcnow()
        stop_time = datetime.utcnow()

        info = WorkerInfo(
            worker_id="worker-123",
            account_id="test-001",
            status=WorkerLifecycleStatus.STOPPED,
            created_at=now,
            started_at=start_time,
            stopped_at=stop_time,
            error="Test error",
            metadata={"test": "data"},
        )

        result = info.to_dict()

        assert result["started_at"] == start_time.isoformat()
        assert result["stopped_at"] == stop_time.isoformat()
        assert result["error"] == "Test error"
        assert result["metadata"] == {"test": "data"}


class TestValidationResult:
    """Test ValidationResult value object"""

    def test_validation_result_immutable(self):
        """ValidationResult should be immutable (frozen dataclass)"""
        result = ValidationResult(
            valid=True,
            account_id="test-001",
        )

        with pytest.raises(AttributeError):
            result.valid = False

    def test_validation_result_required_fields(self):
        """ValidationResult should require key fields"""
        result = ValidationResult(
            valid=True,
            account_id="test-001",
        )

        assert result.valid is True
        assert result.account_id == "test-001"
        assert result.errors == ()
        assert result.warnings == ()

    def test_validation_result_with_errors(self):
        """ValidationResult should handle errors"""
        result = ValidationResult(
            valid=False,
            account_id="test-001",
            errors=("Error 1", "Error 2"),
        )

        assert result.valid is False
        assert len(result.errors) == 2
        assert "Error 1" in result.errors
        assert "Error 2" in result.errors

    def test_validation_result_with_warnings(self):
        """ValidationResult should handle warnings"""
        result = ValidationResult(
            valid=True,
            account_id="test-001",
            warnings=("Warning 1", "Warning 2"),
        )

        assert result.valid is True
        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings
        assert "Warning 2" in result.warnings

    def test_validation_result_to_dict(self):
        """ValidationResult should convert to dictionary"""
        result = ValidationResult(
            valid=True,
            account_id="test-001",
            errors=("Error 1",),
            warnings=("Warning 1",),
        )

        dict_result = result.to_dict()

        assert dict_result["valid"] is True
        assert dict_result["account_id"] == "test-001"
        assert dict_result["errors"] == ["Error 1"]
        assert dict_result["warnings"] == ["Warning 1"]

    def test_validation_result_has_errors_property(self):
        """ValidationResult.has_errors should check for errors"""
        result_with_errors = ValidationResult(
            valid=False,
            account_id="test-001",
            errors=("Error 1",),
        )

        result_without_errors = ValidationResult(
            valid=True,
            account_id="test-001",
        )

        assert result_with_errors.has_errors is True
        assert result_without_errors.has_errors is False

    def test_validation_result_has_warnings_property(self):
        """ValidationResult.has_warnings should check for warnings"""
        result_with_warnings = ValidationResult(
            valid=True,
            account_id="test-001",
            warnings=("Warning 1",),
        )

        result_without_warnings = ValidationResult(
            valid=True,
            account_id="test-001",
        )

        assert result_with_warnings.has_warnings is True
        assert result_without_warnings.has_warnings is False

    def test_validation_result_errors_immutable(self):
        """ValidationResult errors should be immutable tuple"""
        result = ValidationResult(
            valid=False,
            account_id="test-001",
            errors=("Error 1",),
        )

        assert isinstance(result.errors, tuple)
        with pytest.raises(AttributeError):
            result.errors.append("Error 2")

    def test_validation_result_warnings_immutable(self):
        """ValidationResult warnings should be immutable tuple"""
        result = ValidationResult(
            valid=True,
            account_id="test-001",
            warnings=("Warning 1",),
        )

        assert isinstance(result.warnings, tuple)
        with pytest.raises(AttributeError):
            result.warnings.append("Warning 2")

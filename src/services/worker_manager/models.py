"""
Worker Manager Models - Value Objects

Immutable value objects for worker manager service.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class WorkerLifecycleStatus(str, Enum):
    """Worker lifecycle status"""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass(frozen=True)
class WorkerCreationRequest:
    """
    Value object for worker creation request

    Contains all information needed to create and start a worker.
    """
    account_id: str
    login: int
    password: str
    server: str
    timeout: int = 60000
    portable: bool = False
    auto_connect: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "account_id": self.account_id,
            "login": self.login,
            "password": "***",  # Mask password
            "server": self.server,
            "timeout": self.timeout,
            "portable": self.portable,
            "auto_connect": self.auto_connect,
        }


@dataclass(frozen=True)
class WorkerInfo:
    """
    Value object for worker information

    Provides read-only view of worker state.
    """
    worker_id: str
    account_id: str
    status: WorkerLifecycleStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "worker_id": self.worker_id,
            "account_id": self.account_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "error": self.error,
            "metadata": self.metadata or {},
        }


@dataclass(frozen=True)
class ValidationResult:
    """
    Value object for configuration validation result

    Reports whether config is valid and provides error messages.
    """
    valid: bool
    account_id: str
    errors: tuple = ()  # Tuple for immutability
    warnings: tuple = ()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "valid": self.valid,
            "account_id": self.account_id,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }

    @property
    def has_errors(self) -> bool:
        """Check if has errors"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if has warnings"""
        return len(self.warnings) > 0

"""
Worker Handle - Worker Encapsulation

Provides high-level interface for managing individual workers.

Design Pattern: Facade (partial)
- Simplifies worker interaction
- Encapsulates queue management
- Provides async-style interface

SOLID: Single Responsibility - manages one worker lifecycle
"""

from typing import Dict, Any, Optional
from multiprocessing import Queue
import logging
from datetime import datetime

from src.workers.interfaces import IWorker, ICommand, WorkerState


logger = logging.getLogger(__name__)


class WorkerHandle:
    """
    Handle for managing a single worker

    Provides convenient interface for:
    - Starting/stopping worker
    - Sending commands
    - Retrieving results
    - Monitoring state

    Usage:
        handle = WorkerHandle(worker)
        handle.start()
        result = handle.execute_command(ConnectCommand(...))
        handle.stop()
    """

    def __init__(
        self,
        worker: IWorker,
        command_queue: Queue,
        result_queue: Queue,
        account_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize worker handle

        Args:
            worker: Worker instance
            command_queue: Command queue for this worker
            result_queue: Result queue for this worker
            account_id: Associated account ID
            metadata: Additional metadata (login, server, etc.)
        """
        self.worker = worker
        self.command_queue = command_queue
        self.result_queue = result_queue
        self.account_id = account_id
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None

    @property
    def worker_id(self) -> str:
        """Get worker ID"""
        return self.worker.worker_id if hasattr(self.worker, 'worker_id') else str(id(self.worker))

    def start(self) -> None:
        """
        Start the worker

        Raises:
            RuntimeError: If worker is already running
        """
        if self.is_alive():
            raise RuntimeError(f"Worker {self.worker_id} is already running")

        logger.info(f"Starting worker {self.worker_id}")
        self.worker.start()
        self.started_at = datetime.utcnow()

    def stop(self, timeout: Optional[float] = None) -> None:
        """
        Stop the worker gracefully

        Args:
            timeout: Maximum time to wait for shutdown (seconds)
        """
        if not self.is_alive():
            logger.warning(f"Worker {self.worker_id} is not running")
            return

        logger.info(f"Stopping worker {self.worker_id}")
        self.worker.stop(timeout=timeout)
        self.stopped_at = datetime.utcnow()

    def is_alive(self) -> bool:
        """Check if worker is alive"""
        return self.worker.is_alive()

    def get_state(self) -> WorkerState:
        """Get worker state"""
        return self.worker.get_state()

    def send_command(self, command: ICommand, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Send command and wait for result

        Args:
            command: Command to execute
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Command execution result

        Raises:
            RuntimeError: If worker is not running
            TimeoutError: If result not received within timeout
        """
        if not self.is_alive():
            raise RuntimeError(f"Worker {self.worker_id} is not running")

        # Send command
        self.worker.send_command(command)

        # Wait for result
        result = self.worker.get_result(timeout=timeout)

        return result

    def get_info(self) -> Dict[str, Any]:
        """
        Get worker information

        Returns:
            Dictionary with worker details
        """
        uptime = None
        if self.started_at and self.is_alive():
            uptime = (datetime.utcnow() - self.started_at).total_seconds()

        return {
            "worker_id": self.worker_id,
            "account_id": self.account_id,
            "state": self.get_state().value if self.is_alive() else "stopped",
            "alive": self.is_alive(),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "uptime_seconds": uptime,
            "metadata": self.metadata,
        }

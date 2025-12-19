"""
Worker Pool Manager - Facade Pattern Implementation

Provides unified interface for managing multiple MT5 workers.

Design Pattern: Facade Pattern
- Simplifies complex worker pool operations
- Provides high-level API for worker management
- Hides implementation details

SOLID: Single Responsibility - manages worker lifecycle and coordination
"""

from typing import Dict, Optional, List
from multiprocessing import Queue
import logging
from datetime import datetime

from src.workers.interfaces import ICommand, IWorkerObserver
from src.workers.mt5_worker import MT5Worker
from src.workers.handle import WorkerHandle
from src.workers.commands import ConnectCommand


logger = logging.getLogger(__name__)


class WorkerPoolManager:
    """
    Worker Pool Manager (Facade)

    Provides high-level interface for managing multiple MT5 workers.

    Features:
    - Start/stop workers per account
    - Execute commands on specific workers
    - Monitor worker health
    - Handle worker failures
    - Observer pattern for events

    Usage:
        pool = WorkerPoolManager()

        # Start worker for account
        worker_id = await pool.start_worker(
            account_id="account-001",
            login=12345,
            password="secret",
            server="Broker-Server"
        )

        # Execute command
        result = await pool.execute_command(
            worker_id,
            GetAccountInfoCommand()
        )

        # Stop worker
        await pool.stop_worker(worker_id)
    """

    def __init__(self, max_workers: int = 10):
        """
        Initialize worker pool manager

        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self._workers: Dict[str, WorkerHandle] = {}
        self._account_to_worker: Dict[str, str] = {}  # account_id -> worker_id
        self._observers: List[IWorkerObserver] = []

        logger.info(f"Initialized WorkerPoolManager (max_workers={max_workers})")

    # =============================================================================
    # Worker Lifecycle Management
    # =============================================================================

    def start_worker(
        self,
        account_id: str,
        login: int,
        password: str,
        server: str,
        timeout: int = 60000,
        portable: bool = False,
        auto_connect: bool = True
    ) -> str:
        """
        Start new worker for account

        Args:
            account_id: Unique account identifier
            login: MT5 login
            password: MT5 password
            server: Broker server
            timeout: Connection timeout (ms)
            portable: Use portable mode
            auto_connect: Automatically connect after starting

        Returns:
            Worker ID

        Raises:
            RuntimeError: If worker already exists for account
            ValueError: If max_workers limit reached
        """
        # Check if worker already exists for this account
        if account_id in self._account_to_worker:
            existing_worker_id = self._account_to_worker[account_id]
            raise RuntimeError(
                f"Worker already exists for account {account_id}: {existing_worker_id}"
            )

        # Check max workers limit
        if len(self._workers) >= self.max_workers:
            raise ValueError(
                f"Maximum workers limit reached ({self.max_workers})"
            )

        # Create worker ID
        worker_id = f"worker-{account_id}-{int(datetime.utcnow().timestamp())}"

        logger.info(f"Starting worker {worker_id} for account {account_id}")

        # Create queues for IPC
        command_queue = Queue()
        result_queue = Queue()

        # Create worker
        worker = MT5Worker(
            worker_id=worker_id,
            command_queue=command_queue,
            result_queue=result_queue,
            observers=self._observers,
            instance_id=account_id
        )

        # Create handle
        handle = WorkerHandle(
            worker=worker,
            command_queue=command_queue,
            result_queue=result_queue,
            account_id=account_id,
            metadata={
                "login": login,
                "server": server,
                "timeout": timeout,
                "portable": portable,
            }
        )

        # Start worker process
        handle.start()

        # Store handle
        self._workers[worker_id] = handle
        self._account_to_worker[account_id] = worker_id

        logger.info(f"Started worker {worker_id}")

        # Auto-connect if requested
        if auto_connect:
            connect_cmd = ConnectCommand(
                login=login,
                password=password,
                server=server,
                timeout=timeout,
                portable=portable
            )

            result = handle.send_command(connect_cmd, timeout=10.0)

            if not result.get("success"):
                logger.error(f"Failed to connect worker {worker_id}: {result.get('error')}")
                # Clean up worker
                self.stop_worker(worker_id)
                raise RuntimeError(f"Failed to connect worker: {result.get('error')}")

            logger.info(f"Worker {worker_id} connected successfully")

        return worker_id

    def stop_worker(self, worker_id: str, timeout: Optional[float] = 5.0) -> None:
        """
        Stop worker gracefully

        Args:
            worker_id: Worker to stop
            timeout: Maximum time to wait for shutdown (seconds)

        Raises:
            KeyError: If worker not found
        """
        handle = self._workers.get(worker_id)
        if not handle:
            raise KeyError(f"Worker not found: {worker_id}")

        logger.info(f"Stopping worker {worker_id}")

        # Stop worker
        handle.stop(timeout=timeout)

        # Remove from tracking
        account_id = handle.account_id
        if account_id in self._account_to_worker:
            del self._account_to_worker[account_id]

        del self._workers[worker_id]

        logger.info(f"Stopped worker {worker_id}")

    def stop_all_workers(self, timeout: Optional[float] = 5.0) -> None:
        """
        Stop all workers gracefully

        Args:
            timeout: Maximum time to wait for each worker shutdown (seconds)
        """
        logger.info(f"Stopping all workers ({len(self._workers)} active)")

        worker_ids = list(self._workers.keys())

        for worker_id in worker_ids:
            try:
                self.stop_worker(worker_id, timeout=timeout)
            except Exception as e:
                logger.error(f"Error stopping worker {worker_id}: {e}", exc_info=True)

        logger.info("All workers stopped")

    # =============================================================================
    # Command Execution
    # =============================================================================

    def execute_command(
        self,
        worker_id: str,
        command: ICommand,
        timeout: Optional[float] = 10.0
    ) -> Dict:
        """
        Execute command on specific worker

        Args:
            worker_id: Target worker
            command: Command to execute
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Command execution result

        Raises:
            KeyError: If worker not found
            RuntimeError: If worker is not running
            TimeoutError: If command times out
        """
        handle = self._workers.get(worker_id)
        if not handle:
            raise KeyError(f"Worker not found: {worker_id}")

        logger.debug(f"Executing command {command.get_type()} on worker {worker_id}")

        result = handle.send_command(command, timeout=timeout)

        return result

    def execute_command_on_account(
        self,
        account_id: str,
        command: ICommand,
        timeout: Optional[float] = 10.0
    ) -> Dict:
        """
        Execute command on worker managing specific account

        Args:
            account_id: Target account
            command: Command to execute
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Command execution result

        Raises:
            KeyError: If no worker found for account
        """
        worker_id = self._account_to_worker.get(account_id)
        if not worker_id:
            raise KeyError(f"No worker found for account: {account_id}")

        return self.execute_command(worker_id, command, timeout=timeout)

    # =============================================================================
    # Worker Information
    # =============================================================================

    def get_worker(self, worker_id: str) -> WorkerHandle:
        """
        Get worker handle

        Args:
            worker_id: Worker identifier

        Returns:
            WorkerHandle

        Raises:
            KeyError: If worker not found
        """
        handle = self._workers.get(worker_id)
        if not handle:
            raise KeyError(f"Worker not found: {worker_id}")
        return handle

    def get_worker_by_account(self, account_id: str) -> WorkerHandle:
        """
        Get worker handle by account ID

        Args:
            account_id: Account identifier

        Returns:
            WorkerHandle

        Raises:
            KeyError: If no worker found for account
        """
        worker_id = self._account_to_worker.get(account_id)
        if not worker_id:
            raise KeyError(f"No worker found for account: {account_id}")
        return self.get_worker(worker_id)

    def list_workers(self) -> List[Dict]:
        """
        List all active workers

        Returns:
            List of worker information dictionaries
        """
        return [handle.get_info() for handle in self._workers.values()]

    def get_worker_count(self) -> int:
        """Get number of active workers"""
        return len(self._workers)

    def get_account_worker_id(self, account_id: str) -> Optional[str]:
        """
        Get worker ID for account

        Args:
            account_id: Account identifier

        Returns:
            Worker ID or None if no worker exists
        """
        return self._account_to_worker.get(account_id)

    def has_worker_for_account(self, account_id: str) -> bool:
        """
        Check if worker exists for account

        Args:
            account_id: Account identifier

        Returns:
            True if worker exists
        """
        return account_id in self._account_to_worker

    # =============================================================================
    # Health Monitoring
    # =============================================================================

    def check_worker_health(self, worker_id: str) -> Dict:
        """
        Check worker health

        Args:
            worker_id: Worker to check

        Returns:
            Health check result

        Raises:
            KeyError: If worker not found
        """
        from src.workers.commands import HealthCheckCommand

        handle = self._workers.get(worker_id)
        if not handle:
            raise KeyError(f"Worker not found: {worker_id}")

        # Check if process is alive
        if not handle.is_alive():
            return {
                "healthy": False,
                "reason": "Worker process not alive",
                "worker_id": worker_id,
            }

        # Execute health check command
        try:
            result = handle.send_command(HealthCheckCommand(), timeout=5.0)

            if result.get("success"):
                return result.get("result", {})
            else:
                return {
                    "healthy": False,
                    "reason": result.get("error"),
                    "worker_id": worker_id,
                }

        except Exception as e:
            return {
                "healthy": False,
                "reason": str(e),
                "worker_id": worker_id,
            }

    def check_all_workers_health(self) -> Dict[str, Dict]:
        """
        Check health of all workers

        Returns:
            Dictionary mapping worker_id to health check result
        """
        return {
            worker_id: self.check_worker_health(worker_id)
            for worker_id in self._workers.keys()
        }

    # =============================================================================
    # Observer Pattern Support
    # =============================================================================

    def add_observer(self, observer: IWorkerObserver) -> None:
        """
        Add observer for worker events

        Args:
            observer: Observer to add
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Added observer: {observer}")

    def remove_observer(self, observer: IWorkerObserver) -> None:
        """
        Remove observer

        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Removed observer: {observer}")

    # =============================================================================
    # Context Manager Support
    # =============================================================================

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup all workers"""
        self.stop_all_workers()
        return False

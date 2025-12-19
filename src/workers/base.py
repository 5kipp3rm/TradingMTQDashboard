"""
Base Worker - Template Method Pattern Implementation

Provides abstract base class for workers with lifecycle template.

Design Pattern: Template Method
- Defines skeleton of worker lifecycle
- Subclasses override specific steps
- Ensures consistent behavior across worker types

SOLID: Open/Closed - open for extension via hooks, closed for modification
"""

from multiprocessing import Process, Queue
from typing import Dict, Any, Optional, List
import logging
from abc import abstractmethod
import time

from src.workers.interfaces import (
    IWorker,
    ICommand,
    IWorkerObserver,
    WorkerState,
    WorkerEvent,
    WorkerEventData,
)
from datetime import datetime


logger = logging.getLogger(__name__)


class BaseWorker(Process, IWorker):
    """
    Abstract base worker class with Template Method pattern

    Defines the lifecycle skeleton for all workers:
    1. start() - Initialize and start event loop
    2. run() - Main event loop (template method)
    3. _process_commands() - Handle incoming commands
    4. stop() - Graceful shutdown

    Subclasses must implement:
    - _on_start() - Worker-specific initialization
    - _on_stop() - Worker-specific cleanup
    - _execute_command() - Command execution logic
    - _on_idle() - Idle time processing (optional)

    SOLID: Template Method ensures consistent lifecycle
    """

    def __init__(
        self,
        worker_id: str,
        command_queue: Queue,
        result_queue: Queue,
        observers: Optional[List[IWorkerObserver]] = None
    ):
        """
        Initialize base worker

        Args:
            worker_id: Unique worker identifier
            command_queue: Queue for receiving commands
            result_queue: Queue for sending results
            observers: List of event observers
        """
        Process.__init__(self)
        self.worker_id = worker_id
        self._command_queue = command_queue
        self._result_queue = result_queue
        self._observers = observers or []
        self._state = WorkerState.IDLE
        self._is_running = False
        self._shutdown_requested = False

        logger.info(f"Initialized worker {worker_id}")

    # =============================================================================
    # Template Method - Defines Lifecycle Skeleton
    # =============================================================================

    def run(self) -> None:
        """
        Main worker event loop (Template Method)

        Defines the overall algorithm structure while allowing
        subclasses to customize specific steps via hooks.

        Lifecycle:
        1. _on_start() - Initialization hook
        2. Event loop - Process commands
        3. _on_stop() - Cleanup hook

        SOLID: Template Method - skeleton algorithm
        """
        try:
            # Step 1: Initialize (hook)
            self._on_start()
            self._state = WorkerState.RUNNING
            self._is_running = True
            self._notify_observers(WorkerEvent.STARTED, {"worker_id": self.worker_id})

            # Step 2: Main event loop
            while self._is_running and not self._shutdown_requested:
                # Process commands
                self._process_commands()

                # Idle processing (hook)
                self._on_idle()

                # Prevent busy-waiting
                time.sleep(0.01)

        except Exception as e:
            logger.error(f"Worker {self.worker_id} error: {e}", exc_info=True)
            self._state = WorkerState.ERROR
            self._notify_observers(
                WorkerEvent.ERROR,
                {"worker_id": self.worker_id, "error": str(e)}
            )

        finally:
            # Step 3: Cleanup (hook)
            try:
                self._on_stop()
            except Exception as e:
                logger.error(f"Worker {self.worker_id} cleanup error: {e}", exc_info=True)

            self._state = WorkerState.STOPPED
            self._is_running = False
            self._notify_observers(WorkerEvent.STOPPED, {"worker_id": self.worker_id})

    def _process_commands(self) -> None:
        """
        Process commands from command queue

        This is part of the template method and should not be overridden.
        """
        if self._command_queue.empty():
            return

        try:
            # Get command (non-blocking)
            command_data = self._command_queue.get_nowait()

            self._notify_observers(
                WorkerEvent.COMMAND_RECEIVED,
                {"worker_id": self.worker_id, "command_type": command_data.get("type")}
            )

            # Execute command (hook)
            result = self._execute_command(command_data)

            # Send result
            self._result_queue.put({
                "success": True,
                "worker_id": self.worker_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })

            self._notify_observers(
                WorkerEvent.COMMAND_COMPLETED,
                {"worker_id": self.worker_id, "command_type": command_data.get("type")}
            )

        except Exception as e:
            logger.error(f"Command execution error: {e}", exc_info=True)

            # Send error result
            self._result_queue.put({
                "success": False,
                "worker_id": self.worker_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            })

            self._notify_observers(
                WorkerEvent.COMMAND_FAILED,
                {"worker_id": self.worker_id, "error": str(e)}
            )

    # =============================================================================
    # Hooks for Subclasses (Template Method Steps)
    # =============================================================================

    @abstractmethod
    def _on_start(self) -> None:
        """
        Hook called when worker starts

        Subclasses should implement initialization logic here:
        - Initialize connections
        - Load configuration
        - Set up resources

        Raises:
            WorkerStartError: If initialization fails
        """
        pass

    @abstractmethod
    def _on_stop(self) -> None:
        """
        Hook called when worker stops

        Subclasses should implement cleanup logic here:
        - Close connections
        - Release resources
        - Save state
        """
        pass

    @abstractmethod
    def _execute_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook for executing commands

        Args:
            command_data: Command dictionary from queue

        Returns:
            Command execution result

        Raises:
            CommandExecutionError: If command execution fails
        """
        pass

    def _on_idle(self) -> None:
        """
        Hook called when worker is idle (no commands to process)

        Subclasses can override to implement:
        - Background tasks
        - Health checks
        - Maintenance operations

        Default implementation does nothing.
        """
        pass

    # =============================================================================
    # IWorker Interface Implementation
    # =============================================================================

    def stop(self, timeout: Optional[float] = None) -> None:
        """
        Stop worker gracefully

        Args:
            timeout: Maximum time to wait for shutdown (seconds)
        """
        logger.info(f"Stopping worker {self.worker_id}")
        self._state = WorkerState.STOPPING
        self._shutdown_requested = True
        self._is_running = False

        # Wait for process to terminate
        if timeout:
            self.join(timeout=timeout)
            if self.is_alive():
                logger.warning(f"Worker {self.worker_id} did not stop gracefully, terminating")
                self.terminate()
        else:
            self.join()

    def is_alive(self) -> bool:
        """Check if worker process is alive"""
        return super().is_alive()

    def get_state(self) -> WorkerState:
        """Get current worker state"""
        return self._state

    def send_command(self, command: ICommand) -> None:
        """
        Send command to worker

        Args:
            command: Command to execute

        Raises:
            RuntimeError: If worker is not running
        """
        if not self._is_running:
            raise RuntimeError(f"Worker {self.worker_id} is not running")

        self._command_queue.put(command.to_dict())

    def get_result(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Get command execution result

        Args:
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Result dictionary

        Raises:
            TimeoutError: If result not available within timeout
        """
        if timeout:
            result = self._result_queue.get(timeout=timeout)
        else:
            result = self._result_queue.get()

        return result

    # =============================================================================
    # Observer Pattern Support
    # =============================================================================

    def _notify_observers(self, event_type: WorkerEvent, data: Dict[str, Any]) -> None:
        """
        Notify all observers of worker event

        Args:
            event_type: Type of event
            data: Event data
        """
        event = WorkerEventData(
            event_type=event_type,
            worker_id=self.worker_id,
            timestamp=datetime.utcnow(),
            data=data
        )

        for observer in self._observers:
            try:
                observer.on_worker_event(event)
            except Exception as e:
                logger.error(f"Observer notification error: {e}", exc_info=True)

    def add_observer(self, observer: IWorkerObserver) -> None:
        """
        Add event observer

        Args:
            observer: Observer to add
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: IWorkerObserver) -> None:
        """
        Remove event observer

        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)

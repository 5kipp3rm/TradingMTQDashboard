"""
Worker Interfaces - Abstract Definitions

Defines interfaces for the worker pool architecture following SOLID principles.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class WorkerState(str, Enum):
    """Worker lifecycle states"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class WorkerEvent(str, Enum):
    """Worker event types for Observer pattern"""
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    COMMAND_RECEIVED = "command_received"
    COMMAND_COMPLETED = "command_completed"
    COMMAND_FAILED = "command_failed"


@dataclass
class WorkerEventData:
    """Data associated with worker events"""
    event_type: WorkerEvent
    worker_id: str
    timestamp: datetime
    data: Dict[str, Any]
    error: Optional[Exception] = None


class IWorker(ABC):
    """
    Interface for worker processes (Open/Closed Principle)

    All worker implementations must implement this interface to ensure
    they can be used interchangeably in the worker pool.

    SOLID: Liskov Substitution - all workers are substitutable
    """

    @abstractmethod
    def start(self) -> None:
        """
        Start the worker process

        This method starts the worker's event loop and begins processing commands.

        Raises:
            WorkerStartError: If worker fails to start
        """
        pass

    @abstractmethod
    def stop(self, timeout: Optional[float] = None) -> None:
        """
        Stop the worker process gracefully

        Args:
            timeout: Maximum time to wait for graceful shutdown (seconds)

        Raises:
            WorkerStopError: If worker fails to stop gracefully
        """
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """
        Check if worker process is alive

        Returns:
            True if worker process is running
        """
        pass

    @abstractmethod
    def get_state(self) -> WorkerState:
        """
        Get current worker state

        Returns:
            Current WorkerState
        """
        pass

    @abstractmethod
    def send_command(self, command: 'ICommand') -> None:
        """
        Send command to worker for execution

        Args:
            command: Command to execute

        Raises:
            WorkerNotRunningError: If worker is not in RUNNING state
            CommandError: If command cannot be sent
        """
        pass

    @abstractmethod
    def get_result(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Get result of last command execution

        Args:
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Command execution result

        Raises:
            TimeoutError: If result not available within timeout
            WorkerError: If command execution failed
        """
        pass


class ICommand(ABC):
    """
    Interface for worker commands (Command Pattern)

    Encapsulates operations that can be sent to workers.

    SOLID: Single Responsibility - each command does one thing
    """

    @abstractmethod
    def get_type(self) -> str:
        """
        Get command type identifier

        Returns:
            Unique command type string
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize command to dictionary

        Returns:
            Dictionary representation of command

        Notes:
            Must be serializable for IPC (Inter-Process Communication)
        """
        pass

    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> 'ICommand':
        """
        Deserialize command from dictionary

        Args:
            data: Dictionary representation

        Returns:
            Command instance
        """
        pass


class IWorkerObserver(ABC):
    """
    Interface for worker event observers (Observer Pattern)

    Allows objects to subscribe to worker events without tight coupling.

    SOLID: Dependency Inversion - depend on observer interface, not concrete
    """

    @abstractmethod
    def on_worker_event(self, event: WorkerEventData) -> None:
        """
        Handle worker event

        Args:
            event: Event data

        Notes:
            This method should not block. For long-running operations,
            spawn a separate task/thread.
        """
        pass


class ICommandHandler(ABC):
    """
    Interface for command execution handlers

    Allows workers to delegate command execution to specialized handlers.

    SOLID: Single Responsibility - each handler handles specific command types
    """

    @abstractmethod
    def can_handle(self, command: ICommand) -> bool:
        """
        Check if handler can execute this command

        Args:
            command: Command to check

        Returns:
            True if handler can execute command
        """
        pass

    @abstractmethod
    def handle(self, command: ICommand) -> Dict[str, Any]:
        """
        Execute command and return result

        Args:
            command: Command to execute

        Returns:
            Execution result

        Raises:
            CommandExecutionError: If execution fails
        """
        pass

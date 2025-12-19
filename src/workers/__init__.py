"""
Workers Module - Multi-Worker MT5 Architecture

Provides process-based worker pool for running multiple MT5 instances simultaneously.

Design Patterns:
- Template Method: BaseWorker defines lifecycle skeleton
- Command Pattern: Commands encapsulate worker operations
- Observer Pattern: Worker events notification
- Facade Pattern: WorkerPoolManager simplifies complexity

SOLID Principles:
- Single Responsibility: Each worker handles one account
- Open/Closed: Extensible through IWorker interface
- Liskov Substitution: All workers implement IWorker
- Interface Segregation: Minimal worker interfaces
- Dependency Inversion: Depend on abstractions

Usage:
    from src.workers import WorkerPoolManager, MT5Worker

    # Create worker pool
    pool = WorkerPoolManager()

    # Start worker for account
    worker_id = await pool.start_worker(
        account_id="account-001",
        login=12345,
        password="secret",
        server="Broker-Server"
    )

    # Execute trading cycle
    result = await pool.execute_command(
        worker_id,
        ExecuteTradingCycleCommand()
    )

    # Stop worker
    await pool.stop_worker(worker_id)
"""

from src.workers.interfaces import (
    IWorker,
    ICommand,
    IWorkerObserver,
    WorkerState,
    WorkerEvent,
)

from src.workers.commands import (
    ConnectCommand,
    DisconnectCommand,
    ExecuteTradingCycleCommand,
    GetAccountInfoCommand,
    GetPositionsCommand,
    PlaceOrderCommand,
    CommandFactory,
)

from src.workers.base import BaseWorker

from src.workers.mt5_worker import MT5Worker

from src.workers.pool import WorkerPoolManager

from src.workers.handle import WorkerHandle

__all__ = [
    # Interfaces
    "IWorker",
    "ICommand",
    "IWorkerObserver",
    "WorkerState",
    "WorkerEvent",
    # Commands
    "ConnectCommand",
    "DisconnectCommand",
    "ExecuteTradingCycleCommand",
    "GetAccountInfoCommand",
    "GetPositionsCommand",
    "PlaceOrderCommand",
    "CommandFactory",
    # Workers
    "BaseWorker",
    "MT5Worker",
    # Pool Management
    "WorkerPoolManager",
    "WorkerHandle",
]

"""
MT5 Worker - Concrete Worker Implementation

Implements worker for MetaTrader 5 connections in separate process.

Each MT5Worker runs in its own process with isolated MT5 connection,
solving the limitation that mt5.initialize() is process-wide.

Design Pattern: Template Method (extends BaseWorker)
SOLID: Liskov Substitution - fully substitutable for BaseWorker
"""

from typing import Dict, Any, Optional
from multiprocessing import Queue
import logging

from src.workers.base import BaseWorker
from src.workers.commands import CommandFactory
from src.workers.interfaces import IWorkerObserver
from src.connectors.mt5_connector import MT5Connector


logger = logging.getLogger(__name__)


class MT5Worker(BaseWorker):
    """
    MT5 Worker implementation

    Runs in separate process with isolated MT5 connection.
    Implements hooks from BaseWorker template.

    Features:
    - Isolated MT5 connection per worker
    - Command-based operation
    - Automatic connection management
    - Health monitoring

    Usage:
        worker = MT5Worker(
            worker_id="account-001",
            command_queue=cmd_queue,
            result_queue=result_queue
        )
        worker.start()  # Starts in separate process
    """

    def __init__(
        self,
        worker_id: str,
        command_queue: Queue,
        result_queue: Queue,
        observers: Optional[list[IWorkerObserver]] = None,
        instance_id: Optional[str] = None
    ):
        """
        Initialize MT5 worker

        Args:
            worker_id: Unique worker identifier
            command_queue: Queue for receiving commands
            result_queue: Queue for sending results
            observers: List of event observers
            instance_id: MT5 connector instance ID (defaults to worker_id)
        """
        super().__init__(worker_id, command_queue, result_queue, observers)
        self._instance_id = instance_id or worker_id
        self._connector: Optional[MT5Connector] = None
        self._connected = False

    # =============================================================================
    # Template Method Hooks Implementation
    # =============================================================================

    def _on_start(self) -> None:
        """
        Initialize MT5 connector

        This runs in the worker process, creating an isolated MT5 connection.
        """
        logger.info(f"MT5Worker {self.worker_id} starting")

        # Create MT5 connector (in worker process)
        self._connector = MT5Connector(instance_id=self._instance_id)

        logger.info(f"MT5Worker {self.worker_id} initialized MT5 connector")

    def _on_stop(self) -> None:
        """
        Cleanup MT5 connection
        """
        logger.info(f"MT5Worker {self.worker_id} stopping")

        if self._connector and self._connected:
            try:
                self._connector.disconnect()
                self._connected = False
                logger.info(f"MT5Worker {self.worker_id} disconnected from MT5")
            except Exception as e:
                logger.error(f"Error disconnecting MT5: {e}", exc_info=True)

        self._connector = None

    def _execute_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute command using MT5 connector

        Args:
            command_data: Command dictionary

        Returns:
            Execution result
        """
        # Deserialize command
        command = CommandFactory.create_command(command_data)
        command_type = command.get_type()

        logger.debug(f"Executing command: {command_type}")

        # Route to appropriate handler
        if command_type == "connect":
            return self._handle_connect(command)
        elif command_type == "disconnect":
            return self._handle_disconnect(command)
        elif command_type == "get_account_info":
            return self._handle_get_account_info(command)
        elif command_type == "get_positions":
            return self._handle_get_positions(command)
        elif command_type == "place_order":
            return self._handle_place_order(command)
        elif command_type == "modify_position":
            return self._handle_modify_position(command)
        elif command_type == "close_position":
            return self._handle_close_position(command)
        elif command_type == "get_history":
            return self._handle_get_history(command)
        elif command_type == "execute_trading_cycle":
            return self._handle_execute_trading_cycle(command)
        elif command_type == "health_check":
            return self._handle_health_check(command)
        else:
            raise ValueError(f"Unknown command type: {command_type}")

    def _on_idle(self) -> None:
        """
        Idle processing - perform health checks
        """
        # Could implement periodic health checks here if needed
        pass

    # =============================================================================
    # Command Handlers
    # =============================================================================

    def _handle_connect(self, command) -> Dict[str, Any]:
        """Handle connect command"""
        if not self._connector:
            raise RuntimeError("MT5 connector not initialized")

        success = self._connector.connect(
            login=command.login,
            password=command.password,
            server=command.server,
            timeout=command.timeout,
            portable=command.portable,
            path=command.path
        )

        self._connected = success

        return {
            "connected": success,
            "login": command.login,
            "server": command.server,
        }

    def _handle_disconnect(self, command) -> Dict[str, Any]:
        """Handle disconnect command"""
        if not self._connector:
            raise RuntimeError("MT5 connector not initialized")

        self._connector.disconnect()
        self._connected = False

        return {"disconnected": True}

    def _handle_get_account_info(self, command) -> Dict[str, Any]:
        """Handle get account info command"""
        if not self._connector or not self._connected:
            raise RuntimeError("Not connected to MT5")

        account_info = self._connector.get_account_info()

        return {
            "account_info": {
                "login": account_info.login,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.free_margin,
                "margin_level": account_info.margin_level,
                "profit": account_info.profit,
                "currency": account_info.currency,
            }
        }

    def _handle_get_positions(self, command) -> Dict[str, Any]:
        """Handle get positions command"""
        if not self._connector or not self._connected:
            raise RuntimeError("Not connected to MT5")

        positions = self._connector.get_positions(symbol=command.symbol)

        return {
            "positions": [
                {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": pos.type.value,
                    "volume": pos.volume,
                    "price_open": pos.price_open,
                    "price_current": pos.price_current,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "profit": pos.profit,
                    "swap": pos.swap,
                    "commission": pos.commission,
                }
                for pos in positions
            ]
        }

    def _handle_place_order(self, command) -> Dict[str, Any]:
        """Handle place order command"""
        if not self._connector or not self._connected:
            raise RuntimeError("Not connected to MT5")

        from src.connectors.base import TradeRequest, OrderType

        # Create trade request
        request = TradeRequest(
            symbol=command.symbol,
            order_type=OrderType[command.order_type],
            volume=command.volume,
            price=command.price,
            sl=command.sl,
            tp=command.tp,
            comment=command.comment,
            magic_number=command.magic_number,
        )

        result = self._connector.place_order(request)

        return {
            "order_placed": result.success,
            "ticket": result.order_ticket,
            "message": result.message,
            "retcode": result.retcode,
        }

    def _handle_modify_position(self, command) -> Dict[str, Any]:
        """Handle modify position command"""
        if not self._connector or not self._connected:
            raise RuntimeError("Not connected to MT5")

        success = self._connector.modify_position(
            ticket=command.ticket,
            sl=command.sl,
            tp=command.tp
        )

        return {
            "modified": success,
            "ticket": command.ticket,
        }

    def _handle_close_position(self, command) -> Dict[str, Any]:
        """Handle close position command"""
        if not self._connector or not self._connected:
            raise RuntimeError("Not connected to MT5")

        success = self._connector.close_position(
            ticket=command.ticket,
            volume=command.volume
        )

        return {
            "closed": success,
            "ticket": command.ticket,
        }

    def _handle_get_history(self, command) -> Dict[str, Any]:
        """Handle get history command"""
        if not self._connector or not self._connected:
            raise RuntimeError("Not connected to MT5")

        from datetime import datetime

        start_time = None
        if command.start_time:
            start_time = datetime.fromisoformat(command.start_time)

        bars = self._connector.get_ohlc_data(
            symbol=command.symbol,
            timeframe=command.timeframe,
            bars=command.bars,
            start_time=start_time
        )

        return {
            "bars": [
                {
                    "time": bar.time.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "tick_volume": bar.tick_volume,
                }
                for bar in bars
            ]
        }

    def _handle_execute_trading_cycle(self, command) -> Dict[str, Any]:
        """
        Handle execute trading cycle command

        This is a placeholder. In full implementation, this would:
        1. Get currency configurations
        2. Fetch market data
        3. Run strategy analysis
        4. Generate signals
        5. Execute trades

        For now, just return a success indicator.
        """
        if not self._connector or not self._connected:
            raise RuntimeError("Not connected to MT5")

        # TODO: Implement full trading cycle logic
        # This will involve:
        # - Loading CurrencyTrader instances
        # - Running trading cycles
        # - Returning execution results

        return {
            "trading_cycle_executed": True,
            "currencies": command.currency_symbols or [],
            "timestamp": None,  # Would be actual execution time
        }

    def _handle_health_check(self, command) -> Dict[str, Any]:
        """Handle health check command"""
        return {
            "healthy": True,
            "worker_id": self.worker_id,
            "connected": self._connected,
            "state": self._state.value,
        }

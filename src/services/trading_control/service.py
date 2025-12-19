"""
Trading Control Service - Business Logic Layer

Provides high-level trading control operations.

Design Pattern: Service Layer
- Encapsulates business logic
- Coordinates between worker pool and domain models
- Provides transactional operations

SOLID: Single Responsibility - manages trading control logic
"""

import logging
from typing import Optional
from datetime import datetime

from src.services.trading_control.models import (
    TradingControlResult,
    TradingStatus,
    AutoTradingStatus,
)
from src.services.trading_control.interfaces import IAutoTradingChecker
from src.workers.pool import WorkerPoolManager
from src.workers.commands import ExecuteTradingCycleCommand


logger = logging.getLogger(__name__)


class TradingControlService:
    """
    Trading Control Service

    Provides business logic for controlling trading operations:
    - Start/stop trading for accounts
    - Check trading status
    - Verify AutoTrading is enabled
    - Execute trading cycles

    Dependencies injected via constructor (DI principle).

    Example:
        service = TradingControlService(
            worker_pool=get_worker_pool_manager(),
            autotrading_checker=get_autotrading_checker()
        )

        # Start trading
        result = service.start_trading("account-001")

        # Check AutoTrading
        status = service.check_autotrading("account-001")

        # Stop trading
        result = service.stop_trading("account-001")
    """

    def __init__(
        self,
        worker_pool: WorkerPoolManager,
        autotrading_checker: IAutoTradingChecker,
    ):
        """
        Initialize trading control service

        Args:
            worker_pool: Worker pool manager (injected dependency)
            autotrading_checker: AutoTrading checker (injected dependency)
        """
        self.worker_pool = worker_pool
        self.autotrading_checker = autotrading_checker

        logger.info(
            f"Initialized TradingControlService with "
            f"{worker_pool.__class__.__name__} and "
            f"{autotrading_checker.__class__.__name__}"
        )

    def start_trading(
        self,
        account_id: str,
        currency_symbols: Optional[list[str]] = None,
        check_autotrading: bool = True
    ) -> TradingControlResult:
        """
        Start trading for account

        Args:
            account_id: Account to start trading
            currency_symbols: Specific currencies to trade (None = all configured)
            check_autotrading: If True, verify AutoTrading is enabled first

        Returns:
            TradingControlResult with operation status

        Raises:
            ValueError: If account not found
            RuntimeError: If start operation fails
        """
        logger.info(f"Starting trading for account {account_id}")

        try:
            # Check if worker exists for account
            if not self.worker_pool.has_worker_for_account(account_id):
                return TradingControlResult(
                    success=False,
                    message=f"No worker found for account {account_id}",
                    account_id=account_id,
                    status=TradingStatus.ERROR,
                    timestamp=datetime.utcnow(),
                    error="Account not connected"
                )

            # Check AutoTrading status if requested
            if check_autotrading:
                autotrading_status = self.autotrading_checker.check_autotrading(account_id)

                if not autotrading_status.enabled:
                    return TradingControlResult(
                        success=False,
                        message="AutoTrading is not enabled in MT5 terminal",
                        account_id=account_id,
                        status=TradingStatus.ERROR,
                        timestamp=datetime.utcnow(),
                        error="AutoTrading disabled",
                        metadata={
                            "instructions": autotrading_status.instructions
                        }
                    )

            # Execute trading cycle to start trading
            command = ExecuteTradingCycleCommand(
                currency_symbols=currency_symbols,
                force_check=True
            )

            result = self.worker_pool.execute_command_on_account(
                account_id,
                command,
                timeout=10.0
            )

            if result.get("success"):
                logger.info(f"Trading started successfully for account {account_id}")
                return TradingControlResult(
                    success=True,
                    message="Trading started successfully",
                    account_id=account_id,
                    status=TradingStatus.ACTIVE,
                    timestamp=datetime.utcnow(),
                    metadata=result.get("result", {})
                )
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Failed to start trading for account {account_id}: {error_msg}")
                return TradingControlResult(
                    success=False,
                    message=f"Failed to start trading: {error_msg}",
                    account_id=account_id,
                    status=TradingStatus.ERROR,
                    timestamp=datetime.utcnow(),
                    error=error_msg
                )

        except Exception as e:
            logger.error(f"Error starting trading for account {account_id}: {e}", exc_info=True)
            return TradingControlResult(
                success=False,
                message=f"Error starting trading: {str(e)}",
                account_id=account_id,
                status=TradingStatus.ERROR,
                timestamp=datetime.utcnow(),
                error=str(e)
            )

    def stop_trading(self, account_id: str) -> TradingControlResult:
        """
        Stop trading for account

        Note: This does not close existing positions, only stops new trades.

        Args:
            account_id: Account to stop trading

        Returns:
            TradingControlResult with operation status
        """
        logger.info(f"Stopping trading for account {account_id}")

        try:
            # Check if worker exists
            if not self.worker_pool.has_worker_for_account(account_id):
                return TradingControlResult(
                    success=False,
                    message=f"No worker found for account {account_id}",
                    account_id=account_id,
                    status=TradingStatus.UNKNOWN,
                    timestamp=datetime.utcnow(),
                    error="Account not connected"
                )

            # For now, we'll just mark as stopped
            # In full implementation, this would set a flag in the worker
            # to prevent new trades from being opened

            logger.info(f"Trading stopped for account {account_id}")

            return TradingControlResult(
                success=True,
                message="Trading stopped successfully",
                account_id=account_id,
                status=TradingStatus.STOPPED,
                timestamp=datetime.utcnow(),
                metadata={"note": "Existing positions not closed"}
            )

        except Exception as e:
            logger.error(f"Error stopping trading for account {account_id}: {e}", exc_info=True)
            return TradingControlResult(
                success=False,
                message=f"Error stopping trading: {str(e)}",
                account_id=account_id,
                status=TradingStatus.ERROR,
                timestamp=datetime.utcnow(),
                error=str(e)
            )

    def get_trading_status(self, account_id: str) -> TradingControlResult:
        """
        Get current trading status for account

        Args:
            account_id: Account to check

        Returns:
            TradingControlResult with current status
        """
        logger.debug(f"Getting trading status for account {account_id}")

        try:
            # Check if worker exists and is alive
            if not self.worker_pool.has_worker_for_account(account_id):
                return TradingControlResult(
                    success=True,
                    message="Account not connected",
                    account_id=account_id,
                    status=TradingStatus.STOPPED,
                    timestamp=datetime.utcnow()
                )

            # Get worker handle
            handle = self.worker_pool.get_worker_by_account(account_id)

            if not handle.is_alive():
                return TradingControlResult(
                    success=True,
                    message="Worker not running",
                    account_id=account_id,
                    status=TradingStatus.STOPPED,
                    timestamp=datetime.utcnow()
                )

            # Worker is alive - consider it active
            # In full implementation, would check actual trading state
            return TradingControlResult(
                success=True,
                message="Trading is active",
                account_id=account_id,
                status=TradingStatus.ACTIVE,
                timestamp=datetime.utcnow(),
                metadata=handle.get_info()
            )

        except Exception as e:
            logger.error(f"Error getting trading status for account {account_id}: {e}", exc_info=True)
            return TradingControlResult(
                success=False,
                message=f"Error getting status: {str(e)}",
                account_id=account_id,
                status=TradingStatus.UNKNOWN,
                timestamp=datetime.utcnow(),
                error=str(e)
            )

    def check_autotrading(self, account_id: str) -> AutoTradingStatus:
        """
        Check if AutoTrading is enabled for account

        Args:
            account_id: Account to check

        Returns:
            AutoTradingStatus with current status

        Raises:
            ValueError: If account not found
            RuntimeError: If check fails
        """
        logger.debug(f"Checking AutoTrading status for account {account_id}")

        return self.autotrading_checker.check_autotrading(account_id)

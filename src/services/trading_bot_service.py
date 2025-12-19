"""
Trading Bot Service

Manages automated trading execution alongside the API server.
Monitors connected accounts and executes trades based on currency configurations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from src.database.connection import get_session
from src.database.models import TradingAccount
from src.services.session_manager import session_manager
from src.database import currency_models
from src.strategies import SimpleMovingAverageStrategy
from src.trading.orchestrator import MultiCurrencyOrchestrator
from src.trading.currency_trader import CurrencyTraderConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TradingBotService:
    """
    Background service that executes automated trading on connected accounts.

    This service:
    - Monitors connected MT5 accounts from session_manager
    - Loads currency configurations from database
    - Executes trading signals at configured intervals
    - Manages position lifecycle and risk management
    """

    def __init__(self, check_interval: int = 60):
        """
        Initialize trading bot service.

        Args:
            check_interval: Seconds between trading signal checks (default: 60)
        """
        self.check_interval = check_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._orchestrators: Dict[int, MultiCurrencyOrchestrator] = {}  # account_id -> orchestrator

        logger.info(f"Trading bot service initialized with {check_interval}s interval")

    async def start(self):
        """Start the trading bot service."""
        if self.is_running:
            logger.warning("Trading bot service already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_trading_loop())
        logger.info("Trading bot service started")

    async def stop(self):
        """Stop the trading bot service."""
        if not self.is_running:
            return

        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Cleanup orchestrators
        self._orchestrators.clear()

        logger.info("Trading bot service stopped")

    async def _run_trading_loop(self):
        """Main trading loop that runs continuously."""
        logger.info("Trading bot loop started")

        while self.is_running:
            try:
                await self._execute_trading_cycle()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("Trading loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                # Continue running even if there's an error
                await asyncio.sleep(self.check_interval)

    async def _execute_trading_cycle(self):
        """Execute one trading cycle for all connected accounts."""
        # Get all connected account IDs from BOTH systems:
        # 1. SessionManager (old database-based system)
        # 2. WorkerManagerService (new Phase 4 config-based system)

        # Old system: database-based accounts
        session_based_accounts = session_manager.list_active_sessions()

        # New system: Phase 4 workers
        worker_based_accounts = []
        try:
            from src.services.worker_manager import get_worker_manager_service
            worker_service = get_worker_manager_service()

            # Get all running workers
            workers = worker_service.list_workers()
            worker_based_accounts = [
                w.account_id for w in workers
                if worker_service.is_worker_running(w.account_id)
            ]

            if worker_based_accounts:
                logger.info(f"Found {len(worker_based_accounts)} active Phase 4 workers: {worker_based_accounts}")
        except Exception as e:
            logger.debug(f"Phase 4 worker manager not available or no workers: {e}")

        # Combine both lists (session IDs are int, worker IDs are str, keep separate)
        if not session_based_accounts and not worker_based_accounts:
            logger.debug("No connected accounts (session-based or worker-based), skipping trading cycle")
            return

        logger.info(
            f"Executing trading cycle: "
            f"{len(session_based_accounts)} session-based accounts, "
            f"{len(worker_based_accounts)} worker-based accounts"
        )

        # Trade session-based accounts (old system)
        if session_based_accounts:
            with get_session() as db:
                for account_id in session_based_accounts:
                    try:
                        await self._trade_account(account_id, db)
                    except Exception as e:
                        logger.error(f"Error trading session account {account_id}: {e}", exc_info=True)

        # Trade worker-based accounts (Phase 4 system)
        if worker_based_accounts:
            for account_id in worker_based_accounts:
                try:
                    await self._trade_worker_account(account_id)
                except Exception as e:
                    logger.error(f"Error trading worker account {account_id}: {e}", exc_info=True)

    async def _trade_account(self, account_id: int, db: Session):
        """
        Execute trading logic for a single account using MultiCurrencyOrchestrator.

        Args:
            account_id: Account ID to trade
            db: Database session
        """
        # Get connector from session manager
        connector = session_manager.get_session(account_id)
        if not connector:
            logger.warning(f"No connector found for account {account_id}")
            return

        # Get account details
        account = db.get(TradingAccount, account_id)
        if not account or not account.is_active:
            logger.debug(f"Account {account_id} not active, skipping")
            return

        # Get enabled currency configurations from database
        currency_configs = db.query(currency_models.CurrencyConfiguration).filter(
            currency_models.CurrencyConfiguration.enabled == True
        ).all()

        if not currency_configs:
            logger.debug(f"No enabled currencies for account {account_id}")
            return

        logger.info(f"Trading account {account_id} ({account.account_name}) - "
                   f"{len(currency_configs)} active currencies")

        # Get or create orchestrator for this account
        if account_id not in self._orchestrators:
            logger.info(f"Creating new orchestrator for account {account_id}")
            orchestrator = MultiCurrencyOrchestrator(
                connector=connector,
                max_concurrent_trades=15,  # Default from config
                portfolio_risk_percent=10.0,  # Default from config
                use_intelligent_manager=False  # Disable AI features for now
            )

            # Add all enabled currencies to orchestrator
            for config in currency_configs:
                try:
                    # Create strategy
                    strategy = SimpleMovingAverageStrategy({
                        'fast_period': config.fast_period,
                        'slow_period': config.slow_period,
                        'sl_pips': config.sl_pips,
                        'tp_pips': config.tp_pips
                    })

                    # Create trader config
                    trader_config = CurrencyTraderConfig(
                        symbol=config.symbol,
                        strategy=strategy,
                        risk_percent=config.risk_percent,
                        timeframe=config.timeframe,
                        cooldown_seconds=60,  # 1 minute cooldown
                        max_position_size=config.max_position_size,
                        min_position_size=config.min_position_size,
                        use_position_trading=True,  # Use position-based trading
                        allow_position_stacking=False,  # Disable stacking for safety
                        max_positions_same_direction=1,
                        max_total_positions=5,
                        stacking_risk_multiplier=1.0,
                        fast_period=config.fast_period,
                        slow_period=config.slow_period,
                        sl_pips=config.sl_pips,
                        tp_pips=config.tp_pips
                    )

                    # Add currency to orchestrator
                    trader = orchestrator.add_currency(trader_config)
                    if trader:
                        logger.info(f"Added {config.symbol} to orchestrator for account {account_id}")
                    else:
                        logger.warning(f"Failed to add {config.symbol} to orchestrator (symbol not available)")

                except Exception as e:
                    logger.error(f"Error adding {config.symbol} to orchestrator: {e}")

            # Store orchestrator
            self._orchestrators[account_id] = orchestrator
            logger.info(f"Orchestrator created with {len(orchestrator.traders)} currency pairs")
        else:
            orchestrator = self._orchestrators[account_id]
            logger.debug(f"Using existing orchestrator for account {account_id}")

        # Execute one trading cycle using orchestrator
        try:
            logger.info(f"Processing trading cycle for account {account_id}")
            results = orchestrator.process_single_cycle(management_config=None)

            # Log results
            executed_count = sum(1 for r in results['currencies'].values() if r.get('executed'))
            if executed_count > 0:
                logger.info(f"Account {account_id}: {executed_count} trades executed this cycle")
            else:
                logger.debug(f"Account {account_id}: No trades executed this cycle")

            if results.get('errors'):
                for error in results['errors']:
                    logger.error(f"Account {account_id} cycle error: {error}")

        except Exception as e:
            logger.error(f"Error in trading cycle for account {account_id}: {e}", exc_info=True)

    async def _trade_worker_account(self, account_id: str):
        """
        Execute trading logic for Phase 4 worker-based account.

        This method trades accounts managed by WorkerManagerService (Phase 4)
        using currency configurations from the account's YAML config file.

        Args:
            account_id: Worker account ID (string, e.g., "account-001")
        """
        try:
            from src.services.worker_manager import get_worker_manager_service
            from src.config.v2.service import ConfigurationService

            worker_service = get_worker_manager_service()
            config_service = ConfigurationService()

            # Check if worker is still running
            if not worker_service.is_worker_running(account_id):
                logger.debug(f"Worker {account_id} not running, skipping")
                return

            # Get worker info to access connector
            worker_info = worker_service.get_worker_info(account_id)
            if not worker_info:
                logger.warning(f"No worker info for {account_id}")
                return

            # Get connector from worker pool
            try:
                worker_handle = worker_service.worker_pool.get_worker_by_account(account_id)
                connector = worker_handle.worker._connector
            except Exception as e:
                logger.error(f"Failed to get connector for worker {account_id}: {e}")
                return

            # Load account configuration from YAML
            try:
                account_config = config_service.load_account_config(account_id, apply_defaults=True)
            except Exception as e:
                logger.error(f"Failed to load config for account {account_id}: {e}")
                return

            # Get enabled currencies from config
            enabled_currencies = [c for c in account_config.currencies if c.enabled]

            if not enabled_currencies:
                logger.debug(f"No enabled currencies for worker account {account_id}")
                return

            logger.info(f"Trading worker account {account_id} - {len(enabled_currencies)} active currencies")

            # Get or create orchestrator for this worker account
            if account_id not in self._orchestrators:
                logger.info(f"Creating new orchestrator for worker account {account_id}")

                # Use default risk if available, otherwise use first currency's risk
                default_risk = account_config.default_risk or enabled_currencies[0].risk

                orchestrator = MultiCurrencyOrchestrator(
                    connector=connector,
                    max_concurrent_trades=default_risk.max_concurrent_trades or 15,
                    portfolio_risk_percent=default_risk.portfolio_risk_percent or 10.0,
                    use_intelligent_manager=False  # Disable AI features
                )

                # Add all enabled currencies to orchestrator
                for currency_config in enabled_currencies:
                    try:
                        # Use currency-specific strategy from config
                        strategy_config = currency_config.strategy

                        # Create strategy instance
                        strategy = SimpleMovingAverageStrategy({
                            'fast_period': strategy_config.fast_period,
                            'slow_period': strategy_config.slow_period,
                            'sl_pips': currency_config.risk.stop_loss_pips if currency_config.risk else 50,
                            'tp_pips': currency_config.risk.take_profit_pips if currency_config.risk else 100
                        })

                        # Use currency-specific risk or fall back to default
                        risk = currency_config.risk or default_risk

                        # Create trader config
                        trader_config = CurrencyTraderConfig(
                            symbol=currency_config.symbol,
                            strategy=strategy,
                            risk_percent=risk.risk_percent,
                            timeframe=strategy_config.timeframe.value,  # Convert enum to string
                            cooldown_seconds=60,
                            max_position_size=risk.max_positions,
                            min_position_size=1,
                            use_position_trading=True,
                            allow_position_stacking=False,
                            max_positions_same_direction=1,
                            max_total_positions=risk.max_positions,
                            stacking_risk_multiplier=1.0,
                            fast_period=strategy_config.fast_period,
                            slow_period=strategy_config.slow_period,
                            sl_pips=risk.stop_loss_pips if hasattr(risk, 'stop_loss_pips') else 50,
                            tp_pips=risk.take_profit_pips if hasattr(risk, 'take_profit_pips') else 100
                        )

                        # Add currency to orchestrator
                        trader = orchestrator.add_currency(trader_config)
                        if trader:
                            logger.info(f"Added {currency_config.symbol} to orchestrator for worker {account_id}")
                        else:
                            logger.warning(f"Failed to add {currency_config.symbol} (symbol not available)")

                    except Exception as e:
                        logger.error(f"Error adding {currency_config.symbol} to orchestrator: {e}")

                # Store orchestrator
                self._orchestrators[account_id] = orchestrator
                logger.info(f"Worker orchestrator created with {len(orchestrator.traders)} currency pairs")
            else:
                orchestrator = self._orchestrators[account_id]
                logger.debug(f"Using existing orchestrator for worker {account_id}")

            # Execute one trading cycle
            try:
                logger.info(f"Processing trading cycle for worker account {account_id}")
                results = orchestrator.process_single_cycle(management_config=None)

                # Log results
                executed_count = sum(1 for r in results['currencies'].values() if r.get('executed'))
                if executed_count > 0:
                    logger.info(f"Worker {account_id}: {executed_count} trades executed this cycle")
                else:
                    logger.debug(f"Worker {account_id}: No trades executed this cycle")

                if results.get('errors'):
                    for error in results['errors']:
                        logger.error(f"Worker {account_id} cycle error: {error}")

            except Exception as e:
                logger.error(f"Error in trading cycle for worker {account_id}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error trading worker account {account_id}: {e}", exc_info=True)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the trading bot service.

        Returns:
            Status dictionary with both session-based and worker-based accounts
        """
        # Session-based accounts (old system)
        session_based_accounts = session_manager.list_active_sessions()

        # Worker-based accounts (Phase 4 system)
        worker_based_accounts = []
        try:
            from src.services.worker_manager import get_worker_manager_service
            worker_service = get_worker_manager_service()
            workers = worker_service.list_workers()
            worker_based_accounts = [
                w.account_id for w in workers
                if worker_service.is_worker_running(w.account_id)
            ]
        except Exception:
            pass  # Phase 4 not available or no workers

        # Count total currency traders across all orchestrators
        total_traders = sum(
            len(orch.traders) for orch in self._orchestrators.values()
        )

        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "connected_accounts": len(session_based_accounts) + len(worker_based_accounts),
            "session_based_accounts": len(session_based_accounts),
            "worker_based_accounts": len(worker_based_accounts),
            "account_ids": session_based_accounts,  # Legacy field for compatibility
            "worker_ids": worker_based_accounts,  # New field for Phase 4 workers
            "active_traders": total_traders
        }


# Global instance
trading_bot_service = TradingBotService(check_interval=60)

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
        # Get all connected account IDs
        connected_account_ids = session_manager.list_active_sessions()

        if not connected_account_ids:
            logger.debug("No connected accounts, skipping trading cycle")
            return

        logger.info(f"Executing trading cycle for {len(connected_account_ids)} connected accounts")

        with get_session() as db:
            for account_id in connected_account_ids:
                try:
                    await self._trade_account(account_id, db)
                except Exception as e:
                    logger.error(f"Error trading account {account_id}: {e}", exc_info=True)

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

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the trading bot service.

        Returns:
            Status dictionary
        """
        connected_accounts = session_manager.list_active_sessions()

        # Count total currency traders across all orchestrators
        total_traders = sum(
            len(orch.traders) for orch in self._orchestrators.values()
        )

        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "connected_accounts": len(connected_accounts),
            "account_ids": connected_accounts,
            "active_traders": total_traders
        }


# Global instance
trading_bot_service = TradingBotService(check_interval=60)

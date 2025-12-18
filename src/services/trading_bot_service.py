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
from src.trading import CurrencyTraderConfig
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
        self._traders: Dict[int, Any] = {}  # account_id -> trader instance

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

        # Cleanup traders
        self._traders.clear()

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
        Execute trading logic for a single account.

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

        # Get enabled currency configurations for this account
        currency_configs = db.query(currency_models.CurrencyConfiguration).filter(
            currency_models.CurrencyConfiguration.enabled == True
        ).all()

        if not currency_configs:
            logger.debug(f"No enabled currencies for account {account_id}")
            return

        logger.info(f"Trading account {account_id} ({account.account_name}) - "
                   f"{len(currency_configs)} active currencies")

        # Execute trades for each enabled currency
        for config in currency_configs:
            try:
                await self._trade_currency(connector, account, config, db)
            except Exception as e:
                logger.error(f"Error trading {config.symbol} on account {account_id}: {e}")

    async def _trade_currency(self, connector, account: TradingAccount,
                             config: currency_models.CurrencyConfiguration, db: Session):
        """
        Execute trading logic for a single currency on an account.

        Args:
            connector: MT5 connector instance
            account: Trading account
            config: Currency configuration
            db: Database session
        """
        symbol = config.symbol

        # Check if currency is available on MT5
        try:
            symbol_info = connector.get_symbol_info(symbol)
            if not symbol_info:
                logger.warning(f"Symbol {symbol} not available on account {account.account_number}")
                return
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return

        # Get current positions for this symbol
        positions = connector.get_positions_by_symbol(symbol)

        # Create strategy
        strategy = SimpleMovingAverageStrategy(
            fast_period=config.fast_period,
            slow_period=config.slow_period,
            timeframe=config.timeframe
        )

        # Get historical data
        try:
            candles = connector.get_historical_data(
                symbol=symbol,
                timeframe=config.timeframe,
                count=config.slow_period + 50  # Get enough bars for indicators
            )

            if not candles or len(candles) < config.slow_period:
                logger.warning(f"Insufficient data for {symbol}")
                return
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return

        # Generate signal
        signal = strategy.generate_signal(candles)

        if signal == 0:  # No signal
            logger.debug(f"{symbol}: No signal")
            return

        # Determine order type
        order_type = "BUY" if signal > 0 else "SELL"

        # Check if we already have a position in this direction
        existing_position = None
        for pos in positions:
            if pos.type == order_type:
                existing_position = pos
                break

        if existing_position:
            logger.debug(f"{symbol}: Already have {order_type} position #{existing_position.ticket}")
            return

        # Calculate position size based on risk
        volume = self._calculate_position_size(
            connector, symbol, config, account
        )

        if volume <= 0:
            logger.warning(f"{symbol}: Invalid volume calculated: {volume}")
            return

        # Calculate SL/TP
        current_price = symbol_info.ask if order_type == "BUY" else symbol_info.bid
        point = symbol_info.point

        sl_price = None
        tp_price = None

        if config.sl_pips > 0:
            sl_distance = config.sl_pips * 10 * point  # Convert pips to price
            sl_price = current_price - sl_distance if order_type == "BUY" else current_price + sl_distance

        if config.tp_pips > 0:
            tp_distance = config.tp_pips * 10 * point  # Convert pips to price
            tp_price = current_price + tp_distance if order_type == "BUY" else current_price - tp_distance

        # Execute trade
        logger.info(f"{symbol}: {order_type} signal - Opening position (volume: {volume})")

        try:
            result = connector.open_position(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                stop_loss=sl_price,
                take_profit=tp_price,
                comment=f"TradingMTQ Auto - {config.strategy_type}"
            )

            if result and result.get('success'):
                ticket = result.get('ticket')
                logger.info(f"{symbol}: Position opened successfully - Ticket #{ticket}")
            else:
                error = result.get('error', 'Unknown error') if result else 'No response'
                logger.error(f"{symbol}: Failed to open position - {error}")

        except Exception as e:
            logger.error(f"{symbol}: Exception opening position - {e}", exc_info=True)

    def _calculate_position_size(self, connector, symbol: str,
                                 config: currency_models.CurrencyConfiguration,
                                 account: TradingAccount) -> float:
        """
        Calculate position size based on risk management rules.

        Args:
            connector: MT5 connector
            symbol: Trading symbol
            config: Currency configuration
            account: Trading account

        Returns:
            Position size in lots
        """
        try:
            account_info = connector.get_account_info()
            if not account_info:
                return config.min_position_size

            balance = account_info.balance

            # Simple risk-based calculation
            risk_amount = balance * (config.risk_percent / 100)

            # Get symbol info for tick value
            symbol_info = connector.get_symbol_info(symbol)
            if not symbol_info:
                return config.min_position_size

            # Calculate lot size (simplified)
            # In production, this should account for pip value, stop loss distance, etc.
            volume = config.min_position_size

            # Apply max position size limit
            volume = min(volume, config.max_position_size)

            # Ensure within broker limits
            if hasattr(symbol_info, 'volume_min'):
                volume = max(volume, symbol_info.volume_min)
            if hasattr(symbol_info, 'volume_max'):
                volume = min(volume, symbol_info.volume_max)

            return round(volume, 2)

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return config.min_position_size

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the trading bot service.

        Returns:
            Status dictionary
        """
        connected_accounts = session_manager.list_active_sessions()

        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "connected_accounts": len(connected_accounts),
            "account_ids": connected_accounts,
            "active_traders": len(self._traders)
        }


# Global instance
trading_bot_service = TradingBotService(check_interval=60)

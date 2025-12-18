"""
Bot Control Service

Manages the trading bot lifecycle: start, stop, pause, resume.
Controls the MultiCurrencyOrchestrator and tracks bot state in database.
"""
import asyncio
import threading
import os
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from src.database import BotState, BotStatus, get_session
from src.trading.orchestrator import MultiCurrencyOrchestrator
from src.config_manager import ConfigurationManager
from src.utils.logger import get_logger
from src.services.session_manager import session_manager
from src.database import TradingAccount


logger = get_logger(__name__)


class BotControlService:
    """
    Bot lifecycle management service

    Manages a single instance of the trading bot orchestrator.
    Provides start/stop/pause/resume controls with state persistence.
    """

    def __init__(self):
        """Initialize bot control service"""
        self._orchestrator: Optional[MultiCurrencyOrchestrator] = None
        self._bot_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._pause_event: threading.Event = threading.Event()
        self._lock = asyncio.Lock()
        logger.info("BotControlService initialized")

    async def start_bot(
        self,
        db: Session,
        config_file: str = "config/currencies.yaml",
        aggressive: bool = False,
        demo: bool = True,
        interval: Optional[int] = None,
        max_concurrent: Optional[int] = None,
        enable_ml: bool = True,
        enable_llm: bool = True,
        account_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Start the trading bot

        Args:
            db: Database session
            config_file: Path to configuration file
            aggressive: Use aggressive configuration
            demo: Run in demo mode
            interval: Override interval seconds
            max_concurrent: Override max concurrent trades
            enable_ml: Enable ML enhancement
            enable_llm: Enable LLM sentiment
            account_id: Specific account to trade (None = use default)

        Returns:
            (success, error_message)
        """
        async with self._lock:
            try:
                # Check if bot is already running
                current_state = await self._get_bot_state(db)
                if current_state and current_state.status in [BotStatus.RUNNING, BotStatus.STARTING]:
                    return False, f"Bot is already {current_state.status.value}"

                # Update state to STARTING
                bot_state = await self._update_bot_state(
                    db,
                    status=BotStatus.STARTING,
                    config_file=config_file,
                    is_aggressive=aggressive,
                    is_demo=demo,
                    ml_enabled=enable_ml,
                    llm_enabled=enable_llm
                )

                logger.info(
                    f"Starting bot with config={config_file}, aggressive={aggressive}, "
                    f"ml={enable_ml}, llm={enable_llm}"
                )

                # Load configuration
                config_manager = ConfigurationManager()

                # Use aggressive config if specified
                if aggressive:
                    config_file = "config/currencies_aggressive.yaml"

                config = config_manager.load_config(config_file)

                # Apply overrides
                if interval is not None:
                    config.global_config.interval_seconds = interval
                if max_concurrent is not None:
                    config.global_config.max_concurrent_trades = max_concurrent

                # Get account and connector
                if account_id is None:
                    # Get default account
                    query = select(TradingAccount).where(
                        TradingAccount.is_active == True,
                        TradingAccount.is_default == True
                    )
                    result = db.execute(query)
                    account = result.scalar_one_or_none()

                    if not account:
                        # Get first active account
                        query = select(TradingAccount).where(TradingAccount.is_active == True)
                        result = db.execute(query)
                        account = result.scalar_one_or_none()
                else:
                    account = db.get(TradingAccount, account_id)

                if not account:
                    await self._update_bot_state(
                        db,
                        status=BotStatus.ERROR,
                        last_error="No active trading account found"
                    )
                    return False, "No active trading account found"

                # Ensure account is connected
                connector = session_manager.get_session(account.id)
                if not connector:
                    # Connect the account
                    success, error = await session_manager.connect_account(account, db)
                    if not success:
                        await self._update_bot_state(
                            db,
                            status=BotStatus.ERROR,
                            last_error=f"Failed to connect to MT5: {error}"
                        )
                        return False, f"Failed to connect to MT5: {error}"

                    connector = session_manager.get_session(account.id)

                # Create orchestrator
                self._orchestrator = MultiCurrencyOrchestrator(
                    connector=connector,
                    config=config,
                    enable_ml=enable_ml,
                    enable_llm=enable_llm
                )

                # Add currencies from config
                active_currencies = []
                for symbol, currency_config in config.currencies.items():
                    if currency_config.enabled:
                        self._orchestrator.add_currency(currency_config)
                        active_currencies.append(symbol)
                        logger.info(f"Added currency: {symbol}")

                if not active_currencies:
                    await self._update_bot_state(
                        db,
                        status=BotStatus.ERROR,
                        last_error="No enabled currencies in configuration"
                    )
                    return False, "No enabled currencies in configuration"

                # Update state with active currencies
                await self._update_bot_state(
                    db,
                    active_currencies={'symbols': active_currencies},
                    config_overrides={
                        'interval': interval,
                        'max_concurrent': max_concurrent
                    }
                )

                # Start bot in background thread
                self._stop_event.clear()
                self._pause_event.clear()
                self._bot_thread = threading.Thread(
                    target=self._run_bot_loop,
                    args=(db,),
                    daemon=True
                )
                self._bot_thread.start()

                # Update state to RUNNING
                await self._update_bot_state(
                    db,
                    status=BotStatus.RUNNING,
                    started_at=datetime.utcnow(),
                    process_id=os.getpid(),
                    thread_id=str(self._bot_thread.ident)
                )

                logger.info(f"Bot started successfully with {len(active_currencies)} currencies")
                return True, None

            except Exception as e:
                logger.error(f"Failed to start bot: {e}", exc_info=True)
                await self._update_bot_state(
                    db,
                    status=BotStatus.ERROR,
                    last_error=str(e),
                    last_error_at=datetime.utcnow()
                )
                return False, str(e)

    async def stop_bot(self, db: Session) -> Tuple[bool, Optional[str]]:
        """
        Stop the trading bot

        Args:
            db: Database session

        Returns:
            (success, error_message)
        """
        async with self._lock:
            try:
                # Check if bot is running
                current_state = await self._get_bot_state(db)
                if not current_state or current_state.status not in [BotStatus.RUNNING, BotStatus.PAUSED]:
                    return False, f"Bot is not running (current status: {current_state.status.value if current_state else 'unknown'})"

                logger.info("Stopping bot...")

                # Update state to STOPPING
                await self._update_bot_state(db, status=BotStatus.STOPPING)

                # Signal stop
                self._stop_event.set()
                self._pause_event.clear()  # Unpause if paused

                # Wait for thread to finish (with timeout)
                if self._bot_thread and self._bot_thread.is_alive():
                    self._bot_thread.join(timeout=30.0)

                    if self._bot_thread.is_alive():
                        logger.warning("Bot thread did not stop gracefully within timeout")

                # Cleanup
                self._orchestrator = None
                self._bot_thread = None

                # Update state to STOPPED
                await self._update_bot_state(
                    db,
                    status=BotStatus.STOPPED,
                    stopped_at=datetime.utcnow()
                )

                logger.info("Bot stopped successfully")
                return True, None

            except Exception as e:
                logger.error(f"Failed to stop bot: {e}", exc_info=True)
                await self._update_bot_state(
                    db,
                    status=BotStatus.ERROR,
                    last_error=str(e),
                    last_error_at=datetime.utcnow()
                )
                return False, str(e)

    async def pause_bot(self, db: Session) -> Tuple[bool, Optional[str]]:
        """
        Pause the trading bot

        Args:
            db: Database session

        Returns:
            (success, error_message)
        """
        async with self._lock:
            try:
                # Check if bot is running
                current_state = await self._get_bot_state(db)
                if not current_state or current_state.status != BotStatus.RUNNING:
                    return False, f"Bot is not running (current status: {current_state.status.value if current_state else 'unknown'})"

                logger.info("Pausing bot...")

                # Update state to PAUSING
                await self._update_bot_state(db, status=BotStatus.PAUSING)

                # Signal pause
                self._pause_event.set()

                # Update state to PAUSED
                await self._update_bot_state(
                    db,
                    status=BotStatus.PAUSED,
                    paused_at=datetime.utcnow()
                )

                logger.info("Bot paused successfully")
                return True, None

            except Exception as e:
                logger.error(f"Failed to pause bot: {e}", exc_info=True)
                return False, str(e)

    async def resume_bot(self, db: Session) -> Tuple[bool, Optional[str]]:
        """
        Resume the paused trading bot

        Args:
            db: Database session

        Returns:
            (success, error_message)
        """
        async with self._lock:
            try:
                # Check if bot is paused
                current_state = await self._get_bot_state(db)
                if not current_state or current_state.status != BotStatus.PAUSED:
                    return False, f"Bot is not paused (current status: {current_state.status.value if current_state else 'unknown'})"

                logger.info("Resuming bot...")

                # Clear pause signal
                self._pause_event.clear()

                # Update state to RUNNING
                await self._update_bot_state(db, status=BotStatus.RUNNING)

                logger.info("Bot resumed successfully")
                return True, None

            except Exception as e:
                logger.error(f"Failed to resume bot: {e}", exc_info=True)
                return False, str(e)

    async def get_bot_status(self, db: Session) -> Dict[str, Any]:
        """
        Get current bot status

        Args:
            db: Database session

        Returns:
            Bot status dictionary
        """
        try:
            bot_state = await self._get_bot_state(db)

            if not bot_state:
                return {
                    'status': 'stopped',
                    'is_running': False,
                    'is_paused': False,
                    'autotrading_enabled': None,
                    'message': 'No bot state found'
                }

            # Check AutoTrading status if bot is running
            autotrading_enabled = None
            if bot_state.status == BotStatus.RUNNING and self._orchestrator:
                try:
                    connector = self._orchestrator.connector
                    if connector and hasattr(connector, 'is_autotrading_enabled'):
                        autotrading_enabled = connector.is_autotrading_enabled()
                except Exception as e:
                    logger.warning(f"Failed to check AutoTrading status: {e}")

            return {
                **bot_state.to_dict(),
                'is_running': bot_state.status == BotStatus.RUNNING,
                'is_paused': bot_state.status == BotStatus.PAUSED,
                'autotrading_enabled': autotrading_enabled,
                'has_error': bot_state.status == BotStatus.ERROR
            }

        except Exception as e:
            logger.error(f"Failed to get bot status: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }

    def _run_bot_loop(self, db: Session):
        """
        Bot main loop (runs in background thread)

        Args:
            db: Database session
        """
        logger.info("Bot loop started")

        try:
            while not self._stop_event.is_set():
                # Check if paused
                if self._pause_event.is_set():
                    self._stop_event.wait(timeout=1.0)
                    continue

                # Run one cycle
                try:
                    self._orchestrator.process_single_cycle()

                    # Update heartbeat and stats
                    with get_session() as session:
                        bot_state = session.query(BotState).order_by(desc(BotState.id)).first()
                        if bot_state:
                            bot_state.last_heartbeat = datetime.utcnow()
                            bot_state.total_cycles += 1
                            bot_state.successful_cycles += 1
                            session.commit()

                except Exception as e:
                    logger.error(f"Error in bot cycle: {e}", exc_info=True)

                    # Update error stats
                    with get_session() as session:
                        bot_state = session.query(BotState).order_by(desc(BotState.id)).first()
                        if bot_state:
                            bot_state.failed_cycles += 1
                            bot_state.error_count += 1
                            bot_state.last_error = str(e)
                            bot_state.last_error_at = datetime.utcnow()
                            session.commit()

                # Wait for next interval
                interval = self._orchestrator.config.global_config.interval_seconds
                self._stop_event.wait(timeout=interval)

            logger.info("Bot loop stopped")

        except Exception as e:
            logger.error(f"Fatal error in bot loop: {e}", exc_info=True)

            # Update state to ERROR
            with get_session() as session:
                bot_state = session.query(BotState).order_by(desc(BotState.id)).first()
                if bot_state:
                    bot_state.status = BotStatus.ERROR
                    bot_state.last_error = str(e)
                    bot_state.last_error_at = datetime.utcnow()
                    session.commit()

    async def _get_bot_state(self, db: Session) -> Optional[BotState]:
        """Get current bot state from database"""
        query = select(BotState).order_by(desc(BotState.id))
        result = db.execute(query)
        return result.scalar_one_or_none()

    async def _update_bot_state(
        self,
        db: Session,
        status: Optional[BotStatus] = None,
        **kwargs
    ) -> BotState:
        """Update or create bot state"""
        bot_state = await self._get_bot_state(db)

        if not bot_state:
            # Create new state
            bot_state = BotState()
            db.add(bot_state)

        # Update fields
        if status is not None:
            bot_state.status = status

        for key, value in kwargs.items():
            if hasattr(bot_state, key):
                setattr(bot_state, key, value)

        bot_state.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(bot_state)

        return bot_state


# Global bot control service instance
bot_service = BotControlService()

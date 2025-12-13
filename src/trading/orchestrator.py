"""
Multi-Currency Trading Orchestrator
Manages multiple currency traders with independent configurations

Refactored to use Phase 0 patterns:
- Structured JSON logging with correlation IDs
- Specific exceptions instead of silent errors
- Error context preservation
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Phase 0 imports - NEW
from src.exceptions import (
    TradingError, InvalidSymbolError, OrderExecutionError,
    build_order_context
)
from src.utils.structured_logger import StructuredLogger, CorrelationContext
from src.utils.error_handlers import handle_mt5_errors

from src.connectors.base import BaseMetaTraderConnector
from src.strategies.base import BaseStrategy
from .currency_trader import CurrencyTrader, CurrencyTraderConfig
from .position_manager import PositionManager
from .intelligent_position_manager import IntelligentPositionManager, PositionAction

# Database imports - Phase 5.1
from src.database.repository import AccountSnapshotRepository
from src.database.connection import get_session

logger = StructuredLogger(__name__)


class MultiCurrencyOrchestrator:
    """
    Orchestrates trading across multiple currency pairs
    - Each currency has independent configuration
    - Isolated error handling per currency
    - Portfolio-level risk management
    - Optional parallel execution

    Uses Phase 0 patterns:
    - Structured logging with correlation IDs
    - Specific exception types
    - Automatic error context
    """

    def __init__(self,
                 connector: BaseMetaTraderConnector,
                 max_concurrent_trades: int = 15,
                 portfolio_risk_percent: float = 10.0,
                 use_intelligent_manager: bool = True):
        """
        Initialize orchestrator

        Args:
            connector: MT5 connector instance
            max_concurrent_trades: Soft limit for positions (intelligent manager can override)
            portfolio_risk_percent: Total risk limit across all pairs
            use_intelligent_manager: Use AI-powered position management
        """
        self.connector = connector
        self.max_concurrent_trades = max_concurrent_trades
        self.portfolio_risk_percent = portfolio_risk_percent
        self.use_intelligent_manager = use_intelligent_manager

        # Currency traders
        self.traders: Dict[str, CurrencyTrader] = {}

        # Position manager for automatic SL/TP
        self.position_manager = PositionManager(connector)

        # Intelligent position manager (AI-powered)
        if use_intelligent_manager:
            self.intelligent_manager = IntelligentPositionManager(connector)
            logger.info("Intelligent Position Manager enabled", feature="ai_manager")
        else:
            self.intelligent_manager = None

        # Portfolio statistics
        self.total_cycles = 0
        self.start_time = datetime.now()

        # Database repository - Phase 5.1
        self.snapshot_repo = AccountSnapshotRepository()

        logger.info(
            "MultiCurrencyOrchestrator initialized",
            max_concurrent_trades=max_concurrent_trades,
            portfolio_risk_percent=portfolio_risk_percent,
            intelligent_manager=use_intelligent_manager
        )

    def add_currency(self, config: CurrencyTraderConfig) -> Optional[CurrencyTrader]:
        """
        Add a currency pair to trade

        Args:
            config: Currency trader configuration

        Returns:
            Created CurrencyTrader instance or None if validation failed
        """
        with CorrelationContext():
            if config.symbol in self.traders:
                logger.warning(
                    "Currency already added, skipping",
                    symbol=config.symbol,
                    action="skip"
                )
                return None

            trader = CurrencyTrader(config, self.connector, self.intelligent_manager)

            # Check if symbol is valid
            if not trader.is_valid:
                logger.warning(
                    "Skipping currency - not available on broker",
                    symbol=config.symbol,
                    action="skip"
                )
                return None

            self.traders[config.symbol] = trader

            logger.info(
                "Currency added successfully",
                symbol=config.symbol,
                strategy=config.strategy.name,
                risk_percent=config.risk_percent,
                mode='position' if config.use_position_trading else 'crossover'
            )

            return trader

    def enable_ml_for_all(self, ml_model):
        """
        Enable ML enhancement for all currency traders

        Args:
            ml_model: Trained ML model instance
        """
        with CorrelationContext():
            for symbol, trader in self.traders.items():
                trader.enable_ml_enhancement(ml_model)

            if self.intelligent_manager:
                self.intelligent_manager.set_ml_predictor(ml_model)

            logger.info(
                "ML enabled for all currency pairs",
                currency_count=len(self.traders),
                feature="ml_enhancement"
            )

    def enable_llm_for_all(self, sentiment_analyzer, market_analyst=None):
        """
        Enable LLM sentiment filtering for all currency traders

        Args:
            sentiment_analyzer: LLM sentiment analyzer instance
            market_analyst: Optional LLM market analyst
        """
        with CorrelationContext():
            for symbol, trader in self.traders.items():
                trader.enable_sentiment_filter(sentiment_analyzer, market_analyst)

            if self.intelligent_manager:
                self.intelligent_manager.set_sentiment_analyzer(sentiment_analyzer)
                if market_analyst:
                    self.intelligent_manager.set_llm_analyst(market_analyst)

            logger.info(
                "LLM enabled for all currency pairs",
                currency_count=len(self.traders),
                has_market_analyst=market_analyst is not None,
                feature="llm_sentiment"
            )

    def add_currencies_from_config(self,
                                   symbols: List[str],
                                   strategy: BaseStrategy,
                                   default_config: Dict[str, Any]) -> None:
        """
        Add multiple currencies with same base configuration

        Args:
            symbols: List of currency symbols
            strategy: Strategy instance (will be shared or cloned)
            default_config: Default configuration parameters
        """
        with CorrelationContext():
            for symbol in symbols:
                config = CurrencyTraderConfig(
                    symbol=symbol,
                    strategy=strategy,
                    **default_config
                )
                self.add_currency(config)

            logger.info(
                "Bulk currencies added",
                symbol_count=len(symbols),
                strategy=strategy.name
            )

    def remove_currency(self, symbol: str) -> bool:
        """
        Remove a currency from trading

        Args:
            symbol: Currency symbol to remove

        Returns:
            True if removed, False if not found
        """
        with CorrelationContext():
            if symbol in self.traders:
                del self.traders[symbol]
                logger.info("Currency removed from trading", symbol=symbol)
                return True

            logger.warning("Currency not found for removal", symbol=symbol)
            return False

    @handle_mt5_errors(retry_count=2, fallback_return=0)
    def get_open_positions_count(self) -> int:
        """
        Get current number of open positions for managed currencies only

        Returns:
            Number of open positions
        """
        with CorrelationContext():
            positions = self.connector.get_positions()

            # Filter to only show positions for currencies we're managing
            managed_positions = [pos for pos in positions if pos.symbol in self.traders] if positions else []
            count = len(managed_positions)

            if managed_positions:
                total_profit = sum(pos.profit for pos in managed_positions)
                logger.debug(
                    "Open positions summary",
                    count=count,
                    total_profit=total_profit,
                    positions=[{
                        'symbol': pos.symbol,
                        'ticket': pos.ticket,
                        'volume': pos.volume,
                        'profit': pos.profit
                    } for pos in managed_positions]
                )

            # Return total count (including non-managed positions for limits)
            return len(positions) if positions else 0

    def can_open_new_position(self) -> bool:
        """
        Check if can open new position based on intelligent manager or limits

        Returns:
            True if can open new position
        """
        with CorrelationContext():
            open_count = self.get_open_positions_count()

            if self.use_intelligent_manager and self.intelligent_manager:
                # Use intelligent limit
                recommended_limit = self.intelligent_manager.get_position_limit_recommendation()
                can_open = open_count < recommended_limit

                if not can_open:
                    logger.info(
                        "Intelligent position limit reached",
                        open_count=open_count,
                        recommended_limit=recommended_limit,
                        feature="ai_limit"
                    )

                return can_open
            else:
                # Use hard limit
                can_open = open_count < self.max_concurrent_trades
                logger.debug(
                    "Position limit check",
                    open_count=open_count,
                    max_limit=self.max_concurrent_trades,
                    can_open=can_open
                )
                return can_open

    def process_single_cycle(self, management_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process one trading cycle for all currencies sequentially

        Args:
            management_config: Configuration for automatic position management

        Returns:
            Dictionary with cycle results
        """
        with CorrelationContext():
            results = {
                'timestamp': datetime.now(),
                'currencies': {},
                'errors': []
            }

            logger.debug("Starting trading cycle", cycle_number=self.total_cycles + 1)

            # Process automatic position management first
            if management_config:
                try:
                    self.position_manager.cleanup_closed_positions()
                    self.position_manager.process_all_positions(management_config)
                    logger.debug("Position management completed")
                except Exception as e:
                    error_msg = f"Position management error: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(
                        "Position management failed",
                        error=str(e),
                        exc_info=True
                    )

            # Let intelligent manager analyze and close positions EVERY cycle
            if self.use_intelligent_manager and self.intelligent_manager:
                try:
                    # Get all open positions and analyze them
                    positions = self.connector.get_positions()
                    if positions:
                        logger.info(
                            "AI analyzing positions",
                            position_count=len(positions),
                            feature="ai_analysis"
                        )
                        portfolio_state = self.intelligent_manager.analyze_portfolio()

                        for position in positions:
                            close_decision = self.intelligent_manager.should_close_position(position, portfolio_state)
                            if close_decision.action == PositionAction.CLOSE_LOSING:
                                logger.info(
                                    "AI closing position",
                                    ticket=position.ticket,
                                    symbol=position.symbol,
                                    reasoning=close_decision.reasoning,
                                    feature="ai_close"
                                )
                                result = self.connector.close_position(position.ticket)
                                if result.success:
                                    logger.info(
                                        "Position closed successfully",
                                        ticket=position.ticket,
                                        symbol=position.symbol
                                    )
                                else:
                                    logger.error(
                                        "Failed to close position",
                                        ticket=position.ticket,
                                        symbol=position.symbol,
                                        error=result.error_message
                                    )
                except Exception as e:
                    logger.error(
                        "AI position analysis error",
                        error=str(e),
                        exc_info=True,
                        feature="ai_analysis"
                    )

            # Process each currency trader
            for symbol, trader in self.traders.items():
                try:
                    # Let the trader handle the full cycle (analyze + execute if needed)
                    cycle_result = trader.process_cycle()
                    results['currencies'][symbol] = cycle_result

                except Exception as e:
                    error_msg = f"{symbol}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(
                        "Currency cycle error",
                        symbol=symbol,
                        error=str(e),
                        exc_info=True
                    )

            self.total_cycles += 1
            logger.debug("Cycle completed", cycle_number=self.total_cycles)

            # Save account snapshot to database - Phase 5.1
            self._save_account_snapshot()

            return results

    def process_parallel_cycle(self, max_workers: int = 3) -> Dict[str, Any]:
        """
        Process one trading cycle for all currencies in parallel

        Args:
            max_workers: Maximum parallel threads

        Returns:
            Dictionary with cycle results
        """
        with CorrelationContext():
            results = {
                'timestamp': datetime.now(),
                'currencies': {},
                'errors': []
            }

            logger.debug(
                "Starting parallel trading cycle",
                cycle_number=self.total_cycles + 1,
                max_workers=max_workers
            )

            # Use ThreadPoolExecutor for parallel execution
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all traders
                future_to_symbol = {
                    executor.submit(trader.process_cycle): symbol
                    for symbol, trader in self.traders.items()
                }

                # Collect results as they complete
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        cycle_result = future.result()
                        results['currencies'][symbol] = cycle_result
                    except Exception as e:
                        error_msg = f"{symbol}: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(
                            "Parallel execution error",
                            symbol=symbol,
                            error=str(e),
                            exc_info=True
                        )

            self.total_cycles += 1
            logger.debug("Parallel cycle completed", cycle_number=self.total_cycles)

            # Save account snapshot to database - Phase 5.1
            self._save_account_snapshot()

            return results

    def run_continuous(self,
                      interval_seconds: int = 30,
                      parallel: bool = False,
                      max_cycles: Optional[int] = None) -> None:
        """
        Run continuous trading loop

        Args:
            interval_seconds: Seconds between cycles
            parallel: Use parallel execution
            max_cycles: Maximum cycles (None = infinite)
        """
        with CorrelationContext():
            logger.info("=" * 80)
            logger.info("  MULTI-CURRENCY TRADING ORCHESTRATOR")
            logger.info("=" * 80)
            logger.info(
                "Orchestrator starting",
                currencies=len(self.traders),
                mode='parallel' if parallel else 'sequential',
                interval_seconds=interval_seconds,
                max_positions=self.max_concurrent_trades,
                portfolio_risk_percent=self.portfolio_risk_percent
            )
            logger.info("=" * 80)

            cycle_count = 0

            try:
                while True:
                    # Check cycle limit
                    if max_cycles and cycle_count >= max_cycles:
                        logger.info(
                            "Maximum cycles reached",
                            max_cycles=max_cycles,
                            total_cycles=cycle_count
                        )
                        break

                    # Process cycle
                    cycle_time = datetime.now()
                    logger.info(f"\n{'=' * 80}")
                    logger.info(
                        "Cycle starting",
                        cycle_number=cycle_count + 1,
                        timestamp=cycle_time.strftime('%a %Y-%m-%d %H:%M:%S')
                    )
                    logger.info("=" * 80)

                    if parallel:
                        results = self.process_parallel_cycle()
                    else:
                        results = self.process_single_cycle()

                    # Determine market status and activity
                    now = datetime.now()
                    is_weekend = now.weekday() >= 5  # Saturday=5, Sunday=6

                    executed_count = sum(1 for r in results['currencies'].values()
                                       if r.get('executed'))
                    signals_count = len(results['currencies'])
                    rejected_count = sum(1 for r in results['currencies'].values()
                                        if r.get('reason'))

                    # Count signals by type
                    buy_signals = sum(1 for r in results['currencies'].values()
                                     if r.get('signal') and r['signal'].type.name == 'BUY')
                    sell_signals = sum(1 for r in results['currencies'].values()
                                      if r.get('signal') and r['signal'].type.name == 'SELL')
                    hold_signals = sum(1 for r in results['currencies'].values()
                                      if r.get('signal') and r['signal'].type.name == 'HOLD')

                    # Show portfolio P/L for managed currencies only
                    positions = self.connector.get_positions()
                    if positions:
                        managed_positions = [pos for pos in positions if pos.symbol in self.traders]
                        if managed_positions:
                            total_profit = sum(pos.profit for pos in managed_positions)
                            profit_positive = total_profit >= 0
                            logger.info(
                                "Portfolio P/L",
                                profit=total_profit,
                                profit_positive=profit_positive,
                                managed_positions=len(managed_positions)
                            )

                    # Cycle summary
                    logger.info(
                        "Cycle summary",
                        executed_count=executed_count,
                        rejected_count=rejected_count,
                        buy_signals=buy_signals,
                        sell_signals=sell_signals,
                        hold_signals=hold_signals,
                        is_weekend=is_weekend,
                        monitored_pairs=len(self.traders)
                    )

                    cycle_count += 1

                    # Wait before next cycle
                    logger.info(
                        "Waiting for next cycle",
                        interval_seconds=interval_seconds,
                        is_weekend=is_weekend
                    )
                    time.sleep(interval_seconds)

            except KeyboardInterrupt:
                logger.info("Trading stopped by user", reason="keyboard_interrupt")
                self.print_final_statistics()

    def print_final_statistics(self) -> None:
        """Print final statistics for managed currencies only"""
        with CorrelationContext():
            logger.info("=" * 80)
            logger.info("  FINAL STATISTICS")
            logger.info("=" * 80)

            total_trades = 0
            total_successful = 0

            # Collect all statistics
            stats_data = []
            for symbol, trader in self.traders.items():
                stats = trader.get_statistics()
                total_trades += stats['total_trades']
                total_successful += stats['successful']
                stats_data.append({
                    'symbol': symbol,
                    'stats': stats
                })

            # Log structured statistics
            logger.info(
                "Final trading statistics",
                total_traders=len(self.traders),
                total_trades=total_trades,
                total_successful=total_successful,
                total_failed=total_trades - total_successful,
                win_rate=(total_successful / total_trades * 100) if total_trades > 0 else 0.0,
                total_cycles=self.total_cycles,
                runtime_seconds=(datetime.now() - self.start_time).total_seconds(),
                trader_stats=stats_data
            )

            # Also print human-readable table
            logger.info("")
            logger.info(f"{'Symbol':<12} {'Total':<8} {'Success':<8} {'Failed':<8} {'Win Rate':<10} {'Last Trade':<20}")
            logger.info("-" * 80)

            for data in stats_data:
                stats = data['stats']
                last_trade = stats['last_trade'] or 'Never'
                logger.info(f"{data['symbol']:<12} {stats['total_trades']:<8} {stats['successful']:<8} "
                           f"{stats['failed']:<8} {stats['win_rate']:>7.1f}%   {last_trade:<20}")

            # Portfolio summary
            logger.info("-" * 80)
            win_rate = (total_successful / total_trades * 100) if total_trades > 0 else 0.0
            logger.info(f"{'PORTFOLIO':<12} {total_trades:<8} {total_successful:<8} "
                       f"{total_trades - total_successful:<8} {win_rate:>7.1f}%   Cycles: {self.total_cycles}")

            runtime = datetime.now() - self.start_time
            logger.info(f"  Runtime: {runtime}")
            logger.info("=" * 80 + "\n")

    def get_trader(self, symbol: str) -> Optional[CurrencyTrader]:
        """Get trader for specific currency"""
        return self.traders.get(symbol)

    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics for all currencies"""
        return {
            symbol: trader.get_statistics()
            for symbol, trader in self.traders.items()
        }

    def __len__(self) -> int:
        """Number of currencies being traded"""
        return len(self.traders)

    def _save_account_snapshot(self) -> None:
        """
        Save current account state to database

        Phase 5.1 database integration - saves portfolio snapshots after each cycle
        """
        try:
            # Get account info from connector
            account_info = self.connector.get_account_info()
            if not account_info:
                logger.warning("Could not retrieve account info for snapshot")
                return

            # Get current positions
            positions = self.connector.get_positions()
            open_positions = len(positions) if positions else 0
            total_volume = sum(p.volume for p in positions) if positions else 0.0

            with get_session() as session:
                snapshot = self.snapshot_repo.create(
                    session,
                    account_number=account_info.login,
                    server=account_info.server,
                    broker=account_info.company,
                    balance=account_info.balance,
                    equity=account_info.equity,
                    profit=account_info.profit,
                    margin=account_info.margin,
                    margin_free=account_info.margin_free,
                    margin_level=account_info.margin_level if hasattr(account_info, 'margin_level') else None,
                    open_positions=open_positions,
                    total_volume=total_volume,
                    snapshot_time=datetime.now()
                )

                logger.debug(
                    "Account snapshot saved",
                    snapshot_id=snapshot.id,
                    balance=float(account_info.balance),
                    equity=float(account_info.equity),
                    open_positions=open_positions
                )
        except Exception as e:
            # Don't fail trading if snapshot save fails
            logger.error(
                "Failed to save account snapshot",
                error=str(e),
                exc_info=True
            )

    def __repr__(self) -> str:
        symbols = list(self.traders.keys())
        return f"MultiCurrencyOrchestrator(currencies={symbols}, cycles={self.total_cycles})"

"""
Multi-Currency Trading Orchestrator
Manages multiple currency traders with independent configurations
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.connectors.base import BaseMetaTraderConnector
from src.strategies.base import BaseStrategy
from src.utils.logger import get_logger
from .currency_trader import CurrencyTrader, CurrencyTraderConfig
from .position_manager import PositionManager
from .intelligent_position_manager import IntelligentPositionManager, PositionAction

logger = get_logger(__name__)


class MultiCurrencyOrchestrator:
    """
    Orchestrates trading across multiple currency pairs
    - Each currency has independent configuration
    - Isolated error handling per currency
    - Portfolio-level risk management
    - Optional parallel execution
    """
    
    def __init__(self, 
                 connector: BaseMetaTraderConnector,
                 max_concurrent_trades: int = 15,  # Increased default, will be managed intelligently
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
            logger.info("🧠 Intelligent Position Manager enabled")
        else:
            self.intelligent_manager = None
        
        # Portfolio statistics
        self.total_cycles = 0
        self.start_time = datetime.now()
    
    def add_currency(self, config: CurrencyTraderConfig) -> Optional[CurrencyTrader]:
        """
        Add a currency pair to trade
        
        Args:
            config: Currency trader configuration
            
        Returns:
            Created CurrencyTrader instance or None if validation failed
        """
        if config.symbol in self.traders:
            logger.warning(f"⚠️  Currency {config.symbol} already added, skipping")
            return None
        
        trader = CurrencyTrader(config, self.connector, self.intelligent_manager)
        
        # Check if symbol is valid
        if not trader.is_valid:
            logger.warning(f"⚠️  Skipping {config.symbol} - not available on broker")
            return None
        
        self.traders[config.symbol] = trader
        
        logger.info(f"✓ Added {config.symbol} - "
                   f"Strategy: {config.strategy.name}, "
                   f"Risk: {config.risk_percent}%, "
                   f"Mode: {'Position' if config.use_position_trading else 'Crossover'}")
        
        return trader
    
    def enable_ml_for_all(self, ml_model):
        """
        Enable ML enhancement for all currency traders
        
        Args:
            ml_model: Trained ML model instance
        """
        for symbol, trader in self.traders.items():
            trader.enable_ml_enhancement(ml_model)
        
        if self.intelligent_manager:
            self.intelligent_manager.set_ml_predictor(ml_model)
        
        logger.info(f"✅ ML enabled for {len(self.traders)} currency pairs")
    
    def enable_llm_for_all(self, sentiment_analyzer, market_analyst=None):
        """
        Enable LLM sentiment filtering for all currency traders
        
        Args:
            sentiment_analyzer: LLM sentiment analyzer instance
            market_analyst: Optional LLM market analyst
        """
        for symbol, trader in self.traders.items():
            trader.enable_sentiment_filter(sentiment_analyzer, market_analyst)
        
        if self.intelligent_manager:
            self.intelligent_manager.set_sentiment_analyzer(sentiment_analyzer)
            if market_analyst:
                self.intelligent_manager.set_llm_analyst(market_analyst)
        
        logger.info(f"✅ LLM enabled for {len(self.traders)} currency pairs")
    
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
        for symbol in symbols:
            config = CurrencyTraderConfig(
                symbol=symbol,
                strategy=strategy,
                **default_config
            )
            self.add_currency(config)
    
    def remove_currency(self, symbol: str) -> bool:
        """Remove a currency from trading"""
        if symbol in self.traders:
            del self.traders[symbol]
            logger.info(f"Removed {symbol} from trading")
            return True
        return False
    
    def get_open_positions_count(self) -> int:
        """Get current number of open positions for managed currencies only"""
        positions = self.connector.get_positions()
        
        # Filter to only show positions for currencies we're managing
        managed_positions = [pos for pos in positions if pos.symbol in self.traders] if positions else []
        count = len(managed_positions)
        
        if managed_positions:
            total_profit = sum(pos.profit for pos in managed_positions)
            logger.debug(f"Open positions: {count}, Total P/L: ${total_profit:.2f}")
            for pos in managed_positions:
                logger.debug(f"  [{pos.symbol}] Ticket #{pos.ticket}, Volume {pos.volume}, P/L: ${pos.profit:.2f}")
        
        # Return total count (including non-managed positions for limits)
        return len(positions) if positions else 0
    
    def can_open_new_position(self) -> bool:
        """
        Check if can open new position based on intelligent manager or limits
        
        Returns:
            True if can open new position
        """
        open_count = self.get_open_positions_count()
        
        if self.use_intelligent_manager and self.intelligent_manager:
            # Use intelligent limit
            recommended_limit = self.intelligent_manager.get_position_limit_recommendation()
            can_open = open_count < recommended_limit
            if not can_open:
                logger.info(f"🧠 Intelligent limit: {open_count}/{recommended_limit} positions")
            return can_open
        else:
            # Use hard limit
            return open_count < self.max_concurrent_trades
    
    def process_single_cycle(self, management_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process one trading cycle for all currencies sequentially
        
        Args:
            management_config: Configuration for automatic position management
        
        Returns:
            Dictionary with cycle results
        """
        results = {
            'timestamp': datetime.now(),
            'currencies': {},
            'errors': []
        }
        
        # Process automatic position management first
        if management_config:
            try:
                self.position_manager.cleanup_closed_positions()
                self.position_manager.process_all_positions(management_config)
            except Exception as e:
                results['errors'].append(f"Position management error: {str(e)}")
        
        # Let intelligent manager analyze and close positions EVERY cycle
        if self.use_intelligent_manager and self.intelligent_manager:
            try:
                # Get all open positions and analyze them
                positions = self.connector.get_positions()
                if positions:
                    logger.info(f"🧠 AI analyzing {len(positions)} open positions...")
                    portfolio_state = self.intelligent_manager.analyze_portfolio()
                    
                    for position in positions:
                        close_decision = self.intelligent_manager.should_close_position(position, portfolio_state)
                        if close_decision.action == PositionAction.CLOSE_LOSING:
                            logger.info(f"🚨 AI closing: {close_decision.reasoning}")
                            result = self.connector.close_position(position.ticket)
                            if result.success:
                                logger.info(f"✅ Closed #{position.ticket}")
                            else:
                                logger.error(f"❌ Failed to close #{position.ticket}")
            except Exception as e:
                logger.error(f"⚠️  AI position analysis error: {e}")
        
        for symbol, trader in self.traders.items():
            try:
                # Let the trader handle the full cycle (analyze + execute if needed)
                cycle_result = trader.process_cycle()
                results['currencies'][symbol] = cycle_result
                
            except Exception as e:
                error_msg = f"{symbol}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(f"✗ [{symbol}] Error: {str(e)}")
        
        self.total_cycles += 1
        return results
    
    def process_parallel_cycle(self, max_workers: int = 3) -> Dict[str, Any]:
        """
        Process one trading cycle for all currencies in parallel
        
        Args:
            max_workers: Maximum parallel threads
            
        Returns:
            Dictionary with cycle results
        """
        results = {
            'timestamp': datetime.now(),
            'currencies': {},
            'errors': []
        }
        
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
                    logger.error(f"✗ [{symbol}] Parallel execution error: {str(e)}")
        
        self.total_cycles += 1
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
        logger.info("=" * 80)
        logger.info("  MULTI-CURRENCY TRADING ORCHESTRATOR")
        logger.info("=" * 80)
        logger.info(f"  Currencies: {len(self.traders)}")
        logger.info(f"  Mode: {'Parallel' if parallel else 'Sequential'}")
        logger.info(f"  Interval: {interval_seconds}s")
        logger.info(f"  Max Positions: {self.max_concurrent_trades}")
        logger.info(f"  Portfolio Risk: {self.portfolio_risk_percent}%")
        logger.info("=" * 80)
        
        cycle_count = 0
        
        try:
            while True:
                # Check cycle limit
                if max_cycles and cycle_count >= max_cycles:
                    logger.info(f"Reached maximum cycles ({max_cycles})")
                    break
                
                # Process cycle - less verbose header
                cycle_time = datetime.now()
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Cycle #{cycle_count + 1} - {cycle_time.strftime('%a %Y-%m-%d %H:%M:%S')}")
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
                no_signal_count = sum(1 for r in results['currencies'].values() 
                                     if not r.get('executed') and not r.get('reason'))
                rejected_count = sum(1 for r in results['currencies'].values() 
                                    if r.get('reason'))
                
                # Count signals by type for better visibility
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
                        profit_icon = "💚" if total_profit >= 0 else "❌"
                        logger.info(f"💼 Portfolio P/L: {profit_icon} ${total_profit:.2f} ({len(managed_positions)} managed positions)")
                
                # Cycle summary with context
                signal_summary = f"Signals: {buy_signals}×BUY, {sell_signals}×SELL, {hold_signals}×HOLD" if (buy_signals + sell_signals + hold_signals) > 0 else "No signals"
                
                if is_weekend:
                    logger.info(f"📅 Weekend - Market closed, monitoring only | {signal_summary}")
                elif executed_count > 0:
                    logger.info(f"📊 Cycle Summary: {executed_count} trades executed | {signal_summary}")
                elif rejected_count > 0:
                    logger.info(f"🧠 {rejected_count} signals analyzed, no trades approved by AI | {signal_summary}")
                elif signals_count == 0:
                    logger.info(f"😴 No trading signals detected across {len(self.traders)} pairs")
                else:
                    logger.info(f"📊 Monitoring {len(self.traders)} pairs | {signal_summary} (no changes)")
                
                cycle_count += 1
                
                # Wait before next cycle
                if is_weekend:
                    logger.info(f"⏳ Weekend mode: Waiting {interval_seconds}s...")
                else:
                    logger.info(f"⏳ Waiting {interval_seconds}s until next cycle...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("⏹️  Trading stopped by user")
            self.print_final_statistics()
    
    def print_final_statistics(self) -> None:
        """Print final statistics for managed currencies only"""
        logger.info("=" * 80)
        logger.info("  FINAL STATISTICS")
        logger.info("=" * 80)
        
        total_trades = 0
        total_successful = 0
        
        # Table header
        logger.info("")
        logger.info(f"{'Symbol':<12} {'Total':<8} {'Success':<8} {'Failed':<8} {'Win Rate':<10} {'Last Trade':<20}")
        logger.info("-" * 80)
        
        # Table rows
        for symbol, trader in self.traders.items():
            stats = trader.get_statistics()
            total_trades += stats['total_trades']
            total_successful += stats['successful']
            
            last_trade = stats['last_trade'] or 'Never'
            logger.info(f"{symbol:<12} {stats['total_trades']:<8} {stats['successful']:<8} "
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
    
    def __repr__(self) -> str:
        symbols = list(self.traders.keys())
        return f"MultiCurrencyOrchestrator(currencies={symbols}, cycles={self.total_cycles})"

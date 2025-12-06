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
from .currency_trader import CurrencyTrader, CurrencyTraderConfig
from .position_manager import PositionManager


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
                 max_concurrent_trades: int = 5,
                 portfolio_risk_percent: float = 10.0):
        """
        Initialize orchestrator
        
        Args:
            connector: MT5 connector instance
            max_concurrent_trades: Maximum simultaneous open positions
            portfolio_risk_percent: Total risk limit across all pairs
        """
        self.connector = connector
        self.max_concurrent_trades = max_concurrent_trades
        self.portfolio_risk_percent = portfolio_risk_percent
        
        # Currency traders
        self.traders: Dict[str, CurrencyTrader] = {}
        
        # Position manager for automatic SL/TP
        self.position_manager = PositionManager(connector)
        
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
            print(f"⚠️  Currency {config.symbol} already added, skipping")
            return None
        
        trader = CurrencyTrader(config, self.connector)
        
        # Check if symbol is valid
        if not trader.is_valid:
            print(f"⚠️  Skipping {config.symbol} - not available on broker")
            return None
        
        self.traders[config.symbol] = trader
        
        print(f"✓ Added {config.symbol} - "
              f"Strategy: {config.strategy.name}, "
              f"Risk: {config.risk_percent}%, "
              f"Mode: {'Position' if config.use_position_trading else 'Crossover'}")
        
        return trader
    
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
            print(f"Removed {symbol} from trading")
            return True
        return False
    
    def get_open_positions_count(self) -> int:
        """Get current number of open positions"""
        positions = self.connector.get_positions()
        count = len(positions) if positions else 0
        total_profit = sum(pos.profit for pos in positions) if positions else 0.0
        print(f"🔍 DEBUG: Open positions count = {count}, Total P/L: ${total_profit:.2f}")
        if positions:
            for pos in positions:
                print(f"    - {pos.symbol}: Ticket #{pos.ticket}, Volume {pos.volume}, P/L: ${pos.profit:.2f}")
        return count
    
    def can_open_new_position(self) -> bool:
        """Check if can open new position based on limits"""
        open_count = self.get_open_positions_count()
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
        
        for symbol, trader in self.traders.items():
            try:
                # Check position limit
                open_count = self.get_open_positions_count()
                if open_count >= self.max_concurrent_trades:
                    print(f"⏸️  Position limit reached ({self.max_concurrent_trades})")
                    print(f"    Current open positions: {open_count}")
                    break
                
                # Process currency
                cycle_result = trader.process_cycle()
                results['currencies'][symbol] = cycle_result
                
            except Exception as e:
                error_msg = f"{symbol}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"✗ Orchestrator error: {error_msg}")
        
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
                    print(f"✗ Parallel execution error: {error_msg}")
        
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
        print("\n" + "=" * 80)
        print("  MULTI-CURRENCY TRADING ORCHESTRATOR")
        print("=" * 80)
        print(f"  Currencies: {len(self.traders)}")
        print(f"  Mode: {'Parallel' if parallel else 'Sequential'}")
        print(f"  Interval: {interval_seconds}s")
        print(f"  Max Positions: {self.max_concurrent_trades}")
        print(f"  Portfolio Risk: {self.portfolio_risk_percent}%")
        print("=" * 80 + "\n")
        
        cycle_count = 0
        
        try:
            while True:
                # Check cycle limit
                if max_cycles and cycle_count >= max_cycles:
                    print(f"\nReached maximum cycles ({max_cycles})")
                    break
                
                # Process cycle
                print(f"\n{'='*80}")
                print(f"Cycle #{cycle_count + 1} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*80}")
                
                if parallel:
                    results = self.process_parallel_cycle()
                else:
                    results = self.process_single_cycle()
                
                # Show summary
                executed_count = sum(1 for r in results['currencies'].values() 
                                   if r.get('executed'))
                
                # Show portfolio P/L
                positions = self.connector.get_positions()
                if positions:
                    total_profit = sum(pos.profit for pos in positions)
                    profit_icon = "💚" if total_profit >= 0 else "❌"
                    print(f"\n💼 Portfolio P/L: {profit_icon} ${total_profit:.2f} ({len(positions)} positions)")
                
                if executed_count > 0:
                    print(f"📊 Cycle Summary: {executed_count} trades executed")
                
                cycle_count += 1
                
                # Wait before next cycle
                print(f"\n⏳ Waiting {interval_seconds}s until next cycle...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Trading stopped by user")
            self.print_final_statistics()
    
    def print_final_statistics(self) -> None:
        """Print final statistics for all currencies"""
        print("\n" + "=" * 80)
        print("  FINAL STATISTICS")
        print("=" * 80)
        
        total_trades = 0
        total_successful = 0
        
        for symbol, trader in self.traders.items():
            stats = trader.get_statistics()
            total_trades += stats['total_trades']
            total_successful += stats['successful']
            
            print(f"\n{symbol}:")
            print(f"  Total Trades: {stats['total_trades']}")
            print(f"  Successful: {stats['successful']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Win Rate: {stats['win_rate']:.1f}%")
            print(f"  Last Trade: {stats['last_trade'] or 'Never'}")
        
        print("\n" + "-" * 80)
        print(f"Portfolio Total:")
        print(f"  Total Trades: {total_trades}")
        print(f"  Successful: {total_successful}")
        win_rate = (total_successful / total_trades * 100) if total_trades > 0 else 0.0
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Total Cycles: {self.total_cycles}")
        
        runtime = datetime.now() - self.start_time
        print(f"  Runtime: {runtime}")
        print("=" * 80 + "\n")
    
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

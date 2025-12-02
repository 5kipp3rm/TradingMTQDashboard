"""
Automated Trading Bot
Monitors market and executes trades based on strategy signals
"""
import time
from typing import Dict, List, Optional
from datetime import datetime

from .connectors import BaseMetaTraderConnector, OrderType
from .trading import TradingController
from .strategies import BaseStrategy, SignalType
from .utils import get_logger

logger = get_logger(__name__)


class TradingBot:
    """
    Automated Trading Bot
    
    Continuously monitors specified symbols and executes trades
    based on strategy signals.
    """
    
    def __init__(
        self,
        connector: BaseMetaTraderConnector,
        strategy: BaseStrategy,
        symbols: List[str],
        timeframe: str = "M5",
        volume: float = 0.01,
        max_positions: int = 3,
        check_interval: int = 60
    ):
        """
        Initialize trading bot
        
        Args:
            connector: MetaTrader connector
            strategy: Trading strategy
            symbols: List of symbols to trade
            timeframe: Timeframe to analyze (M1, M5, H1, etc.)
            volume: Trading volume in lots
            max_positions: Maximum concurrent positions
            check_interval: Seconds between checks
        """
        self.connector = connector
        self.controller = TradingController(connector)
        self.strategy = strategy
        self.symbols = symbols
        self.timeframe = timeframe
        self.volume = volume
        self.max_positions = max_positions
        self.check_interval = check_interval
        
        self.running = False
        self.positions: Dict[str, int] = {}  # symbol -> ticket
        
        logger.info(f"TradingBot initialized: {strategy.get_name()}")
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Timeframe: {timeframe}, Volume: {volume}")
    
    def start(self):
        """Start the trading bot"""
        if not self.connector.is_connected():
            logger.error("Cannot start bot: Not connected to MetaTrader")
            return False
        
        self.running = True
        logger.info("🤖 Trading Bot started")
        print("\n" + "=" * 70)
        print(" " * 20 + "🤖 TRADING BOT ACTIVE")
        print("=" * 70)
        print(f"Strategy: {self.strategy.get_name()}")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Volume: {self.volume} lots")
        print(f"Max Positions: {self.max_positions}")
        print("=" * 70)
        print("\nPress Ctrl+C to stop\n")
        
        try:
            self._run_loop()
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping bot...")
            self.stop()
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
            print(f"\n❌ Bot error: {e}")
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the trading bot"""
        self.running = False
        logger.info("Trading Bot stopped")
        print("✓ Bot stopped successfully")
    
    def _run_loop(self):
        """Main trading loop"""
        iteration = 0
        
        while self.running:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n[{timestamp}] Iteration #{iteration}")
            print("-" * 70)
            
            # Check each symbol
            for symbol in self.symbols:
                self._check_symbol(symbol)
            
            # Display summary
            self._display_summary()
            
            # Wait before next check
            if self.running:
                print(f"\n⏳ Waiting {self.check_interval}s until next check...")
                time.sleep(self.check_interval)
    
    def _check_symbol(self, symbol: str):
        """Check a symbol for trading signals"""
        try:
            # Get historical data
            bars = self.connector.get_bars(
                symbol=symbol,
                timeframe=self.timeframe,
                count=100  # Get enough bars for strategy
            )
            
            if not bars or len(bars) < 2:
                print(f"  {symbol}: ⚠ Insufficient data")
                return
            
            # Get signal from strategy
            signal = self.strategy.analyze(symbol, self.timeframe, bars)
            
            current_price = bars[-1].close
            
            # Display signal
            signal_icon = {
                SignalType.BUY: "🟢",
                SignalType.SELL: "🔴",
                SignalType.HOLD: "⚪",
                SignalType.CLOSE_BUY: "🟡",
                SignalType.CLOSE_SELL: "🟡"
            }.get(signal.type, "⚪")
            
            print(f"  {symbol}: {signal_icon} {signal.type.value} @ {current_price:.5f}")
            print(f"           {signal.reason}")
            
            # Execute signal
            if signal.type == SignalType.BUY:
                self._execute_buy(signal)
            elif signal.type == SignalType.SELL:
                self._execute_sell(signal)
            
        except Exception as e:
            logger.error(f"Error checking {symbol}: {e}", exc_info=True)
            print(f"  {symbol}: ❌ Error: {e}")
    
    def _execute_buy(self, signal):
        """Execute buy signal"""
        # Check if already have position for this symbol
        if signal.symbol in self.positions:
            logger.info(f"Already have position for {signal.symbol}, skipping")
            return
        
        # Check max positions
        if len(self.positions) >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached, skipping")
            print(f"           ⚠ Max positions reached")
            return
        
        # Execute trade
        result = self.controller.execute_trade(
            symbol=signal.symbol,
            action=OrderType.BUY,
            volume=self.volume,
            sl=signal.stop_loss,
            tp=signal.take_profit,
            comment=f"{self.strategy.get_name()}"
        )
        
        if result.success and result.order_ticket:
            self.positions[signal.symbol] = result.order_ticket
            logger.info(f"✓ BUY executed: {signal.symbol} @ {signal.price:.5f} (Ticket: {result.order_ticket})")
            print(f"           ✓ ORDER PLACED: Ticket #{result.order_ticket}")
            print(f"           SL: {signal.stop_loss:.5f} | TP: {signal.take_profit:.5f}")
        else:
            logger.error(f"✗ BUY failed: {signal.symbol} - {result.error_message}")
            print(f"           ✗ ORDER FAILED: {result.error_message}")
    
    def _execute_sell(self, signal):
        """Execute sell signal"""
        # Check if already have position for this symbol
        if signal.symbol in self.positions:
            logger.info(f"Already have position for {signal.symbol}, skipping")
            return
        
        # Check max positions
        if len(self.positions) >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached, skipping")
            print(f"           ⚠ Max positions reached")
            return
        
        # Execute trade
        result = self.controller.execute_trade(
            symbol=signal.symbol,
            action=OrderType.SELL,
            volume=self.volume,
            sl=signal.stop_loss,
            tp=signal.take_profit,
            comment=f"{self.strategy.get_name()}"
        )
        
        if result.success and result.order_ticket:
            self.positions[signal.symbol] = result.order_ticket
            logger.info(f"✓ SELL executed: {signal.symbol} @ {signal.price:.5f} (Ticket: {result.order_ticket})")
            print(f"           ✓ ORDER PLACED: Ticket #{result.order_ticket}")
            print(f"           SL: {signal.stop_loss:.5f} | TP: {signal.take_profit:.5f}")
        else:
            logger.error(f"✗ SELL failed: {signal.symbol} - {result.error_message}")
            print(f"           ✗ ORDER FAILED: {result.error_message}")
    
    def _display_summary(self):
        """Display current status summary"""
        positions = self.controller.get_open_positions()
        
        # Update positions dict (remove closed positions)
        closed_symbols = []
        for symbol, ticket in self.positions.items():
            if not any(p.ticket == ticket for p in positions):
                closed_symbols.append(symbol)
        
        for symbol in closed_symbols:
            del self.positions[symbol]
            logger.info(f"Position closed: {symbol}")
        
        if positions:
            print(f"\n📊 Open Positions: {len(positions)}")
            total_profit = sum(p.profit for p in positions)
            
            for pos in positions:
                profit_color = "\033[32m" if pos.profit >= 0 else "\033[31m"
                print(f"   {pos.symbol}: {pos.type.value} {pos.volume} lots | "
                      f"P&L: {profit_color}${pos.profit:.2f}\033[0m | "
                      f"Pips: {pos.pnl_pips:.1f}")
            
            total_color = "\033[32m" if total_profit >= 0 else "\033[31m"
            print(f"   Total P&L: {total_color}${total_profit:.2f}\033[0m")
        else:
            print(f"\n📊 Open Positions: 0")
        
        account = self.connector.get_account_info()
        if account:
            print(f"💰 Balance: ${account.balance:,.2f} | Equity: ${account.equity:,.2f}")

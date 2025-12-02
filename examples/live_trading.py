"""
Live Trading Script
Real trading with MT5 using Simple MA Crossover Strategy

WARNING: This script will execute REAL trades on your MT5 account!
- Start with a DEMO account first
- Test thoroughly before using on live account
- Monitor the bot while running
- Set appropriate risk limits
"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import sys
import os
from typing import Optional, Dict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.connectors import (
    MT5Connector, OrderType, AccountUtils,
    trade_server_return_code_description, error_description
)
from src.strategies import SimpleMovingAverageStrategy, Signal, SignalType

# ============================================================================
# CONFIGURATION - UPDATE THESE BEFORE RUNNING!
# ============================================================================

# MT5 Connection
MT5_LOGIN = 12345678  # Your MT5 login
MT5_PASSWORD = "your_password"  # Your MT5 password
MT5_SERVER = "YourBroker-Demo"  # Your broker server

# Trading Parameters
SYMBOL = "EURUSD"  # Symbol to trade
TIMEFRAME = "M5"  # 5-minute timeframe
BARS_TO_ANALYZE = 100  # Number of bars for strategy analysis

# Strategy Parameters
STRATEGY_PARAMS = {
    'fast_period': 10,   # Fast MA period
    'slow_period': 20,   # Slow MA period
    'sl_pips': 20,       # Stop loss in pips
    'tp_pips': 40,       # Take profit in pips
}

# Risk Management
RISK_PERCENT = 1.0  # Risk 1% of account per trade
MAX_POSITIONS = 1   # Maximum concurrent positions
USE_RISK_MANAGEMENT = True  # Use AccountUtils for position sizing

# Trading Hours (24-hour format, broker time)
TRADING_START_HOUR = 0   # Start trading at midnight
TRADING_END_HOUR = 23    # Stop trading at 11 PM

# Loop Settings
CHECK_INTERVAL = 30  # Check for signals every 30 seconds
MAX_RUNTIME_HOURS = 24  # Maximum runtime in hours (0 = unlimited)

# ============================================================================


class LiveTrader:
    """Live trading bot"""
    
    def __init__(self):
        self.connector = MT5Connector("live_trader")
        self.data_handler = None
        self.strategy = None
        self.positions: Dict[int, Dict] = {}  # ticket -> position info
        self.last_signal_time = None
        self.start_time = datetime.now()
        
    def connect(self) -> bool:
        """Connect to MT5"""
        print("\n" + "=" * 80)
        print("  LIVE TRADING BOT - INITIALIZING")
        print("=" * 80)
        print(f"\nStarting at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\nConnecting to MT5...")
        print(f"  Server: {MT5_SERVER}")
        print(f"  Login: {MT5_LOGIN}")
        
        success = self.connector.connect(
            login=MT5_LOGIN,
            password=MT5_PASSWORD,
            server=MT5_SERVER
        )
        
        if not success:
            print("✗ Failed to connect to MT5!")
            print("  Please check:")
            print("  - MT5 is running")
            print("  - Credentials are correct")
            print("  - Server name is correct")
            return False
        
        print("✓ Connected to MT5")
        
        # Display account info
        account = self.connector.get_account_info()
        if account:
            print(f"\nAccount Information:")
            print(f"  Balance: ${account.balance:.2f}")
            print(f"  Equity: ${account.equity:.2f}")
            print(f"  Free Margin: ${account.margin_free:.2f}")
            print(f"  Leverage: 1:{account.leverage}")
            print(f"  Currency: {account.currency}")
        
        return True
    
    def setup_trading(self) -> bool:
        """Setup strategy"""
        print(f"\nSetting up trading components...")
        
        # Initialize strategy
        self.strategy = SimpleMovingAverageStrategy(STRATEGY_PARAMS)
        
        print(f"✓ Strategy: {self.strategy.name}")
        print(f"  Parameters: {STRATEGY_PARAMS}")
        
        # Verify symbol is available
        symbol_info = self.connector.get_symbol_info(SYMBOL)
        if not symbol_info:
            print(f"✗ Symbol {SYMBOL} not available!")
            return False
        
        print(f"\n✓ Symbol: {SYMBOL}")
        print(f"  Bid: {symbol_info.bid:.5f}")
        print(f"  Ask: {symbol_info.ask:.5f}")
        print(f"  Spread: {symbol_info.spread} points")
        print(f"  Min Volume: {symbol_info.volume_min}")
        print(f"  Max Volume: {symbol_info.volume_max}")
        
        return True
    
    def is_trading_hours(self) -> bool:
        """Check if within trading hours"""
        now = datetime.now()
        current_hour = now.hour
        
        if TRADING_START_HOUR <= current_hour < TRADING_END_HOUR:
            return True
        return False
    
    def check_max_runtime(self) -> bool:
        """Check if max runtime exceeded"""
        if MAX_RUNTIME_HOURS == 0:
            return False
        
        elapsed = datetime.now() - self.start_time
        if elapsed.total_seconds() / 3600 >= MAX_RUNTIME_HOURS:
            return True
        return False
    
    def get_current_positions(self):
        """Get current open positions for symbol"""
        positions = self.connector.get_positions(symbol=SYMBOL)
        if positions:
            self.positions = {pos.ticket: {
                'ticket': pos.ticket,
                'type': pos.type,
                'volume': pos.volume,
                'price_open': pos.price_open,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit
            } for pos in positions}
        else:
            self.positions = {}
        return len(self.positions)
    
    def calculate_position_size(self, signal: Signal) -> float:
        """Calculate position size based on risk management"""
        if not USE_RISK_MANAGEMENT or not signal.stop_loss:
            # Use minimum volume
            symbol_info = self.connector.get_symbol_info(SYMBOL)
            return symbol_info.volume_min if symbol_info else 0.01
        
        # Use risk-based position sizing
        order_type = mt5.ORDER_TYPE_BUY if signal.type == SignalType.BUY else mt5.ORDER_TYPE_SELL
        
        lot_size = AccountUtils.risk_based_lot_size(
            symbol=SYMBOL,
            order_type=order_type,
            entry_price=signal.price,
            stop_loss=signal.stop_loss,
            risk_percent=RISK_PERCENT
        )
        
        if lot_size:
            # Round to symbol's volume step
            symbol_info = self.connector.get_symbol_info(SYMBOL)
            if symbol_info:
                volume_step = symbol_info.volume_step
                lot_size = round(lot_size / volume_step) * volume_step
                # Ensure within limits
                lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
            return lot_size
        
        # Fallback to minimum
        return 0.01
    
    def execute_signal(self, signal: Signal):
        """Execute trading signal"""
        if signal.type == SignalType.HOLD:
            return
        
        # Check position limit
        if len(self.positions) >= MAX_POSITIONS:
            print(f"  ⚠ Max positions reached ({MAX_POSITIONS}), skipping signal")
            return
        
        # Calculate position size
        volume = self.calculate_position_size(signal)
        
        print(f"\n{'─' * 80}")
        print(f"EXECUTING SIGNAL:")
        print(f"  Type: {signal.type.name}")
        print(f"  Price: {signal.price:.5f}")
        print(f"  Volume: {volume:.2f} lots")
        print(f"  Stop Loss: {signal.stop_loss:.5f}" if signal.stop_loss else "  Stop Loss: None")
        print(f"  Take Profit: {signal.take_profit:.5f}" if signal.take_profit else "  Take Profit: None")
        print(f"  Reason: {signal.reason}")
        print(f"  Confidence: {signal.confidence:.1%}")
        
        if USE_RISK_MANAGEMENT and signal.stop_loss:
            # Calculate risk amount
            account = self.connector.get_account_info()
            risk_amount = account.balance * (RISK_PERCENT / 100)
            print(f"  Risk: ${risk_amount:.2f} ({RISK_PERCENT}% of balance)")
        
        # Execute order
        order_type = OrderType.BUY if signal.type == SignalType.BUY else OrderType.SELL
        
        result = self.connector.send_order(
            symbol=SYMBOL,
            order_type=order_type,
            volume=volume,
            price=signal.price,
            sl=signal.stop_loss,
            tp=signal.take_profit,
            comment=f"{self.strategy.name}_{signal.type.name}"
        )
        
        if result.success:
            print(f"✓ ORDER EXECUTED")
            print(f"  Ticket: #{result.order_ticket}")
            print(f"  Fill Price: {result.price:.5f}")
            self.last_signal_time = datetime.now()
            
            # Update positions
            self.get_current_positions()
        else:
            error_msg = trade_server_return_code_description(result.error_code)
            print(f"✗ ORDER FAILED")
            print(f"  Error: {error_msg}")
            print(f"  Details: {result.error_message}")
    
    def monitor_positions(self):
        """Monitor and report current positions"""
        if not self.positions:
            return
        
        print(f"\nCurrent Positions ({len(self.positions)}):")
        total_profit = 0.0
        
        for ticket, pos in self.positions.items():
            pos_type = "BUY" if pos['type'] == 0 else "SELL"
            print(f"  #{ticket} - {pos_type} {pos['volume']:.2f} @ {pos['price_open']:.5f}")
            print(f"    SL: {pos['sl']:.5f}, TP: {pos['tp']:.5f}, P/L: ${pos['profit']:.2f}")
            total_profit += pos['profit']
        
        print(f"  Total P/L: ${total_profit:.2f}")
    
    def run(self):
        """Main trading loop"""
        print("\n" + "=" * 80)
        print("  STARTING LIVE TRADING")
        print("=" * 80)
        print(f"\nSymbol: {SYMBOL}")
        print(f"Timeframe: {TIMEFRAME}")
        print(f"Check Interval: {CHECK_INTERVAL} seconds")
        print(f"Risk per Trade: {RISK_PERCENT}%")
        print(f"Max Positions: {MAX_POSITIONS}")
        
        if MAX_RUNTIME_HOURS > 0:
            print(f"Max Runtime: {MAX_RUNTIME_HOURS} hours")
        
        print(f"\nTrading Hours: {TRADING_START_HOUR:02d}:00 - {TRADING_END_HOUR:02d}:00")
        print("\nPress Ctrl+C to stop trading")
        print("=" * 80)
        
        try:
            iteration = 0
            while True:
                iteration += 1
                now = datetime.now()
                
                # Check max runtime
                if self.check_max_runtime():
                    print(f"\n⚠ Max runtime of {MAX_RUNTIME_HOURS} hours reached. Stopping...")
                    break
                
                # Check trading hours
                if not self.is_trading_hours():
                    if iteration % 10 == 1:  # Print every 5 minutes
                        print(f"\n[{now.strftime('%H:%M:%S')}] Outside trading hours, waiting...")
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Checking market...")
                
                # Get current positions
                num_positions = self.get_current_positions()
                
                # Get market data
                bars = self.connector.get_bars(
                    symbol=SYMBOL,
                    timeframe=TIMEFRAME,
                    count=BARS_TO_ANALYZE
                )
                
                if not bars:
                    print("  ⚠ Failed to get market data")
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                # Analyze with strategy
                signal = self.strategy.analyze(SYMBOL, TIMEFRAME, bars)
                
                # Report current state
                current_price = bars[-1].close
                print(f"  Price: {current_price:.5f}")
                print(f"  Signal: {signal.type.name} (confidence: {signal.confidence:.1%})")
                print(f"  Reason: {signal.reason}")
                print(f"  Open Positions: {num_positions}")
                
                # Monitor positions
                self.monitor_positions()
                
                # Execute signal if appropriate
                if signal.type != SignalType.HOLD:
                    # Avoid duplicate signals (wait at least 1 minute)
                    if self.last_signal_time:
                        time_since_last = (now - self.last_signal_time).total_seconds()
                        if time_since_last < 60:
                            print(f"  ⚠ Signal too soon after last ({time_since_last:.0f}s), skipping")
                        else:
                            self.execute_signal(signal)
                    else:
                        self.execute_signal(signal)
                
                # Wait before next check
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
        except Exception as e:
            print(f"\n\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Cleanup and shutdown"""
        print("\n" + "=" * 80)
        print("  SHUTTING DOWN")
        print("=" * 80)
        
        # Get final positions
        self.get_current_positions()
        
        if self.positions:
            print(f"\n⚠ You have {len(self.positions)} open position(s):")
            self.monitor_positions()
            print("\nThese positions will remain open after shutdown.")
            print("Close them manually in MT5 or create a separate close script.")
        else:
            print("\n✓ No open positions")
        
        # Show account status
        account = self.connector.get_account_info()
        if account:
            print(f"\nFinal Account Status:")
            print(f"  Balance: ${account.balance:.2f}")
            print(f"  Equity: ${account.equity:.2f}")
            print(f"  Profit: ${account.profit:.2f}")
        
        # Disconnect
        self.connector.disconnect()
        print("\n✓ Disconnected from MT5")
        print("\nBot stopped at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("=" * 80)


def main():
    """Main entry point"""
    # Verify configuration
    if MT5_LOGIN == 12345678 or MT5_PASSWORD == "your_password":
        print("\n" + "!" * 80)
        print("  ERROR: UPDATE CREDENTIALS BEFORE RUNNING!")
        print("!" * 80)
        print("\nPlease update the following in the script:")
        print("  - MT5_LOGIN")
        print("  - MT5_PASSWORD")
        print("  - MT5_SERVER")
        print("\nAlso review:")
        print("  - SYMBOL (current: {})".format(SYMBOL))
        print("  - RISK_PERCENT (current: {}%)".format(RISK_PERCENT))
        print("  - MAX_POSITIONS (current: {})".format(MAX_POSITIONS))
        print("=" * 80)
        return
    
    # Create and run trader
    trader = LiveTrader()
    
    if not trader.connect():
        return
    
    if not trader.setup_trading():
        trader.connector.disconnect()
        return
    
    # Confirmation
    print("\n" + "!" * 80)
    print("  READY TO START LIVE TRADING")
    print("!" * 80)
    print(f"\nThis bot will:")
    print(f"  - Trade {SYMBOL} on {TIMEFRAME} timeframe")
    print(f"  - Use {trader.strategy.name}")
    print(f"  - Risk {RISK_PERCENT}% per trade")
    print(f"  - Allow maximum {MAX_POSITIONS} position(s)")
    print(f"  - Check every {CHECK_INTERVAL} seconds")
    print("\n⚠ WARNING: This will execute REAL trades on your account!")
    
    response = input("\nType 'START' to begin trading: ")
    
    if response.strip().upper() == 'START':
        trader.run()
    else:
        print("\nCancelled by user")
        trader.connector.disconnect()


if __name__ == "__main__":
    main()

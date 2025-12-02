"""
Quick Start - Simple Live Trading
Minimal configuration for quick testing
"""
import MetaTrader5 as mt5
from datetime import datetime
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.connectors import MT5Connector, OrderType, AccountUtils
from src.strategies import SimpleMovingAverageStrategy, SignalType

# ============================================================================
# UPDATE YOUR CREDENTIALS HERE
# ============================================================================
LOGIN = input("Enter MT5 Login: ").strip()
PASSWORD = input("Enter MT5 Password: ").strip()
SERVER = input("Enter MT5 Server: ").strip()

SYMBOL = input("Enter Symbol (default: EURUSD): ").strip() or "EURUSD"
RISK_PERCENT = float(input("Risk % per trade (default: 1.0): ").strip() or "1.0")

# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("  QUICK START - LIVE TRADING")
    print("=" * 80)
    
    # Connect
    connector = MT5Connector()
    print(f"\nConnecting to {SERVER}...")
    
    if not connector.connect(int(LOGIN), PASSWORD, SERVER):
        print("✗ Connection failed!")
        print("  Check credentials and ensure MT5 is running")
        return
    
    print("✓ Connected!")
    
    # Show account
    account = connector.get_account_info()
    print(f"\nAccount: {account.login}")
    print(f"Balance: ${account.balance:.2f}")
    print(f"Equity: ${account.equity:.2f}")
    print(f"Leverage: 1:{account.leverage}")
    
    # Verify symbol
    symbol_info = connector.get_symbol_info(SYMBOL)
    if not symbol_info:
        print(f"\n✗ Symbol {SYMBOL} not available!")
        connector.disconnect()
        return
    
    print(f"\nSymbol: {SYMBOL}")
    print(f"Bid: {symbol_info.bid:.5f}, Ask: {symbol_info.ask:.5f}")
    
    # Create strategy
    strategy = SimpleMovingAverageStrategy({
        'fast_period': 10,
        'slow_period': 20,
        'sl_pips': 20,
        'tp_pips': 40
    })
    
    print(f"\nStrategy: {strategy.name}")
    print(f"Risk per trade: {RISK_PERCENT}%")
    
    # Confirm
    print("\n" + "!" * 80)
    print("  WARNING: This will execute REAL trades!")
    print("!" * 80)
    confirm = input("\nType 'GO' to start trading: ").strip().upper()
    
    if confirm != 'GO':
        print("Cancelled")
        connector.disconnect()
        return
    
    print("\n" + "=" * 80)
    print("  TRADING ACTIVE - Press Ctrl+C to stop")
    print("=" * 80)
    
    last_signal_time = None
    
    try:
        while True:
            # Get bars
            bars = connector.get_bars(SYMBOL, 'M5', 100)
            
            if not bars:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to get data")
                time.sleep(30)
                continue
            
            # Analyze
            signal = strategy.analyze(SYMBOL, 'M5', bars)
            
            current_price = bars[-1].close
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
                  f"{SYMBOL} @ {current_price:.5f} - "
                  f"Signal: {signal.type.name} ({signal.confidence:.0%})")
            
            # Execute if signal
            if signal.type != SignalType.HOLD:
                # Avoid duplicates
                if last_signal_time:
                    elapsed = (datetime.now() - last_signal_time).total_seconds()
                    if elapsed < 60:
                        print(f"  ⏭ Skipping (too soon: {elapsed:.0f}s)")
                        time.sleep(30)
                        continue
                
                # Calculate lot size
                order_type = mt5.ORDER_TYPE_BUY if signal.type == SignalType.BUY else mt5.ORDER_TYPE_SELL
                lot_size = AccountUtils.risk_based_lot_size(
                    SYMBOL, order_type, signal.price, signal.stop_loss, RISK_PERCENT
                )
                
                if not lot_size:
                    lot_size = symbol_info.volume_min
                
                print(f"  📊 Executing {signal.type.name} - {lot_size:.2f} lots")
                print(f"     Entry: {signal.price:.5f}, SL: {signal.stop_loss:.5f}, TP: {signal.take_profit:.5f}")
                
                # Send order
                result = connector.send_order(
                    TradeRequest(
                        symbol=SYMBOL,
                        order_type=order_type,
                        volume=lot_size,
                        price=signal.price,
                        sl=signal.stop_loss,
                        tp=signal.take_profit
                    )
                )
                
                if result.success:
                    print(f"  ✓ Order #{result.order_ticket} executed @ {result.price:.5f}")
                    last_signal_time = datetime.now()
                else:
                    print(f"  ✗ Failed: {result.error_message}")
            
            time.sleep(30)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Stopped by user")
    finally:
        # Show positions
        positions = connector.get_positions(symbol=SYMBOL)
        if positions:
            print(f"\n📍 Open positions: {len(positions)}")
            for pos in positions:
                print(f"   #{pos.ticket} - {'BUY' if pos.type == 0 else 'SELL'} "
                      f"{pos.volume:.2f} @ {pos.price_open:.5f} - P/L: ${pos.profit:.2f}")
        
        connector.disconnect()
        print("\n✓ Disconnected")


if __name__ == "__main__":
    from src.connectors.base import TradeRequest
    main()

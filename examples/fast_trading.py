"""
Fast Trading Strategy - Trades based on MA position (not crossover)
This is more aggressive and will generate more signals
"""
import MetaTrader5 as mt5
from datetime import datetime
import time
import os
from dotenv import load_dotenv
from src.connectors import MT5Connector, OrderType
from src.connectors.base import TradeRequest
import numpy as np

# Load credentials
load_dotenv()
login = int(os.getenv('MT5_LOGIN', 0))
password = os.getenv('MT5_PASSWORD', '')
server = os.getenv('MT5_SERVER', '')

print("=" * 80)
print("  FAST MA POSITION TRADING")
print("=" * 80)
print("\n📊 Strategy: Trade when Fast MA is above/below Slow MA")
print("   (Not waiting for crossover - more signals!)")
print("=" * 80)

# Settings
symbol = input("\nSymbol (default: EURUSD): ").strip() or "EURUSD"
lot_size = input("Lot size (default: 0.01): ").strip() or "0.01"
lot_size = float(lot_size)

print(f"\n✓ Symbol: {symbol}")
print(f"✓ Lot size: {lot_size}")

# Connect
connector = MT5Connector()
print(f"\nConnecting to {server}...")

if not connector.connect(login, password, server):
    print("❌ Connection failed!")
    exit(1)

print("✓ Connected!")

# Check symbol
symbol_info = connector.get_symbol_info(symbol)
if not symbol_info:
    print(f"❌ Symbol {symbol} not available!")
    connector.disconnect()
    exit(1)

print(f"\nSymbol Info:")
print(f"  Bid: {symbol_info.bid:.5f}")
print(f"  Ask: {symbol_info.ask:.5f}")

print("\n" + "=" * 80)
print("  STARTING FAST TRADING")
print("  Strategy: BUY when Fast MA > Slow MA, SELL when Fast MA < Slow MA")
print("  Check interval: 30 seconds")
print("  Press Ctrl+C to stop")
print("=" * 80)

trade_count = 0
last_signal = None

try:
    while True:
        # Get bars
        bars = connector.get_bars(symbol, 'M5', 100)
        
        if not bars:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Failed to get data")
            time.sleep(30)
            continue
        
        # Calculate MAs
        fast_ma = np.mean([bar.close for bar in bars[-10:]])
        slow_ma = np.mean([bar.close for bar in bars[-20:]])
        current_price = bars[-1].close
        
        # Determine signal
        if fast_ma > slow_ma:
            signal_type = 'BUY'
        elif fast_ma < slow_ma:
            signal_type = 'SELL'
        else:
            signal_type = 'HOLD'
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {symbol} @ {current_price:.5f}")
        print(f"  Fast MA: {fast_ma:.5f} | Slow MA: {slow_ma:.5f}")
        print(f"  Signal: {signal_type}")
        
        # Only trade if signal changed
        if signal_type != last_signal and signal_type != 'HOLD':
            tick = mt5.symbol_info_tick(symbol)
            
            if signal_type == 'BUY':
                action = OrderType.BUY
                price = tick.ask
                sl = price - 0.0020  # 20 pips
                tp = price + 0.0040  # 40 pips
            else:  # SELL
                action = OrderType.SELL
                price = tick.bid
                sl = price + 0.0020  # 20 pips
                tp = price - 0.0040  # 40 pips
            
            print(f"  🎯 Executing {signal_type} order - {lot_size} lots")
            print(f"     Entry: {price:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")
            
            result = connector.send_order(
                TradeRequest(
                    symbol=symbol,
                    action=action,
                    volume=lot_size,
                    price=price,
                    sl=sl,
                    tp=tp
                )
            )
            
            if result.success:
                trade_count += 1
                print(f"  ✅ SUCCESS! Order #{result.order_ticket} executed @ {result.price:.5f}")
                print(f"  📊 Total trades executed: {trade_count}")
                last_signal = signal_type
            else:
                print(f"  ❌ FAILED: {result.error_message} (Code: {result.error_code})")
        else:
            print(f"  ⏭ No new signal (last: {last_signal})")
        
        print(f"  ⏳ Waiting 30 seconds...")
        time.sleep(30)

except KeyboardInterrupt:
    print("\n\n⚠️  Stopped by user")

finally:
    # Show summary
    print("\n" + "=" * 80)
    print("  TRADING SUMMARY")
    print("=" * 80)
    
    positions = connector.get_positions(symbol=symbol)
    if positions:
        total_profit = sum(pos.profit for pos in positions)
        print(f"\n📊 Open Positions: {len(positions)}")
        print(f"💰 Total P/L: ${total_profit:.2f}")
        
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            print(f"\n  #{pos.ticket} - {pos_type} {pos.volume:.2f} @ {pos.price_open:.5f}")
            print(f"     Current: {pos.price_current:.5f}")
            print(f"     P/L: ${pos.profit:.2f}")
    else:
        print("\n  No open positions")
    
    print(f"\n✓ Total trades executed this session: {trade_count}")
    
    connector.disconnect()
    print("\n✓ Disconnected")
    print("=" * 80)

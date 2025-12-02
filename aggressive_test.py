"""
Aggressive trading test - Forces frequent BUY/SELL signals for testing
WARNING: This will trade A LOT - only use on demo accounts!
"""
import MetaTrader5 as mt5
from datetime import datetime
import time
import os
import subprocess
import winreg
from dotenv import load_dotenv
from src.connectors import MT5Connector, OrderType
from src.connectors.base import TradeRequest
import random

def check_mt5_running():
    """Check if MT5 terminal is running"""
    try:
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        return 'terminal64.exe' in result.stdout.lower() or 'terminal.exe' in result.stdout.lower()
    except:
        return False

def find_mt5_executable():
    """Find MT5 installation path from registry"""
    paths_to_check = [
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    ]
    
    # Check registry
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\MetaQuotes\MetaTrader 5")
        install_path = winreg.QueryValueEx(key, "Install_Path")[0]
        winreg.CloseKey(key)
        paths_to_check.insert(0, os.path.join(install_path, "terminal64.exe"))
    except:
        pass
    
    for path in paths_to_check:
        if os.path.exists(path):
            return path
    return None

def start_mt5():
    """Start MT5 terminal if not running"""
    if check_mt5_running():
        print("✓ MT5 already running")
        return True
    
    print("⚠️  MT5 not running, attempting to start...")
    mt5_path = find_mt5_executable()
    
    if not mt5_path:
        print("❌ Could not find MT5 installation!")
        return False
    
    try:
        subprocess.Popen([mt5_path])
        print(f"✓ Starting MT5 from {mt5_path}")
        print("⏳ Waiting 5 seconds for MT5 to initialize...")
        time.sleep(5)
        return True
    except Exception as e:
        print(f"❌ Failed to start MT5: {e}")
        return False

# Load credentials
load_dotenv()
login = int(os.getenv('MT5_LOGIN', 0))
password = os.getenv('MT5_PASSWORD', '')
server = os.getenv('MT5_SERVER', '')

print("=" * 80)
print("  AGGRESSIVE TRADING TEST - DEMO ONLY")
print("=" * 80)
print("\n⚠️  WARNING: This will execute MANY trades!")
print("⚠️  Only use on DEMO accounts!")
print("=" * 80)

# Check/start MT5
print("\n🔍 Checking MT5 terminal...")
if not start_mt5():
    print("\n❌ Please start MetaTrader 5 manually and try again.")
    exit(1)

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
print(f"  Spread: {symbol_info.spread}")

# Check auto-trading
terminal_info = mt5.terminal_info()
if not terminal_info.trade_allowed:
    print("\n" + "!" * 80)
    print("  ⚠️  AUTO-TRADING IS DISABLED!")
    print("  Enable it in MT5 toolbar or this won't work!")
    print("!" * 80)
    proceed = input("\nContinue anyway to test? (yes/no): ").strip().lower()
    if proceed not in ['yes', 'y']:
        connector.disconnect()
        exit(0)

print("\n" + "=" * 80)
print("  STARTING AGGRESSIVE TRADING")
print("  Strategy: Alternating BUY/SELL every 10 seconds")
print("  Press Ctrl+C to stop")
print("=" * 80)

trade_count = 0
last_action = None

try:
    while True:
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Failed to get tick")
            time.sleep(10)
            continue
        
        current_price = tick.bid
        
        # Alternate between BUY and SELL
        if last_action == 'BUY':
            action = OrderType.SELL
            price = tick.bid
            sl = price + 0.0020  # 20 pips above (losing SL for SELL)
            tp = price - 0.0040  # 40 pips below (winning TP for SELL)
        else:
            action = OrderType.BUY
            price = tick.ask
            sl = price - 0.0020  # 20 pips below (losing SL for BUY)
            tp = price + 0.0040  # 40 pips above (winning TP for BUY)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {symbol} @ {current_price:.5f}")
        print(f"  🎯 Executing {action.name} order - {lot_size} lots")
        print(f"     Price: {price:.5f}")
        print(f"     SL: {sl:.5f}")
        print(f"     TP: {tp:.5f}")
        
        # Send order
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
            last_action = action.name
        else:
            print(f"  ❌ FAILED: {result.error_message} (Code: {result.error_code})")
            if result.error_code == 10027:
                print(f"  💡 Error 10027 = Auto-trading disabled in MT5!")
        
        # Wait before next trade
        print(f"  ⏳ Waiting 10 seconds...")
        time.sleep(10)

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
            print(f"     SL: {pos.sl:.5f}" if pos.sl > 0 else "     SL: Not set")
            print(f"     TP: {pos.tp:.5f}" if pos.tp > 0 else "     TP: Not set")
    else:
        print("\n  No open positions")
    
    print(f"\n✓ Total trades executed this session: {trade_count}")
    
    connector.disconnect()
    print("\n✓ Disconnected")
    print("=" * 80)

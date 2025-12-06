"""
Emergency Position Closer
Closes all open positions in MT5 - Enhanced version with multiple retry methods
"""
import os
import MetaTrader5 as mt5
from dotenv import load_dotenv
from src.connectors import ConnectorFactory
from src.connectors.base import PlatformType

# Load environment
load_dotenv()

def close_position_direct(position):
    """Close position using direct MT5 API with multiple filling modes"""
    symbol = position.symbol
    ticket = position.ticket
    volume = position.volume
    pos_type = position.type
    
    # Get current price
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return False, "Failed to get tick data"
    
    # Determine close type (opposite of position type)
    close_type = mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY
    price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
    
    # Try different filling modes
    filling_modes = [
        (mt5.ORDER_FILLING_FOK, "FOK"),
        (mt5.ORDER_FILLING_IOC, "IOC"),
        (mt5.ORDER_FILLING_RETURN, "RETURN")
    ]
    
    for filling_mode, mode_name in filling_modes:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Emergency close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }
        
        result = mt5.order_send(request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return True, f"Closed with {mode_name}"
        
    # If all failed, return last error
    if result:
        return False, f"Retcode: {result.retcode}, Comment: {result.comment}"
    return False, "No result from order_send"


def main():
    print("=" * 80)
    print("  EMERGENCY POSITION CLOSER - ENHANCED")
    print("=" * 80)
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        return
    
    # Connect to MT5
    print("\n🔌 Connecting to MT5...")
    
    login = int(os.getenv('MT5_LOGIN', 0))
    password = os.getenv('MT5_PASSWORD', '')
    server = os.getenv('MT5_SERVER', '')
    
    if not mt5.login(login, password, server):
        print(f"❌ Connection failed: {mt5.last_error()}")
        mt5.shutdown()
        return
    
    print("✓ Connected to MT5")
    
    # Get all positions
    positions = mt5.positions_get()
    
    if not positions or len(positions) == 0:
        print("\n✓ No open positions found")
        mt5.shutdown()
        return
    
    print(f"\n📊 Found {len(positions)} open positions:")
    total_pnl = 0
    for pos in positions:
        pnl = pos.profit
        total_pnl += pnl
        pos_type = "BUY" if pos.type == 0 else "SELL"
        print(f"  - {pos.symbol}: {pos_type} {pos.volume} lots, "
              f"Ticket #{pos.ticket}, P/L: ${pnl:.2f}")
    
    print(f"\n💰 Total P/L: ${total_pnl:.2f}")
    
    # Confirm
    print("\n⚠️  WARNING: This will close ALL positions!")
    response = input("Type 'YES' to confirm: ")
    
    if response.upper() != 'YES':
        print("\n❌ Cancelled - No positions closed")
        mt5.shutdown()
        return
    
    # Close all positions
    print("\n🔄 Closing positions...")
    closed_count = 0
    failed_count = 0
    
    for pos in positions:
        pos_type = "BUY" if pos.type == 0 else "SELL"
        print(f"  Closing {pos.symbol} {pos_type} (#{pos.ticket})...", end=" ")
        
        success, message = close_position_direct(pos)
        
        if success:
            print(f"✓ {message}")
            closed_count += 1
        else:
            print(f"✗ {message}")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Closed: {closed_count}")
    if failed_count > 0:
        print(f"✗ Failed: {failed_count}")
        print("\nIf positions failed to close:")
        print("  1. Close them manually in MT5 terminal")
        print("  2. Check if they have pending modifications")
        print("  3. Ensure auto-trading is enabled in MT5")
    print(f"💰 Final P/L: ${total_pnl:.2f}")
    print("=" * 80)
    
    # Shutdown
    mt5.shutdown()
    print("\n✓ Disconnected")
    
    if closed_count > 0:
        print("\n✅ Positions closed! You can now restart the bot:")
        print("  python main.py")
    else:
        print("\n⚠️  Please close positions manually in MT5 terminal")


if __name__ == '__main__':
    main()

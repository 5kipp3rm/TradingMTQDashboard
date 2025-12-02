"""
Demo: Enhanced MT5 Features
Demonstrates new pending orders, error descriptions, and account utilities
"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.connectors import (
    MT5Connector, OrderType, AccountUtils,
    trade_server_return_code_description, error_description
)


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_error_descriptions():
    """Demonstrate error description functionality"""
    print_section("ERROR DESCRIPTIONS")
    
    # Sample trade return codes
    print("Trade Server Return Codes:")
    codes = [
        mt5.TRADE_RETCODE_DONE,
        mt5.TRADE_RETCODE_REQUOTE,
        mt5.TRADE_RETCODE_NO_MONEY,
        mt5.TRADE_RETCODE_INVALID_VOLUME,
        mt5.TRADE_RETCODE_MARKET_CLOSED,
    ]
    
    for code in codes:
        desc = trade_server_return_code_description(code)
        print(f"  {code:5d} -> {desc}")
    
    # Sample error codes
    print("\nRuntime Error Codes:")
    error_codes = [0, 4301, 4704, 4707, 5001]
    
    for code in error_codes:
        desc = error_description(code)
        print(f"  {code:5d} -> {desc}")


def demo_account_utils(connector: MT5Connector):
    """Demonstrate account utility functions"""
    print_section("ACCOUNT UTILITIES")
    
    symbol = "EURUSD"
    
    # Get symbol info
    symbol_info = connector.get_symbol_info(symbol)
    if not symbol_info:
        print(f"Failed to get symbol info for {symbol}")
        return
    
    print(f"Symbol: {symbol}")
    print(f"Bid: {symbol_info.bid:.5f}, Ask: {symbol_info.ask:.5f}")
    print(f"Min Volume: {symbol_info.volume_min}, Max Volume: {symbol_info.volume_max}")
    
    # Margin check
    print("\n1. Margin Check:")
    required_margin = AccountUtils.margin_check(
        symbol, mt5.ORDER_TYPE_BUY, 0.1, symbol_info.ask
    )
    
    if required_margin:
        print(f"   Required margin for 0.1 lot BUY: ${required_margin:.2f}")
    
    # Max lot check
    print("\n2. Maximum Lot Size:")
    max_lots_100 = AccountUtils.max_lot_check(
        symbol, mt5.ORDER_TYPE_BUY, symbol_info.ask, percent=100
    )
    max_lots_50 = AccountUtils.max_lot_check(
        symbol, mt5.ORDER_TYPE_BUY, symbol_info.ask, percent=50
    )
    
    if max_lots_100:
        print(f"   Max lots (100% margin): {max_lots_100:.2f}")
    if max_lots_50:
        print(f"   Max lots (50% margin): {max_lots_50:.2f}")
    
    # Risk-based lot sizing
    print("\n3. Risk-Based Lot Sizing:")
    entry_price = symbol_info.ask
    stop_loss = entry_price - 0.0020  # 20 pips stop
    
    lot_1pct = AccountUtils.risk_based_lot_size(
        symbol, mt5.ORDER_TYPE_BUY, entry_price, stop_loss, risk_percent=1.0
    )
    lot_2pct = AccountUtils.risk_based_lot_size(
        symbol, mt5.ORDER_TYPE_BUY, entry_price, stop_loss, risk_percent=2.0
    )
    
    if lot_1pct:
        print(f"   Lot size for 1% risk: {lot_1pct:.2f}")
    if lot_2pct:
        print(f"   Lot size for 2% risk: {lot_2pct:.2f}")
    
    # Profit estimation
    print("\n4. Profit Estimation:")
    exit_price = entry_price + 0.0030  # 30 pips profit
    estimated_profit = AccountUtils.order_profit_check(
        symbol, mt5.ORDER_TYPE_BUY, 0.1, entry_price, exit_price
    )
    
    if estimated_profit:
        print(f"   Estimated profit for 0.1 lot (30 pips): ${estimated_profit:.2f}")
    
    # Account mode descriptions
    print("\n5. Account Information:")
    account = connector.get_account_info()
    if account:
        print(f"   Balance: ${account.balance:.2f}")
        print(f"   Equity: ${account.equity:.2f}")
        print(f"   Free Margin: ${account.margin_free:.2f}")
        print(f"   Leverage: 1:{account.leverage}")


def demo_pending_orders(connector: MT5Connector):
    """Demonstrate pending order functionality"""
    print_section("PENDING ORDERS")
    
    symbol = "EURUSD"
    
    # Get current prices
    symbol_info = connector.get_symbol_info(symbol)
    if not symbol_info:
        print(f"Failed to get symbol info for {symbol}")
        return
    
    ask = symbol_info.ask
    bid = symbol_info.bid
    lot_size = symbol_info.volume_min
    
    print(f"Current Prices - Bid: {bid:.5f}, Ask: {ask:.5f}")
    print(f"Using minimum lot size: {lot_size}")
    
    # Set expiration time
    expiration = datetime.now() + timedelta(minutes=30)
    
    print("\n1. Buy Limit Order (below current ask):")
    buy_limit_price = ask - 0.0020
    result = connector.buy_limit(
        symbol=symbol,
        volume=lot_size,
        price=buy_limit_price,
        sl=buy_limit_price - 0.0020,
        tp=buy_limit_price + 0.0030,
        type_time=mt5.ORDER_TIME_SPECIFIED,
        expiration=expiration,
        comment="Demo Buy Limit"
    )
    
    if result.success:
        print(f"   ✓ Buy Limit placed: Order #{result.order_ticket} @ {buy_limit_price:.5f}")
        buy_limit_ticket = result.order_ticket
    else:
        print(f"   ✗ Failed: {result.error_message}")
        buy_limit_ticket = None
    
    print("\n2. Sell Stop Order (below current bid):")
    sell_stop_price = bid - 0.0020
    result = connector.sell_stop(
        symbol=symbol,
        volume=lot_size,
        price=sell_stop_price,
        sl=sell_stop_price + 0.0020,
        tp=sell_stop_price - 0.0030,
        type_time=mt5.ORDER_TIME_SPECIFIED,
        expiration=expiration,
        comment="Demo Sell Stop"
    )
    
    if result.success:
        print(f"   ✓ Sell Stop placed: Order #{result.order_ticket} @ {sell_stop_price:.5f}")
        sell_stop_ticket = result.order_ticket
    else:
        print(f"   ✗ Failed: {result.error_message}")
        sell_stop_ticket = None
    
    # Modify an order
    if buy_limit_ticket:
        print(f"\n3. Modifying Buy Limit Order #{buy_limit_ticket}:")
        new_price = buy_limit_price - 0.0005
        result = connector.modify_order(
            ticket=buy_limit_ticket,
            price=new_price,
            sl=new_price - 0.0025,
            tp=new_price + 0.0035
        )
        
        if result.success:
            print(f"   ✓ Order modified: New price {new_price:.5f}")
        else:
            print(f"   ✗ Modify failed: {result.error_message}")
    
    # Delete orders
    print("\n4. Deleting Pending Orders:")
    for ticket in [buy_limit_ticket, sell_stop_ticket]:
        if ticket:
            result = connector.delete_order(ticket)
            if result.success:
                print(f"   ✓ Order #{ticket} deleted")
            else:
                print(f"   ✗ Delete failed for #{ticket}: {result.error_message}")


def demo_symbol_refresh(connector: MT5Connector):
    """Demonstrate symbol refresh functionality"""
    print_section("SYMBOL REFRESH")
    
    symbol = "EURUSD"
    
    print(f"Getting symbol info for {symbol}...")
    info1 = connector.get_symbol_info(symbol)
    
    if info1:
        print(f"Initial - Bid: {info1.bid:.5f}, Ask: {info1.ask:.5f}, Spread: {info1.spread:.5f}")
    
    print("\nRefreshing symbol info...")
    info2 = connector.refresh_symbol_info(symbol)
    
    if info2:
        print(f"Refreshed - Bid: {info2.bid:.5f}, Ask: {info2.ask:.5f}, Spread: {info2.spread:.5f}")
        
        if info1 and info2:
            bid_change = info2.bid - info1.bid
            ask_change = info2.ask - info1.ask
            print(f"\nChanges - Bid: {bid_change:+.5f}, Ask: {ask_change:+.5f}")


def main():
    """Main demo function"""
    print("\n" + "=" * 80)
    print("  ENHANCED MT5 FEATURES DEMONSTRATION")
    print("=" * 80)
    
    # Demo error descriptions (doesn't need connection)
    demo_error_descriptions()
    
    # Initialize MT5
    print("\n\nInitializing MT5 connection...")
    print("Note: Update credentials in the code before running!")
    
    connector = MT5Connector("demo_instance")
    
    # TODO: Update these credentials
    connected = connector.connect(
        login=12345678,  # Your MT5 login
        password="your_password",  # Your MT5 password
        server="YourBroker-Demo"  # Your broker server
    )
    
    if not connected:
        print("✗ Failed to connect to MT5")
        print("  Update the credentials in the code and ensure MT5 is installed")
        return
    
    print("✓ Connected to MT5")
    
    try:
        # Demonstrate features
        demo_account_utils(connector)
        demo_symbol_refresh(connector)
        
        # Pending orders demo (commented out by default to avoid accidental trades)
        print("\n\n" + "!" * 80)
        print("  PENDING ORDERS DEMO IS DISABLED BY DEFAULT")
        print("  Uncomment the line below to test pending order placement")
        print("!" * 80)
        # demo_pending_orders(connector)
        
    finally:
        connector.disconnect()
        print("\n\nDisconnected from MT5")


if __name__ == "__main__":
    main()

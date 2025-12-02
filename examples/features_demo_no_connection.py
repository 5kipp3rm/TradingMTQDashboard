"""
Demo: Error Descriptions and Utility Functions (No MT5 Connection Required)
Demonstrates error descriptions and utility function signatures
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.connectors import trade_server_return_code_description, error_description
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("Note: MetaTrader5 package not installed. Some examples will be limited.\n")


def demo_error_descriptions():
    """Demonstrate comprehensive error description functionality"""
    print("=" * 80)
    print("  ERROR DESCRIPTION SYSTEM")
    print("=" * 80)
    
    if not MT5_AVAILABLE:
        print("\nMetaTrader5 package not available - showing concept only")
        return
    
    print("\n1. TRADE SERVER RETURN CODES (Common Errors):")
    print("-" * 80)
    
    important_codes = [
        (mt5.TRADE_RETCODE_DONE, "Success"),
        (mt5.TRADE_RETCODE_REQUOTE, "Price changed"),
        (mt5.TRADE_RETCODE_REJECT, "Rejected"),
        (mt5.TRADE_RETCODE_NO_MONEY, "Insufficient funds"),
        (mt5.TRADE_RETCODE_INVALID_VOLUME, "Bad volume"),
        (mt5.TRADE_RETCODE_INVALID_PRICE, "Bad price"),
        (mt5.TRADE_RETCODE_INVALID_STOPS, "Bad SL/TP"),
        (mt5.TRADE_RETCODE_MARKET_CLOSED, "Market closed"),
        (mt5.TRADE_RETCODE_TRADE_DISABLED, "Trading disabled"),
        (mt5.TRADE_RETCODE_INVALID_FILL, "Bad fill type"),
    ]
    
    for code, category in important_codes:
        desc = trade_server_return_code_description(code)
        print(f"  {code:5d} ({category:20s}) -> {desc}")
    
    print("\n2. RUNTIME ERROR CODES (System Errors):")
    print("-" * 80)
    
    important_errors = [
        (0, "Success"),
        (1, "Internal error"),
        (4301, "Symbol error"),
        (4302, "Symbol not in MW"),
        (4704, "Position not found"),
        (4705, "Order not found"),
        (4707, "Trade failed"),
        (5001, "File limit"),
        (5004, "File open error"),
    ]
    
    for code, category in important_errors:
        desc = error_description(code)
        print(f"  {code:5d} ({category:20s}) -> {desc}")
    
    print("\n3. USAGE IN CODE:")
    print("-" * 80)
    print("""
    # In your trading code, instead of:
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Error: {result.retcode}")
    
    # You can now use:
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        error_msg = trade_server_return_code_description(result.retcode)
        logger.error(f"Trade failed: {error_msg}")
        # Shows: "Trade failed: There is not enough money to complete the request"
    """)


def demo_account_utils_info():
    """Show AccountUtils capabilities"""
    print("\n" + "=" * 80)
    print("  ACCOUNT UTILITIES")
    print("=" * 80)
    
    print("\n1. MARGIN CHECK - Calculate required margin for a trade")
    print("-" * 80)
    print("""
    from src.connectors import AccountUtils
    import MetaTrader5 as mt5
    
    # Calculate margin needed for 0.1 lot BUY on EURUSD at 1.0850
    required_margin = AccountUtils.margin_check(
        symbol="EURUSD",
        order_type=mt5.ORDER_TYPE_BUY,
        volume=0.1,
        price=1.0850
    )
    # Returns: 108.50 (example - depends on leverage)
    
    if required_margin:
        print(f"Need ${required_margin:.2f} margin for this trade")
    """)
    
    print("\n2. MAX LOT CHECK - Calculate maximum position size")
    print("-" * 80)
    print("""
    # Calculate max lots using 50% of available margin
    max_lots = AccountUtils.max_lot_check(
        symbol="EURUSD",
        order_type=mt5.ORDER_TYPE_BUY,
        price=1.0850,
        percent=50  # Use 50% of free margin
    )
    # Returns: 2.35 (example - based on your account)
    
    print(f"Maximum safe lot size: {max_lots:.2f}")
    """)
    
    print("\n3. RISK-BASED LOT SIZING - Professional position sizing ⭐")
    print("-" * 80)
    print("""
    # Calculate lot size to risk exactly 2% of account
    lot_size = AccountUtils.risk_based_lot_size(
        symbol="EURUSD",
        order_type=mt5.ORDER_TYPE_BUY,
        entry_price=1.0850,
        stop_loss=1.0830,     # 20 pips stop loss
        risk_percent=2.0       # Risk 2% of account balance
    )
    # Returns: 0.15 (example - will vary by account size)
    
    # This is the PROPER way to size positions!
    # If your account is $10,000 and you risk 2%, you risk $200
    # With 20 pip stop, the lot size is calculated to lose exactly $200 if hit
    """)
    
    print("\n4. PROFIT ESTIMATION - Estimate trade profit")
    print("-" * 80)
    print("""
    # Estimate profit for 0.1 lot, 30 pip move
    estimated_profit = AccountUtils.order_profit_check(
        symbol="EURUSD",
        order_type=mt5.ORDER_TYPE_BUY,
        volume=0.1,
        price_open=1.0850,
        price_close=1.0880   # 30 pips profit
    )
    # Returns: 30.00 (example)
    
    print(f"Expected profit: ${estimated_profit:.2f}")
    """)
    
    print("\n5. FREE MARGIN CHECK - Check remaining margin after trade")
    print("-" * 80)
    print("""
    # Check how much free margin will remain after opening position
    remaining_margin = AccountUtils.free_margin_check(
        symbol="EURUSD",
        order_type=mt5.ORDER_TYPE_BUY,
        volume=0.5,
        price=1.0850
    )
    # Returns: 8500.00 (example - your free margin after the trade)
    
    if remaining_margin and remaining_margin > 1000:
        print("Safe to open position")
    else:
        print("Not enough margin buffer")
    """)


def demo_pending_orders_info():
    """Show pending order capabilities"""
    print("\n" + "=" * 80)
    print("  PENDING ORDERS")
    print("=" * 80)
    
    print("\n1. BUY LIMIT - Buy at lower price")
    print("-" * 80)
    print("""
    from src.connectors import MT5Connector
    from datetime import datetime, timedelta
    import MetaTrader5 as mt5
    
    connector = MT5Connector()
    connector.connect(login, password, server)
    
    # Place buy limit 30 pips below current ask
    symbol_info = connector.get_symbol_info("EURUSD")
    buy_price = symbol_info.ask - 0.0030
    
    expiration = datetime.now() + timedelta(hours=2)
    
    result = connector.buy_limit(
        symbol="EURUSD",
        volume=0.1,
        price=buy_price,
        sl=buy_price - 0.0020,
        tp=buy_price + 0.0040,
        type_time=mt5.ORDER_TIME_SPECIFIED,
        expiration=expiration,
        comment="Buy Limit 2hr"
    )
    
    if result.success:
        print(f"Order placed: #{result.order_ticket}")
    """)
    
    print("\n2. SELL STOP - Sell on breakdown")
    print("-" * 80)
    print("""
    # Place sell stop 20 pips below current bid
    symbol_info = connector.get_symbol_info("EURUSD")
    sell_price = symbol_info.bid - 0.0020
    
    result = connector.sell_stop(
        symbol="EURUSD",
        volume=0.1,
        price=sell_price,
        sl=sell_price + 0.0020,
        tp=sell_price - 0.0040,
        type_time=mt5.ORDER_TIME_GTC,  # Good til canceled
        comment="Sell Stop"
    )
    """)
    
    print("\n3. MODIFY PENDING ORDER")
    print("-" * 80)
    print("""
    # Modify existing pending order
    result = connector.modify_order(
        ticket=12345,
        price=1.0835,      # New trigger price
        sl=1.0815,         # New stop loss
        tp=1.0865          # New take profit
    )
    """)
    
    print("\n4. DELETE PENDING ORDER")
    print("-" * 80)
    print("""
    # Delete pending order
    result = connector.delete_order(ticket=12345)
    
    if result.success:
        print("Order deleted")
    """)


def demo_complete_example():
    """Show a complete trading example"""
    print("\n" + "=" * 80)
    print("  COMPLETE EXAMPLE: RISK-MANAGED TRADE")
    print("=" * 80)
    
    print("""
from src.connectors import MT5Connector, AccountUtils, OrderType
from datetime import datetime, timedelta
import MetaTrader5 as mt5

# 1. CONNECT
connector = MT5Connector()
connector.connect(login=12345, password="pass", server="Broker-Demo")

# 2. ANALYZE SETUP
symbol = "EURUSD"
symbol_info = connector.get_symbol_info(symbol)

# Current price: 1.0850
# Strategy: Buy limit at 1.0820 (30 pips below)
# Stop loss: 1.0800 (20 pips from entry)
# Take profit: 1.0870 (50 pips from entry)

entry_price = 1.0820
stop_loss = 1.0800
take_profit = 1.0870

# 3. CALCULATE SAFE LOT SIZE (Risk 2% of account)
lot_size = AccountUtils.risk_based_lot_size(
    symbol=symbol,
    order_type=mt5.ORDER_TYPE_BUY,
    entry_price=entry_price,
    stop_loss=stop_loss,
    risk_percent=2.0  # Risk 2% of account
)

print(f"Calculated lot size: {lot_size:.2f} lots")

# 4. VERIFY MARGIN REQUIREMENT
required_margin = AccountUtils.margin_check(
    symbol, mt5.ORDER_TYPE_BUY, lot_size, entry_price
)

account = connector.get_account_info()
print(f"Account balance: ${account.balance:.2f}")
print(f"Free margin: ${account.margin_free:.2f}")
print(f"Required margin: ${required_margin:.2f}")

if required_margin > account.margin_free:
    print("ERROR: Not enough margin!")
    exit()

# 5. ESTIMATE POTENTIAL PROFIT
potential_profit = AccountUtils.order_profit_check(
    symbol, mt5.ORDER_TYPE_BUY, lot_size, entry_price, take_profit
)
potential_loss = AccountUtils.order_profit_check(
    symbol, mt5.ORDER_TYPE_BUY, lot_size, entry_price, stop_loss
)

print(f"\\nRisk/Reward:")
print(f"  Potential profit: ${potential_profit:.2f}")
print(f"  Potential loss: ${potential_loss:.2f}")
print(f"  Risk/Reward ratio: {abs(potential_profit/potential_loss):.2f}")

# 6. PLACE PENDING ORDER WITH EXPIRATION
expiration = datetime.now() + timedelta(hours=4)

result = connector.buy_limit(
    symbol=symbol,
    volume=lot_size,
    price=entry_price,
    sl=stop_loss,
    tp=take_profit,
    type_time=mt5.ORDER_TIME_SPECIFIED,
    expiration=expiration,
    comment="Risk 2% Strategy"
)

if result.success:
    print(f"\\n✓ ORDER PLACED SUCCESSFULLY")
    print(f"  Order #: {result.order_ticket}")
    print(f"  Entry: {entry_price:.5f}")
    print(f"  Stop Loss: {stop_loss:.5f}")
    print(f"  Take Profit: {take_profit:.5f}")
    print(f"  Lot Size: {lot_size:.2f}")
    print(f"  Expires: {expiration}")
else:
    error_desc = trade_server_return_code_description(result.error_code)
    print(f"\\n✗ ORDER FAILED")
    print(f"  Error: {error_desc}")

# 7. CLEANUP
connector.disconnect()
""")


def main():
    """Main demo function"""
    print("\n" + "=" * 80)
    print("  TRADINGMTQ ENHANCED FEATURES - DOCUMENTATION DEMO")
    print("  (No MT5 Connection Required)")
    print("=" * 80)
    
    # Show all capabilities
    demo_error_descriptions()
    demo_account_utils_info()
    demo_pending_orders_info()
    demo_complete_example()
    
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print("""
What you get with the enhanced features:

✓ ERROR DESCRIPTIONS
  - 800+ error codes with human-readable messages
  - Better debugging and error reporting
  
✓ ACCOUNT UTILITIES  
  - Margin calculations
  - Position sizing based on risk %
  - Profit/loss estimation
  
✓ PENDING ORDERS
  - Buy/Sell Limit orders
  - Buy/Sell Stop orders  
  - Order modification
  - Order deletion
  - Expiration control
  
✓ PROFESSIONAL RISK MANAGEMENT
  - Risk-based position sizing
  - Margin verification
  - R/R ratio calculation

To use with live MT5 connection:
  1. Update credentials in examples/enhanced_features_demo.py
  2. Run: python examples/enhanced_features_demo.py
  
Documentation:
  - INTEGRATION_COMPLETE.md - Full integration details
  - QUICK_REFERENCE.md - Quick reference guide
  - examples/enhanced_features_demo.py - Live examples
""")
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()

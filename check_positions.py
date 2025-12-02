"""Check all positions and recent trades in MT5"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv()
login = int(os.getenv('MT5_LOGIN', 0))
password = os.getenv('MT5_PASSWORD', '')
server = os.getenv('MT5_SERVER', '')

print("=" * 80)
print("  MT5 POSITIONS & TRADE HISTORY CHECK")
print("=" * 80)

# Initialize and connect
if not mt5.initialize():
    print(f"❌ MT5 initialization failed: {mt5.last_error()}")
    exit(1)

if not mt5.login(login, password, server):
    print(f"❌ Login failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

print(f"\n✓ Connected to {server}")

# Check account info
account = mt5.account_info()
if account:
    print(f"\nAccount: {account.login}")
    print(f"Balance: ${account.balance:,.2f}")
    print(f"Equity: ${account.equity:,.2f}")
    print(f"Margin: ${account.margin:,.2f}")
    print(f"Free Margin: ${account.margin_free:,.2f}")

# Get all open positions
print("\n" + "=" * 80)
print("  OPEN POSITIONS")
print("=" * 80)

positions = mt5.positions_get()
if positions:
    print(f"\nTotal: {len(positions)} position(s)")
    for pos in positions:
        pos_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
        print(f"\n  Ticket: #{pos.ticket}")
        print(f"  Symbol: {pos.symbol}")
        print(f"  Type: {pos_type}")
        print(f"  Volume: {pos.volume:.2f} lots")
        print(f"  Open Price: {pos.price_open:.5f}")
        print(f"  Current Price: {pos.price_current:.5f}")
        print(f"  SL: {pos.sl:.5f}" if pos.sl > 0 else "  SL: Not set")
        print(f"  TP: {pos.tp:.5f}" if pos.tp > 0 else "  TP: Not set")
        print(f"  Profit: ${pos.profit:.2f}")
        print(f"  Time: {datetime.fromtimestamp(pos.time)}")
else:
    print("\n  No open positions")

# Get recent deals (trades)
print("\n" + "=" * 80)
print("  RECENT DEALS (Last 24 hours)")
print("=" * 80)

from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

deals = mt5.history_deals_get(from_date, to_date)
if deals:
    print(f"\nTotal: {len(deals)} deal(s)")
    for deal in deals:
        deal_type = ""
        if deal.type == mt5.DEAL_TYPE_BUY:
            deal_type = "BUY"
        elif deal.type == mt5.DEAL_TYPE_SELL:
            deal_type = "SELL"
        else:
            deal_type = f"Type {deal.type}"
        
        entry = ""
        if deal.entry == mt5.DEAL_ENTRY_IN:
            entry = "ENTRY"
        elif deal.entry == mt5.DEAL_ENTRY_OUT:
            entry = "EXIT"
        else:
            entry = "INOUT"
        
        print(f"\n  Deal: #{deal.ticket} | Order: #{deal.order}")
        print(f"  Time: {datetime.fromtimestamp(deal.time)}")
        print(f"  Symbol: {deal.symbol}")
        print(f"  Type: {deal_type} ({entry})")
        print(f"  Volume: {deal.volume:.2f} lots")
        print(f"  Price: {deal.price:.5f}")
        print(f"  Profit: ${deal.profit:.2f}")
        print(f"  Comment: {deal.comment}")
else:
    print("\n  No deals in the last 24 hours")

# Get recent orders
print("\n" + "=" * 80)
print("  RECENT ORDERS (Last 24 hours)")
print("=" * 80)

orders = mt5.history_orders_get(from_date, to_date)
if orders:
    print(f"\nTotal: {len(orders)} order(s)")
    for order in orders:
        order_type = ""
        if order.type == mt5.ORDER_TYPE_BUY:
            order_type = "BUY"
        elif order.type == mt5.ORDER_TYPE_SELL:
            order_type = "SELL"
        else:
            order_type = f"Type {order.type}"
        
        state = ""
        if order.state == mt5.ORDER_STATE_FILLED:
            state = "FILLED"
        elif order.state == mt5.ORDER_STATE_REJECTED:
            state = "REJECTED"
        elif order.state == mt5.ORDER_STATE_CANCELED:
            state = "CANCELED"
        else:
            state = f"State {order.state}"
        
        print(f"\n  Order: #{order.ticket}")
        print(f"  Time: {datetime.fromtimestamp(order.time_setup)}")
        print(f"  Symbol: {order.symbol}")
        print(f"  Type: {order_type}")
        print(f"  Volume: {order.volume_initial:.2f} lots")
        print(f"  Price: {order.price_open:.5f}")
        print(f"  State: {state}")
        print(f"  Comment: {order.comment}")
else:
    print("\n  No orders in the last 24 hours")

mt5.shutdown()
print("\n" + "=" * 80)

# Quick Reference: Enhanced MT5 Features

## 🚀 Quick Start

```python
from src.connectors import MT5Connector, AccountUtils, OrderType
import MetaTrader5 as mt5

# Initialize
connector = MT5Connector()
connector.connect(login=12345, password="pass", server="Broker-Demo")
```

---

## 📊 Account Utilities

### 1. Check Required Margin
```python
margin = AccountUtils.margin_check("EURUSD", mt5.ORDER_TYPE_BUY, 0.1, 1.0850)
# Returns: 108.50 (example)
```

### 2. Calculate Max Lot Size
```python
# Use 50% of available margin
max_lots = AccountUtils.max_lot_check("EURUSD", mt5.ORDER_TYPE_BUY, 1.0850, percent=50)
# Returns: 2.5 (example)
```

### 3. Risk-Based Position Sizing ⭐
```python
lot_size = AccountUtils.risk_based_lot_size(
    symbol="EURUSD",
    order_type=mt5.ORDER_TYPE_BUY,
    entry_price=1.0850,
    stop_loss=1.0830,  # 20 pips
    risk_percent=2.0    # Risk 2% of account
)
# Returns: 0.15 (example)
```

### 4. Estimate Profit
```python
profit = AccountUtils.order_profit_check("EURUSD", mt5.ORDER_TYPE_BUY, 0.1, 1.0850, 1.0880)
# Returns: 30.00 (example - 30 pips profit)
```

---

## 📝 Pending Orders

### Buy Limit (Below Current Price)
```python
from datetime import datetime, timedelta

expiration = datetime.now() + timedelta(hours=1)

result = connector.buy_limit(
    symbol="EURUSD",
    volume=0.1,
    price=1.0830,     # Below ask
    sl=1.0810,
    tp=1.0860,
    type_time=mt5.ORDER_TIME_SPECIFIED,
    expiration=expiration
)
```

### Sell Stop (Below Current Price)
```python
result = connector.sell_stop(
    symbol="EURUSD",
    volume=0.1,
    price=1.0820,     # Below bid
    sl=1.0840,
    tp=1.0790,
    type_time=mt5.ORDER_TIME_GTC  # Good til canceled
)
```

### Buy Stop (Above Current Price)
```python
result = connector.buy_stop(
    symbol="EURUSD",
    volume=0.1,
    price=1.0870,     # Above ask
    sl=1.0850,
    tp=1.0900
)
```

### Sell Limit (Above Current Price)
```python
result = connector.sell_limit(
    symbol="EURUSD",
    volume=0.1,
    price=1.0870,     # Above bid
    sl=1.0890,
    tp=1.0840
)
```

---

## 🔧 Order Management

### Modify Pending Order
```python
result = connector.modify_order(
    ticket=12345,
    price=1.0835,   # New price
    sl=1.0815,      # New SL
    tp=1.0865       # New TP
)
```

### Delete Pending Order
```python
result = connector.delete_order(ticket=12345)
```

---

## 📡 Symbol Refresh

```python
# Force refresh from server
symbol_info = connector.refresh_symbol_info("EURUSD")
print(f"Latest Ask: {symbol_info.ask:.5f}")
```

---

## ⚠️ Error Descriptions

### Trade Return Codes
```python
from src.connectors import trade_server_return_code_description

desc = trade_server_return_code_description(mt5.TRADE_RETCODE_NO_MONEY)
# Returns: "There is not enough money to complete the request"
```

### Runtime Errors
```python
from src.connectors import error_description

desc = error_description(4707)
# Returns: "Trade request sending failed"
```

---

## 💡 Common Patterns

### Pattern 1: Risk-Managed Entry
```python
# Get current price
symbol_info = connector.get_symbol_info("EURUSD")
entry = symbol_info.ask
sl = entry - 0.0020  # 20 pips

# Calculate safe lot size
lot = AccountUtils.risk_based_lot_size(
    "EURUSD", mt5.ORDER_TYPE_BUY, entry, sl, risk_percent=1.0
)

# Place trade
if lot and lot >= symbol_info.volume_min:
    result = connector.send_order(TradeRequest(
        symbol="EURUSD",
        action=OrderType.BUY,
        volume=lot,
        sl=sl,
        tp=entry + 0.0040
    ))
```

### Pattern 2: Check Margin Before Trading
```python
# Check if we have enough margin
required = AccountUtils.margin_check("EURUSD", mt5.ORDER_TYPE_BUY, 0.5, 1.0850)
account = connector.get_account_info()

if required and required <= account.margin_free:
    print("✓ Sufficient margin")
    # Place order
else:
    print("✗ Insufficient margin")
    max_lots = AccountUtils.max_lot_check("EURUSD", mt5.ORDER_TYPE_BUY, 1.0850)
    print(f"Max lots: {max_lots}")
```

### Pattern 3: Pending Order with Automatic Cleanup
```python
from datetime import datetime, timedelta

# Place pending order with 30 min expiration
expiration = datetime.now() + timedelta(minutes=30)

result = connector.buy_limit(
    symbol="EURUSD",
    volume=0.1,
    price=1.0830,
    sl=1.0810,
    tp=1.0860,
    type_time=mt5.ORDER_TIME_SPECIFIED,
    expiration=expiration,
    comment="Auto-expire in 30m"
)

# Order will automatically be removed after 30 minutes if not triggered
```

---

## 📋 Order Type Reference

| Order Type | When to Use | Price Relationship |
|------------|-------------|-------------------|
| BUY_LIMIT | Buy cheaper | Below current ask |
| SELL_LIMIT | Sell higher | Above current bid |
| BUY_STOP | Buy breakout | Above current ask |
| SELL_STOP | Sell breakdown | Below current bid |

---

## ⏰ Expiration Types

```python
import MetaTrader5 as mt5

# Good til canceled (default)
type_time = mt5.ORDER_TIME_GTC

# Expires at end of day
type_time = mt5.ORDER_TIME_DAY

# Expires at specific time (requires expiration parameter)
type_time = mt5.ORDER_TIME_SPECIFIED
expiration = datetime.now() + timedelta(hours=2)

# Expires at end of specified day
type_time = mt5.ORDER_TIME_SPECIFIED_DAY
```

---

## 🎯 Complete Example

```python
from src.connectors import MT5Connector, AccountUtils, OrderType
from datetime import datetime, timedelta
import MetaTrader5 as mt5

# Connect
connector = MT5Connector()
connector.connect(login=12345, password="pass", server="Broker-Demo")

# Get symbol info
symbol = "EURUSD"
info = connector.get_symbol_info(symbol)

# Strategy: Buy limit below current price with 2% risk
entry_price = info.ask - 0.0030  # 30 pips below
stop_loss = entry_price - 0.0020  # 20 pips stop
take_profit = entry_price + 0.0050  # 50 pips profit

# Calculate lot size for 2% risk
lot_size = AccountUtils.risk_based_lot_size(
    symbol=symbol,
    order_type=mt5.ORDER_TYPE_BUY,
    entry_price=entry_price,
    stop_loss=stop_loss,
    risk_percent=2.0
)

# Verify we have enough margin
required_margin = AccountUtils.margin_check(
    symbol, mt5.ORDER_TYPE_BUY, lot_size, entry_price
)

account = connector.get_account_info()

if required_margin and required_margin <= account.margin_free:
    # Place pending order with 2 hour expiration
    expiration = datetime.now() + timedelta(hours=2)
    
    result = connector.buy_limit(
        symbol=symbol,
        volume=lot_size,
        price=entry_price,
        sl=stop_loss,
        tp=take_profit,
        type_time=mt5.ORDER_TIME_SPECIFIED,
        expiration=expiration,
        comment="2% Risk Buy Limit"
    )
    
    if result.success:
        print(f"✓ Order #{result.order_ticket} placed")
        print(f"  Lot size: {lot_size:.2f}")
        print(f"  Risk: 2% of ${account.balance:.2f}")
        print(f"  Required margin: ${required_margin:.2f}")
        print(f"  Expires: {expiration}")
    else:
        print(f"✗ Failed: {result.error_message}")
else:
    print("✗ Insufficient margin")

# Disconnect
connector.disconnect()
```

---

## 📚 See Also

- `INTEGRATION_COMPLETE.md` - Full integration documentation
- `examples/enhanced_features_demo.py` - Complete demo script
- `src/connectors/account_utils.py` - Account utility source
- `src/connectors/error_descriptions.py` - Error code mappings

---

*Quick Reference - TradingMTQ Enhanced Features*  
*Last Updated: November 30, 2025*

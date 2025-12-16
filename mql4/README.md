# MT4 Bridge Server - MQL4 Expert Advisor

This Expert Advisor (EA) provides an HTTP bridge between MT4 and Python, allowing external applications to control MT4 via REST API.

## Features

- ✅ HTTP REST API server running inside MT4
- ✅ Account information retrieval
- ✅ Symbol and market data access
- ✅ Position management
- ✅ Real-time tick data
- ✅ Historical bars (OHLC data)
- ✅ Order execution
- ✅ CORS enabled for web applications

## Installation

### Step 1: Copy Files

**For Mac:**
```bash
cp mt4_bridge_server.mq4 ~/Library/Application\ Support/MetaTrader\ 4/MQL4/Experts/
```

**For Windows:**
```cmd
copy mt4_bridge_server.mq4 "C:\Program Files\MetaTrader 4\MQL4\Experts\"
```

Alternatively, you can:
1. Open MT4
2. Click File → Open Data Folder
3. Navigate to `MQL4/Experts/`
4. Copy `mt4_bridge_server.mq4` here

### Step 2: Compile the EA

1. Open MetaTrader 4
2. Press `F4` to open MetaEditor
3. In the Navigator panel, expand "Experts"
4. Double-click `mt4_bridge_server.mq4`
5. Press `F7` to compile
6. You should see "0 error(s), 0 warning(s)" at the bottom
7. Close MetaEditor

### Step 3: Attach EA to Chart

1. In MT4, open any chart (e.g., EURUSD M15)
2. In the Navigator panel (Ctrl+N), expand "Expert Advisors"
3. Drag `mt4_bridge_server` onto your chart
4. A settings dialog will appear

### Step 4: Configure EA Settings

In the EA settings dialog:

**Inputs Tab:**
- `ServerPort`: 8080 (default, change if port is in use)
- `AllowedIPs`: "127.0.0.1" (localhost only for security)
- `EnableAutoTrading`: true
- `MagicNumber`: 20241215 (or your preferred magic number)
- `LogLevel`: "INFO" (or "DEBUG" for more logs)

**Common Tab:**
- ✅ Allow DLL imports (REQUIRED)
- ✅ Allow WebRequest for listed URL (if needed)
- ✅ Allow external experts imports

Click "OK"

### Step 5: Enable AutoTrading

In MT4 toolbar, click the "AutoTrading" button (or press Ctrl+E).
The button should turn green, and you should see a smiley face in the top-right corner of the chart.

### Step 6: Verify Server is Running

Check the "Experts" tab at the bottom of MT4. You should see:

```
=== MT4 Bridge Server Initializing ===
Port: 8080
Allowed IPs: 127.0.0.1
AutoTrading: true
=== MT4 Bridge Server Started ===
Listening on http://localhost:8080
Send test request: http://localhost:8080/ping
```

## Testing the Server

### Command Line Test (Mac/Linux)

```bash
# Test ping endpoint
curl http://localhost:8080/ping

# Expected response:
# {"success": true, "message": "pong"}

# Test status endpoint
curl http://localhost:8080/status

# Test account info
curl http://localhost:8080/account/info
```

### Command Line Test (Windows PowerShell)

```powershell
# Test ping endpoint
Invoke-WebRequest -Uri http://localhost:8080/ping

# Test status endpoint
Invoke-WebRequest -Uri http://localhost:8080/status

# Test account info
Invoke-WebRequest -Uri http://localhost:8080/account/info
```

### Browser Test

Open your browser and navigate to:
- http://localhost:8080/ping
- http://localhost:8080/status
- http://localhost:8080/account/info

You should see JSON responses.

## Python Connection Test

```python
import requests

# Test connection
response = requests.get('http://localhost:8080/ping')
print(response.json())
# Output: {'success': True, 'message': 'pong'}

# Get account info
response = requests.get('http://localhost:8080/account/info')
print(response.json())
# Output: {'success': True, 'message': 'Account info retrieved', 'data': {...}}
```

## API Endpoints

### Health Check

**GET /ping**
- Check if server is running
- Response: `{"success": true, "message": "pong"}`

**GET /status**
- Get MT4 connection status
- Response: `{"success": true, "message": "Status retrieved", "data": {...}}`

### Account Information

**GET /account/info**
- Get detailed account information
- Response includes: login, server, balance, equity, margin, profit, currency, leverage, company

### Market Data

**GET /symbols**
- Get list of available symbols
- Response: `{"success": true, "data": {"symbols": ["EURUSD", "GBPUSD", ...]}}`

**GET /ticks/{symbol}**
- Get current tick for symbol
- Example: `/ticks/EURUSD`
- Response: `{"success": true, "data": {"symbol": "EURUSD", "bid": 1.09123, "ask": 1.09125, ...}}`

**GET /bars/{symbol}?timeframe=H1&count=100**
- Get historical OHLC bars
- Example: `/bars/EURUSD?timeframe=H1&count=100`
- Response: Array of bars with time, open, high, low, close, volume

### Positions

**GET /positions**
- Get all open positions
- Response: Array of positions with ticket, symbol, type, volume, profit, etc.

**DELETE /positions/{ticket}**
- Close position by ticket number
- Example: `/positions/12345`
- Response: `{"success": true, "message": "Position closed"}`

**PUT /positions/{ticket}**
- Modify position SL/TP
- Body: `{"sl": 1.09000, "tp": 1.10000}`
- Response: `{"success": true, "message": "Position modified"}`

### Trading

**POST /orders**
- Send new order
- Body: `{"symbol": "EURUSD", "order_type": "BUY", "volume": 0.01, "sl": 1.09000, "tp": 1.10000}`
- Response: `{"success": true, "data": {"order": 12345, ...}}`

## Configuration

### Change Port

If port 8080 is already in use:

1. Right-click the EA on the chart
2. Select "Expert properties"
3. Go to "Inputs" tab
4. Change `ServerPort` to another port (e.g., 8081)
5. Click OK
6. Update Python connector:
   ```python
   connector = MT4ConnectorV3Bridge(host='localhost', port=8081)
   ```

### Security Configuration

**Localhost Only (Recommended):**
- `AllowedIPs`: "127.0.0.1"
- Only local applications can connect

**Network Access (Advanced):**
- `AllowedIPs`: "127.0.0.1,192.168.1.100"
- Allow specific IP addresses (comma separated)
- ⚠️ Warning: Only use on trusted networks

### Debug Logging

For troubleshooting:
1. Set `LogLevel` to "DEBUG"
2. Watch the Experts tab for detailed logs
3. Check Journal tab for system messages

## Troubleshooting

### EA not starting

**Problem:** EA shows error on start

**Solutions:**
1. Ensure AutoTrading is enabled (green button in toolbar)
2. Check "Allow DLL imports" is enabled in EA settings
3. Verify port is not in use by another application
4. Check MT4 is connected to broker

### Connection refused from Python

**Problem:** `Connection refused` error

**Solutions:**
1. Verify EA is running (check Experts tab for "Server Started" message)
2. Check port number matches (default 8080)
3. Ensure MT4 is running
4. Test with curl/browser first
5. Check firewall settings

### No response from endpoints

**Problem:** Server running but endpoints return errors

**Solutions:**
1. Check MT4 is logged in to broker
2. Verify symbol exists (for market data endpoints)
3. Check Experts tab for error messages
4. Enable DEBUG logging for more details

### Position operations fail

**Problem:** Cannot open/close positions

**Solutions:**
1. Verify AutoTrading is enabled
2. Check account has sufficient margin
3. Verify symbol is tradable
4. Check broker allows automated trading
5. Review MT4 Journal tab for trade errors

### Server stops responding

**Problem:** Server stops after some time

**Solutions:**
1. Check MT4 hasn't disconnected from broker
2. Ensure chart with EA is still open
3. Check computer hasn't gone to sleep
4. Review Experts tab for errors
5. Restart EA if needed

## Using with Python

### Basic Connection

```python
from src.connectors.mt4_connector_v3_bridge import MT4ConnectorV3Bridge

# Create connector
connector = MT4ConnectorV3Bridge(
    instance_id="my_account",
    host="localhost",
    port=8080
)

# Connect (verifies bridge is accessible)
success = connector.connect(
    login=12345678,
    password="your_password",
    server="YourBroker-Demo"
)

if success:
    print("Connected to MT4!")

    # Get account info
    account = connector.get_account_info()
    print(f"Balance: {account.balance}")
    print(f"Equity: {account.equity}")

    # Get positions
    positions = connector.get_positions()
    print(f"Open positions: {len(positions)}")

else:
    print("Connection failed")
```

### With Session Manager

```python
from src.services.session_manager import session_manager
from src.database.models import TradingAccount, PlatformType

# Account is configured with platform_type = MT4
# Session manager automatically selects MT4ConnectorV3Bridge

account = db.query(TradingAccount).filter_by(platform_type=PlatformType.MT4).first()

success, error = await session_manager.connect_account(account, db)

if success:
    connector = session_manager.get_session(account.id)
    # Use connector...
```

## Performance Notes

- Bridge adds ~10-50ms latency compared to direct API
- Suitable for most trading strategies
- For high-frequency trading, consider direct API or FIX protocol
- HTTP requests are synchronous (blocking)

## Limitations

- MT4 must be running for bridge to work
- One EA instance per MT4 terminal
- HTTP (not HTTPS) - use localhost only
- Limited to MT4's order execution capabilities
- Some advanced order types may not be supported

## Advanced Usage

### Multiple MT4 Instances

To run multiple MT4 instances:

1. Install MT4 in different directories
2. Use different ports for each EA (8080, 8081, etc.)
3. Create separate connectors for each instance

```python
# Account 1 (MT4 instance on port 8080)
connector1 = MT4ConnectorV3Bridge(port=8080)

# Account 2 (MT4 instance on port 8081)
connector2 = MT4ConnectorV3Bridge(port=8081)
```

### Custom Magic Numbers

Use magic numbers to identify orders from different strategies:

```python
# Set magic number in EA settings
# Use same magic number in Python requests

request = TradeRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=0.01,
    magic=20241215  # Must match EA's MagicNumber setting
)
```

## Support

For issues or questions:
1. Check MT4 Experts tab for error messages
2. Enable DEBUG logging in EA settings
3. Test with curl/browser before using Python
4. Review this README for common solutions
5. Check GitHub issues for similar problems

## Security Best Practices

1. ✅ Use localhost only (127.0.0.1)
2. ✅ Don't expose to internet
3. ✅ Use firewall to block external access
4. ✅ Keep MT4 and EA up to date
5. ✅ Test on demo account first
6. ✅ Use strong account passwords
7. ✅ Monitor EA logs regularly
8. ❌ Don't share API port publicly
9. ❌ Don't use on public WiFi
10. ❌ Don't disable security features

## License

This EA is part of the TradingMTQ project.

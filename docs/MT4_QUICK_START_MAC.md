# MT4 Quick Start Guide for Mac

This guide will help you connect your MT4 account on Mac to TradingMTQ using the bridge solution.

## Why Bridge Solution for Mac?

MT4 on Mac has limitations with external APIs. The bridge solution is the most reliable approach:
- ✅ Works with any broker
- ✅ No broker approval needed
- ✅ Simple HTTP communication
- ✅ Full MT4 functionality
- ✅ Easy to debug and monitor

## Prerequisites

- ✅ MT4 installed on your Mac
- ✅ MT4 connected to your broker
- ✅ TradingMTQ installed
- ✅ Python requests package (`pip install requests`)

## Step-by-Step Setup (15 minutes)

### Step 1: Copy MQL4 Expert Advisor to MT4

```bash
# Navigate to TradingMTQ directory
cd /Users/mfinkels/CodePlatform/PersonalCode/TradingMTQ

# Copy EA to MT4 Experts folder
cp mql4/mt4_bridge_server.mq4 ~/Library/Application\ Support/MetaTrader\ 4/MQL4/Experts/
```

### Step 2: Compile the EA

1. Open MetaTrader 4
2. Press `⌘+F4` (or Tools → MetaQuotes Language Editor)
3. In MetaEditor Navigator panel:
   - Expand "Experts"
   - Double-click `mt4_bridge_server.mq4`
4. Press `⌘+F7` (or Compile → Compile)
5. Check bottom: "0 error(s), 0 warning(s)" ✅
6. Close MetaEditor

### Step 3: Attach EA to Chart

1. In MT4, open any chart (e.g., EURUSD, any timeframe)
2. Press `⌘+N` to open Navigator
3. Expand "Expert Advisors"
4. Drag `mt4_bridge_server` onto the chart
5. Settings dialog appears

### Step 4: Configure EA Settings

**Inputs Tab:**
- ServerPort: `8080` (default)
- AllowedIPs: `127.0.0.1` (localhost only)
- EnableAutoTrading: `true` ✅
- MagicNumber: `20241215`
- LogLevel: `INFO`

**Common Tab:**
- ✅ Allow DLL imports (REQUIRED - check this box!)
- ✅ Allow external experts imports

Click **OK**

### Step 5: Enable AutoTrading

- In MT4 toolbar, click "AutoTrading" button
- Button should turn GREEN
- Smiley face appears in chart top-right corner ✅

### Step 6: Verify Server is Running

Check MT4 "Experts" tab (bottom of screen). You should see:

```
=== MT4 Bridge Server Initializing ===
Port: 8080
Allowed IPs: 127.0.0.1
AutoTrading: true
=== MT4 Bridge Server Started ===
Listening on http://localhost:8080
```

✅ If you see this, the server is running!

### Step 7: Test Connection from Terminal

Open Terminal and run:

```bash
# Test ping
curl http://localhost:8080/ping

# Expected output:
# {"success": true, "message": "pong"}

# Test account info
curl http://localhost:8080/account/info

# Expected output:
# {"success": true, "message": "Account info retrieved", "data": {...}}
```

✅ If you get JSON responses, the bridge is working!

### Step 8: Connect from Python/TradingMTQ

Your MT4 account in TradingMTQ dashboard should now connect successfully!

When you click "Connect" button:
1. UI sends request to Python API
2. Python creates MT4ConnectorV3Bridge
3. Bridge sends HTTP request to MT4 EA
4. EA responds with account status
5. Connection succeeds! ✅

## Verification Checklist

Before clicking "Connect" in TradingMTQ UI:

- [ ] MT4 is running
- [ ] MT4 is logged in to your broker
- [ ] EA is attached to a chart
- [ ] AutoTrading button is GREEN
- [ ] Smiley face visible on chart
- [ ] Experts tab shows "Server Started"
- [ ] Terminal curl test succeeds
- [ ] Account platform_type is set to "MT4" in UI

## Testing the Connection

### From TradingMTQ UI

1. Go to http://localhost:8000 (or http://0.0.0.0:8000)
2. Navigate to Accounts page
3. Find your MT4 account
4. Click "Connect" button
5. Status should change to "Connected" ✅
6. Connection icon turns green
7. "Last Connected" shows current time

### From Python Code

```python
from src.services.session_manager import session_manager
from src.database.models import TradingAccount, PlatformType
from src.database.connection import get_session
import asyncio

async def test_mt4_connection():
    with get_session() as db:
        # Get your MT4 account
        account = db.query(TradingAccount).filter(
            TradingAccount.platform_type == PlatformType.MT4
        ).first()

        if not account:
            print("No MT4 account found in database")
            return

        print(f"Connecting to MT4 account: {account.account_name}")

        # Connect
        success, error = await session_manager.connect_account(account, db)

        if success:
            print("✅ Connected to MT4!")

            # Get connector
            connector = session_manager.get_session(account.id)

            # Test account info
            info = connector.get_account_info()
            if info:
                print(f"Account: {info.login}")
                print(f"Balance: {info.balance}")
                print(f"Equity: {info.equity}")
                print(f"Server: {info.server}")

            # Get positions
            positions = connector.get_positions()
            print(f"Open positions: {len(positions)}")

        else:
            print(f"❌ Connection failed: {error}")

# Run test
asyncio.run(test_mt4_connection())
```

## Troubleshooting

### EA Not Starting

**Problem:** EA shows "Disconnect from server" or error

**Solutions:**
1. Check AutoTrading is enabled (green button)
2. Verify "Allow DLL imports" is checked in EA settings
3. Check MT4 is connected to broker
4. Review Experts tab for specific error messages

### Connection Refused

**Problem:** `curl` returns "Connection refused"

**Solutions:**
1. Verify EA shows "Server Started" in Experts tab
2. Check port 8080 isn't used by another app:
   ```bash
   lsof -i :8080
   ```
3. Try different port (update in EA settings and Python code)
4. Check firewall settings

### Python Connection Fails

**Problem:** TradingMTQ shows "Connection failed"

**Solutions:**
1. First test with curl to isolate issue
2. Check logs in `logs/trading_YYYYMMDD.log`
3. Verify MT4 EA is still running
4. Check account credentials are correct
5. Restart MT4 EA if needed

### Orders Not Executing

**Problem:** Can get data but can't place orders

**Solutions:**
1. Verify AutoTrading is enabled
2. Check account has sufficient margin
3. Verify symbol is tradable
4. Check broker allows automated trading
5. Review MT4 Journal tab for trade-specific errors

## Keeping Bridge Running

### Persistent Setup

To keep the bridge always available:

1. **Open MT4 on startup:**
   - System Preferences → Users & Groups → Login Items
   - Add MT4 to login items

2. **Auto-attach EA:**
   - MT4 → Tools → Options → Expert Advisors
   - ✅ Enable "Allow automated trading"
   - Save workspace with EA attached

3. **Prevent Mac sleep:**
   - System Preferences → Energy Saver
   - Prevent computer from sleeping while display is off

### Monitoring

Check EA status:
- Green smiley face = Running ✅
- Red crossed face = Stopped ❌

View logs in MT4:
- **Experts tab**: EA messages
- **Journal tab**: MT4 system messages

## Advanced Configuration

### Using Different Port

If port 8080 is in use:

1. **In MT4 EA settings:**
   - Change ServerPort to 8081

2. **In Python connector:**
   ```python
   from src.connectors.mt4_connector_v3_bridge import MT4ConnectorV3Bridge

   # Use custom port
   connector = MT4ConnectorV3Bridge(
       instance_id="my_mt4",
       host="localhost",
       port=8081  # Match EA port
   )
   ```

### Running Multiple MT4 Instances

To connect multiple MT4 accounts:

1. Install MT4 in different locations
2. Use different ports for each EA (8080, 8081, 8082)
3. Each account connects to its specific port

## Security Notes

- ✅ Bridge only accepts localhost connections (127.0.0.1)
- ✅ No external network access by default
- ✅ Data never leaves your computer
- ❌ Don't expose port to internet
- ❌ Don't disable security settings

## Performance

- Bridge adds ~10-50ms latency
- Suitable for most trading strategies
- Not recommended for high-frequency trading
- HTTP requests are synchronous

## Next Steps

Once connected:

1. ✅ View real-time account balance and equity
2. ✅ Monitor open positions
3. ✅ Execute trades via UI or Python
4. ✅ View historical data and charts
5. ✅ Set up automated trading strategies

## Support

If you encounter issues:

1. Check MT4 Experts tab for errors
2. Review `logs/trading_YYYYMMDD.log`
3. Test with curl before Python
4. See full troubleshooting: [mql4/README.md](../mql4/README.md)
5. See detailed guide: [docs/MT4_INTEGRATION_GUIDE.md](MT4_INTEGRATION_GUIDE.md)

## Summary

✅ **What You Did:**
- Installed MQL4 Expert Advisor in MT4
- Configured EA to run HTTP server on port 8080
- Connected Python to MT4 via HTTP bridge
- Your MT4 account is now fully integrated with TradingMTQ!

✅ **What Works:**
- Real-time account information
- Position management
- Market data and ticks
- Order execution
- Historical data

🎉 **You're ready to trade with MT4 on your Mac!**

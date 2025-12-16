# Direct MetaTrader Packages Setup Guide

## Overview

TradingMTQ now uses **direct Python packages** for MetaTrader 4 and 5 integration, designed for **Windows and Linux** environments where the official packages are natively supported.

## Architecture

```
Python Application
    ↓
MetaTrader5/MetaTrader4 Package (official)
    ↓
MT5/MT4 Terminal
    ↓
Broker
```

**Simple, direct API access with no intermediate layers.**

## Requirements

### System Requirements
- **Operating System:** Windows 10/11 or Linux (Ubuntu 20.04+)
- **Python:** 3.8+ (3.14 tested and working)
- **MetaTrader 5** and/or **MetaTrader 4** installed

### Python Packages

**For MT5:**
```bash
pip install MetaTrader5
```

**For MT4:**
```bash
pip install MetaTrader4
```

**Note:** These packages are **only available on Windows and Linux**. They will not install on macOS.

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/TradingMTQ.git
cd TradingMTQ
git checkout initial-claude-refactor
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt

# Install MT5 package (for MT5 accounts)
pip install MetaTrader5

# Install MT4 package (for MT4 accounts)
pip install MetaTrader4
```

### 4. Configure Database
```bash
# Initialize database
python src/database/migration_utils.py init

# Run migrations
python src/database/migration_utils.py upgrade
```

## Configuration

### 1. Environment Variables

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
# Database
DATABASE_URL=sqlite:///./tradingmtq.db

# MT5 Account (if using MT5)
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=broker_server_name

# MT4 Account (if using MT4)
MT4_LOGIN=your_account_number
MT4_PASSWORD=your_password
MT4_SERVER=broker_server_name
```

### 2. Add Accounts via UI

1. Start the server:
   ```bash
   python -m src.api.app
   ```

2. Open http://localhost:8000/accounts.html

3. Click "Add Account"

4. Fill in details:
   - **Account Number:** Your MT4/MT5 login
   - **Account Name:** Any descriptive name
   - **Broker:** Your broker name
   - **Server:** Broker server (e.g., "MetaQuotes-Demo")
   - **Platform Type:** Select "MT5" or "MT4"
   - **Login:** Your account number
   - **Password:** Your account password (optional, for auto-connect)

5. Save

## Usage

### Starting the Server

```bash
# Start API server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Or with reload for development
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Connecting Accounts

**Via UI:**
1. Go to http://localhost:8000/accounts.html
2. Click "Connect" next to your account
3. Status should change to "Connected" ✅

**Via API:**
```bash
curl -X POST http://localhost:8000/api/accounts/connect-all
```

**Via Python:**
```python
from src.connectors import MT5Connector, MT4Connector

# Connect MT5
mt5 = MT5Connector()
mt5.connect(
    login=12345678,
    password="your_password",
    server="YourBroker-Demo"
)

# Get account info
account_info = mt5.get_account_info()
print(f"Balance: {account_info.balance}")
print(f"Equity: {account_info.equity}")

# Get positions
positions = mt5.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.type} {pos.volume} lots @ {pos.price_open}")

# Disconnect
mt5.disconnect()
```

## Verifying Installation

### Test MT5 Connection
```python
./venv/bin/python -c "
import MetaTrader5 as mt5
print('MetaTrader5 version:', mt5.__version__)
if mt5.initialize():
    print('✅ MT5 initialized successfully')
    print('Terminal info:', mt5.terminal_info())
    mt5.shutdown()
else:
    print('❌ MT5 initialization failed')
"
```

### Test MT4 Connection
```python
./venv/bin/python -c "
import MetaTrader4 as mt4
print('✅ MetaTrader4 package installed')
# Note: MT4 package has different initialization
"
```

### Test TradingMTQ Connectors
```bash
./venv/bin/python -c "
from src.connectors import MT5Connector, MT4Connector
print('✅ MT5Connector:', MT5Connector)
print('✅ MT4Connector:', MT4Connector)
"
```

## Platform Selection

TradingMTQ supports both MT4 and MT5:

1. **In the UI:** Select platform type when adding account
2. **In the database:** `accounts.platform_type` field ("MT4" or "MT5")
3. **Automatic routing:** System automatically uses correct connector based on platform_type

## Troubleshooting

### MetaTrader5 Package Not Found

**Error:** `ModuleNotFoundError: No module named 'MetaTrader5'`

**Solution:**
```bash
# Verify Python version (3.8+ required)
python --version

# Install in correct environment
pip install MetaTrader5

# If still failing, check platform:
python -c "import platform; print(platform.system())"
# Must be "Windows" or "Linux", not "Darwin" (macOS)
```

### MT5 Initialization Failed

**Error:** `mt5.initialize() returns False`

**Possible causes:**
1. **MT5 not installed:** Install MetaTrader 5 from your broker
2. **MT5 not running:** Launch MT5 terminal
3. **Wrong credentials:** Check login, password, server
4. **Firewall blocking:** Allow MT5 in firewall

**Debug:**
```python
import MetaTrader5 as mt5
if not mt5.initialize():
    error = mt5.last_error()
    print(f"Error: {error}")
```

### Connection Refused

**Error:** "Connection refused" when connecting via API

**Solution:**
1. Check server is running: `curl http://localhost:8000/health`
2. Restart server: `pkill -f uvicorn && uvicorn src.api.app:app`
3. Check logs: `tail -f logs/trading_*.log`

### Account Not Connecting

**Symptoms:** Account shows "Disconnected" in UI

**Solutions:**
1. **Verify credentials:**
   - Login to MT5/MT4 terminal manually
   - Check account number, password, server
2. **Check MT5/MT4 is running:**
   - Terminal must be open and logged in
   - Check "Tools → Options → Expert Advisors → Allow automated trading"
3. **Check database:**
   ```bash
   sqlite3 tradingmtq.db "SELECT * FROM accounts;"
   ```
4. **Check logs:**
   ```bash
   tail -f logs/trading_*.log
   ```

### Import Errors

**Error:** `ImportError: cannot import name 'MT5Connector'`

**Solution:**
```bash
# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# Reinstall in development mode
pip install -e .
```

## Development

### Running Tests
```bash
# Unit tests
python test_database.py

# Integration tests
python test_trading_with_db.py

# Connector tests
python -m pytest tests/test_connectors.py -v
```

### Code Structure
```
src/
├── connectors/
│   ├── mt5_connector.py      # MT5 direct package connector
│   ├── mt4_connector.py      # MT4 direct package connector
│   ├── base.py               # Base connector interface
│   ├── account_utils.py      # Account utilities
│   └── error_descriptions.py # Error code descriptions
├── api/
│   ├── app.py               # FastAPI application
│   └── routes/
│       └── accounts.py      # Account management routes
└── services/
    └── session_manager.py   # Connection management
```

## Benefits of Direct Package Approach

✅ **Simplicity:** No bridge layers, MQL EAs, or complex setup
✅ **Performance:** Direct API access, no HTTP overhead
✅ **Reliability:** Official packages maintained by MetaQuotes
✅ **Features:** Full access to all MT4/MT5 functionality
✅ **Debugging:** Easier to troubleshoot, standard Python debugging
✅ **Deployment:** Simple pip install, no external dependencies

## Migration from Bridge Version

If you were using the bridge-based connectors (tag: `mt4-mt5-bridge-v1.0`):

1. **Checkout this version:**
   ```bash
   git checkout initial-claude-refactor
   ```

2. **Uninstall bridge dependencies:**
   ```bash
   # No special dependencies to remove
   ```

3. **Install direct packages:**
   ```bash
   pip install MetaTrader5 MetaTrader4
   ```

4. **Update accounts:**
   - Platform type should already be set correctly
   - No changes needed to database

5. **Remove MQL EAs:**
   - Delete any bridge EAs from MT4/MT5 Experts folder
   - Not needed anymore

6. **Restart:**
   ```bash
   uvicorn src.api.app:app --host 0.0.0.0 --port 8000
   ```

## Support

### Documentation
- [README.md](../README.md) - Main documentation
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [src/connectors/README.md](../src/connectors/README.md) - Connector details

### Logs
```bash
# View recent logs
tail -f logs/trading_$(date +%Y%m%d).log

# Search for errors
grep ERROR logs/trading_*.log
```

### Common Issues
1. **"MetaTrader5 not available"** → Run on Windows/Linux
2. **"Connection failed"** → Check MT5/MT4 is running and logged in
3. **"Import error"** → Clear Python cache, reinstall packages
4. **"Database locked"** → Close other connections, restart server

## Production Deployment

For production deployment on Windows/Linux servers:

1. **Use dedicated server:** Windows Server 2019+ or Ubuntu 20.04+
2. **Install MT5/MT4:** From broker website
3. **Setup service:** Use systemd (Linux) or Windows Service
4. **Configure logging:** Rotate logs, monitor errors
5. **Enable monitoring:** Set up health checks
6. **Backup database:** Regular automated backups

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

---

## Summary

✅ **Removed:** Bridge connectors, MQL EAs, socket tests, Mac docs (~5,000 lines)
✅ **Restored:** Direct MetaTrader5/MetaTrader4 package integration
✅ **Target:** Windows/Linux environments only
✅ **Status:** Production ready

**Git Tags:**
- `direct-packages-only-v1.0` - This version (direct packages)
- `mt4-mt5-bridge-v1.0` - Previous version (bridge solution)

**Current Branch:** `initial-claude-refactor`
**Commit:** `8ba985c` (refactor: Remove bridge layer)

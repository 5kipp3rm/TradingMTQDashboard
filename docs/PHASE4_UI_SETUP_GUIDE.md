# Phase 4 Worker UI Setup Guide

## Overview

The UI has been updated to use the **Phase 4 Worker System** for multi-account MT5 connections. This guide explains how to set up and use the new system.

---

## What Changed

### Before (Old System)
- **Connection Method**: Session Manager (database-based)
- **Account IDs**: Integer database IDs (1, 2, 3...)
- **MT5 Instances**: Single shared instance (disconnected first account when starting second)
- **Endpoints**: `/api/accounts/{account_id}/connect`
- **Trading Bot**: Only worked with session-based accounts

### After (Phase 4 System)
- **Connection Method**: Worker Manager Service (config-based)
- **Account IDs**: String config IDs ("account-001", "account-002"...)
- **MT5 Instances**: Multiple isolated instances (both accounts run simultaneously)
- **Endpoints**: `/api/workers/{account_id}/start`
- **Trading Bot**: Works with both session-based AND worker-based accounts

---

## Setup Steps

### Step 1: Create Account Configuration Files

For each trading account, create a YAML configuration file in `config/accounts/`:

**Example**: `config/accounts/account-001.yml`

```yaml
account_id: "account-001"
login: 5012345678          # Your MT5 login number
password: "your_password"   # Your MT5 password
server: "Broker-Server"     # Your broker's server name
platform_type: "MT5"
portable: true              # Enable multi-instance support

currencies:
  - symbol: "EURUSD"
    enabled: true
    risk:
      risk_percent: 1.0
      max_positions: 3
      stop_loss_pips: 50
      take_profit_pips: 100
    strategy:
      strategy_type: "SIMPLE_MA"
      timeframe: "M5"
      fast_period: 10
      slow_period: 20

  - symbol: "GBPUSD"
    enabled: true
    risk:
      risk_percent: 1.0
      max_positions: 3
      stop_loss_pips: 50
      take_profit_pips: 100
    strategy:
      strategy_type: "SIMPLE_MA"
      timeframe: "M5"
      fast_period: 10
      slow_period: 20

# Add more currency pairs as needed
```

**Example**: `config/accounts/account-002.yml`

```yaml
account_id: "account-002"
login: 5098765432
password: "your_password"
server: "Broker-Server"
platform_type: "MT5"
portable: true

currencies:
  - symbol: "EURUSD"
    enabled: true
    risk:
      risk_percent: 1.0
      max_positions: 3
      stop_loss_pips: 50
      take_profit_pips: 100
    strategy:
      strategy_type: "SIMPLE_MA"
      timeframe: "M5"
      fast_period: 10
      slow_period: 20
```

### Step 2: Create Default Configuration (Optional)

Create `config/accounts/default.yml` to provide default values:

```yaml
default_risk:
  risk_percent: 1.0
  max_positions: 5
  max_concurrent_trades: 15
  portfolio_risk_percent: 10.0
  stop_loss_pips: 50
  take_profit_pips: 100

platform_type: "MT5"
portable: true
timeout: 60000
```

---

## Using the UI

### 1. Open the Dashboard

Navigate to `http://localhost:8000` (or your configured host)

### 2. Go to Accounts Page

Click on "Accounts" in the navigation menu

### 3. Connect Accounts

**Option A: Connect Individual Account**
1. Find your account in the list
2. Click the "Connect" button
3. The UI will use the Phase 4 worker system automatically
4. You'll see a success message: "✅ Phase 4 worker started successfully!"

**Option B: Connect All Accounts**
1. Click "Connect All" button in the header
2. All active accounts with Phase 4 configurations will connect
3. You'll see: "✅ Phase 4: Connected N of M accounts"

### 4. Verify Multi-Instance MT5

**On Windows**:
- Open Task Manager
- Look for multiple `terminal64.exe` processes
- You should see one process per connected account

**On macOS**:
- Open Activity Monitor
- Look for multiple wine processes
- Each account runs in its own wine instance

### 5. Use Quick Trade

1. Click "Quick Trade" button (⚡ icon)
2. **Select Trading Account**: Dropdown shows all connected Phase 4 workers
3. **Select Currency Pair**: Choose from available pairs
4. **Enter Trade Details**: Volume, SL, TP
5. **Execute Trade**: Click BUY or SELL

---

## Automated Trading

### How It Works

The trading bot **automatically detects and trades** on Phase 4 workers:

1. **Trading Bot Service** starts automatically with API server
2. Every **60 seconds**, it checks for:
   - Session-based accounts (old system)
   - Worker-based accounts (Phase 4)
3. For each Phase 4 worker:
   - Loads currency configs from YAML
   - Creates MultiCurrencyOrchestrator
   - Executes trading cycle
   - Places trades based on strategy signals

### Check Trading Bot Status

```bash
GET http://localhost:8000/api/trading-bot/status
```

**Response**:
```json
{
  "is_running": true,
  "check_interval": 60,
  "connected_accounts": 2,
  "session_based_accounts": 0,
  "worker_based_accounts": 2,
  "account_ids": [],
  "worker_ids": ["account-001", "account-002"],
  "active_traders": 4
}
```

### View Logs

Check logs for trading bot activity:

```bash
# Trading cycle logs
grep "Executing trading cycle" logs/tradingmtq.log

# Phase 4 worker detection logs
grep "Found.*active Phase 4 workers" logs/tradingmtq.log

# Trading execution logs
grep "Trading worker account" logs/tradingmtq.log
```

---

## Troubleshooting

### Issue: "No connected accounts" in Quick Trade dropdown

**Cause**: No Phase 4 workers are connected

**Solution**:
1. Go to Accounts page
2. Connect at least one account using the "Connect" button
3. Return to dashboard and open Quick Trade again

### Issue: "Failed to start worker: No such file or directory"

**Cause**: Missing account configuration file

**Solution**:
1. Create `config/accounts/account-{login}.yml`
2. Fill in account details (see Step 1 above)
3. Try connecting again

### Issue: "Validation failed" when connecting

**Cause**: Invalid configuration in YAML file

**Solution**:
1. Validate your YAML syntax
2. Check required fields are present:
   - `account_id`
   - `login`
   - `password`
   - `server`
3. Fix errors and try again

### Issue: First account disconnects when second connects

**Cause**: Still using old session manager system

**Solution**:
1. Ensure `worker-connector.js` is loaded in HTML
2. Check browser console for errors
3. Verify Phase 4 config files exist
4. Clear browser cache and reload

### Issue: "Worker already exists for account"

**Cause**: Attempting to start a worker that's already running

**Solution**:
1. Disconnect the existing worker first
2. Then reconnect if needed

---

## API Endpoints

### Phase 4 Worker Management

```bash
# Start worker
POST /api/workers/{account_id}/start
Body: {"apply_defaults": true, "validate": true}

# Stop worker
POST /api/workers/{account_id}/stop
Body: {"timeout": 5.0}

# Get worker info
GET /api/workers/{account_id}

# List all workers
GET /api/workers

# Validate config
GET /api/workers/{account_id}/validate

# Start all enabled workers
POST /api/workers/start-all?apply_defaults=true&validate=true

# Stop all workers
POST /api/workers/stop-all
```

### Trading Bot

```bash
# Get trading bot status
GET /api/trading-bot/status

# Start trading bot (automatic on server start)
POST /api/trading-bot/start

# Stop trading bot
POST /api/trading-bot/stop
```

---

## Account ID Mapping

The system automatically maps database account IDs to Phase 4 worker IDs:

| Database Account ID | Account Number (Login) | Phase 4 Worker ID |
|---------------------|------------------------|-------------------|
| 1                   | 5012345678             | account-5012345678 |
| 2                   | 5098765432             | account-5098765432 |

Create your YAML configs using the format: `config/accounts/account-{login}.yml`

---

## Next Steps

1. ✅ Create YAML configs for your accounts
2. ✅ Start the API server: `./venv/bin/tradingmtq serve`
3. ✅ Open the dashboard: `http://localhost:8000`
4. ✅ Connect your accounts via Phase 4 workers
5. ✅ Verify multi-instance MT5 is working
6. ✅ Check trading bot status and logs
7. ✅ Test quick trade with account selection

---

## Benefits of Phase 4 System

✅ **Multi-Account Support**: Run multiple accounts simultaneously without disconnections

✅ **Process Isolation**: Each account in separate MT5 instance (crash-proof)

✅ **Config-Based**: Easy to manage account settings via YAML files

✅ **Automated Trading**: Trading bot automatically detects and trades on Phase 4 workers

✅ **Scalable Architecture**: Clean separation of concerns, easy to extend

✅ **Backwards Compatible**: Old session manager still works as fallback

---

**Status**: Ready for Testing! 🚀

All Phase 4 features are implemented and the UI is fully integrated. You can now connect multiple accounts and they will run simultaneously with isolated MT5 instances.

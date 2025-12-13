# Production Deployment Checklist - TradingMTQ

**Date:** December 13, 2025
**Target:** Windows Machine + MetaTrader5
**Phase:** 5.1 Production Deployment
**Estimated Time:** 1-2 hours

---

## 🎯 Pre-Deployment Overview

### What You'll Accomplish
- ✅ Deploy TradingMTQ to Windows with MT5
- ✅ Setup production PostgreSQL database
- ✅ Configure MT5 credentials securely
- ✅ Test system in demo mode
- ✅ Go live with full database tracking

### What's Already Ready
- ✅ Code: Phase 5.1 complete with testing
- ✅ Database: Models, repositories, migrations
- ✅ CLI: Commands ready (`tradingmtq trade`)
- ✅ Tests: 106 tests passing
- ✅ Quality: Python 3.14 compatible, zero warnings

---

## 📋 Pre-Deployment Checklist

### 1. Windows Machine Requirements

**Hardware:**
- [ ] Windows 10/11 (64-bit)
- [ ] 8GB RAM minimum (16GB recommended)
- [ ] Multi-core CPU (4+ cores recommended)
- [ ] 20GB+ free disk space
- [ ] Stable internet connection

**Software:**
- [ ] MetaTrader 5 installed and configured
- [ ] Python 3.9+ installed (3.11+ recommended)
- [ ] Git installed (for cloning repo)
- [ ] PostgreSQL 13+ installed (or plan to use SQLite)

---

## 🚀 Deployment Steps

### Step 1: Environment Setup (15 minutes)

#### 1.1 Clone Repository

```powershell
# Navigate to your projects directory
cd C:\Projects

# Clone the repository
git clone https://github.com/5kipp3rm/TradingMTQ.git
cd TradingMTQ

# Checkout the working branch
git checkout initial-claude-refactor
```

**Verification:**
```powershell
dir
# Should see: src/, tests/, config/, docs/, main.py, etc.
```

---

#### 1.2 Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Or if using CMD
.\venv\Scripts\activate.bat

# Verify activation (should see (venv) prefix)
```

**Verification:**
```powershell
python --version
# Should show: Python 3.9+ (3.11+ recommended)
```

---

#### 1.3 Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .
```

**Verification:**
```powershell
# Test CLI installation
tradingmtq version

# Expected output:
# TradingMTQ v2.0.0
# Advanced Multi-Currency Trading Bot
```

---

### Step 2: MetaTrader5 Setup (10 minutes)

#### 2.1 Verify MT5 Installation

- [ ] Open MetaTrader 5
- [ ] Login to your demo or live account
- [ ] Verify "Algo Trading" button is enabled (top toolbar)
- [ ] Go to Tools → Options → Expert Advisors
  - [ ] Check "Allow automated trading"
  - [ ] Check "Allow DLL imports"
  - [ ] Check "Allow WebRequest for listed URLs" (if needed)

#### 2.2 Get Account Credentials

**From MT5 Terminal:**
1. View → Toolbox → Trade tab
2. Right-click → Account → Properties
3. Note down:
   - Login number
   - Server name
   - Password (you should know this)

**Example:**
```
Login:    12345678
Server:   ICMarkets-Demo01
Password: YourPassword123
```

---

### Step 3: Database Setup (20 minutes)

#### Option A: PostgreSQL (Production - Recommended)

**3.1 Install PostgreSQL:**
```powershell
# Download from: https://www.postgresql.org/download/windows/
# Or use Chocolatey
choco install postgresql
```

**3.2 Create Database:**
```powershell
# Open psql terminal (Start Menu → PostgreSQL → SQL Shell)

# Login as postgres user
# Enter password when prompted

# Create database
CREATE DATABASE tradingmtq;

# Create user (optional but recommended)
CREATE USER tradingmtq_user WITH ENCRYPTED PASSWORD 'YourSecurePassword123';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tradingmtq TO tradingmtq_user;

# Exit
\q
```

**3.3 Connection String:**
```
postgresql://tradingmtq_user:YourSecurePassword123@localhost:5432/tradingmtq
```

---

#### Option B: SQLite (Quick Start/Testing)

**No setup required!** Database file will be created automatically.

**Connection String:**
```
sqlite:///./tradingmtq.db
```

---

### Step 4: Configuration (15 minutes)

#### 4.1 Create `.env` File

```powershell
# Create .env file in project root
# Use notepad or your preferred editor
notepad .env
```

**Paste this content (update with your values):**

```bash
# MetaTrader 5 Configuration
MT5_LOGIN=12345678
MT5_PASSWORD=YourPassword123
MT5_SERVER=ICMarkets-Demo01

# Database Configuration
# For PostgreSQL:
TRADING_MTQ_DATABASE_URL=postgresql://tradingmtq_user:YourSecurePassword123@localhost:5432/tradingmtq

# For SQLite (alternative):
# TRADING_MTQ_DATABASE_URL=sqlite:///./tradingmtq.db

# Optional: OpenAI for LLM sentiment analysis
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Anthropic for LLM sentiment analysis
ANTHROPIC_API_KEY=your-anthropic-key-here

# Feature Flags
ENABLE_ML=true
ENABLE_LLM=true
```

**Save and close.**

---

#### 4.2 Review Trading Configuration

```powershell
# Open trading config
notepad config\currencies.yaml
```

**Key Settings to Review:**

```yaml
trading:
  interval_seconds: 30        # How often to check for signals
  max_concurrent_trades: 15   # Portfolio limit
  portfolio_risk_percent: 10.0

currencies:
  EURUSD:
    enabled: true             # Enable/disable this pair
    risk_percent: 1.0         # Risk per trade
    timeframe: M5             # 5-minute candles
    fast_period: 10           # Fast MA period
    slow_period: 20           # Slow MA period
    sl_pips: 20               # Stop loss in pips
    tp_pips: 40               # Take profit in pips
    max_positions: 3          # Max concurrent positions per pair
```

**Recommendation for First Run:**
- Start with 1-2 currency pairs
- Use conservative settings
- Test in demo mode first

---

### Step 5: Database Initialization (5 minutes)

```powershell
# Initialize database schema
python src\database\migration_utils.py init

# Expected output:
# Database initialization started...
# Creating database schema...
# Running migrations...
# Database initialized successfully!
```

**Verification:**
```powershell
# Check database health
python -c "from src.database.connection import check_database_health; print('Health:', check_database_health())"

# Expected output:
# Health: True
```

---

### Step 6: System Validation (10 minutes)

#### 6.1 Run System Check

```powershell
tradingmtq check
```

**Expected Output:**
```
System Check

  Python Version: 3.11.x

Dependencies:
  [OK] MetaTrader5
  [OK] numpy
  [OK] pandas
  [OK] pyyaml
  [OK] scikit-learn
  [OK] click
```

---

#### 6.2 Run Unit Tests

```powershell
# Run database tests
pytest tests\test_models.py tests\test_repositories.py -v

# Expected: 25/25 tests passing
```

---

#### 6.3 Test MT5 Connection

```powershell
# Create a quick test script
python -c "import MetaTrader5 as mt5; print('MT5 Available:', mt5.initialize()); mt5.shutdown()"

# Expected output:
# MT5 Available: True
```

If False:
- [ ] Check MT5 is running
- [ ] Check "Algo Trading" is enabled
- [ ] Check DLL imports are allowed
- [ ] Restart MT5 and try again

---

### Step 7: Demo Mode Testing (15-30 minutes)

#### 7.1 Start in Demo Mode

```powershell
# Start trading with demo flag
tradingmtq trade --demo

# Or with specific settings
tradingmtq trade --demo -i 60 -m 10
```

**What to Watch:**
```
[2025-12-13 14:00:00] INFO - Starting trading cycle #1
[2025-12-13 14:00:01] INFO - EURUSD: Signal BUY (confidence: 0.85)
[2025-12-13 14:00:02] INFO - Trade executed: Ticket=123456
[2025-12-13 14:00:02] DEBUG - Signal saved to database (ID: 1)
[2025-12-13 14:00:02] DEBUG - Trade saved to database (ID: 1)
[2025-12-13 14:00:05] INFO - Portfolio snapshot saved (ID: 1)
```

---

#### 7.2 Monitor Database

**Open new terminal while trading runs:**

```powershell
# Check trades in database
python -c "from src.database.repository import TradeRepository; from src.database.connection import get_session; repo = TradeRepository(); session = get_session().__enter__(); trades = repo.get_all_trades(session); print(f'Trades: {len(trades)}'); session.close()"

# Check signals
python -c "from src.database.repository import SignalRepository; from src.database.connection import get_session; repo = SignalRepository(); session = get_session().__enter__(); signals = repo.get_recent_signals(session, limit=10); print(f'Signals: {len(signals)}'); session.close()"
```

---

#### 7.3 Verify Data Persistence

```powershell
# Stop trading (Ctrl+C)

# Restart and check data persists
tradingmtq trade --demo

# Should see previous trades loaded
```

---

### Step 8: Production Mode (When Ready)

#### 8.1 Pre-Production Checklist

- [ ] Demo mode tested successfully
- [ ] Trades executed and saved to database
- [ ] Account snapshots captured
- [ ] Statistics calculated correctly
- [ ] No errors in logs
- [ ] Comfortable with system behavior

---

#### 8.2 Switch to Production

**Update `.env` if needed:**
```bash
# Switch from demo to live account
MT5_LOGIN=your_live_account
MT5_PASSWORD=your_live_password
MT5_SERVER=your_live_server
```

**Start Production Trading:**
```powershell
# Start with default settings
tradingmtq trade

# Or with aggressive mode
tradingmtq trade --aggressive

# Or with custom settings
tradingmtq trade -c config\production.yaml -i 30 -m 15
```

---

### Step 9: Monitoring Setup (10 minutes)

#### 9.1 Setup Logging

**Logs Location:** `logs/trading.log`

**Monitor in Real-Time:**
```powershell
# PowerShell
Get-Content logs\trading.log -Wait

# Or use a log viewer
notepad logs\trading.log
```

---

#### 9.2 Create Monitoring Script

**Create `monitor.py`:**
```python
"""Real-time trading monitor"""
from src.database.repository import TradeRepository, AccountSnapshotRepository
from src.database.connection import get_session
import time
from datetime import datetime, timedelta

def monitor_loop():
    trade_repo = TradeRepository()
    snap_repo = AccountSnapshotRepository()

    while True:
        with get_session() as session:
            # Get today's stats
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            stats = trade_repo.get_trade_statistics(session, start_date=today)

            # Get latest snapshot
            snapshot = snap_repo.get_latest_snapshot(session)

            # Display
            print(f"\n{'='*50}")
            print(f"Time: {datetime.now()}")
            print(f"Balance: ${snapshot.balance:.2f}" if snapshot else "No data")
            print(f"Equity: ${snapshot.equity:.2f}" if snapshot else "No data")
            print(f"Open Positions: {snapshot.open_positions}" if snapshot else "0")
            print(f"\nToday's Stats:")
            print(f"  Trades: {stats['total_trades']}")
            print(f"  Win Rate: {stats['win_rate']:.2f}%")
            print(f"  Profit: ${stats['total_profit']:.2f}")
            print(f"{'='*50}")

        time.sleep(60)  # Update every minute

if __name__ == "__main__":
    monitor_loop()
```

**Run Monitor:**
```powershell
python monitor.py
```

---

## 🔒 Security Checklist

### Production Security

- [ ] `.env` file is in `.gitignore` (already done ✅)
- [ ] Database password is strong
- [ ] PostgreSQL is not exposed to public internet
- [ ] MT5 account has 2FA enabled (if available)
- [ ] API keys are not committed to git
- [ ] Windows firewall is enabled
- [ ] Antivirus is up to date

---

## 📊 Post-Deployment Validation

### After 24 Hours

**Check These Metrics:**

```powershell
# Get 24-hour statistics
python -c "
from src.database.repository import TradeRepository
from src.database.connection import get_session
from datetime import datetime, timedelta

repo = TradeRepository()
with get_session() as session:
    yesterday = datetime.now() - timedelta(days=1)
    stats = repo.get_trade_statistics(session, start_date=yesterday)

    print(f'24-Hour Performance:')
    print(f'  Total Trades: {stats[\"total_trades\"]}')
    print(f'  Winning Trades: {stats[\"winning_trades\"]}')
    print(f'  Losing Trades: {stats[\"losing_trades\"]}')
    print(f'  Win Rate: {stats[\"win_rate\"]:.2f}%')
    print(f'  Gross Profit: ${stats[\"gross_profit\"]:.2f}')
    print(f'  Gross Loss: ${stats[\"gross_loss\"]:.2f}')
    print(f'  Net Profit: ${stats[\"total_profit\"]:.2f}')
    print(f'  Profit Factor: {stats[\"profit_factor\"]:.2f}')
"
```

**Expected Results:**
- [ ] System has been running continuously
- [ ] Trades are being executed
- [ ] Database is growing (trades, signals, snapshots)
- [ ] No critical errors in logs
- [ ] Performance metrics are reasonable

---

## 🆘 Troubleshooting

### Issue: MT5 Connection Failed

**Error:** `MT5 initialization failed`

**Solutions:**
1. Check MT5 is running
2. Verify credentials in `.env` are correct
3. Enable "Algo Trading" in MT5 toolbar
4. Enable DLL imports: Tools → Options → Expert Advisors
5. Restart MT5 terminal
6. Run as administrator if needed

---

### Issue: Database Connection Failed

**Error:** `Database initialization failed: could not connect to server`

**Solutions:**

**For PostgreSQL:**
```powershell
# Check PostgreSQL is running
pg_ctl status

# Start PostgreSQL service
net start postgresql-x64-13

# Verify connection string in .env
```

**For SQLite:**
- No server needed
- Check file permissions in project directory
- Try absolute path in connection string

---

### Issue: Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solutions:**
```powershell
# Reinstall package in editable mode
pip install -e .

# Or add to PYTHONPATH
$env:PYTHONPATH = (Get-Location).Path
```

---

### Issue: No Trades Executing

**Possible Causes:**
1. No signals being generated (check config)
2. Insufficient margin/balance
3. Market is closed
4. MT5 "Algo Trading" disabled
5. Configuration issues

**Debug:**
```powershell
# Check signals are being generated
python -c "from src.database.repository import SignalRepository; from src.database.connection import get_session; repo = SignalRepository(); session = get_session().__enter__(); signals = repo.get_recent_signals(session, limit=10); print(f'Recent signals: {len(signals)}'); for s in signals: print(f'{s.symbol} {s.signal_type} {s.timestamp}')"
```

---

## 📝 Daily Operations

### Morning Routine
1. Check logs for any overnight issues
2. Verify system is still running
3. Review overnight trades
4. Check account balance/equity

### Evening Routine
1. Review daily performance
2. Check for any anomalies
3. Backup database (if not automated)
4. Plan for next day

---

## 🔄 Backup Strategy

### Database Backups

**PostgreSQL:**
```powershell
# Manual backup
pg_dump -U tradingmtq_user -d tradingmtq > backups\tradingmtq_backup_$(Get-Date -Format 'yyyyMMdd').sql

# Restore from backup
psql -U tradingmtq_user -d tradingmtq < backups\tradingmtq_backup_20251213.sql
```

**SQLite:**
```powershell
# Manual backup
copy tradingmtq.db backups\tradingmtq_$(Get-Date -Format 'yyyyMMdd').db
```

**Automated Backup Script:**
Create `backup_database.ps1`:
```powershell
# Daily backup script
$date = Get-Date -Format 'yyyyMMdd'
$backupFile = "backups\tradingmtq_backup_$date.sql"

# PostgreSQL backup
pg_dump -U tradingmtq_user -d tradingmtq > $backupFile

# Keep only last 30 days
Get-ChildItem backups\*.sql | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item

Write-Host "Backup completed: $backupFile"
```

**Schedule with Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 3 AM
4. Action: Start Program → PowerShell → `backup_database.ps1`

---

## ✅ Deployment Complete

### Success Criteria

- [x] System deployed on Windows
- [x] MT5 connected successfully
- [x] Database initialized
- [x] Tests passing
- [x] Demo mode tested
- [x] Production mode started
- [x] Monitoring in place
- [x] Backups configured

---

## 🎯 Next Steps: Phase 5.2

Once production is stable (24-48 hours):
- Build analytics dashboard
- Create daily performance reports
- Setup email notifications
- Add web-based monitoring

See: [Phase 5.2 Plan](PHASE_5.2_ANALYTICS_PLAN.md) (to be created)

---

**Deployment Date:** _____________
**Deployed By:** _____________
**Production Start:** _____________
**Status:** _____________

---

**Support:**
- Documentation: [docs/](.)
- Troubleshooting: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Database Guide: [src/database/README.md](../src/database/README.md)

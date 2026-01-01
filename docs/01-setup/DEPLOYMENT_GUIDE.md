# TradingMTQ Deployment Guide - Phase 5.1 Complete

**Last Updated:** December 13, 2025
**Phase:** 5.1 - Database Integration Complete
**Status:** ✅ Ready for Production

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Database Setup](#database-setup)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Monitoring & Analytics](#monitoring--analytics)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware
- **OS**: Windows 10/11 (for MetaTrader 5)
- **RAM**: 8GB minimum, 16GB recommended
- **CPU**: Multi-core processor (4+ cores recommended)
- **Storage**: 20GB+ free space
- **Network**: Stable internet connection

### Software
- **Python**: 3.9 or higher
- **MetaTrader 5**: Latest version
- **PostgreSQL**: 13+ (production) or SQLite (development)
- **Git**: For version control

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/5kipp3rm/TradingMTQ.git
cd TradingMTQ
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Package (Editable Mode)

```bash
pip install -e .
```

This installs the `tradingmtq` and `mtq` CLI commands.

---

## Database Setup

### Option 1: SQLite (Development/Testing)

SQLite requires no additional setup. Database file will be created automatically:

```bash
# Database will be created at: tradingmtq.db
# No configuration needed for development
```

### Option 2: PostgreSQL (Production - Recommended)

#### Install PostgreSQL

**Windows:**
```bash
# Download from: https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

#### Create Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE tradingmtq;

# Create user (optional)
CREATE USER tradingmtq_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE tradingmtq TO tradingmtq_user;

# Exit
\q
```

#### Configure Connection

Create `.env` file in project root:

```bash
# Database Configuration
TRADING_MTQ_DATABASE_URL=postgresql://tradingmtq_user:your_secure_password@localhost:5432/tradingmtq

# MT5 Configuration (optional)
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server

# Optional: OpenAI for LLM features
OPENAI_API_KEY=sk-...
```

#### Initialize Database Schema

```bash
# Using Python API
python -c "from src.database.migration_utils import initialize_database; initialize_database()"

# Or using CLI
python src/database/migration_utils.py init

# Or using Alembic directly
alembic upgrade head
```

---

## Configuration

### 1. Currency Configuration

Edit `config/currencies.yaml`:

```yaml
# Trading Configuration
trading:
  interval_seconds: 30      # Trading cycle interval
  max_concurrent_trades: 15 # Portfolio limit
  portfolio_risk_percent: 10.0

# Currency Pairs
currencies:
  EURUSD:
    enabled: true
    risk_percent: 1.0
    timeframe: M5
    fast_period: 10
    slow_period: 20
    sl_pips: 20
    tp_pips: 40
    max_positions: 3

  GBPUSD:
    enabled: true
    # ... similar configuration
```

### 2. Environment Variables

Create `.env` file (see `.env.example`):

```bash
# MT5 Connection
MT5_LOGIN=12345678
MT5_PASSWORD=YourPassword
MT5_SERVER=YourBroker-Demo

# Database (Production)
TRADING_MTQ_DATABASE_URL=postgresql://user:pass@localhost:5432/tradingmtq

# Optional Features
OPENAI_API_KEY=sk-...  # For LLM sentiment analysis
ENABLE_ML=true         # Enable ML enhancement
ENABLE_LLM=true        # Enable LLM analysis
```

---

## Running the System

### Using CLI Commands

#### 1. Check System

```bash
tradingmtq check
```

Output:
```
System Check

  Python Version: 3.11.0

Dependencies:
  [OK] MetaTrader5
  [OK] numpy
  [OK] pandas
  [OK] pyyaml
  [OK] scikit-learn
  [OK] click
```

#### 2. Start Trading (Default Configuration)

```bash
# Start with default config (ML & LLM enabled)
tradingmtq trade

# Or use the short alias
mtq trade
```

#### 3. Start with Options

```bash
# Aggressive trading
tradingmtq trade --aggressive

# Custom config file
tradingmtq trade -c config/custom.yaml

# Override settings
tradingmtq trade -i 60 -m 20  # 60s interval, 20 max positions

# Disable ML/LLM
tradingmtq trade --disable-ml
tradingmtq trade --disable-llm
tradingmtq trade --disable-ml --disable-llm  # Both disabled

# Demo mode
tradingmtq trade --demo
```

#### 4. Show Version

```bash
tradingmtq version
```

### Using Python Directly

```bash
# Run main.py (legacy mode)
python main.py

# Or run with options
python main.py trade --aggressive
```

---

## What Happens When You Run

### 1. Database Initialization

The system automatically:
- ✅ Connects to database (creates tables if needed)
- ✅ Runs health checks
- ✅ Prepares repositories

### 2. MT5 Connection

- ✅ Connects to MetaTrader 5
- ✅ Validates credentials
- ✅ Retrieves account information
- ✅ Saves initial account snapshot

### 3. Trading Cycle (Every 30-60 seconds)

**For Each Currency Pair:**
1. Fetch market data (OHLC bars)
2. Calculate indicators (Moving Averages)
3. Generate signal (BUY/SELL/HOLD)
4. **→ Save signal to database** (Phase 5.1)
5. ML enhancement (if enabled)
6. LLM sentiment analysis (if enabled)
7. Execute trade if signal confidence is high
8. **→ Save trade to database** (Phase 5.1)

**Portfolio Management:**
1. Check open positions
2. Update stop loss/take profit
3. AI position analysis (if enabled)
4. Close positions if needed
5. **→ Save account snapshot** (Phase 5.1)

### 4. Data Persistence (Phase 5.1 - NEW)

All trading activity is automatically saved:
- ✅ Every signal generated
- ✅ Every trade executed
- ✅ Trade closures with profit/loss
- ✅ Account snapshots every cycle
- ✅ ML/AI metadata preserved

---

## Monitoring & Analytics

### Real-Time Monitoring

The system logs all activity to console and log files:

```
[2025-12-13 14:00:00] INFO - Starting trading cycle #42
[2025-12-13 14:00:01] INFO - EURUSD: Signal BUY (confidence: 0.85)
[2025-12-13 14:00:02] INFO - Trade executed: Ticket=123456
[2025-12-13 14:00:02] DEBUG - Signal saved to database (ID: 1)
[2025-12-13 14:00:02] DEBUG - Trade saved to database (ID: 1)
[2025-12-13 14:00:05] INFO - Portfolio snapshot saved (ID: 42)
```

### Database Queries

#### Get Trade Statistics

```python
from src.database.repository import TradeRepository
from src.database.connection import get_session

repo = TradeRepository()

with get_session() as session:
    stats = repo.get_trade_statistics(session)

    print(f"Total Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    print(f"Total Profit: ${stats['total_profit']:.2f}")
    print(f"Profit Factor: {stats['profit_factor']:.2f}")
```

#### Query Recent Signals

```python
from src.database.repository import SignalRepository
from src.database.connection import get_session

repo = SignalRepository()

with get_session() as session:
    signals = repo.get_recent_signals(session, symbol="EURUSD", limit=10)

    for signal in signals:
        print(f"{signal.timestamp} - {signal.symbol} {signal.signal_type}")
        print(f"  Confidence: {signal.confidence:.2f}")
        print(f"  Executed: {signal.executed}")
```

#### Track Account Balance

```python
from src.database.repository import AccountSnapshotRepository
from src.database.connection import get_session
from datetime import datetime, timedelta

repo = AccountSnapshotRepository()

with get_session() as session:
    # Last 24 hours
    start = datetime.now() - timedelta(days=1)
    snapshots = repo.get_snapshots_by_date_range(
        session,
        account_number=12345,
        start_date=start,
        end_date=datetime.now()
    )

    for snap in snapshots:
        print(f"{snap.snapshot_time}: Balance=${snap.balance:.2f}")
```

### Using SQL Directly

```sql
-- PostgreSQL/SQLite queries

-- Total profit by currency
SELECT symbol, COUNT(*) as trades, SUM(profit) as total_profit
FROM trades
WHERE status = 'CLOSED'
GROUP BY symbol
ORDER BY total_profit DESC;

-- Win rate by strategy
SELECT strategy_name,
       COUNT(*) as total_trades,
       SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
       ROUND(SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate
FROM trades
WHERE status = 'CLOSED'
GROUP BY strategy_name;

-- Account balance over time
SELECT DATE(snapshot_time) as date,
       MAX(balance) as end_balance,
       MAX(equity) as end_equity
FROM account_snapshots
GROUP BY DATE(snapshot_time)
ORDER BY date;
```

---

## Next Steps (Phase 5.2+)

### Recommended Enhancements

1. **Analytics Dashboard**
   - Web-based real-time dashboard
   - Charts for balance, equity, P&L
   - Strategy performance comparison

2. **Automated Reporting**
   - Daily/weekly performance reports
   - Email notifications for milestones
   - Export to CSV/Excel

3. **Advanced Analytics**
   - Backtesting integration with database
   - Machine learning model training from historical data
   - Strategy optimization based on statistics

4. **Multi-Account Support**
   - Track multiple MT5 accounts
   - Portfolio aggregation
   - Cross-account analytics

5. **Backup & Disaster Recovery**
   - Automated PostgreSQL backups
   - Data retention policies
   - Restore procedures

---

## Troubleshooting

### Database Connection Fails

**Error:** `Database initialization failed: could not connect to server`

**Solution:**
```bash
# Check PostgreSQL is running
pg_ctl status

# Start PostgreSQL
pg_ctl start

# Verify connection string in .env
echo $TRADING_MTQ_DATABASE_URL
```

### MT5 Connection Fails

**Error:** `MT5 initialization failed`

**Solution:**
1. Check MetaTrader 5 is running
2. Verify credentials in `.env`
3. Enable "Allow DLL imports" in MT5 settings
4. Ensure "Algo Trading" button is enabled

### Database Migration Issues

**Error:** `Migration failed: table already exists`

**Solution:**
```bash
# Check current migration
alembic current

# Stamp current state
alembic stamp head

# Or recreate database
python -c "from src.database.connection import init_db; init_db('sqlite:///./tradingmtq.db', echo=True)"
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Reinstall package
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

---

## Production Checklist

Before deploying to production:

- [ ] PostgreSQL database configured and tested
- [ ] `.env` file created with production credentials
- [ ] Database backups configured
- [ ] MT5 account verified (demo or live)
- [ ] Configuration tuned for risk tolerance
- [ ] Monitoring/alerts configured
- [ ] Log rotation configured
- [ ] Disk space monitoring enabled
- [ ] System tested in demo mode
- [ ] Emergency stop procedure documented

---

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/5kipp3rm/TradingMTQ/issues
- **Documentation**: [docs/](../docs/)
- **Database Guide**: [src/database/README.md](../src/database/README.md)

---

**Last Updated:** December 13, 2025
**Version:** 2.0.0 (Phase 5.1 Complete)
**Status:** ✅ Production Ready with Database Integration

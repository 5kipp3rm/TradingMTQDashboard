# TradingMTQ - Complete Setup from Scratch

This guide will walk you through setting up the entire TradingMTQ platform from a fresh clone, including database setup, configuration, dependencies, and running the system.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone Repository](#clone-repository)
3. [Python Environment Setup](#python-environment-setup)
4. [Install Dependencies](#install-dependencies)
5. [Database Setup](#database-setup)
6. [Configuration](#configuration)
7. [Initialize Database](#initialize-database)
8. [Run the System](#run-the-system)
9. [Verify Installation](#verify-installation)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.9+** (Python 3.10 or 3.11 recommended)
- **Git** (for cloning the repository)
- **SQLite** (comes with Python) or **PostgreSQL** (optional, for production)

### Optional but Recommended

- **MetaTrader 5** (Windows only, for live trading)
- **Visual Studio Code** or your preferred IDE

### System Requirements

- **OS**: Windows 10/11 (for MT5 trading), macOS/Linux (for development/testing)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 500MB for application + data

---

## 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/5kipp3rm/TradingMTQ.git
cd TradingMTQ

# Checkout the main development branch
git checkout initial-claude-refactor

# Verify you're on the correct branch
git branch
```

---

## 2. Python Environment Setup

### Option A: Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.9+
```

### Option B: Using conda

```bash
# Create conda environment
conda create -n tradingmtq python=3.10

# Activate environment
conda activate tradingmtq
```

---

## 3. Install Dependencies

### Install Core Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
# Check installed packages
pip list | grep -E "(sqlalchemy|fastapi|reportlab|apscheduler)"
```

Expected output:
```
apscheduler       3.10.4
fastapi           0.104.1
reportlab         4.0.7
sqlalchemy        2.0.23
```

---

## 4. Database Setup

### SQLite (Default - For Development)

SQLite database will be created automatically. No additional setup needed.

**Database location**: `./trading.db` (created on first run)

### PostgreSQL (Optional - For Production)

#### macOS

```bash
# Install PostgreSQL
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create database
createdb tradingmtq
```

#### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql

# Create database
sudo -u postgres createdb tradingmtq

# Create user (optional)
sudo -u postgres createuser -P tradingmtq
```

#### Windows

```powershell
# Download and install PostgreSQL from:
# https://www.postgresql.org/download/windows/

# Or using Chocolatey:
choco install postgresql

# PostgreSQL service starts automatically after installation

# Create database using pgAdmin (GUI):
# 1. Open pgAdmin
# 2. Connect to PostgreSQL server
# 3. Right-click "Databases" → Create → Database
# 4. Name: tradingmtq

# Or using Command Prompt/PowerShell:
# Add PostgreSQL to PATH (usually: C:\Program Files\PostgreSQL\15\bin)
# Then run:
createdb -U postgres tradingmtq

# Or using psql:
psql -U postgres
CREATE DATABASE tradingmtq;
\q
```

**Update connection string** in config.yaml (see Configuration section below)

---

## 5. Configuration

### Create Configuration File

```bash
# Copy example config (if available)
cp config.example.yaml config.yaml

# Or create new config.yaml
touch config.yaml
```

### Edit `config.yaml`

```yaml
# Database Configuration
database:
  # For SQLite (default)
  url: "sqlite:///./trading.db"

  # For PostgreSQL (production)
  # url: "postgresql://username:password@localhost/tradingmtq"

# API Server Configuration
api:
  host: "0.0.0.0"
  port: 8000
  debug: true
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:5173"
    - "http://127.0.0.1:3000"
    - "http://127.0.0.1:5173"

# Report Configuration (optional)
reports:
  output_dir: "./reports"

# Email Configuration (optional - for report delivery)
email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "your_email@gmail.com"
  smtp_password: "your_app_password"
  from_email: "your_email@gmail.com"
  from_name: "TradingMTQ Reports"
  use_tls: true

# Logging Configuration
logging:
  level: "INFO"
  file: "logs/tradingmtq.log"
```

### Environment Variables (Alternative to config.yaml)

Create `.env` file in project root:

```bash
# .env file
DATABASE_URL=sqlite:///./trading.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Email Configuration (for reports)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=TradingMTQ Reports
SMTP_USE_TLS=true
```

### Gmail Setup (For Email Reports)

1. Enable 2-Factor Authentication on your Gmail account
2. Generate App Password:
   - Go to: https://myaccount.google.com/security
   - Select "2-Step Verification"
   - Scroll to bottom, select "App passwords"
   - Generate password for "Mail"
3. Use the generated password in `SMTP_PASSWORD`

---

## 6. Initialize Database

### Check CLI is Installed

```bash
# Verify tradingmtq CLI is available
tradingmtq --help

# If not available, install in development mode
pip install -e .
```

### Initialize Database Tables

```bash
# Initialize database and create all tables
tradingmtq aggregate --initialize

# Or use Python directly
python -c "from src.database import init_db; init_db()"
```

**This creates:**
- `trades` table
- `signals` table
- `account_snapshots` table
- `daily_performance` table
- `trading_accounts` table
- `alert_configurations` table
- `alert_history` table
- `report_configurations` table
- `report_history` table

### Verify Database Creation

```bash
# Check if database file exists
ls -lh trading.db

# Check tables (using Python)
python -c "
from src.database import get_session
from src.database.models import Base
from sqlalchemy import inspect

with get_session() as session:
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    print(f'Tables created: {len(tables)}')
    for table in sorted(tables):
        print(f'  - {table}')
"
```

Expected output:
```
Tables created: 9
  - account_snapshots
  - alert_configurations
  - alert_history
  - daily_performance
  - report_configurations
  - report_history
  - signals
  - trades
  - trading_accounts
```

---

## 7. Run the System

### Option 1: Run API Server (Web Dashboard + API)

```bash
# Start the FastAPI server
tradingmtq serve

# Or specify host/port
tradingmtq serve --host 0.0.0.0 --port 8000

# Or use uvicorn directly
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

**Server starts at:**
- Dashboard: http://localhost:8000/
- API Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Option 2: Run CLI Data Aggregation

```bash
# Aggregate data from MetaTrader 5 (Windows only)
tradingmtq aggregate

# Aggregate for specific date range
tradingmtq aggregate --start-date 2025-01-01 --end-date 2025-01-31

# Force re-aggregation
tradingmtq aggregate --force
```

### Option 3: Run Both (Recommended)

**Terminal 1 - API Server:**
```bash
tradingmtq serve
```

**Terminal 2 - Data Aggregation:**
```bash
# Run once to populate data
tradingmtq aggregate

# Or run continuously (every hour)
while true; do
  tradingmtq aggregate
  sleep 3600
done
```

---

## 8. Verify Installation

### Test 1: Check API Health

```bash
# Check health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","version":"2.5.0"}
```

### Test 2: Access Dashboard

Open browser to: http://localhost:8000/

**You should see:**
- ✅ Summary cards (Total Trades, Net Profit, Win Rate, Avg Daily Profit)
- ✅ Charts (Cumulative Profit, Daily Performance)
- ✅ Navigation links (Charts, Alerts, Reports)

### Test 3: Check API Documentation

Open browser to: http://localhost:8000/api/docs

**You should see Swagger UI with endpoints:**
- `/api/health` - Health check
- `/api/analytics/*` - Analytics endpoints
- `/api/trades/*` - Trade endpoints
- `/api/alerts/*` - Alert endpoints
- `/api/charts/*` - Chart endpoints
- `/api/accounts` - Account endpoints
- `/api/reports/*` - Report endpoints

### Test 4: Create Test Trading Account

```bash
# Using Python
python -c "
from src.database import get_session, TradingAccount
from decimal import Decimal

with get_session() as session:
    account = TradingAccount(
        account_number=12345,
        account_name='Demo Account',
        broker='Demo Broker',
        server='DemoServer-01',
        login=12345,
        is_demo=True,
        is_active=True,
        is_default=True,
        initial_balance=Decimal('10000.00'),
        currency='USD'
    )
    session.add(account)
    session.commit()
    print(f'Created account: {account.account_name} (ID: {account.id})')
"
```

### Test 5: Generate Test Report

```bash
# Using API
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "include_trades": true,
    "include_charts": false
  }'
```

### Test 6: Run Unit Tests

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_report_generator.py -v
pytest tests/test_email_service.py -v
pytest tests/test_reports_api.py -v
pytest tests/test_reports_integration.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

---

## 9. Initial Data Setup (Optional)

### Add Sample Trading Account

```bash
python -c "
from src.database import get_session, TradingAccount
from decimal import Decimal

with get_session() as session:
    # Create demo account
    demo = TradingAccount(
        account_number=99999,
        account_name='Demo Trading Account',
        broker='Demo Broker',
        server='DemoServer-Live',
        login=99999,
        is_demo=True,
        is_active=True,
        is_default=True,
        initial_balance=Decimal('10000.00'),
        currency='USD'
    )
    session.add(demo)
    session.commit()
    print('✅ Demo account created')
"
```

### Add Sample Performance Data

```bash
python -c "
from src.database import get_session, DailyPerformance, TradingAccount
from decimal import Decimal
from datetime import date, timedelta

with get_session() as session:
    # Get first account
    account = session.query(TradingAccount).first()
    if not account:
        print('❌ No accounts found. Create account first.')
        exit(1)

    # Add 30 days of sample data
    base_date = date.today() - timedelta(days=30)
    for i in range(30):
        perf = DailyPerformance(
            date=base_date + timedelta(days=i),
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            net_profit=Decimal('100.00') if i % 2 == 0 else Decimal('-50.00'),
            gross_profit=Decimal('200.00'),
            gross_loss=Decimal('-100.00'),
            win_rate=Decimal('60.00'),
            average_win=Decimal('33.33'),
            average_loss=Decimal('-25.00'),
            largest_win=Decimal('100.00'),
            largest_loss=Decimal('-50.00'),
            start_balance=Decimal(f'{10000 + i * 50}.00'),
            end_balance=Decimal(f'{10000 + (i + 1) * 50}.00'),
            start_equity=Decimal(f'{10000 + i * 50}.00'),
            end_equity=Decimal(f'{10000 + (i + 1) * 50}.00'),
            account_id=account.id
        )
        session.add(perf)

    session.commit()
    print(f'✅ Added 30 days of sample performance data for {account.account_name}')
"
```

### Create Sample Alert Configuration

```bash
python -c "
from src.database import get_session, AlertConfiguration, AlertType, NotificationChannel

with get_session() as session:
    alert = AlertConfiguration(
        name='Daily Profit Alert',
        alert_type=AlertType.DAILY_PROFIT_THRESHOLD,
        is_active=True,
        threshold_value=100.0,
        notification_channels=[NotificationChannel.EMAIL],
        email_recipients='your_email@example.com'
    )
    session.add(alert)
    session.commit()
    print('✅ Sample alert configuration created')
"
```

---

## 10. Troubleshooting

### Issue: "No module named 'src'"

**Solution:**
```bash
# Install package in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "tradingmtq: command not found"

**Solution:**
```bash
# Reinstall package
pip install -e .

# Or use python -m
python -m src.cli --help
```

### Issue: Database locked (SQLite)

**Solution:**
```bash
# Close all connections
pkill -f tradingmtq

# Remove database lock
rm trading.db-journal

# Restart application
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
tradingmtq serve --port 8001
```

### Issue: Import errors for reportlab/apscheduler

**Solution:**
```bash
# Reinstall dependencies
pip install reportlab pillow apscheduler --upgrade

# Or reinstall all
pip install -r requirements.txt --force-reinstall
```

### Issue: Email not sending

**Solutions:**
1. Verify Gmail app password (not regular password)
2. Check firewall allows port 587
3. Test connection:
```python
from src.reports.email_service import EmailService, EmailConfiguration

config = EmailConfiguration(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your_email@gmail.com",
    smtp_password="your_app_password",
    from_email="your_email@gmail.com",
    use_tls=True
)
service = EmailService(config)
success = service.test_connection()
print(f"Connection: {'✅ Success' if success else '❌ Failed'}")
```

### Issue: MetaTrader 5 not connecting (Windows only)

**Solution:**
```bash
# Check MT5 is installed
python -c "import MetaTrader5 as mt5; print(f'MT5 Version: {mt5.__version__}')"

# Check MT5 terminal is running
tasklist | findstr terminal64.exe

# Verify login credentials
tradingmtq check
```

### Issue: Dashboard shows no data

**Solutions:**
1. Check database has data:
```bash
python -c "
from src.database import get_session, DailyPerformance
with get_session() as session:
    count = session.query(DailyPerformance).count()
    print(f'Performance records: {count}')
"
```

2. Run aggregation to populate data:
```bash
tradingmtq aggregate
```

3. Add sample data (see Initial Data Setup section)

### Issue: Tests failing

**Solution:**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run tests with verbose output
pytest -v

# Run specific failing test
pytest tests/test_report_generator.py::TestReportGeneratorInitialization::test_init_with_default_directory -v
```

---

## Quick Start Checklist

Use this checklist for a fresh setup:

- [ ] Clone repository
- [ ] Create virtual environment
- [ ] Activate virtual environment
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Create config.yaml or .env file
- [ ] Initialize database (`tradingmtq aggregate --initialize`)
- [ ] Create test trading account
- [ ] Add sample performance data (optional)
- [ ] Start API server (`tradingmtq serve`)
- [ ] Open dashboard (http://localhost:8000)
- [ ] Verify API docs (http://localhost:8000/api/docs)
- [ ] Run tests (`pytest`)

---

## Next Steps

After successful setup:

1. **Configure Email** (for report delivery)
   - See [Email Configuration](#gmail-setup-for-email-reports)
   - Test connection with `test_connection()`

2. **Create Report Schedules**
   - Navigate to http://localhost:8000/reports.html
   - Click "New Report" and configure schedule

3. **Connect MetaTrader 5** (Windows only)
   - Install MT5
   - Configure connection in config.yaml
   - Run `tradingmtq aggregate` to import trades

4. **Set Up Alerts**
   - Navigate to http://localhost:8000/alerts.html
   - Create alert configurations

5. **Explore API**
   - Read API documentation at http://localhost:8000/api/docs
   - Try example API calls

6. **Review Documentation**
   - [Reports System](./REPORTS.md)
   - [API Reference](http://localhost:8000/api/docs)
   - Main README.md

---

## Production Deployment

For production deployment:

1. **Use PostgreSQL** instead of SQLite
2. **Set DEBUG=false** in configuration
3. **Use proper CORS origins** (your domain)
4. **Set up HTTPS** with reverse proxy (nginx/Apache)
5. **Use systemd/supervisor** for process management
6. **Set up log rotation** for application logs
7. **Configure firewall** rules
8. **Use environment variables** for secrets (not config files)
9. **Set up backups** for database and reports
10. **Monitor system** with logging and alerting

### Example systemd Service

Create `/etc/systemd/system/tradingmtq.service`:

```ini
[Unit]
Description=TradingMTQ API Server
After=network.target

[Service]
Type=simple
User=tradingmtq
WorkingDirectory=/opt/tradingmtq
Environment="PATH=/opt/tradingmtq/venv/bin"
ExecStart=/opt/tradingmtq/venv/bin/tradingmtq serve --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tradingmtq
sudo systemctl start tradingmtq
sudo systemctl status tradingmtq
```

---

## Support

If you encounter issues:

1. Check logs: `logs/tradingmtq.log`
2. Review this troubleshooting section
3. Check GitHub Issues: https://github.com/5kipp3rm/TradingMTQ/issues
4. Run diagnostic: `tradingmtq check`

---

## License

This project is licensed under the MIT License - see LICENSE file for details.

# macOS/Linux Quick Start Guide

**Purpose:** Development and testing of the database layer
**Note:** MetaTrader5 is Windows-only. For production trading, use Windows deployment.

---

## 🚀 One-Command Setup

### Quick Setup

```bash
# Navigate to project directory
cd /path/to/TradingMTQ

# Run setup script
bash deploy/macos/setup.sh

# Or with options:
bash deploy/macos/setup.sh --skip-tests
bash deploy/macos/setup.sh --use-postgresql
```

**That's it!** The script will:
- Check Python version (3.9+ required)
- Create virtual environment
- Install all dependencies
- Initialize SQLite database
- Run unit tests
- Verify installation

---

## ⚙️ What You Can Do on macOS/Linux

### ✅ Available Features

1. **Test Database Layer**
   - All database models work
   - All repository methods work
   - SQLite or PostgreSQL

2. **Run Unit Tests**
   - 106 tests available
   - 25 database-specific tests
   - Fast execution (< 2 seconds)

3. **Develop & Test Code**
   - Write new features
   - Test database queries
   - Develop analytics (Phase 5.2)

### ❌ Not Available

- MetaTrader5 integration (Windows-only)
- Live trading
- MT5-dependent tests

---

## 🧪 Running Tests

### Database Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run database tests
pytest tests/test_models.py tests/test_repositories.py -v

# Expected: 25/25 passing
```

### All Available Tests

```bash
# Run all non-MT5 tests
pytest tests/test_models.py \
       tests/test_repositories.py \
       tests/test_config.py \
       tests/test_logger.py \
       tests/test_config_manager.py \
       tests/test_utils_config.py -v

# Expected: 106/106 passing
```

### With Coverage

```bash
# Generate coverage report
pytest tests/test_models.py tests/test_repositories.py \
       --cov=src.database --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

---

## 💾 Database Testing

### Initialize Database

```bash
# Already done by setup script, but you can reinit:
python src/database/migration_utils.py init
```

### Test Database Operations

```bash
# Check database health
python -c "from src.database.connection import check_database_health; print('DB Health:', check_database_health())"

# Create test trade
python -c "
from src.database.repository import TradeRepository
from src.database.connection import get_session
from datetime import datetime
from decimal import Decimal

repo = TradeRepository()
with get_session() as session:
    trade = repo.create(
        session,
        ticket=999999,
        symbol='EURUSD',
        trade_type='BUY',
        status='OPEN',
        entry_price=Decimal('1.0850'),
        entry_time=datetime.now(),
        volume=Decimal('0.1')
    )
    print(f'Created trade: {trade.id}')
"

# Query trades
python -c "
from src.database.repository import TradeRepository
from src.database.connection import get_session

repo = TradeRepository()
with get_session() as session:
    trades = repo.get_all_trades(session)
    print(f'Total trades in DB: {len(trades)}')
    for trade in trades[:5]:  # Show first 5
        print(f'  {trade.ticket}: {trade.symbol} {trade.trade_type}')
"
```

---

## 🛠️ Development Workflow

### 1. Make Code Changes

```bash
# Edit any file
nano src/database/models.py

# Or use your favorite editor
code .
```

### 2. Run Tests

```bash
# Test your changes
pytest tests/test_models.py -v

# Or run specific test
pytest tests/test_models.py::TestTradeModel::test_trade_creation -v
```

### 3. Check Coverage

```bash
pytest tests/ --cov=src.database --cov-report=term
```

---

## 🐘 PostgreSQL Setup (Optional)

If you want to test with PostgreSQL instead of SQLite:

### Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Create Database

```bash
# Create database
createdb tradingmtq

# Or with specific user
psql postgres
# Then in psql:
CREATE DATABASE tradingmtq;
CREATE USER tradingmtq_user WITH ENCRYPTED PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE tradingmtq TO tradingmtq_user;
\q
```

### Update .env

```bash
# Edit .env
nano .env

# Change to:
TRADING_MTQ_DATABASE_URL=postgresql://tradingmtq_user:dev_password@localhost:5432/tradingmtq
```

### Reinitialize

```bash
python src/database/migration_utils.py init
```

---

## 📊 CLI Commands (Limited Functionality)

Some CLI commands work without MT5:

```bash
# Activate environment
source venv/bin/activate

# Show version
tradingmtq version

# System check (will show MT5 not available)
tradingmtq check

# Run aggregation (if you have data)
tradingmtq aggregate --backfill
```

**Note:** `tradingmtq trade` will fail because MT5 is not available.

---

## 🔄 Transfer to Windows for Production

When ready to deploy:

### 1. Prepare Project

```bash
# Ensure everything is committed
git status
git add -A
git commit -m "Ready for Windows deployment"
git push origin initial-claude-refactor
```

### 2. Transfer Options

**Option A: Git Clone on Windows**
```powershell
# On Windows machine
git clone https://github.com/5kipp3rm/TradingMTQ.git
cd TradingMTQ
git checkout initial-claude-refactor
```

**Option B: ZIP Archive**
```bash
# On macOS
cd ..
zip -r TradingMTQ.zip TradingMTQ -x "*.git*" "*venv*" "*__pycache__*"

# Transfer ZIP to Windows
# Unzip on Windows
```

### 3. Run Windows Setup

On Windows machine:
```powershell
cd TradingMTQ
.\deploy\windows\quick-start.bat
```

See: [deploy/windows/WINDOWS_QUICK_START.md](../windows/WINDOWS_QUICK_START.md)

---

## 🧹 Cleanup

```bash
# Remove virtual environment
rm -rf venv

# Remove database
rm tradingmtq.db

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Start fresh
bash deploy/macos/setup.sh
```

---

## 📚 Development Tasks You Can Do

### 1. Database Development

- Add new models
- Create new repository methods
- Write database migrations
- Test query performance

### 2. Analytics Development (Phase 5.2)

- Build daily aggregation
- Create REST API
- Develop reporting engine
- Test export functionality

### 3. Testing

- Write more unit tests
- Add integration tests
- Improve coverage
- Performance testing

### 4. Documentation

- Update guides
- Add code examples
- Write tutorials

---

## 🆘 Troubleshooting

### Python Version Issues

```bash
# Check Python version
python3 --version

# If too old, install newer version:
# macOS
brew install python@3.11

# Linux (Ubuntu/Debian)
sudo apt-get install python3.11
```

### Permission Denied on setup.sh

```bash
# Make script executable
chmod +x deploy/macos/setup.sh

# Run again
bash deploy/macos/setup.sh
```

### Virtual Environment Issues

```bash
# Remove and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Database Connection Issues

**SQLite:**
- No server needed
- File created automatically
- Check write permissions in project directory

**PostgreSQL:**
```bash
# Check if running
brew services list | grep postgresql
# or
sudo systemctl status postgresql

# Start if needed
brew services start postgresql@15
# or
sudo systemctl start postgresql
```

---

## ✅ Development Checklist

- [ ] Repository cloned
- [ ] Python 3.9+ installed
- [ ] Setup script run successfully
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database initialized
- [ ] Tests passing
- [ ] CLI commands working
- [ ] Can query database
- [ ] Ready for development

---

## 🎯 Next Steps

### For Development

1. **Run tests** to ensure everything works
2. **Explore the codebase** - understand the structure
3. **Try database operations** - create, query, update
4. **Start Phase 5.2** - build analytics dashboard

### For Production Deployment

1. **Commit your changes** to git
2. **Transfer to Windows machine**
3. **Install MetaTrader 5**
4. **Run Windows setup**
5. **Configure and test**
6. **Start trading**

---

## 📖 Resources

- **Windows Guide:** [../windows/WINDOWS_QUICK_START.md](../windows/WINDOWS_QUICK_START.md)
- **Full Deployment:** [../../docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md](../../docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md)
- **Database Guide:** [../../src/database/README.md](../../src/database/README.md)
- **Current Status:** [../../docs/CURRENT_STATUS.md](../../docs/CURRENT_STATUS.md)

---

## 💡 Tips

- Use SQLite for quick testing
- PostgreSQL for production-like testing
- Write tests before deploying to Windows
- Test database queries thoroughly
- Keep git history clean for Windows transfer

---

**Estimated setup time:** 5-10 minutes
**Test execution time:** < 2 seconds for database tests

Happy developing! 🚀

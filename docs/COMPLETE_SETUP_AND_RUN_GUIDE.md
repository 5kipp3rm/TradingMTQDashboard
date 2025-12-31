# TradingMTQ - Complete Setup, Run, and Deployment Guide

**Complete guide covering:**
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Dashboard Setup & Usage](#dashboard-setup--usage)
- [Development Workflow](#development-workflow)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation & Setup](#installation--setup)
3. [Running the Backend (Trading Bot)](#running-the-backend-trading-bot)
4. [Running the Dashboard (Frontend)](#running-the-dashboard-frontend)
5. [Configuration](#configuration)
6. [Development Workflow](#development-workflow)
7. [Deployment Options](#deployment-options)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Topics](#advanced-topics)

---

## System Requirements

### Backend Requirements

- **Operating System**: Windows (for MetaTrader 5 API), macOS, or Linux (for development/testing without MT5)
- **Python**: 3.10 or higher
- **MetaTrader 5**: Terminal installed and configured
- **Memory**: Minimum 4GB RAM (8GB recommended for ML features)
- **Disk Space**: Minimum 2GB free space

### Dashboard Requirements

- **Node.js**: 18.x or higher
- **npm**: 8.x or higher (or yarn/pnpm/bun)
- **Browser**: Modern browser (Chrome, Firefox, Safari, Edge)
- **Memory**: Minimum 2GB RAM

### Development Tools (Optional)

- **Git**: For version control
- **VS Code**: Recommended IDE
- **Docker**: For containerized deployment (optional)

---

## Installation & Setup

### Step 1: Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/5kipp3rm/TradingMTQ.git
cd TradingMTQ

# Initialize the dashboard submodule
git submodule init
git submodule update
```

**Alternative** (if dashboard is already checked out):
```bash
git clone --recurse-submodules https://github.com/5kipp3rm/TradingMTQ.git
cd TradingMTQ
```

### Step 2: Backend Setup (Python)

#### 2.1 Create Virtual Environment

**On Windows:**
```bash
# Using venv (built-in)
python -m venv venv
venv\Scripts\activate

# Or using virtualenv
pip install virtualenv
virtualenv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
# Using venv
python3 -m venv venv
source venv/bin/activate

# Or using virtualenv
pip install virtualenv
virtualenv venv
source venv/bin/activate
```

#### 2.2 Install Python Dependencies

```bash
# Install all dependencies (includes ML and LLM packages)
pip install -r requirements.txt

# Or install in stages:
# Core dependencies only
pip install MetaTrader5 pandas numpy python-dotenv pyyaml

# Add ML capabilities
pip install scikit-learn tensorflow matplotlib seaborn optuna

# Add LLM capabilities
pip install openai anthropic beautifulsoup4

# Add web API (Phase 5)
pip install fastapi uvicorn websockets sqlalchemy alembic
```

#### 2.3 Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your favorite editor
```

**.env file contents:**
```env
# MetaTrader 5 Credentials
MT5_LOGIN=12345678
MT5_PASSWORD=YourPassword
MT5_SERVER=YourBroker-Server

# API Keys (Optional - for LLM features)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database (Optional - for Phase 5+)
DATABASE_URL=sqlite:///./trading_bot.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost/tradingmtq

# API Configuration (Optional - for web dashboard backend)
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot.log
```

#### 2.4 Configure Trading Settings

Edit [config/currencies.yaml](../config/currencies.yaml) to customize your trading pairs:

```yaml
# config/currencies.yaml
currencies:
  EURUSD:
    enabled: true
    timeframe: M5
    lot_size: 0.01
    max_spread: 3
    strategy: multi_indicator

  GBPUSD:
    enabled: true
    timeframe: M15
    lot_size: 0.01
    max_spread: 4
    strategy: rsi_strategy

  # Add more pairs...
```

#### 2.5 Verify Installation

```bash
# Test Python environment
python --version

# Test MT5 connection (safe - no trading)
python examples/test_connection.py

# Run pre-flight checks
python check_readiness.py
```

### Step 3: Dashboard Setup (Frontend)

#### 3.1 Navigate to Dashboard Directory

```bash
cd dashboard
```

#### 3.2 Install Node.js Dependencies

**Using npm (default):**
```bash
npm install
```

**Using yarn:**
```bash
yarn install
```

**Using pnpm:**
```bash
pnpm install
```

**Using bun (fastest):**
```bash
bun install
```

#### 3.3 Configure Dashboard Environment

Create a `.env` file in the `dashboard/` directory:

```bash
# dashboard/.env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

#### 3.4 Verify Dashboard Setup

```bash
# Test build (should complete without errors)
npm run build

# Or test development server
npm run dev
```

### Step 4: Database Setup (Optional - for Phase 5+)

#### 4.1 Initialize SQLite Database (Default)

```bash
# The database will be created automatically on first run
python -c "from src.database.base import init_db; init_db()"
```

#### 4.2 Initialize PostgreSQL (Production)

```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
createdb tradingmtq

# Update .env with PostgreSQL connection
# DATABASE_URL=postgresql://username:password@localhost/tradingmtq

# Run migrations
alembic upgrade head
```

### Step 5: MetaTrader 5 Setup

#### 5.1 Install MetaTrader 5

1. Download from [MetaTrader 5 website](https://www.metatrader5.com/)
2. Install and launch the terminal
3. Create a demo account from a broker (e.g., MetaQuotes, IC Markets)

#### 5.2 Enable Algo Trading

1. In MT5 Terminal: **Tools → Options → Expert Advisors**
2. Enable:
   - ✅ Allow algorithmic trading
   - ✅ Allow DLL imports
   - ✅ Allow WebRequest for listed URLs

#### 5.3 Verify Connection

```bash
# Make sure MT5 is running and logged in
python examples/test_connection.py
```

**Expected output:**
```
=== MetaTrader 5 Connection Test ===

✓ MT5 package imported successfully
✓ MT5 terminal initialized
✓ Connected to account 12345678

Account Information:
  Balance: $10,000.00
  Equity: $10,000.00
  Margin: $0.00
  Free Margin: $10,000.00
  Profit: $0.00

Connection test passed!
```

---

## Running the Application

### Option 1: Run Everything Together (Recommended for Development)

#### Terminal 1: Start Backend API

```bash
# From project root
cd /path/to/TradingMTQ

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start FastAPI backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Terminal 2: Start Trading Bot

```bash
# From project root
cd /path/to/TradingMTQ

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the trading bot
python main.py

# Or use the CLI
tradingmtq trade --pairs EURUSD,GBPUSD --mode live
```

#### Terminal 3: Start Dashboard

```bash
# From project root
cd /path/to/TradingMTQ/dashboard

# Start development server
npm run dev
```

**Expected output:**
```
VITE v5.4.19  ready in 823 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.1.100:5173/
  ➜  press h + enter to show help
```

#### Access the Application

- **Dashboard**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

### Option 2: Run Backend Only (Headless Trading)

```bash
# Activate virtual environment
source venv/bin/activate

# Run the main trading bot
python main.py
```

**What this does:**
- ✅ Connects to MetaTrader 5
- ✅ Loads configuration from `config/currencies.yaml`
- ✅ Starts trading all enabled currency pairs
- ✅ Applies automatic SL/TP management
- ✅ Hot-reloads configuration changes every 60 seconds
- ✅ Logs all activity to console and `logs/trading_bot.log`

### Option 3: Run with CLI Commands

```bash
# Install package in development mode
pip install -e .

# Use CLI commands
tradingmtq --help

# Trade with specific pairs
tradingmtq trade --pairs EURUSD,GBPUSD --mode live

# Check account status
tradingmtq status

# Check open positions
tradingmtq positions

# Close all positions (emergency)
tradingmtq close-all
```

### Option 4: Run Dashboard Only (Demo Mode)

```bash
cd dashboard
npm run dev
```

The dashboard will work in demo mode with mock data if the backend API is not running.

---

## Running the Backend (Trading Bot)

### Main Entry Points

#### 1. **main.py** - Simplest Way (Recommended)

```bash
python main.py
```

**Features:**
- Auto-loads configuration from `config/currencies.yaml`
- Trades all enabled currency pairs automatically
- Hot-reloads config changes every 60 seconds
- Automatic SL/TP management
- No manual intervention required

#### 2. **run.py** - Interactive Menu

```bash
python run.py
```

**Features:**
- Interactive menu interface
- Pre-flight checks before trading
- Select specific pairs to trade
- Choose strategy per pair
- Safer for beginners

#### 3. **CLI Commands** - Production Usage

```bash
# Install package
pip install -e .

# Run trading with CLI
tradingmtq trade --mode live
tradingmtq trade --pairs EURUSD,GBPUSD --dry-run
tradingmtq status
tradingmtq positions
tradingmtq close-all
```

### Testing Scripts (Safe - No Trading)

#### Test Connection
```bash
python examples/test_connection.py
```
Tests MT5 connection and displays account info.

#### Check Positions
```bash
python scripts/check_positions.py
```
Shows all open positions without modifying them.

#### Modify Positions (Interactive)
```bash
python examples/modify_positions.py
```
Interactive tool to modify SL/TP on existing positions.

#### Check Trading Signals
```bash
python scripts/check_signal.py
```
Analyzes current market and shows trading signals without executing trades.

### Live Trading Scripts

#### Single Currency Trading
```bash
python examples/live_trading.py
```

#### Multi-Currency Trading (OOP)
```bash
python examples/demo_multi_currency_oop.py
```

#### Fast Trading (Aggressive Mode)
```bash
python examples/fast_trading.py
```

### Machine Learning Examples

#### Phase 3: ML Demo (LSTM + Random Forest)
```bash
python examples/phase3_ml_demo.py
```

#### Phase 4: LLM Demo (GPT-4 + Claude)
```bash
python examples/phase4_llm_demo.py
```

### Utility Scripts

#### Close All Positions (Emergency)
```bash
python scripts/close_all_positions.py
```

#### Check Autotrading Status
```bash
python scripts/check_autotrading.py
```

#### Data Collection for ML
```bash
python scripts/collect_data.py
```

#### Train ML Models
```bash
python scripts/train_models.py
```

---

## Running the Dashboard (Frontend)

### Development Mode

```bash
cd dashboard
npm run dev
```

**Features:**
- Hot-reload on file changes
- Source maps for debugging
- Fast refresh
- Development build

**Access:** http://localhost:5173

### Production Build

```bash
cd dashboard
npm run build
```

**Output:** `dashboard/dist/` directory with optimized static files

### Preview Production Build

```bash
cd dashboard
npm run build
npm run preview
```

**Access:** http://localhost:4173

### Build for Deployment

```bash
cd dashboard

# Production build
npm run build

# Build with development mode (keeps debugging)
npm run build:dev
```

---

## Configuration

### Backend Configuration Files

#### 1. `.env` - Credentials & Secrets

```env
# MetaTrader 5
MT5_LOGIN=12345678
MT5_PASSWORD=YourPassword
MT5_SERVER=YourBroker-Server

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=sqlite:///./trading_bot.db

# API
API_HOST=0.0.0.0
API_PORT=8000
```

#### 2. `config/currencies.yaml` - Trading Settings

```yaml
currencies:
  EURUSD:
    enabled: true
    timeframe: M5              # M1, M5, M15, M30, H1, H4, D1
    lot_size: 0.01             # Lot size per trade
    max_spread: 3              # Maximum spread in points
    strategy: multi_indicator   # Strategy to use
    risk_percent: 1.0          # Risk per trade as % of account

    # Stop Loss & Take Profit
    sl_pips: 20
    tp_pips: 40

    # Automatic SL/TP Management
    breakeven:
      enabled: true
      trigger_pips: 15         # Move SL to breakeven after 15 pips profit

    trailing_stop:
      enabled: true
      activation_pips: 20      # Start trailing after 20 pips profit
      distance_pips: 10        # Trail 10 pips behind current price

    partial_profits:
      enabled: true
      levels:
        - target_pips: 20      # Close 50% at 20 pips profit
          close_percent: 50
        - target_pips: 40      # Close 30% at 40 pips profit
          close_percent: 30

    # ML/AI Settings (Optional)
    use_ml: true               # Use machine learning signals
    use_llm: false             # Use LLM analysis (costs money)

  GBPUSD:
    enabled: true
    timeframe: M15
    lot_size: 0.01
    # ... (similar structure)
```

#### 3. `config/api_keys.yaml` - LLM API Keys (Alternative to .env)

```yaml
openai:
  api_key: "sk-..."
  model: "gpt-4o"
  temperature: 0.7

anthropic:
  api_key: "sk-ant-..."
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 1024
```

### Dashboard Configuration

#### `dashboard/.env` - Frontend Environment

```env
# API Backend URL
VITE_API_URL=http://localhost:8000

# WebSocket URL
VITE_WS_URL=ws://localhost:8000/ws

# Optional: Enable debug mode
VITE_DEBUG=true
```

### Hot-Reload Configuration

The trading bot automatically reloads `config/currencies.yaml` every 60 seconds. You can modify trading settings while the bot is running:

```bash
# Edit configuration
nano config/currencies.yaml

# The bot will detect changes and apply them within 60 seconds
# Check logs for: "Configuration reloaded successfully"
```

---

## Development Workflow

### Day-to-Day Development

#### 1. Start Development Environment

```bash
# Terminal 1: Backend API
cd TradingMTQ
source venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Trading Bot (optional - for testing)
cd TradingMTQ
source venv/bin/activate
python main.py

# Terminal 3: Dashboard
cd TradingMTQ/dashboard
npm run dev
```

#### 2. Make Code Changes

**Backend (Python):**
- Edit files in `src/`
- FastAPI will auto-reload on file changes (if using `--reload`)
- Run tests: `pytest tests/`

**Dashboard (React + TypeScript):**
- Edit files in `dashboard/src/`
- Vite will hot-reload automatically
- Check console for errors

#### 3. Test Changes

**Backend Tests:**
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_mt5_connector.py

# Run specific test
pytest tests/test_mt5_connector.py::TestMT5Connector::test_connect
```

**Dashboard Tests:**
```bash
cd dashboard

# Lint code
npm run lint

# Type check
tsc --noEmit

# Build to verify no errors
npm run build
```

#### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add new trading strategy"

# Push to remote
git push origin feature/new-strategy
```

### Git Workflow

#### Branch Naming Convention

```
feature/description       - New features
fix/description          - Bug fixes
refactor/description     - Code refactoring
docs/description         - Documentation updates
test/description         - Test additions/updates
```

#### Commit Message Format

```
feat: add new RSI strategy
fix: correct spread calculation
refactor: improve error handling
docs: update installation guide
test: add unit tests for indicators
```

### Submodule Management (Dashboard)

#### Update Dashboard Submodule

```bash
# Navigate to dashboard
cd dashboard

# Check current commit
git log -1

# Pull latest changes
git pull origin lovely-dashboard-refactor

# Return to parent and commit submodule update
cd ..
git add dashboard
git commit -m "chore: update dashboard submodule"
git push
```

#### Push Dashboard Changes

See [SUBMODULE_PUSH_GUIDE.md](SUBMODULE_PUSH_GUIDE.md) for detailed instructions.

---

## Deployment Options

### Option 1: Local Deployment (Windows with MT5)

**Use Case:** Personal trading on your local machine with MetaTrader 5.

#### Setup

1. Install all dependencies as per [Installation](#installation--setup)
2. Configure `.env` with MT5 credentials
3. Run the trading bot as a background process

#### Run as Background Service (Windows)

**Using Windows Task Scheduler:**

1. Open Task Scheduler
2. Create New Task:
   - Name: TradingMTQ Bot
   - Trigger: At system startup
   - Action: Start a program
   - Program: `C:\path\to\TradingMTQ\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\TradingMTQ\main.py`
   - Start in: `C:\path\to\TradingMTQ`

**Using NSSM (Non-Sucking Service Manager):**

```cmd
# Download NSSM from nssm.cc
nssm install TradingMTQ "C:\path\to\venv\Scripts\python.exe" "C:\path\to\main.py"
nssm set TradingMTQ AppDirectory "C:\path\to\TradingMTQ"
nssm start TradingMTQ
```

### Option 2: VPS Deployment (Cloud Windows Server)

**Use Case:** 24/7 trading on a remote Windows VPS with MetaTrader 5.

#### Recommended VPS Providers

- **Forex VPS**: MetaTrader-optimized VPS (low latency to brokers)
- **Contabo**: Affordable Windows VPS
- **Vultr**: Flexible Windows instances
- **DigitalOcean**: Windows droplets

#### Setup

1. Connect to VPS via Remote Desktop (RDP)
2. Install Python 3.10+
3. Install MetaTrader 5 terminal
4. Clone repository and follow [Installation](#installation--setup)
5. Configure MT5 to auto-login on startup
6. Set up TradingMTQ as a Windows Service (see Option 1)

#### Keep-Alive Configuration

**Prevent Windows from sleeping:**
```cmd
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
```

### Option 3: Docker Deployment (Backend Only - No MT5)

**Use Case:** Deploy the backend API and dashboard without MT5 integration.

#### Backend Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose API port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Dashboard Dockerfile

Create `Dockerfile` in `dashboard/` directory:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Production image
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/tradingmtq
    volumes:
      - ./logs:/app/logs
    depends_on:
      - db
    restart: unless-stopped

  dashboard:
    build: ./dashboard
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: tradingmtq
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Deploy

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 4: Cloud Deployment (Full Stack)

**Use Case:** Deploy backend API + dashboard on cloud platforms.

#### Heroku Deployment

```bash
# Install Heroku CLI
brew install heroku/brew/heroku  # macOS
# Or download from heroku.com

# Login
heroku login

# Create app
heroku create tradingmtq-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set MT5_LOGIN=12345678
heroku config:set MT5_PASSWORD=password
heroku config:set MT5_SERVER=broker-server

# Deploy
git push heroku main

# Open app
heroku open
```

#### AWS Deployment (EC2 + RDS + S3)

1. **EC2 Instance**: Launch Ubuntu/Amazon Linux instance
2. **RDS Database**: Create PostgreSQL database
3. **S3 Bucket**: Store logs and ML models
4. **CloudFront**: CDN for dashboard static files
5. **Route 53**: Custom domain setup

#### Vercel Deployment (Dashboard Only)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy dashboard
cd dashboard
vercel --prod
```

### Option 5: Kubernetes Deployment

See [docs/DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed Kubernetes deployment instructions.

---

## Troubleshooting

### Common Issues

#### 1. MT5 Connection Fails

**Symptom:**
```
ERROR: Failed to connect to MetaTrader 5
```

**Solutions:**
- ✅ Verify MT5 terminal is running and logged in
- ✅ Check `.env` credentials (MT5_LOGIN, MT5_PASSWORD, MT5_SERVER)
- ✅ Enable "Allow algorithmic trading" in MT5 settings
- ✅ Check if demo account is still active (they expire)
- ✅ Try restarting MT5 terminal

#### 2. Module Not Found Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'MetaTrader5'
```

**Solutions:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python -c "import MetaTrader5; print('OK')"
```

#### 3. Dashboard Won't Start

**Symptom:**
```
Error: Cannot find module 'vite'
```

**Solutions:**
```bash
cd dashboard

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Or use another package manager
yarn install
# or
pnpm install
```

#### 4. API Connection Errors in Dashboard

**Symptom:**
Dashboard shows "Unable to connect to API"

**Solutions:**
- ✅ Check if backend API is running on port 8000
- ✅ Verify `dashboard/.env` has correct `VITE_API_URL`
- ✅ Check CORS settings in backend API
- ✅ Test API directly: http://localhost:8000/docs

#### 5. Database Errors

**Symptom:**
```
sqlalchemy.exc.OperationalError: unable to open database file
```

**Solutions:**
```bash
# Check database URL in .env
cat .env | grep DATABASE_URL

# Initialize database
python -c "from src.database.base import init_db; init_db()"

# Or run migrations
alembic upgrade head
```

#### 6. Permission Errors (Git Push)

**Symptom:**
```
remote: Permission to 5kipp3rm/TradingMTQ.git denied to user
```

**Solutions:**
See [SUBMODULE_PUSH_GUIDE.md](SUBMODULE_PUSH_GUIDE.md) for detailed git authentication fixes.

#### 7. Trading Bot Not Opening Positions

**Symptom:**
Bot runs but doesn't open any trades

**Solutions:**
- ✅ Check if account has sufficient margin
- ✅ Verify currency pairs are enabled in `config/currencies.yaml`
- ✅ Check spread is within max_spread limit
- ✅ Verify market is open (check Forex market hours)
- ✅ Review logs for signal generation: `tail -f logs/trading_bot.log`

#### 8. High CPU/Memory Usage

**Solutions:**
```bash
# Reduce number of active currency pairs
# Edit config/currencies.yaml and disable some pairs

# Disable ML features if not needed
# Set use_ml: false in currency config

# Increase timeframe (reduces tick processing)
# Use M15 or M30 instead of M1 or M5
```

### Debug Mode

#### Enable Verbose Logging

Edit `.env`:
```env
LOG_LEVEL=DEBUG
```

Or run with debug flag:
```bash
python main.py --debug
```

#### View Logs

```bash
# Real-time log monitoring
tail -f logs/trading_bot.log

# Search for errors
grep ERROR logs/trading_bot.log

# View last 100 lines
tail -100 logs/trading_bot.log
```

### Getting Help

1. **Check Documentation**: [docs/](../docs/)
2. **Search Issues**: https://github.com/5kipp3rm/TradingMTQ/issues
3. **Open New Issue**: Provide logs, configuration, and system info
4. **Discord/Community**: (Add link if available)

---

## Advanced Topics

### Custom Strategies

Create your own trading strategy by extending the base strategy class:

```python
# src/strategies/my_strategy.py
from src.strategies.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def analyze(self, data):
        # Your strategy logic here
        if condition:
            return 'BUY'
        elif other_condition:
            return 'SELL'
        return 'HOLD'
```

Register in `config/currencies.yaml`:
```yaml
EURUSD:
  strategy: my_strategy
```

### Machine Learning Integration

Train custom ML models:

```bash
# Collect historical data
python scripts/collect_data.py --pair EURUSD --days 365

# Train LSTM model
python scripts/train_models.py --model lstm --pair EURUSD

# Train Random Forest
python scripts/train_models.py --model rf --pair EURUSD

# Use in trading
# Edit config/currencies.yaml: use_ml: true
```

### API Integration

Use the REST API for external integrations:

```python
import requests

# Get account status
response = requests.get('http://localhost:8000/api/account')
print(response.json())

# Get open positions
response = requests.get('http://localhost:8000/api/positions')
print(response.json())

# Close position
response = requests.post('http://localhost:8000/api/positions/123/close')
```

### WebSocket Real-Time Updates

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};

// Subscribe to position updates
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'positions'
}));
```

---

## Summary

This guide covered:

✅ **Installation**: Python, Node.js, dependencies, MetaTrader 5
✅ **Configuration**: Environment variables, trading settings, API keys
✅ **Running**: Backend bot, dashboard, various entry points
✅ **Development**: Workflow, testing, git operations
✅ **Deployment**: Local, VPS, Docker, cloud platforms
✅ **Troubleshooting**: Common issues and solutions

**Quick Start Reminder:**
```bash
# Backend
python main.py

# Dashboard
cd dashboard && npm run dev
```

**Next Steps:**
- Review [docs/guides/LIVE_TRADING_GUIDE.md](guides/LIVE_TRADING_GUIDE.md) for trading strategies
- Check [docs/guides/GETTING_STARTED.md](guides/GETTING_STARTED.md) for detailed walkthroughs
- Explore [examples/](../examples/) for code samples

---

**Built with ❤️ for algorithmic trading enthusiasts**

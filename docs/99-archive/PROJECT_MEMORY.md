# TradingMTQ - Project Memory & Architecture Analysis

**Generated:** 2025-12-19
**Purpose:** Comprehensive codebase analysis for safe implementation changes

---

## Executive Summary (TL;DR)

- **Multi-currency automated trading platform** for MetaTrader 5 (forex) with optional ML/LLM enhancement for signal generation and sentiment filtering
- **Two primary execution modes**: CLI-based trading (`tradingmtq trade`) and REST API server (`tradingmtq serve`) with real-time WebSocket updates
- **Configuration-driven architecture**: YAML files define per-currency strategies (MA crossover, RSI, MACD, BB, multi-indicator), risk parameters, SL/TP rules, position stacking, and AI enablement
- **Data pipeline**: Market data (bars/ticks) → Strategy analysis → Optional ML prediction → Optional LLM sentiment filter → Signal generation → Risk-based position sizing → Order execution → Position management (trailing stop, breakeven, partial close) → Trade persistence (SQLite/PostgreSQL) → Analytics aggregation
- **Comprehensive observability**: Structured JSON logging with correlation IDs, database-backed trade/signal history, daily performance aggregation, alerts via WebSocket/email, and REST API for dashboards
- **Production-grade infrastructure**: Alembic migrations, retry decorators, connection pooling, health checks, CORS-enabled FastAPI server, multi-account support, and automated daily aggregation scheduler

---

## Architecture Overview

### System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ENTRYPOINTS                              │
├─────────────────────────────────────────────────────────────────┤
│  main.py           │  tradingmtq CLI    │  FastAPI Server      │
│  (legacy)          │  (Click-based)     │  (uvicorn)           │
└──────┬─────────────┴──────┬─────────────┴──────┬───────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BOOTSTRAP & CONFIGURATION                      │
├─────────────────────────────────────────────────────────────────┤
│  • load_dotenv (.env credentials)                               │
│  • ConfigurationManager (config/currencies.yaml)                │
│  • init_db (SQLAlchemy + Alembic migrations)                    │
│  • Analytics Scheduler (daily 00:05 UTC aggregation)            │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONNECTOR LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  ConnectorFactory → MT5Connector / MT4Connector                 │
│  • mt5.initialize(login, password, server)                      │
│  • Connection pooling, retries, error mapping                   │
│  • Real-time tick/bar data streaming                            │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│              ORCHESTRATOR & TRADING LOOP                        │
├─────────────────────────────────────────────────────────────────┤
│  MultiCurrencyOrchestrator                                      │
│  ├── CurrencyTrader (per symbol)                                │
│  ├── PositionManager (auto SL/TP)                               │
│  └── IntelligentPositionManager (AI-driven closures)            │
│                                                                  │
│  process_single_cycle() / process_parallel_cycle()              │
│  • Iterates through all currency traders                        │
│  • Enforces portfolio position limits                           │
│  • Saves account snapshots every cycle                          │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│           SIGNAL GENERATION & EXECUTION                         │
├─────────────────────────────────────────────────────────────────┤
│  CurrencyTrader.process_cycle()                                 │
│  │                                                               │
│  ├─► analyze_market()                                           │
│  │    ├─► Fetch bars from connector                             │
│  │    ├─► Strategy.analyze() [MA, RSI, MACD, etc.]              │
│  │    ├─► Optional: ML enhancement (LSTM/RF prediction)         │
│  │    └─► Optional: LLM sentiment filter                        │
│  │                                                               │
│  ├─► should_execute_signal()                                    │
│  │    ├─► Check cooldown                                        │
│  │    ├─► Check position stacking rules                         │
│  │    └─► Optional: Intelligent manager approval                │
│  │                                                               │
│  ├─► calculate_lot_size()                                       │
│  │    └─► AccountUtils.risk_based_lot_size()                    │
│  │        (risk_percent of balance, adjusted for stacking)      │
│  │                                                               │
│  └─► execute_trade()                                            │
│       ├─► connector.send_order() → mt5.order_send()             │
│       └─► Save Trade to database (TradeRepository)              │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  POSITION MANAGEMENT                            │
├─────────────────────────────────────────────────────────────────┤
│  PositionManager.process_all_positions()                        │
│  ├─► Breakeven: Move SL to entry + offset @ profit trigger      │
│  ├─► Trailing: Update SL following price @ trailing start       │
│  └─► Partial Close: Close X% @ profit target                    │
│                                                                  │
│  IntelligentPositionManager (AI-powered)                        │
│  ├─► analyze_portfolio(): ML + risk scoring                     │
│  └─► Close losing positions if confidence < threshold           │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│               PERSISTENCE & ANALYTICS                           │
├─────────────────────────────────────────────────────────────────┤
│  Database (SQLite / PostgreSQL)                                 │
│  ├─► Trade (entry/exit, P&L, ML metadata)                       │
│  ├─► Signal (all generated signals, executed + rejected)        │
│  ├─► AccountSnapshot (balance/equity every cycle)               │
│  ├─► DailyPerformance (aggregated metrics by date)              │
│  └─► TradingAccount, AlertConfiguration, AlertHistory           │
│                                                                  │
│  DailyAggregator                                                │
│  └─► Query closed trades → Calculate win_rate, profit_factor    │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API & DASHBOARD                              │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Application                                            │
│  ├─► REST Endpoints: /api/analytics, /api/trades, /api/positions│
│  ├─► WebSocket: Real-time trade/position updates                │
│  └─► Static Files: dashboard/ (HTML/CSS/JS)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Entrypoints & Runtime Modes

### 1. CLI Trading Mode

**Command:**
```bash
tradingmtq trade [--config config/currencies.yaml] [--aggressive] [--enable-ml] [--enable-llm]
# OR legacy:
python main.py
```

**Entry File:** [main.py:48](main.py#L48) `_run_legacy_trading()` or [src/cli/commands.py:7](src/cli/commands.py#L7) `run_trading()`

**Flow:**
1. Load environment variables (`.env` with MT5 credentials)
2. Initialize database: [init_db()](src/database/connection.py#L71)
3. Start analytics scheduler (daily aggregation at 00:05 UTC)
4. Load configuration: [ConfigurationManager("config/currencies.yaml")](main.py#L110)
5. Create connector: [ConnectorFactory.create_connector(PlatformType.MT5)](main.py#L124)
6. Connect to MT5 terminal using `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`
7. Create orchestrator: [MultiCurrencyOrchestrator(connector)](main.py#L139)
8. Add currencies from config (6-20 currency pairs)
9. **Optional:** Load ML models from `models/` directory
10. **Optional:** Initialize LLM providers (OpenAI/Anthropic)
11. **Trading loop:** `while True: orchestrator.process_single_cycle() → sleep(interval)`
12. On `KeyboardInterrupt`: Print statistics → Disconnect connector → Close DB

### 2. API Server Mode

**Command:**
```bash
tradingmtq serve [--host 0.0.0.0] [--port 8000] [--reload]
```

**Entry File:** [src/api/app.py:169](src/api/app.py#L169) `app = create_app()`

**Flow:**
1. FastAPI lifespan startup:
   - Setup structured logging
   - Initialize database
   - Start WebSocket heartbeat loop
   - Start [TradingBotService](src/services/trading_bot_service.py) (background trading)
2. Serve REST API + static dashboard
3. WebSocket endpoint for real-time updates
4. On shutdown: Stop trading service → Cancel heartbeat

### 3. Aggregation Mode

**Command:**
```bash
tradingmtq aggregate --backfill  # All historical trades
tradingmtq aggregate --date 2025-12-13  # Single day
tradingmtq aggregate --start 2025-12-01 --end 2025-12-13  # Range
```

**Entry File:** [src/cli/app.py:123](src/cli/app.py#L123) `aggregate()`

**Flow:**
1. Query [TradeRepository](src/database/repository.py) for closed trades
2. Calculate metrics: `win_rate`, `profit_factor`, `avg_win`, `avg_loss`
3. Save to [DailyPerformance](src/database/models.py#L404) table

---

## Key Abstractions & Responsibilities

### Core Classes

| Class | File | Responsibility |
|-------|------|----------------|
| **MultiCurrencyOrchestrator** | [src/trading/orchestrator.py:36](src/trading/orchestrator.py#L36) | Portfolio management; global position limits; cycle execution (serial/parallel); account snapshots |
| **CurrencyTrader** | [src/trading/currency_trader.py:73](src/trading/currency_trader.py#L73) | Per-symbol trading; signal generation; lot size calculation; trade execution; DB persistence |
| **MT5Connector** | [src/connectors/mt5_connector.py:79](src/connectors/mt5_connector.py#L79) | MT5 API wrapper; connection management; order execution; data retrieval; error handling |
| **BaseStrategy** | [src/strategies/base.py:39](src/strategies/base.py#L39) | Abstract strategy interface; requires `analyze(symbol, timeframe, bars) → Signal` |
| **PositionManager** | [src/trading/position_manager.py](src/trading/position_manager.py) | Automatic SL/TP management; breakeven, trailing stop, partial close |
| **IntelligentPositionManager** | [src/trading/intelligent_position_manager.py](src/trading/intelligent_position_manager.py) | AI-powered position management; early closure of losing positions |
| **ConfigurationManager** | [src/config_manager.py](src/config_manager.py) | YAML config loading; hot-reload; validation; emergency stop checks |
| **TradeRepository** | [src/database/repository.py](src/database/repository.py) | CRUD for Trade model; pagination; filtering by symbol/date/status |
| **DailyAggregator** | [src/analytics/aggregator.py](src/analytics/aggregator.py) | Trade aggregation; daily performance metrics calculation |

### Data Flow: Signals → Orders → Executions → Positions → P&L

```
1. Market Data (MT5)
   ↓
2. Strategy Analysis (MA crossover, RSI, MACD, etc.)
   ↓
3. ML Enhancement (optional: LSTM/RF prediction)
   ↓
4. LLM Sentiment Filter (optional: news/sentiment analysis)
   ↓
5. Signal Generation (BUY/SELL/HOLD + SL/TP + confidence)
   ↓
6. Approval Checks (cooldown, stacking, AI manager)
   ↓
7. Lot Size Calculation (risk-based via AccountUtils)
   ↓
8. Order Execution (mt5.order_send)
   ↓
9. Trade Persistence (Database: Trade table)
   ↓
10. Position Management (trailing stop, breakeven, partial close)
    ↓
11. Daily Aggregation (win_rate, profit_factor, etc.)
```

---

## Configuration Model

### Configuration Hierarchy (Precedence)

1. **CLI Flags** (Highest) → `--interval 120`, `--max-concurrent 20`, `--enable-ml`
2. **YAML Config** → `config/currencies.yaml`, `config/currencies_aggressive.yaml`
3. **Environment Variables** → `.env` (MT5 credentials, API keys)
4. **Code Defaults** (Lowest) → Dataclass defaults in `CurrencyTraderConfig`

### Key Configuration Files

| File | Purpose |
|------|---------|
| `config/currencies.yaml` | Default config: 6 pairs, 1% risk, 60s interval |
| `config/currencies_aggressive.yaml` | Higher risk (2%), lower SL/TP, faster MA periods |
| `.env` | Secrets: `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`, `OPENAI_API_KEY` |

### Configuration Hot-Reload

- **Mechanism:** [ConfigurationManager.check_and_reload()](src/config_manager.py) checks file mtime every `reload_interval` seconds
- **Behavior:** Reloads YAML if changed; applies to NEW trades only (not existing positions)
- **Safety:** Emergency stop (`emergency.emergency_stop: true`) immediately halts trading loop

### Sample Configuration Structure

```yaml
global:
  max_concurrent_trades: 15        # Portfolio position limit
  portfolio_risk_percent: 8.0      # Total risk across all pairs
  interval_seconds: 60             # Cycle frequency
  parallel_execution: false        # Serial vs parallel execution
  auto_reload_enabled: true        # Hot-reload config changes
  use_ml_enhancement: false        # Enable ML models
  use_sentiment_filter: false      # Enable LLM sentiment

modifications:
  trailing_stop_enabled: true      # Auto trailing stop
  trailing_stop_pips: 10.0
  breakeven_enabled: true          # Move SL to breakeven
  breakeven_trigger_pips: 15.0
  breakeven_offset_pips: 2.0

emergency:
  emergency_stop: false            # Emergency kill switch
  close_all_on_stop: true          # Close positions on stop

currencies:
  - symbol: EURUSD
    enabled: true
    risk_percent: 1.0              # Risk per trade
    strategy_type: position        # 'position' or 'crossover'
    timeframe: M5
    fast_period: 10
    slow_period: 20
    sl_pips: 20
    tp_pips: 40
    cooldown_seconds: 60
    allow_position_stacking: false # Allow multiple positions same direction
    max_positions_same_direction: 1
```

---

## Database Schema

### Core Tables

| Table | Model | Purpose |
|-------|-------|---------|
| `trades` | [Trade](src/database/models.py#L179) | Trade execution records (entry/exit, P&L, ML metadata) |
| `signals` | [Signal](src/database/models.py#L274) | All generated signals (executed + rejected) |
| `account_snapshots` | [AccountSnapshot](src/database/models.py#L343) | Balance/equity snapshots every cycle |
| `daily_performance` | [DailyPerformance](src/database/models.py#L404) | Aggregated daily metrics (win_rate, profit_factor) |
| `trading_accounts` | [TradingAccount](src/database/models.py#L63) | Multi-account support (broker, server, credentials) |
| `account_connection_states` | [AccountConnectionState](src/database/models.py#L130) | Real-time connection status tracking |
| `alert_configurations` | [AlertConfiguration](src/database/models.py#L471) | Notification preferences |
| `alert_history` | [AlertHistory](src/database/models.py#L545) | Notification delivery audit log |

### Trade Lifecycle

```
1. Signal Generation → Insert into `signals` table (executed=false)
2. Trade Execution → Insert into `trades` table (status='open')
3. Link Signal → Update `signals.trade_id` + `executed=true`
4. Position Close → Update `trades` (status='closed', exit_price, profit)
5. Daily Aggregation → Query closed trades → Insert into `daily_performance`
```

---

## Extension Points

### 1. Add a New Strategy

**Steps:**
1. Create strategy class: `src/strategies/my_strategy.py`
   ```python
   from .base import BaseStrategy, Signal, SignalType

   class MyStrategy(BaseStrategy):
       def __init__(self, params=None):
           super().__init__("My Strategy", params or {'param1': 10})

       def analyze(self, symbol, timeframe, bars):
           # Your logic here
           return Signal(type=SignalType.BUY, ...)
   ```

2. Register in config:
   ```yaml
   currencies:
     - symbol: EURUSD
       strategy_type: my_strategy
   ```

3. Update strategy factory (if needed): `src/strategies/__init__.py`
4. Test: `pytest tests/test_my_strategy.py`

### 2. Add a New Connector/Broker Adapter

**Steps:**
1. Create connector class: `src/connectors/my_broker_connector.py`
   ```python
   from .base import BaseMetaTraderConnector, PlatformType

   class MyBrokerConnector(BaseMetaTraderConnector):
       def connect(self, login, password, server, **kwargs):
           # Your connection logic (REST API, WebSocket, etc.)
           pass

       def send_order(self, request):
           # Map TradeRequest to broker API
           pass

       # Implement all abstract methods
   ```

2. Register in factory: `src/connectors/factory.py`
3. Add platform type: `src/connectors/base.py` → `PlatformType.MY_BROKER`
4. Test: `pytest tests/test_my_broker_connector.py`

### 3. Add a New Indicator/Feature

**Steps:**
1. Create indicator function: `src/indicators/my_indicator.py`
   ```python
   def calculate_my_indicator(bars, period=14):
       # Your calculation
       return [...]
   ```

2. Register in FeatureEngineer: `src/ml/feature_engineer.py`
3. Use in strategy: Import indicator in strategy class
4. Test: `pytest tests/test_my_indicator.py`

### 4. Add a New Notification Channel

**Steps:**
1. Create notification service: `src/notifications/my_channel.py`
2. Add DB field: `AlertConfiguration.my_channel_enabled`
3. Create migration: `alembic revision -m "Add my_channel_enabled"`
4. Wire into alert dispatcher: `src/api/routes/alerts.py`
5. Test: `pytest tests/test_my_channel_notifier.py`

### 5. Add a New Config Option (End-to-End)

**Example: Dynamic lot sizing based on volatility**

**Steps:**
1. Add config field: `config/currencies.yaml` → `use_dynamic_lot_sizing: true`
2. Update Pydantic schema: `src/config/schemas.py` → `CurrencyConfig`
3. Extend ConfigurationManager: Add getter method
4. Modify trader logic: `CurrencyTrader.calculate_lot_size()` → Calculate ATR → Adjust risk
5. Update documentation: `docs/configuration.md`
6. Test: `pytest tests/test_dynamic_lot_sizing.py`
7. Verify end-to-end: Run `python main.py` → Check logs → Verify DB trades

---

## Critical Hotspots & Risks

### 🔴 Tight Coupling

**Issue:** MultiCurrencyOrchestrator directly instantiates CurrencyTrader; no dependency injection.
**Risk:** Hard to mock connectors for unit tests; difficult to swap orchestrator logic.
**Fix:** Introduce `TradingEngine` interface; use DI container (e.g., `Injector` library).

**Example:**
```python
# Current (tightly coupled):
trader = CurrencyTrader(config, connector, intelligent_manager)

# Better (DI):
trader = container.resolve(CurrencyTrader, config=config)
```

### 🟡 Global State

**Issue:** Database engine (`_engine`, `_SessionFactory`) are module-level globals in [src/database/connection.py:30](src/database/connection.py#L30).
**Risk:** Not thread-safe if multiple orchestrators run concurrently.
**Fix:** Use `contextvars` or pass engine explicitly via dependency injection.

**Issue:** MT5 initialization (`mt5.initialize()`) is process-wide but `_initialized` is instance-level.
**Risk:** Multiple connectors can't initialize with different accounts simultaneously.
**Fix:** Use MT5 portable mode with separate working directories per instance.

### 🟡 Hidden IO

**Issue:** ConfigurationManager reads YAML file synchronously during trading loop.
**Risk:** Blocks cycle execution during file read (especially on slow disk).
**Fix:** Async file read or load config in background thread with queue.

**Issue:** ML model loading reads large pickle files synchronously at startup.
**Risk:** Multi-second startup delay if models are large (100MB+ LSTM models).
**Fix:** Lazy-load models on first signal generation; show loading progress.

### 🔴 Concurrency Assumptions

**Issue:** `process_parallel_cycle()` uses `ThreadPoolExecutor` but MT5 connector is not thread-safe.
**Risk:** Race conditions in `mt5.order_send()` (Python GIL helps but not guaranteed).
**Fix:** Use process pool (`ProcessPoolExecutor`) or ensure connector methods use `threading.Lock`.

**Issue:** Hot-reload updates config dict while traders reference it.
**Risk:** Traders may read partially updated config (torn reads).
**Fix:** Use `threading.Lock` or copy-on-write config updates (immutable config objects).

### 🔴 Risk Management Gaps

| Gap | Risk | Fix |
|-----|------|-----|
| **No aggregate loss limit** | Unchecked drawdown during losing streak | Add `max_daily_loss_percent` in global config; check before each trade |
| **No margin check before order** | Order rejected due to insufficient margin even if count limit not reached | Query `account.margin_free` before approving trade |
| **Position stacking without correlation check** | Concentrated risk on correlated pairs (EURUSD + GBPUSD both BUY) | Add correlation matrix; limit positions per direction across correlated pairs |
| **No slippage tracking** | Can't analyze execution quality | Add `expected_price` field in `TradeResult`; log slippage in DB |

### 🟠 Money-Safety Issues

| Issue | Risk | Fix |
|-------|------|-----|
| **Plaintext passwords in .env** | Exposed if `.env` file leaked | Use encrypted credential store (e.g., `keyring` library) |
| **No trade confirmation** | Erroneous trades due to bug or config error | Add `dry_run_mode` flag that logs orders without executing |
| **Emergency stop not checked in all paths** | Positions still modified after emergency stop activated | Check emergency stop in position manager + intelligent manager |
| **No audit log for config changes** | Can't audit who changed what during hot-reload | Log config diffs to database on reload |

### 🟠 Testing Gaps

| Gap | Risk | Fix |
|-----|------|-----|
| **No integration tests for API** | Regressions in API behavior | Add `tests/integration/test_api.py` using `TestClient` + SQLite in-memory |
| **No backtest validation** | Incorrect backtest metrics | Create golden test with EURUSD 2023 data + known expected performance |
| **No stress tests for concurrent trading** | Deadlocks or race conditions under load | Add `tests/stress/test_parallel_trading.py` with 20+ symbols |
| **Mocks for MT5** | Tests pass but real MT5 API breaks | Add optional integration tests with MT5 demo account in sandbox |

### 🟡 Security Footguns

| Issue | Risk | Fix |
|-------|------|-----|
| **No API authentication** | Anyone can read/write trades if API exposed | Add API key authentication (`X-API-Key` header) or OAuth2 |
| **CORS allow all** | CSRF if dashboard runs on different port | Restrict to exact origin + add CSRF tokens |
| **SQL injection (low risk)** | Potential if raw SQL used | Audit all `session.execute(text(...))` for user input; use parameterized queries |

---

## Dependencies & Build

### Package Management

- **Build System:** `setuptools>=61.0` ([pyproject.toml:1](pyproject.toml#L1))
- **Version:** `2.0.0`
- **Package Name:** `tradingmtq`
- **Entry Points:** `tradingmtq` and `mtq` CLI commands

### Installation

```bash
# Core installation
pip install -e .

# With all optional features
pip install -e .[dev,ml-full,llm,trading,postgres]
```

### Dependency Categories

| Category | Key Packages | Purpose |
|----------|--------------|---------|
| **Core** | `numpy`, `pandas`, `pyyaml`, `python-dotenv`, `click` | Data processing, config, CLI |
| **Database** | `sqlalchemy>=2.0.23`, `alembic>=1.13.0` | ORM, migrations |
| **Trading** | `MetaTrader5>=5.0.45` (Windows-only) | MT5 connector |
| **ML** | `scikit-learn`, `tensorflow`, `optuna`, `matplotlib` | Machine learning models |
| **LLM** | `openai>=1.3`, `anthropic>=0.7`, `beautifulsoup4` | AI sentiment analysis |
| **API** | `fastapi`, `uvicorn`, `pydantic>=2.0` | REST API server |
| **Dev** | `pytest`, `pytest-cov`, `black`, `flake8`, `mypy` | Testing, linting |

### External Requirements

- **MT5 Terminal:** Windows application (or Wine on macOS for testing)
- **Broker Account:** Demo or live account with valid credentials
- **API Keys:** `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (optional)
- **GPU:** Optional for TensorFlow/LSTM (CPU works but slower)

### Local Development Workflow

```bash
# 1. Install dependencies
pip install -e .[dev,ml-full,llm]

# 2. Run tests
pytest -v --cov=src --cov-report=html

# 3. Lint code
black src/ tests/
flake8 src/ tests/
mypy src/

# 4. Run database migrations
alembic upgrade head

# 5. Start trading (development)
python main.py

# 6. Start API server (development)
tradingmtq serve --reload

# 7. Run aggregation
tradingmtq aggregate --backfill
```

---

## Error Handling & Observability

### Structured Logging

- **Library:** [src/utils/structured_logger.py:StructuredLogger](src/utils/structured_logger.py)
- **Format:** JSON-structured logs with `timestamp`, `correlation_id`, `level`, `message`, `context`
- **Correlation IDs:** Auto-generated UUID per operation via [CorrelationContext](src/utils/structured_logger.py)
- **Destinations:** Console (STDOUT) + rotating file logs in `logs/` directory

**Example Log Entry:**
```json
{
  "timestamp": "2025-12-19T15:30:45.123Z",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "level": "INFO",
  "logger": "src.trading.currency_trader",
  "message": "Trade executed successfully",
  "symbol": "EURUSD",
  "action": "BUY",
  "volume": 0.01,
  "price": 1.0850,
  "ticket": 123456789
}
```

### Retry & Error Handling

- **Retry Decorator:** [handle_mt5_errors(retry_count=3, retry_delay=1.0)](src/utils/error_handlers.py)
  - Applied to: `connect()`, `send_order()`, `get_bars()`, `close_position()`
  - Retries on: Connection timeout, server busy, requote
  - Backoff: Exponential (`sleep(retry_delay * (attempt ** 2))`)

- **Connection Timeout:** `mt5.initialize(timeout=60000)` (60 seconds)
- **Order Timeout:** `deviation=20` pips in `TradeRequest` (slippage window)

### Failure Modes & Recovery

| Failure | Detection | Recovery | Risk Mitigation |
|---------|-----------|----------|-----------------|
| **Connector Disconnect** | `connector.is_connected() == False` | Auto-reconnect with stored credentials | Missed signals during downtime; log reconnection attempts |
| **Order Reject** | `TradeResult.success == False` | Log error + raise `OrderExecutionError` | No position opened; signal wasted; check broker reasons |
| **DB Error** | Exception in `get_session()` | Rollback + log error; trading continues | Loss of trade history if DB down; queue writes for retry |
| **Broker Requote** | `TRADE_RETCODE_REQUOTE` | Retry with updated price (auto via decorator) | May execute at worse price; monitor slippage |
| **Python Crash** | Process exit | No auto-restart (external supervisor needed) | Trading stops; use systemd/Docker restart policy |
| **Config Error** | Validation in ConfigurationManager | Warn + skip invalid currencies | Reduced trading opportunities; log validation errors |
| **ML Model Error** | Try/except in `_enhance_with_ml()` | Fall back to technical signal only | No ML enhancement; trading continues with base strategy |

---

## Data Pipeline

### Inputs

| Input | Source | Format | Storage |
|-------|--------|--------|---------|
| **Market Data** | MT5 Terminal (`mt5.copy_rates_from_pos()`) | `OHLCBar` objects | Not persisted (live streaming) |
| **Account State** | MT5 Terminal (`mt5.account_info()`) | `AccountInfo` objects | Persisted as `AccountSnapshot` |
| **Config Files** | `config/*.yaml` | YAML dicts | Hot-reloaded by ConfigurationManager |
| **ML Models** | `models/*.pkl`, `models/*.h5` | Pickled scikit-learn / TensorFlow | Loaded at startup |
| **API Keys** | `.env` or `config/api_keys.yaml` | Environment variables | In-memory only |

### Outputs

| Output | Destination | Format | Purpose |
|--------|-------------|--------|---------|
| **Orders** | MT5 Terminal (`mt5.order_send()`) | `TradeRequest` → `TradeResult` | Trade execution |
| **Trades** | Database `trades` table | SQLAlchemy `Trade` model | Historical trade log |
| **Signals** | Database `signals` table | SQLAlchemy `Signal` model | All signals (executed + rejected) |
| **Daily Performance** | Database `daily_performance` | `DailyPerformance` model | Aggregated metrics |
| **Account Snapshots** | Database `account_snapshots` | `AccountSnapshot` model | Portfolio snapshots |
| **Logs** | `logs/` directory | JSON-structured logs | Debugging, auditing |
| **API Responses** | HTTP JSON | REST endpoints | Web dashboard data |
| **Alerts** | WebSocket + Email | JSON events + HTML | Real-time notifications |

### Backtest vs Live Mode

| Aspect | Backtest | Live |
|--------|----------|------|
| **Data Source** | Historical bars from `data/` or MT5 | Real-time bars via connector |
| **Order Execution** | Simulated fills at OHLC prices | Real fills via MT5 broker API |
| **Slippage** | Not simulated (perfect fills) | Real slippage from broker |
| **Commission/Swap** | Configurable in backtest | Real from broker |
| **Position Tracking** | In-memory Position list | MT5 terminal + Database |
| **Risk Management** | Simulated SL/TP checks | Real SL/TP + automatic manager |
| **Persistence** | `BacktestResult` dataclass | Database trades, retrievable via API |

---

## Critical Files Reference

| File Path | Purpose |
|-----------|---------|
| [main.py](main.py#L48) | Legacy CLI entrypoint; trading loop |
| [src/cli/app.py](src/cli/app.py#L12) | Click-based CLI (trade, serve, aggregate) |
| [src/api/app.py](src/api/app.py#L66) | FastAPI application factory |
| [src/trading/orchestrator.py](src/trading/orchestrator.py#L36) | Multi-currency portfolio manager |
| [src/trading/currency_trader.py](src/trading/currency_trader.py#L73) | Per-symbol trading logic |
| [src/connectors/mt5_connector.py](src/connectors/mt5_connector.py#L79) | MT5 API wrapper |
| [src/strategies/base.py](src/strategies/base.py#L39) | Strategy interface |
| [src/database/models.py](src/database/models.py#L18) | SQLAlchemy ORM models |
| [src/database/connection.py](src/database/connection.py#L71) | Database initialization |
| [config/currencies.yaml](config/currencies.yaml) | Default trading configuration |
| [pyproject.toml](pyproject.toml#L1) | Package metadata and dependencies |
| [alembic/env.py](alembic/env.py#L1) | Database migration configuration |

---

## Quick Reference Commands

```bash
# Trading
python main.py                          # Legacy mode
tradingmtq trade                        # CLI mode (default config)
tradingmtq trade --aggressive           # Aggressive config
tradingmtq trade --disable-ml           # Disable ML
tradingmtq trade --disable-llm          # Disable LLM

# API Server
tradingmtq serve                        # Start API server
tradingmtq serve --port 8080            # Custom port
tradingmtq serve --reload               # Auto-reload on changes

# Analytics
tradingmtq aggregate --backfill         # Aggregate all historical data
tradingmtq aggregate --date 2025-12-13  # Single day
tradingmtq aggregate --start 2025-12-01 --end 2025-12-13  # Range

# Development
pytest -v --cov=src                     # Run tests
black src/ tests/                       # Format code
flake8 src/ tests/                      # Lint code
alembic upgrade head                    # Run migrations
alembic revision -m "Add feature"       # Create migration

# Version & Health
tradingmtq version                      # Show version
tradingmtq check                        # System check
```

---

## Next Steps for Development

### Immediate Priorities

1. **Add Integration Tests:** Create `tests/integration/test_api.py` for FastAPI routes
2. **Implement API Authentication:** Add `X-API-Key` header validation in middleware
3. **Add Aggregate Loss Limit:** Implement `max_daily_loss_percent` check before trades
4. **Improve Concurrency Safety:** Add `threading.Lock` for config hot-reload
5. **Encrypt Credentials:** Replace plaintext `.env` with `keyring` library

### Medium-Term Enhancements

1. **Slippage Tracking:** Add `expected_price` to `TradeResult`; analyze execution quality
2. **Correlation Matrix:** Limit positions per direction across correlated pairs
3. **Stress Testing:** Create `tests/stress/test_parallel_trading.py` with 20+ symbols
4. **Dry Run Mode:** Add flag to log orders without executing (for testing)
5. **Audit Logging:** Track config changes, login attempts, and emergency stops

### Long-Term Goals

1. **Microservices Architecture:** Split orchestrator, connectors, and API into separate services
2. **Prometheus Metrics:** Add `/metrics` endpoint for Grafana dashboards
3. **Multi-Exchange Support:** Extend connectors to Binance, Coinbase, etc.
4. **Advanced ML Models:** Integrate transformer-based models for market prediction
5. **Mobile App:** Create React Native app for trade monitoring

---

**Document Version:** 1.0
**Last Updated:** 2025-12-19
**Maintainer:** Development Team

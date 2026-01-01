# TradingMTQ Enhancement Roadmap

**Last Updated**: 2025-12-29
**Based On**: Comprehensive codebase analysis
**Priority Levels**: 🔴 Critical | 🟡 High | 🟢 Medium | 🔵 Low

---

## 🔴 CRITICAL: Money-Safety & Risk Management

### 1. Implement Drawdown Monitoring
**Priority**: 🔴 Critical
**Risk**: Bot could lose entire account in severe market conditions
**Location**: New module `src/risk/drawdown_monitor.py`

**Tasks**:
- [ ] Create `DrawdownMonitor` class with configurable thresholds
- [ ] Track daily, weekly, and account drawdown percentages
- [ ] Implement automatic trading halt when drawdown limit exceeded
- [ ] Add recovery conditions (e.g., wait 24h, manual approval)
- [ ] Persist drawdown state to database for restart recovery
- [ ] Add API endpoint to view/reset drawdown limits
- [ ] Alert via email/Telegram when approaching limits (80%, 90%, 100%)

**Config Addition**:
```yaml
risk_management:
  max_daily_drawdown_percent: 5.0      # Stop trading if daily loss > 5%
  max_weekly_drawdown_percent: 10.0    # Stop trading if weekly loss > 10%
  max_account_drawdown_percent: 20.0   # Emergency stop if total DD > 20%
  recovery_wait_hours: 24              # Wait before auto-resume
```

---

### 2. Implement Daily Loss Limits
**Priority**: 🔴 Critical
**Risk**: Bot continues trading during severe losing streaks
**Location**: `src/risk/loss_limiter.py`

**Tasks**:
- [ ] Create `DailyLossLimiter` class
- [ ] Track daily P&L from midnight UTC (or market open)
- [ ] Halt all trading when daily loss limit reached
- [ ] Add manual override flag (emergency mode)
- [ ] Integrate with `TradingBot` main loop check
- [ ] Add dashboard widget showing daily P&L vs limit
- [ ] Test with simulated losing trades

**Integration Point**: [src/bot.py:112](src/bot.py#L112) - Add check before `_check_symbol()`

---

### 3. Portfolio-Wide Position Limits ✅ **COMPLETE**

**Priority**: 🔴 Critical
**Risk**: Max position check is local only, ignores manual trades
**Location**: [src/bot.py:172-184](src/bot.py#L172-L184), [src/trading/controller.py:213-275](src/trading/controller.py#L213-L275)
**Completed**: 2025-12-30

**Tasks**:
- [x] Change position check to query MT5 for ALL open positions (not just bot-tracked)
- [x] Implement `TradingController.get_total_open_positions_count()`
- [x] Add account-wide exposure calculation (total volume × contract size)
- [x] Enforce portfolio risk percentage limit (foundation laid via exposure calculation)
- [x] Consider positions opened by other bots/manual trades
- [ ] Add test cases with mixed bot/manual positions (requires testing framework)

**Implementation Details**: See [docs/PHASE1_TASK3_PORTFOLIO_POSITION_LIMITS.md](docs/PHASE1_TASK3_PORTFOLIO_POSITION_LIMITS.md)

**Current Code** (flawed):
```python
if len(self.positions) >= self.max_positions:  # Only checks bot's dict!
```

**Fixed Code**:
```python
all_positions = self.controller.get_open_positions()  # Query MT5
if len(all_positions) >= self.max_positions:
```

---

### 4. Position Size Validation (Equity-Based)
**Priority**: 🔴 Critical
**Risk**: Bot uses fixed lot size regardless of account equity
**Location**: [src/trading/controller.py:83-89](src/trading/controller.py#L83-L89)

**Tasks**:
- [ ] Calculate required margin for trade BEFORE execution
- [ ] Validate margin requirement is < `free_margin * safety_factor` (e.g., 80%)
- [ ] Implement position sizing based on risk percentage (e.g., 1% of equity)
- [ ] Add Kelly Criterion optional sizing
- [ ] Reject trades that would push margin level below threshold (e.g., 200%)
- [ ] Add `calculate_position_size()` method to risk manager
- [ ] Test with varying account sizes and leverage levels

**Config Addition**:
```yaml
risk_management:
  risk_per_trade_percent: 1.0        # Risk 1% of equity per trade
  min_margin_level_percent: 200.0    # Don't trade if margin level < 200%
  margin_safety_factor: 0.8          # Use max 80% of free margin
```

---

### 5. Mandatory Stop Loss Enforcement
**Priority**: 🔴 Critical
**Risk**: Strategies can generate signals without SL/TP (unlimited risk)
**Location**: [src/trading/controller.py:36-37](src/trading/controller.py#L36-L37)

**Tasks**:
- [ ] Make SL parameter REQUIRED in `TradingController.execute_trade()`
- [ ] Reject orders if `sl=None` (raise `InvalidOrderError`)
- [ ] Add default SL calculation based on ATR or fixed pips if strategy omits
- [ ] Validate SL is within broker's min/max distance from entry
- [ ] Add TP validation (optional but must be > SL distance if provided)
- [ ] Update all strategies to ALWAYS set SL/TP
- [ ] Add integration test verifying orders rejected without SL

**Code Change**:
```python
def execute_trade(self, symbol: str, action: OrderType, volume: float,
                 sl: float, tp: Optional[float] = None, ...):  # SL now required!
    if sl is None:
        raise InvalidOrderError("Stop loss is mandatory for all trades")
```

---

### 6. AutoTrading Status Pre-Flight Check
**Priority**: 🔴 Critical
**Risk**: Bot executes loop but orders silently fail if AutoTrading disabled
**Location**: [src/connectors/mt5_connector.py:358-409](src/connectors/mt5_connector.py#L358-L409)

**Tasks**:
- [ ] Move AutoTrading check from post-connection to pre-trade execution
- [ ] Add `TradingBot.preflight_check()` method called before main loop
- [ ] Raise `AutoTradingDisabledError` if disabled (halt bot immediately)
- [ ] Re-check AutoTrading status every N cycles (e.g., every 10 iterations)
- [ ] Add dashboard indicator showing AutoTrading status (red/green)
- [ ] Create troubleshooting guide linked from error message
- [ ] Test with AutoTrading toggled mid-session

**Integration Point**: [src/bot.py:63-92](src/bot.py#L63-L92) - Add check before starting loop

---

## 🟡 HIGH: Security & Production Readiness

### 7. Implement API Authentication
**Priority**: 🟡 High
**Risk**: Dashboard is publicly accessible, anyone can view trades/trigger actions
**Location**: [src/api/app.py:74-176](src/api/app.py#L74-L176)

**Tasks**:
- [ ] Add JWT-based authentication using `fastapi-jwt-auth` or `python-jose`
- [ ] Create `/api/auth/login` endpoint (username/password or API key)
- [ ] Store hashed credentials in database (`User` model)
- [ ] Add `Depends(get_current_user)` to protected routes
- [ ] Implement role-based access control (RBAC): viewer vs trader vs admin
- [ ] Add API key support for programmatic access
- [ ] Rate limit login attempts (防暴力破解)
- [ ] Add logout endpoint to invalidate tokens
- [ ] Update dashboard to include login page
- [ ] Document authentication in API docs

**Dependencies**:
```toml
fastapi-jwt-auth = "^0.5.0"
passlib[bcrypt] = "^1.7.4"
python-jose[cryptography] = "^3.3.0"
```

---

### 8. Secrets Management (Replace .env)
**Priority**: 🟡 High
**Risk**: MT5 credentials stored in plaintext .env file
**Location**: [src/main.py:30-36](src/main.py#L30-L36)

**Tasks**:
- [ ] Integrate HashiCorp Vault or AWS Secrets Manager
- [ ] Create `SecretsManager` abstraction with multiple backends:
  - Vault (production)
  - AWS Secrets Manager (cloud)
  - Encrypted local file (dev fallback)
- [ ] Store MT5 credentials, API keys (OpenAI, Anthropic) in secrets manager
- [ ] Add `SECRETS_BACKEND` environment variable to select backend
- [ ] Rotate credentials using secrets manager TTL
- [ ] Add audit logging for secret access
- [ ] Update deployment docs with secrets setup

**Config Change**:
```python
# Old: os.getenv("MT5_PASSWORD")
# New:
from src.security.secrets_manager import secrets
password = secrets.get("mt5/password")
```

---

### 9. CORS Configuration for Production
**Priority**: 🟡 High
**Risk**: CORS allows localhost origins, vulnerable in production
**Location**: [src/api/app.py:124-140](src/api/app.py#L124-L140)

**Tasks**:
- [ ] Make CORS origins configurable via environment variable
- [ ] Default to strict origins in production (e.g., `https://yourdomain.com`)
- [ ] Allow localhost only when `ENVIRONMENT=development`
- [ ] Remove `allow_origins=["*"]` fallback
- [ ] Add CORS origin validation (reject invalid domains)
- [ ] Document CORS setup in deployment guide

**Code Change**:
```python
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
if not allowed_origins and os.getenv("ENVIRONMENT") == "development":
    allowed_origins = ["http://localhost:3000", "http://localhost:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # No wildcards!
    ...
)
```

---

### 10. API Rate Limiting
**Priority**: 🟡 High
**Risk**: Dashboard endpoints can be DoS'd
**Location**: New middleware in [src/api/app.py](src/api/app.py)

**Tasks**:
- [ ] Install `slowapi` (rate limiting for FastAPI)
- [ ] Add rate limiter middleware with configurable limits:
  - `/api/auth/login`: 5 requests/minute
  - `/api/trades`: 60 requests/minute
  - `/api/positions`: 30 requests/minute
  - WebSocket connections: 10/minute per IP
- [ ] Store rate limit state in Redis (for multi-worker scenarios)
- [ ] Return HTTP 429 with `Retry-After` header
- [ ] Add rate limit headers to responses (`X-RateLimit-Remaining`)
- [ ] Whitelist internal IPs (e.g., 127.0.0.1)
- [ ] Add monitoring/alerting for rate limit violations

**Dependencies**:
```toml
slowapi = "^0.1.9"
redis = "^5.0.1"  # For distributed rate limiting
```

---

### 11. SQL Injection Audit
**Priority**: 🟡 High
**Risk**: Raw SQL queries not audited
**Location**: All database code ([src/database/](src/database/))

**Tasks**:
- [ ] Audit all `session.execute(text(...))` calls
- [ ] Replace raw SQL with SQLAlchemy ORM queries where possible
- [ ] Use parameterized queries for unavoidable raw SQL
- [ ] Run `bandit` security scanner on codebase
- [ ] Add SQL injection test cases (fuzzing)
- [ ] Document safe query patterns in dev guide

**Command**:
```bash
bandit -r src/ -f json -o security-report.json
```

---

## 🟢 MEDIUM: Code Quality & Architecture

### 12. Decouple TradingBot from TradingController
**Priority**: 🟢 Medium
**Risk**: Hard to test, can't swap execution strategies
**Location**: [src/bot.py:48](src/bot.py#L48)

**Tasks**:
- [ ] Change `TradingBot.__init__()` to accept `controller` parameter (dependency injection)
- [ ] Create factory function `create_trading_bot()` that builds bot + controller
- [ ] Add abstract `ExecutionController` interface
- [ ] Create `MockExecutionController` for testing (no MT5 required)
- [ ] Update tests to use mocked controller
- [ ] Document dependency injection pattern

**Code Change**:
```python
# Old:
def __init__(self, connector, strategy, ...):
    self.controller = TradingController(connector)  # Tight coupling!

# New:
def __init__(self, controller, strategy, ...):
    self.controller = controller  # Injected dependency
```

---

### 13. Strategy Plugin System
**Priority**: 🟢 Medium
**Risk**: Requires code changes to add new strategies
**Location**: [src/main.py:162-167](src/main.py#L162-L167)

**Tasks**:
- [ ] Create `StrategyRegistry` with `register_strategy()` decorator
- [ ] Add strategy discovery via entry points (setuptools)
- [ ] Load strategies from config: `strategy_class: "MyStrategy"`
- [ ] Support strategy parameters from YAML/database
- [ ] Add hot-reload for strategy code changes (development mode)
- [ ] Create example external strategy package
- [ ] Document plugin development guide

**Config Example**:
```yaml
currencies:
  EURUSD:
    strategy_class: "strategies.MyCustomStrategy"
    strategy_params:
      fast_period: 10
      slow_period: 20
```

---

### 14. Eliminate Global Database State
**Priority**: 🟢 Medium
**Risk**: Module-level globals cause testing issues, potential race conditions
**Location**: [src/database/connection.py:31-32](src/database/connection.py#L31-L32)

**Tasks**:
- [ ] Refactor `_engine` and `_SessionFactory` into `DatabaseManager` class
- [ ] Use singleton pattern or FastAPI dependency injection
- [ ] Make `DatabaseManager` thread-safe with locks
- [ ] Support multiple database connections (multi-tenancy)
- [ ] Add `DatabaseManager.reset()` for testing
- [ ] Update all database imports to use new manager
- [ ] Test with concurrent sessions

**Code Change**:
```python
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
```

---

### 15. Persistent Position Tracking
**Priority**: 🟢 Medium
**Risk**: `TradingBot.positions` dict lost on restart
**Location**: [src/bot.py:57](src/bot.py#L57)

**Tasks**:
- [ ] Store position state in database (`BotState` table)
- [ ] Add `TradingBot.save_state()` method (called after each cycle)
- [ ] Add `TradingBot.restore_state()` method (called on startup)
- [ ] Track: open positions, last check time, cycle count
- [ ] Handle position closures during bot downtime (reconciliation)
- [ ] Add API endpoint to view bot state history
- [ ] Test restart scenarios (positions opened, bot restarted, positions still open)

**Schema**:
```python
class BotState(Base):
    id = Column(Integer, primary_key=True)
    bot_instance_id = Column(String)
    state_data = Column(JSON)  # {positions: {...}, last_cycle: ...}
    updated_at = Column(DateTime)
```

---

### 16. Async Logging (Non-Blocking)
**Priority**: 🟢 Medium
**Risk**: Disk I/O blocks trading loop if disk slow/full
**Location**: [src/utils/unified_logger.py:217-258](src/utils/unified_logger.py#L217-L258)

**Tasks**:
- [ ] Use `logging.handlers.QueueHandler` + `QueueListener` for async logging
- [ ] Create background thread to write logs from queue
- [ ] Set queue max size (e.g., 10000) with overflow policy (drop oldest)
- [ ] Test with simulated slow disk (add delay to file writes)
- [ ] Monitor queue depth via metrics endpoint
- [ ] Add fallback: if queue full, log to console only (don't block)

**Code Change**:
```python
import queue
from logging.handlers import QueueHandler, QueueListener

log_queue = queue.Queue(maxsize=10000)
queue_handler = QueueHandler(log_queue)
queue_listener = QueueListener(log_queue, file_handler, error_handler)
queue_listener.start()
```

---

### 17. ConfigurationManager Thread Safety
**Priority**: 🟢 Medium
**Risk**: Singleton pattern with no locking
**Location**: [src/config_manager.py:12](src/config_manager.py#L12)

**Tasks**:
- [ ] Add `threading.Lock` around `reload()` method
- [ ] Implement copy-on-write for config dict (atomic updates)
- [ ] Add `@synchronized` decorator for thread-safe methods
- [ ] Test with concurrent config reloads from multiple threads
- [ ] Document thread-safety guarantees

**Code Change**:
```python
import threading

class ConfigurationManager:
    _lock = threading.Lock()

    def reload(self):
        with self._lock:
            # ... existing reload logic
```

---

### 18. MT5Connector Thread Safety
**Priority**: 🟢 Medium
**Risk**: `_initialized` flag not thread-safe
**Location**: [src/connectors/mt5_connector.py:198](src/connectors/mt5_connector.py#L198)

**Tasks**:
- [ ] Add `threading.Lock` around `connect()` method
- [ ] Use `threading.RLock` (reentrant) to allow nested calls
- [ ] Test with multiple threads calling `connect()` simultaneously
- [ ] Document that MT5Connector is NOT thread-safe (use one instance per thread)
- [ ] Consider adding `@not_thread_safe` decorator warning

---

## 🟢 MEDIUM: Testing & Quality Assurance

### 19. Unit Test Coverage (Target: 80%+)
**Priority**: 🟢 Medium
**Risk**: No tests analyzed, can't verify correctness
**Location**: [tests/](tests/) (empty/incomplete)

**Tasks**:
- [ ] **Strategy Tests**:
  - Test signal generation with known bar patterns
  - Verify SL/TP calculation logic
  - Test confidence scoring
- [ ] **Trading Controller Tests**:
  - Test order validation (volume, margin, symbol)
  - Test error handling (invalid symbol, rejected order)
  - Mock MT5Connector for isolation
- [ ] **Risk Manager Tests**:
  - Test drawdown limit enforcement
  - Test position size calculation
  - Test daily loss limits
- [ ] **Database Tests**:
  - Test repository CRUD operations
  - Test concurrent session handling
  - Test migration rollback
- [ ] **Config Tests**:
  - Test YAML parsing
  - Test hot-reload behavior
  - Test validation of invalid configs
- [ ] Set up pytest fixtures for MT5 mock, database setup/teardown
- [ ] Run coverage report: `pytest --cov=src --cov-report=html`
- [ ] Add pre-commit hook to enforce min coverage threshold

---

### 20. Integration Tests (MT5 Mock)
**Priority**: 🟢 Medium
**Risk**: macOS/Linux dev can't validate MT5 integration
**Location**: [tests/integration/](tests/integration/)

**Tasks**:
- [ ] Create comprehensive `MockMT5` class mimicking all MT5 API methods
- [ ] Implement realistic behavior:
  - Simulated order execution with delay
  - Price slippage simulation
  - Reject orders outside market hours
  - Simulate connection drops
- [ ] Test full bot lifecycle on macOS/Linux using mock
- [ ] Test reconnection logic
- [ ] Test AutoTrading disabled scenario
- [ ] Test partial fills (if implemented)
- [ ] Add Docker image with mock MT5 for CI/CD

---

### 21. WebSocket Integration Tests
**Priority**: 🟢 Medium
**Risk**: Dashboard real-time updates could break silently
**Location**: [tests/integration/test_websocket.py](tests/integration/test_websocket.py)

**Tasks**:
- [ ] Install `pytest-asyncio` for async test support
- [ ] Test WebSocket connection/disconnection
- [ ] Test heartbeat mechanism
- [ ] Test broadcast of trade updates to all clients
- [ ] Test client reconnection after disconnect
- [ ] Test concurrent clients (simulate 10+ connections)
- [ ] Test message serialization/deserialization
- [ ] Use `websockets` library to create test clients

**Example Test**:
```python
@pytest.mark.asyncio
async def test_trade_broadcast():
    async with websockets.connect("ws://localhost:8000/api/ws") as ws:
        # Trigger trade execution
        # Assert WebSocket receives trade update message
        message = await ws.recv()
        assert json.loads(message)['type'] == 'trade_executed'
```

---

### 22. Error Path Testing
**Priority**: 🟢 Medium
**Risk**: Retry logic, circuit breakers not validated
**Location**: [tests/unit/test_error_handlers.py](tests/unit/test_error_handlers.py)

**Tasks**:
- [ ] Test retry decorator with transient errors (3 retries → success)
- [ ] Test retry exhaustion (3 retries → final failure)
- [ ] Test exponential backoff timing
- [ ] Test circuit breaker state transitions (closed → open → half-open)
- [ ] Test reconnection logic (MT5 disconnect → auto-reconnect)
- [ ] Test database rollback on error
- [ ] Use `pytest-mock` to simulate failures
- [ ] Test error severity classification (`get_error_severity()`)

---

### 23. Performance & Load Testing
**Priority**: 🔵 Low
**Risk**: System performance under load unknown
**Location**: [tests/performance/](tests/performance/)

**Tasks**:
- [ ] Load test API endpoints with `locust` or `k6`
  - Simulate 100+ concurrent dashboard users
  - Test WebSocket scalability (100+ connections)
- [ ] Benchmark trading loop latency (time from signal to order execution)
- [ ] Profile memory usage (check for leaks in long-running bot)
- [ ] Test database query performance with 1M+ trade records
- [ ] Test log file I/O impact on trading loop
- [ ] Create performance regression tests (fail if latency > threshold)

**Tools**:
```bash
pip install locust  # Load testing
pip install memory-profiler  # Memory profiling
pip install py-spy  # CPU profiling
```

---

## 🔵 LOW: Features & Enhancements

### 24. Backtesting Slippage Model
**Priority**: 🔵 Low
**Risk**: Backtest results overly optimistic
**Location**: [src/backtest/](src/backtest/) (engine not analyzed)

**Tasks**:
- [ ] Add configurable slippage model:
  - Fixed slippage (e.g., 2 pips)
  - Percentage-based (e.g., 0.1% of price)
  - Volume-based (higher volume = more slippage)
  - Market hours-based (wider spread during low liquidity)
- [ ] Add spread simulation (bid-ask spread from historical data)
- [ ] Add commission calculation (per-lot or per-trade)
- [ ] Test backtest results with/without slippage
- [ ] Document slippage assumptions in backtest reports

---

### 25. Multi-Worker Safety (FastAPI)
**Priority**: 🔵 Low
**Risk**: Multiple uvicorn workers = duplicate trading bots
**Location**: [src/api/app.py:34-73](src/api/app.py#L34-L73)

**Tasks**:
- [ ] Add distributed lock (Redis-based) for trading bot service startup
- [ ] Only allow ONE worker to start trading bot service
- [ ] Other workers serve API requests only (read-only mode)
- [ ] Add `/api/status` endpoint showing which worker owns trading service
- [ ] Test with `uvicorn --workers 4` configuration
- [ ] Document single-worker requirement in deployment guide

**Code Change**:
```python
from redis import Redis
from redis.lock import Lock

redis_client = Redis(host='localhost', port=6379)

@asynccontextmanager
async def lifespan(app: FastAPI):
    lock = Lock(redis_client, "trading_bot_service_lock", timeout=60)
    if lock.acquire(blocking=False):
        # This worker owns the trading service
        await trading_bot_service.start()
        yield
        await trading_bot_service.stop()
        lock.release()
    else:
        # Another worker owns trading service, serve API only
        yield
```

---

### 26. Configuration Schema Validation
**Priority**: 🔵 Low
**Risk**: Invalid YAML causes runtime errors
**Location**: [src/config_manager.py:32-56](src/config_manager.py#L32-L56)

**Tasks**:
- [ ] Define Pydantic schema for `currencies.yaml` structure
- [ ] Validate config on load: `Config.parse_obj(yaml_data)`
- [ ] Add detailed validation errors (which field, why invalid)
- [ ] Create `config-schema.json` for editor autocompletion
- [ ] Add CLI command to validate config: `tradingmtq validate-config`
- [ ] Add pre-commit hook to validate config on git commit
- [ ] Document config schema in user guide

**Schema Example**:
```python
from pydantic import BaseModel, Field, validator

class CurrencyConfig(BaseModel):
    enabled: bool = True
    strategy_type: str = Field(..., regex="^(position|scalping)$")
    sl_pips: int = Field(gt=0, le=1000)
    tp_pips: int = Field(gt=0, le=1000)

    @validator('tp_pips')
    def tp_must_exceed_sl(cls, v, values):
        if 'sl_pips' in values and v <= values['sl_pips']:
            raise ValueError('tp_pips must be > sl_pips')
        return v
```

---

### 27. Enhanced ML Features
**Priority**: 🔵 Low
**Risk**: Current ML predictions may be underutilized
**Location**: [src/ml/](src/ml/)

**Tasks**:
- [ ] Add feature importance visualization (which indicators matter most)
- [ ] Implement ensemble models (combine Random Forest + LSTM + XGBoost)
- [ ] Add confidence-based position sizing (higher confidence = larger size)
- [ ] Implement online learning (retrain model weekly on new data)
- [ ] Add model versioning and A/B testing
- [ ] Track model performance metrics (prediction accuracy, Sharpe ratio)
- [ ] Add ML monitoring dashboard (drift detection, feature distributions)

---

### 28. Advanced Order Types
**Priority**: 🔵 Low
**Risk**: Limited trading flexibility
**Location**: [src/connectors/mt5_connector.py:710-1260](src/connectors/mt5_connector.py#L710-L1260)

**Tasks**:
- [ ] Implement trailing stop loss (already started in config but not used)
- [ ] Add breakeven stop (move SL to entry when profit > threshold)
- [ ] Add partial take profit (close 50% at TP1, 50% at TP2)
- [ ] Add OCO orders (one-cancels-other)
- [ ] Add bracket orders (entry + SL + TP as single order)
- [ ] Add time-based exits (close after N hours regardless of P&L)
- [ ] Test advanced orders in backtest and live demo

---

### 29. Dashboard Enhancements
**Priority**: 🔵 Low
**Risk**: Limited visibility into bot behavior
**Location**: [dashboard/](dashboard/)

**Tasks**:
- [ ] Add real-time equity curve chart (ApexCharts or Chart.js)
- [ ] Add strategy performance comparison table
- [ ] Add risk metrics dashboard (Sharpe, max DD, win rate, expectancy)
- [ ] Add trade journal with filtering (by symbol, date, P&L)
- [ ] Add position heat map (exposure by currency)
- [ ] Add economic calendar integration (highlight news events)
- [ ] Add mobile-responsive design
- [ ] Add dark mode toggle
- [ ] Add export to CSV/Excel functionality
- [ ] Add portfolio analytics (correlation matrix, diversification score)

---

### 30. Notification Enhancements
**Priority**: 🔵 Low
**Risk**: Limited alerting channels
**Location**: [src/notifications/](src/notifications/)

**Tasks**:
- [ ] Add Telegram bot integration (most popular for traders)
- [ ] Add Slack webhook support
- [ ] Add SMS alerts via Twilio (for critical events)
- [ ] Add push notifications (via Firebase or OneSignal)
- [ ] Add configurable alert priorities (info/warning/critical)
- [ ] Add alert batching (e.g., max 1 email per 5 minutes)
- [ ] Add alert templates with placeholders
- [ ] Add alert delivery status tracking (sent/failed/retrying)

---

## 📋 Implementation Priority Matrix

### Phase 1: Critical Safety (Weeks 1-2)
Focus on preventing catastrophic losses. **Must complete before live trading.**

1. 🔴 Implement Drawdown Monitoring (#1)
2. 🔴 Implement Daily Loss Limits (#2)
3. 🔴 Portfolio-Wide Position Limits (#3)
4. 🔴 Position Size Validation (#4)
5. 🔴 Mandatory Stop Loss Enforcement (#5)
6. 🔴 AutoTrading Pre-Flight Check (#6)

**Success Criteria**: Bot cannot lose > 5% in a day, > 20% total. All trades have SL.

---

### Phase 2: Security Hardening (Weeks 3-4)
Protect production deployment from external threats.

7. 🟡 Implement API Authentication (#7)
8. 🟡 Secrets Management (#8)
9. 🟡 CORS Configuration (#9)
10. 🟡 API Rate Limiting (#10)
11. 🟡 SQL Injection Audit (#11)

**Success Criteria**: Dashboard requires login. Credentials encrypted. No public endpoints.

---

### Phase 3: Architecture Improvements (Weeks 5-6)
Improve code quality and testability.

12. 🟢 Decouple TradingBot from Controller (#12)
13. 🟢 Strategy Plugin System (#13)
14. 🟢 Eliminate Global Database State (#14)
15. 🟢 Persistent Position Tracking (#15)
16. 🟢 Async Logging (#16)
17. 🟢 Thread Safety Fixes (#17, #18)

**Success Criteria**: 80%+ test coverage. No global state. Clean dependency injection.

---

### Phase 4: Testing & Validation (Weeks 7-8)
Ensure system reliability through comprehensive testing.

19. 🟢 Unit Test Coverage (#19)
20. 🟢 Integration Tests (#20)
21. 🟢 WebSocket Tests (#21)
22. 🟢 Error Path Testing (#22)
23. 🔵 Performance Testing (#23)

**Success Criteria**: All tests pass. CI/CD pipeline green. Performance benchmarks documented.

---

### Phase 5: Feature Enhancements (Weeks 9+)
Polish and expand functionality (can be deferred).

24. 🔵 Backtesting Slippage (#24)
25. 🔵 Multi-Worker Safety (#25)
26. 🔵 Config Schema Validation (#26)
27. 🔵 Enhanced ML Features (#27)
28. 🔵 Advanced Order Types (#28)
29. 🔵 Dashboard Enhancements (#29)
30. 🔵 Notification Enhancements (#30)

**Success Criteria**: Professional-grade features. Positive user feedback.

---

## 📊 Progress Tracking

Use this checklist to track overall progress:

- [ ] Phase 1: Critical Safety (1/6 complete) - **Task #3 ✅**
- [ ] Phase 2: Security Hardening (0/5 complete)
- [ ] Phase 3: Architecture (0/7 complete)
- [ ] Phase 4: Testing (0/5 complete)
- [ ] Phase 5: Features (0/7 complete)

**Total Progress**: 1/30 tasks complete (3.3%)

---

## 🚀 Quick Start for Contributors

1. **Pick a task** from Phase 1 (highest priority)
2. **Create feature branch**: `git checkout -b feature/drawdown-monitoring`
3. **Write tests first** (TDD approach)
4. **Implement feature** following existing patterns
5. **Run test suite**: `pytest --cov=src`
6. **Update TODO.md** to mark task complete
7. **Submit PR** with reference to issue number

---

## 📚 References

- **Codebase Analysis**: See root directory analysis document
- **Architecture Diagram**: See Section 2 of analysis
- **Risk Assessment**: See Section 10 of analysis
- **Extension Guide**: See Section 9 of analysis

---

**Last Updated**: 2025-12-29
**Document Version**: 1.0
**Maintainer**: TradingMTQ Core Team

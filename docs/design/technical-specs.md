# Technical Specifications - TradingMTQ

## API Reference

### MetaTrader5 Python API

Official documentation: https://www.mql5.com/en/docs/python_metatrader5

#### Core Functions Used

**Connection & Authentication**
```python
MetaTrader5.initialize(
    path=None,        # Path to MT5 terminal (optional)
    login=int,        # Account number
    password=str,     # Account password
    server=str,       # Broker server
    timeout=int,      # Connection timeout (ms)
    portable=bool     # Portable mode
) -> bool

MetaTrader5.shutdown() -> None

MetaTrader5.last_error() -> tuple(int, str)
```

**Account Information**
```python
MetaTrader5.account_info() -> AccountInfo
# Returns: login, trade_mode, leverage, limit_orders, margin_so_mode,
#          trade_allowed, trade_expert, balance, credit, profit, equity,
#          margin, margin_free, margin_level, margin_so_call, margin_so_so,
#          currency, etc.
```

**Symbol Operations**
```python
MetaTrader5.symbols_get(group=str) -> tuple[SymbolInfo]
# group examples: "Forex*", "EURUSD", "*USD*"

MetaTrader5.symbol_info(symbol: str) -> SymbolInfo
# Returns: name, path, description, page, currency_base, currency_profit,
#          currency_margin, digits, trade_mode, volume_min, volume_max,
#          volume_step, trade_contract_size, bid, ask, last, etc.

MetaTrader5.symbol_select(symbol: str, enable: bool) -> bool
```

**Market Data**
```python
MetaTrader5.symbol_info_tick(symbol: str) -> Tick
# Returns: time, bid, ask, last, volume, time_msc, flags, volume_real

MetaTrader5.copy_rates_range(
    symbol: str,
    timeframe: int,    # MT5 timeframe constant
    date_from: datetime,
    date_to: datetime
) -> ndarray

MetaTrader5.copy_rates_from_pos(
    symbol: str,
    timeframe: int,
    start_pos: int,    # 0 = current bar
    count: int
) -> ndarray
# Returns array with: time, open, high, low, close, tick_volume, spread, real_volume
```

**Trading Operations**
```python
MetaTrader5.order_send(request: dict) -> OrderSendResult
# request structure:
{
    "action": int,           # TRADE_ACTION_DEAL, TRADE_ACTION_PENDING, etc.
    "symbol": str,
    "volume": float,
    "type": int,             # ORDER_TYPE_BUY, ORDER_TYPE_SELL, etc.
    "price": float,          # For pending orders
    "sl": float,             # Stop Loss
    "tp": float,             # Take Profit
    "deviation": int,        # Price deviation in points
    "magic": int,            # Expert Advisor ID
    "comment": str,
    "type_time": int,        # Order expiration type
    "type_filling": int      # ORDER_FILLING_FOK, ORDER_FILLING_IOC
}

MetaTrader5.order_check(request: dict) -> OrderCheckResult
# Validates order before sending

MetaTrader5.positions_get(symbol=str, group=str, ticket=int) -> tuple[TradePosition]
# Returns: ticket, time, time_msc, time_update, time_update_msc, type,
#          magic, identifier, reason, volume, price_open, sl, tp, price_current,
#          swap, profit, symbol, comment, external_id

MetaTrader5.orders_get(symbol=str, group=str, ticket=int) -> tuple[TradeOrder]

MetaTrader5.history_deals_get(
    date_from: datetime,
    date_to: datetime,
    group=str,
    ticket=int,
    position=int
) -> tuple[TradeDeal]
```

**Timeframe Constants**
```python
TIMEFRAME_M1  = 1        # 1 minute
TIMEFRAME_M5  = 5        # 5 minutes
TIMEFRAME_M15 = 15       # 15 minutes
TIMEFRAME_M30 = 30       # 30 minutes
TIMEFRAME_H1  = 16385    # 1 hour
TIMEFRAME_H4  = 16388    # 4 hours
TIMEFRAME_D1  = 16408    # 1 day
TIMEFRAME_W1  = 32769    # 1 week
TIMEFRAME_MN1 = 49153    # 1 month
```

**Order Types**
```python
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5
ORDER_TYPE_BUY_STOP_LIMIT = 6
ORDER_TYPE_SELL_STOP_LIMIT = 7
```

**Trade Actions**
```python
TRADE_ACTION_DEAL = 1      # Immediate execution
TRADE_ACTION_PENDING = 5   # Place pending order
TRADE_ACTION_SLTP = 6      # Modify SL/TP
TRADE_ACTION_MODIFY = 7    # Modify order
TRADE_ACTION_REMOVE = 8    # Remove order
TRADE_ACTION_CLOSE_BY = 10 # Close by opposite position
```

---

## Data Models

### 1. Market Data Models

**Tick Data**
```python
@dataclass
class TickData:
    symbol: str
    time: datetime
    bid: float
    ask: float
    last: float
    volume: int
    spread: float        # Calculated: ask - bid
    time_msc: int       # Unix timestamp in milliseconds
```

**OHLC Bar**
```python
@dataclass
class OHLCBar:
    symbol: str
    timeframe: str      # "M1", "M5", "H1", "D1", etc.
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    real_volume: float
    spread: int
```

**Symbol Information**
```python
@dataclass
class SymbolInfo:
    name: str
    description: str
    base_currency: str      # e.g., "EUR" in EURUSD
    quote_currency: str     # e.g., "USD" in EURUSD
    digits: int            # Price decimal places
    point: float           # Minimum price change
    trade_mode: str        # "Full", "Close Only", "Disabled"
    volume_min: float      # Minimum lot size
    volume_max: float      # Maximum lot size
    volume_step: float     # Lot size step
    contract_size: float   # 100000 for standard forex
    bid: float
    ask: float
    spread: float
    trade_allowed: bool
```

### 2. Trading Models

**Order Request**
```python
@dataclass
class OrderRequest:
    symbol: str
    action: str           # "BUY", "SELL"
    volume: float         # Lot size
    order_type: str       # "MARKET", "LIMIT", "STOP"
    price: float = None   # For pending orders
    sl: float = None      # Stop Loss price
    tp: float = None      # Take Profit price
    deviation: int = 20   # Max price deviation (points)
    magic: int = 234000   # EA identifier
    comment: str = ""
    
    def to_mt5_request(self) -> dict:
        """Convert to MT5 API format"""
        pass
```

**Position**
```python
@dataclass
class Position:
    ticket: int          # Position ID
    symbol: str
    type: str           # "BUY" or "SELL"
    volume: float       # Lot size
    price_open: float
    price_current: float
    sl: float           # Stop Loss
    tp: float           # Take Profit
    profit: float       # Current P&L in account currency
    swap: float         # Swap charges
    commission: float   # Broker commission
    magic: int
    comment: str
    time_open: datetime
    time_update: datetime
    
    @property
    def pnl_pips(self) -> float:
        """Calculate P&L in pips"""
        pass
    
    @property
    def duration(self) -> timedelta:
        """How long position has been open"""
        pass
```

**Order**
```python
@dataclass
class Order:
    ticket: int
    symbol: str
    type: str              # "BUY_LIMIT", "SELL_STOP", etc.
    volume: float
    price_open: float      # Trigger price
    price_current: float   # Current market price
    sl: float
    tp: float
    time_setup: datetime
    time_expiration: datetime
    comment: str
    state: str            # "STARTED", "PLACED", "CANCELED", "PARTIAL", "FILLED"
```

**Trade Result**
```python
@dataclass
class TradeResult:
    success: bool
    order_ticket: int = None
    deal_ticket: int = None
    volume: float = None
    price: float = None
    bid: float = None
    ask: float = None
    comment: str = ""
    request_id: int = None
    retcode: int = None    # MT5 return code
    error_message: str = ""
    
    @classmethod
    def from_mt5_result(cls, result) -> 'TradeResult':
        """Convert MT5 OrderSendResult to TradeResult"""
        pass
```

### 3. Account Models

**Account Information**
```python
@dataclass
class AccountInfo:
    login: int
    server: str
    name: str
    company: str
    currency: str         # "USD", "EUR", etc.
    balance: float
    equity: float
    profit: float         # Total unrealized profit
    margin: float         # Used margin
    margin_free: float    # Available margin
    margin_level: float   # (Equity / Margin) * 100
    leverage: int         # e.g., 100 (1:100)
    trade_allowed: bool
    trade_expert: bool    # EA trading allowed
    limit_orders: int     # Max pending orders
    
    @property
    def margin_used_percent(self) -> float:
        """Percentage of margin used"""
        return (self.margin / self.equity) * 100 if self.equity > 0 else 0
    
    @property
    def available_for_trading(self) -> float:
        """How much money available for new positions"""
        return self.margin_free
```

### 4. Strategy Models

**Trading Signal**
```python
@dataclass
class TradingSignal:
    symbol: str
    action: str          # "BUY", "SELL", "HOLD", "CLOSE"
    confidence: float    # 0.0 to 1.0
    entry_price: float = None
    sl: float = None
    tp: float = None
    volume: float = None
    reasoning: str = ""  # Why this signal was generated
    indicators: Dict[str, Any] = None  # Supporting indicator values
    timestamp: datetime = None
    source: str = ""     # "RSI_Strategy", "LSTM_Model", "LLM_Analysis", etc.
```

**Strategy Configuration**
```python
@dataclass
class StrategyConfig:
    name: str
    enabled: bool
    symbols: List[str]
    timeframe: str
    parameters: Dict[str, Any]
    risk_per_trade: float     # Percentage of account
    max_positions: int
    trading_hours: Dict[str, Any]  # e.g., {"start": "08:00", "end": "17:00"}
```

**Backtest Result**
```python
@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    period_start: datetime
    period_end: datetime
    initial_balance: float
    final_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    profit_factor: float      # Gross Profit / Gross Loss
    max_drawdown: float       # Maximum peak-to-trough decline
    max_drawdown_percent: float
    sharpe_ratio: float
    sortino_ratio: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    average_trade_duration: timedelta
    trades: List[Dict]        # Individual trade details
    equity_curve: List[Tuple[datetime, float]]
```

### 5. AI/ML Models

**Model Prediction**
```python
@dataclass
class ModelPrediction:
    model_name: str
    model_version: str
    symbol: str
    prediction_type: str  # "price", "direction", "volatility"
    predicted_value: Any
    confidence: float     # Model confidence score
    features_used: Dict[str, float]
    timestamp: datetime
    horizon: str         # "5min", "1hour", "1day"
```

**Feature Set**
```python
@dataclass
class FeatureSet:
    symbol: str
    timestamp: datetime
    price_features: Dict[str, float]  # OHLC, returns, etc.
    technical_indicators: Dict[str, float]  # RSI, MACD, etc.
    statistical_features: Dict[str, float]  # std, skew, kurtosis
    temporal_features: Dict[str, int]      # hour, day_of_week, etc.
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array for ML model input"""
        pass
    
    @classmethod
    def from_market_data(cls, data: pd.DataFrame) -> 'FeatureSet':
        """Generate features from market data"""
        pass
```

---

## Database Schema (PostgreSQL)

### Trades Table
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    ticket BIGINT UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(10) NOT NULL,  -- BUY, SELL
    volume DECIMAL(10, 2) NOT NULL,
    price_open DECIMAL(10, 5) NOT NULL,
    price_close DECIMAL(10, 5),
    sl DECIMAL(10, 5),
    tp DECIMAL(10, 5),
    profit DECIMAL(10, 2),
    swap DECIMAL(10, 2),
    commission DECIMAL(10, 2),
    magic_number INTEGER,
    comment TEXT,
    time_open TIMESTAMP NOT NULL,
    time_close TIMESTAMP,
    duration_seconds INTEGER,
    strategy_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_time ON trades(time_open);
CREATE INDEX idx_trades_strategy ON trades(strategy_name);
```

### Signals Table
```sql
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,  -- BUY, SELL, HOLD
    confidence DECIMAL(5, 4) NOT NULL,
    source VARCHAR(50) NOT NULL,  -- Strategy/model name
    reasoning TEXT,
    indicators JSONB,             -- Store indicator values
    executed BOOLEAN DEFAULT FALSE,
    trade_ticket BIGINT REFERENCES trades(ticket),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_created ON signals(created_at);
```

### Performance Metrics Table
```sql
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    strategy_name VARCHAR(50),
    symbol VARCHAR(20),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    total_profit DECIMAL(10, 2),
    total_loss DECIMAL(10, 2),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, strategy_name, symbol)
);
```

### Market Data Cache (Optional - for faster backtesting)
```sql
CREATE TABLE ohlc_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    time TIMESTAMP NOT NULL,
    open DECIMAL(10, 5) NOT NULL,
    high DECIMAL(10, 5) NOT NULL,
    low DECIMAL(10, 5) NOT NULL,
    close DECIMAL(10, 5) NOT NULL,
    volume BIGINT,
    UNIQUE(symbol, timeframe, time)
);

CREATE INDEX idx_ohlc_symbol_time ON ohlc_data(symbol, timeframe, time);
```

---

## Configuration Files

### config/mt5_config.yaml
```yaml
mt5:
  connection:
    timeout: 60000
    retry_attempts: 3
    retry_delay: 5
  
  trading:
    default_lot: 0.01
    max_lot: 1.0
    magic_number: 234000
    slippage: 20
    
  symbols:
    forex:
      - EURUSD
      - GBPUSD
      - USDJPY
      - AUDUSD
      - USDCAD
      - EURJPY
      - GBPJPY
    
  timeframes:
    - M1
    - M5
    - M15
    - H1
    - D1
```

### config/strategy_config.yaml
```yaml
strategies:
  rsi_strategy:
    enabled: true
    symbols: [EURUSD, GBPUSD]
    timeframe: H1
    parameters:
      rsi_period: 14
      oversold: 30
      overbought: 70
      volume: 0.01
    risk:
      max_positions: 2
      risk_per_trade: 0.02
  
  macd_strategy:
    enabled: false
    symbols: [USDJPY]
    timeframe: M15
    parameters:
      fast_period: 12
      slow_period: 26
      signal_period: 9
      volume: 0.01
```

### config/ai_config.yaml
```yaml
models:
  lstm_predictor:
    enabled: false
    model_path: data/models/lstm/v1.0.0
    input_sequence_length: 60
    prediction_horizon: 5
    confidence_threshold: 0.7
  
  sentiment_analyzer:
    enabled: false
    api_key_env: OPENAI_API_KEY
    model: gpt-4
    update_interval: 3600  # seconds

risk_management:
  max_daily_loss: 100.0     # Account currency
  max_daily_trades: 20
  max_positions_total: 5
  max_positions_per_symbol: 1
  emergency_stop_loss: 500.0
```

---

## API Endpoints (Future - FastAPI)

### Trading Endpoints

```python
POST /api/v1/trade/open
Body: {
    "symbol": "EURUSD",
    "action": "BUY",
    "volume": 0.01,
    "sl": 1.0850,
    "tp": 1.0950
}
Response: TradeResult

POST /api/v1/trade/close
Body: {"ticket": 123456}
Response: TradeResult

GET /api/v1/positions
Response: List[Position]

GET /api/v1/account
Response: AccountInfo
```

### Market Data Endpoints

```python
GET /api/v1/symbols
Response: List[SymbolInfo]

GET /api/v1/price/{symbol}
Response: TickData

GET /api/v1/ohlc/{symbol}?timeframe=H1&count=100
Response: List[OHLCBar]
```

### Strategy Endpoints

```python
GET /api/v1/strategies
Response: List[StrategyConfig]

POST /api/v1/strategies/{name}/enable
Response: {"success": true}

GET /api/v1/signals?symbol=EURUSD
Response: List[TradingSignal]
```

### AI/ML Endpoints

```python
POST /api/v1/ai/predict
Body: {
    "symbol": "EURUSD",
    "model": "lstm_predictor"
}
Response: ModelPrediction

POST /api/v1/ai/analyze
Body: {
    "symbol": "EURUSD",
    "analysis_type": "sentiment"
}
Response: {"sentiment": "bullish", "confidence": 0.75}
```

---

## Error Codes

### Application Error Codes
```python
class ErrorCode:
    # Connection errors (1000-1099)
    MT5_NOT_INITIALIZED = 1000
    MT5_CONNECTION_FAILED = 1001
    MT5_AUTHENTICATION_FAILED = 1002
    MT5_CONNECTION_LOST = 1003
    
    # Trading errors (1100-1199)
    INVALID_SYMBOL = 1100
    INVALID_VOLUME = 1101
    INSUFFICIENT_MARGIN = 1102
    MARKET_CLOSED = 1103
    TRADE_DISABLED = 1104
    INVALID_PRICE = 1105
    INVALID_STOPS = 1106
    
    # Strategy errors (1200-1299)
    STRATEGY_NOT_FOUND = 1200
    STRATEGY_DISABLED = 1201
    INVALID_PARAMETERS = 1202
    
    # Risk management errors (1300-1399)
    MAX_POSITIONS_REACHED = 1300
    DAILY_LOSS_LIMIT = 1301
    RISK_TOO_HIGH = 1302
    
    # AI/ML errors (1400-1499)
    MODEL_NOT_LOADED = 1400
    PREDICTION_FAILED = 1401
    INSUFFICIENT_DATA = 1402
```

---

## Logging Format

### Structured JSON Logging
```json
{
    "timestamp": "2024-03-15T14:30:45.123Z",
    "level": "INFO",
    "module": "trading.controller",
    "function": "execute_trade",
    "message": "Trade executed successfully",
    "data": {
        "symbol": "EURUSD",
        "action": "BUY",
        "volume": 0.01,
        "ticket": 123456,
        "price": 1.0895
    },
    "user_id": null,
    "request_id": "abc-123-def"
}
```

---

## Security Best Practices

1. **Credential Storage**: Use environment variables or secure vault (never commit to Git)
2. **API Keys**: Encrypt sensitive keys at rest
3. **Database**: Use prepared statements to prevent SQL injection
4. **API**: Implement rate limiting and authentication (JWT tokens)
5. **Logs**: Never log passwords or API keys
6. **Backups**: Regular encrypted backups of database
7. **Updates**: Keep all dependencies updated for security patches

---

## Performance Benchmarks

**Expected Performance (Phase 1)**:
- MT5 connection time: < 5 seconds
- Market data retrieval (100 bars): < 1 second
- Order execution: < 2 seconds
- Position query: < 500ms

**Expected Performance (Phase 3 - ML)**:
- Feature generation: < 100ms
- Model inference: < 200ms
- End-to-end signal generation: < 500ms

**Expected Performance (Phase 5 - Web)**:
- API response time: < 200ms
- WebSocket update latency: < 50ms
- Dashboard load time: < 2 seconds

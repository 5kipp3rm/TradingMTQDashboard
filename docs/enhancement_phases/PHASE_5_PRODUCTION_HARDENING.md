# Phase 5: Production Hardening & Monitoring

**Duration:** 2-3 weeks
**Difficulty:** Intermediate
**Focus:** Make the system production-ready with better observability

---

## Overview

This phase focuses on making the trading system enterprise-ready with:
- Advanced logging and monitoring
- Database integration for trade history
- Error recovery and resilience
- Performance tracking

---

## 5.1 Advanced Logging & Monitoring

### Skills to Learn:
- Structured logging with JSON
- Performance metrics collection
- Real-time monitoring
- Log aggregation

### Tasks Checklist:

- [ ] **Structured Logging with JSON**
  - [ ] Replace print statements with structured logging
  - [ ] Add correlation IDs for trade tracking
  - [ ] Implement log levels (DEBUG, INFO, WARNING, ERROR)
  - [ ] Add request/response logging for all API calls

- [ ] **Performance Metrics Collection**
  - [ ] Track execution time per cycle
  - [ ] Monitor API latency to MT5
  - [ ] Record memory usage
  - [ ] Track CPU usage

- [ ] **Real-time Dashboard Data**
  - [ ] Export metrics to JSON/CSV for visualization
  - [ ] Create Prometheus-compatible metrics endpoint
  - [ ] Daily performance summaries
  - [ ] Historical metrics storage

### Files to Create:

```
src/monitoring/
├── __init__.py
├── metrics_collector.py      # Collect system metrics
├── performance_tracker.py    # Track trade performance
└── alerts.py                 # Alert system for errors

src/utils/logger.py           # Enhanced structured logging
```

### Implementation:

#### 1. Metrics Collector

```python
# src/monitoring/metrics_collector.py
from dataclasses import dataclass
from typing import Dict, List
import time
from datetime import datetime
import psutil
import MetaTrader5 as mt5

@dataclass
class PerformanceMetrics:
    cycle_time_ms: float
    trades_executed: int
    signals_generated: int
    api_latency_ms: float
    memory_mb: float
    cpu_percent: float
    timestamp: datetime

class MetricsCollector:
    """Collect and track system performance metrics"""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.process = psutil.Process()

    def record_cycle(self, start_time: float, trades: int, signals: int):
        """Record metrics for a trading cycle"""
        cycle_time = (time.time() - start_time) * 1000

        self.metrics.append(PerformanceMetrics(
            cycle_time_ms=cycle_time,
            trades_executed=trades,
            signals_generated=signals,
            api_latency_ms=self._measure_api_latency(),
            memory_mb=self._get_memory_usage(),
            cpu_percent=self.process.cpu_percent(),
            timestamp=datetime.now()
        ))

    def _measure_api_latency(self) -> float:
        """Measure MT5 API response time"""
        start = time.time()
        try:
            mt5.symbol_info_tick("EURUSD")
            return (time.time() - start) * 1000
        except:
            return 0.0

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024

    def export_to_json(self, filepath: str):
        """Export metrics for analysis"""
        import json
        with open(filepath, 'w') as f:
            json.dump([{
                'cycle_time_ms': m.cycle_time_ms,
                'trades_executed': m.trades_executed,
                'signals_generated': m.signals_generated,
                'api_latency_ms': m.api_latency_ms,
                'memory_mb': m.memory_mb,
                'cpu_percent': m.cpu_percent,
                'timestamp': m.timestamp.isoformat()
            } for m in self.metrics], f, indent=2)

    def get_summary(self) -> Dict[str, float]:
        """Get statistical summary"""
        if not self.metrics:
            return {}

        import numpy as np
        return {
            'avg_cycle_time_ms': np.mean([m.cycle_time_ms for m in self.metrics]),
            'max_cycle_time_ms': np.max([m.cycle_time_ms for m in self.metrics]),
            'avg_api_latency_ms': np.mean([m.api_latency_ms for m in self.metrics]),
            'avg_memory_mb': np.mean([m.memory_mb for m in self.metrics]),
            'avg_cpu_percent': np.mean([m.cpu_percent for m in self.metrics]),
            'total_trades': sum(m.trades_executed for m in self.metrics)
        }
```

#### 2. Structured Logger

```python
# src/utils/logger.py (Enhanced)
import logging
import json
from datetime import datetime
from typing import Dict, Any
import uuid

class StructuredLogger:
    """JSON structured logger for better log analysis"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.correlation_id = None

    def set_correlation_id(self, correlation_id: str = None):
        """Set correlation ID for request tracking"""
        self.correlation_id = correlation_id or str(uuid.uuid4())

    def _format_message(self, level: str, message: str,
                       extra: Dict[str, Any] = None) -> str:
        """Format message as JSON"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'correlation_id': self.correlation_id
        }

        if extra:
            log_entry.update(extra)

        return json.dumps(log_entry)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(self._format_message('INFO', message, kwargs))

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(self._format_message('ERROR', message, kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(self._format_message('WARNING', message, kwargs))

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(self._format_message('DEBUG', message, kwargs))

# Usage example
logger = StructuredLogger('trading_bot')
logger.set_correlation_id()
logger.info("Trade executed", symbol="EURUSD", ticket=12345, profit=25.50)
```

#### 3. Performance Tracker

```python
# src/monitoring/performance_tracker.py
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

class PerformanceTracker:
    """Track trading performance metrics"""

    def __init__(self):
        self.trades_by_symbol = defaultdict(list)
        self.trades_by_strategy = defaultdict(list)
        self.daily_stats = {}

    def record_trade(self, trade: Dict):
        """Record a trade for analysis"""
        symbol = trade['symbol']
        strategy = trade.get('strategy', 'unknown')

        self.trades_by_symbol[symbol].append(trade)
        self.trades_by_strategy[strategy].append(trade)

        # Update daily stats
        date = trade['entry_time'].date()
        if date not in self.daily_stats:
            self.daily_stats[date] = {
                'trades': 0,
                'profit': 0.0,
                'winners': 0,
                'losers': 0
            }

        self.daily_stats[date]['trades'] += 1
        self.daily_stats[date]['profit'] += trade.get('profit', 0)

        if trade.get('profit', 0) > 0:
            self.daily_stats[date]['winners'] += 1
        else:
            self.daily_stats[date]['losers'] += 1

    def get_symbol_performance(self, symbol: str) -> Dict:
        """Get performance for specific symbol"""
        trades = self.trades_by_symbol.get(symbol, [])

        if not trades:
            return {'error': 'No trades found'}

        total_profit = sum(t.get('profit', 0) for t in trades)
        winners = sum(1 for t in trades if t.get('profit', 0) > 0)

        return {
            'symbol': symbol,
            'total_trades': len(trades),
            'total_profit': total_profit,
            'win_rate': (winners / len(trades) * 100) if trades else 0,
            'avg_profit': total_profit / len(trades) if trades else 0
        }

    def get_daily_report(self, date: datetime.date = None) -> Dict:
        """Get daily performance report"""
        date = date or datetime.now().date()
        return self.daily_stats.get(date, {
            'trades': 0,
            'profit': 0.0,
            'winners': 0,
            'losers': 0
        })
```

---

## 5.2 Database Integration

### Skills to Learn:
- SQLAlchemy ORM
- Database design
- Query optimization
- Migrations

### Tasks Checklist:

- [ ] **SQLite/PostgreSQL Setup**
  - [ ] Install SQLAlchemy
  - [ ] Design database schema
  - [ ] Create models for trades, signals, performance
  - [ ] Set up connection pooling

- [ ] **Trade History Storage**
  - [ ] Store all executed trades
  - [ ] Position history tracking
  - [ ] Signal history for analysis
  - [ ] Account snapshots

- [ ] **Performance Analytics Queries**
  - [ ] Win rate by strategy
  - [ ] Profit by currency pair
  - [ ] Time-based performance analysis
  - [ ] Correlation analysis

### Files to Create:

```
src/database/
├── __init__.py
├── models.py                 # SQLAlchemy models
├── repository.py             # Data access layer
└── migrations/               # Database schema versions
    └── v1_initial.sql

src/analysis/
└── performance_analyzer.py   # Query & analyze stored data
```

### Implementation:

#### 1. Database Models

```python
# src/database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    ticket = Column(Integer, unique=True, index=True)
    symbol = Column(String(20), index=True)
    direction = Column(String(10))  # BUY/SELL
    volume = Column(Float)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    entry_time = Column(DateTime, index=True)
    exit_time = Column(DateTime, nullable=True)
    profit = Column(Float, nullable=True)
    profit_pips = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    strategy_name = Column(String(50), index=True)
    ml_confidence = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    is_closed = Column(Boolean, default=False)

    # Relationship to signal
    signal_id = Column(Integer, ForeignKey('signals.id'), nullable=True)
    signal = relationship("Signal", back_populates="trade")

class Signal(Base):
    __tablename__ = 'signals'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
    signal_type = Column(String(10))  # BUY/SELL/HOLD
    confidence = Column(Float)
    price = Column(Float)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    timestamp = Column(DateTime, index=True)
    strategy_name = Column(String(50))
    executed = Column(Boolean, default=False)
    reason = Column(String(500))

    # Relationship to trade
    trade = relationship("Trade", back_populates="signal", uselist=False)

class DailyPerformance(Base):
    __tablename__ = 'daily_performance'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True, index=True)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    total_profit = Column(Float)
    total_profit_pips = Column(Float)
    win_rate = Column(Float)
    largest_win = Column(Float)
    largest_loss = Column(Float)
    max_drawdown = Column(Float)
    end_balance = Column(Float)
    end_equity = Column(Float)

class AccountSnapshot(Base):
    __tablename__ = 'account_snapshots'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True)
    balance = Column(Float)
    equity = Column(Float)
    profit = Column(Float)
    margin = Column(Float)
    margin_free = Column(Float)
    margin_level = Column(Float)
    open_positions = Column(Integer)
```

#### 2. Repository Pattern

```python
# src/database/repository.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from datetime import datetime, timedelta
from .models import Base, Trade, Signal, DailyPerformance

class TradeRepository:
    """Data access layer for trading data"""

    def __init__(self, database_url: str = "sqlite:///trading.db"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def save_trade(self, trade_data: dict) -> Trade:
        """Save a new trade to database"""
        with self.SessionLocal() as session:
            trade = Trade(**trade_data)
            session.add(trade)
            session.commit()
            session.refresh(trade)
            return trade

    def update_trade_exit(self, ticket: int, exit_price: float,
                         exit_time: datetime, profit: float, profit_pips: float):
        """Update trade when closed"""
        with self.SessionLocal() as session:
            trade = session.query(Trade).filter_by(ticket=ticket).first()
            if trade:
                trade.exit_price = exit_price
                trade.exit_time = exit_time
                trade.profit = profit
                trade.profit_pips = profit_pips
                trade.is_closed = True
                session.commit()

    def get_trades_by_date_range(self, start_date: datetime,
                                  end_date: datetime) -> List[Trade]:
        """Get trades within date range"""
        with self.SessionLocal() as session:
            return session.query(Trade).filter(
                Trade.entry_time >= start_date,
                Trade.entry_time <= end_date
            ).all()

    def get_open_trades(self) -> List[Trade]:
        """Get all open trades"""
        with self.SessionLocal() as session:
            return session.query(Trade).filter_by(is_closed=False).all()

    def get_performance_by_strategy(self) -> List[dict]:
        """Get performance metrics grouped by strategy"""
        with self.SessionLocal() as session:
            from sqlalchemy import func

            results = session.query(
                Trade.strategy_name,
                func.count(Trade.id).label('total'),
                func.sum(Trade.profit).label('total_profit'),
                func.avg(Trade.profit).label('avg_profit'),
                func.count(Trade.id).filter(Trade.profit > 0).label('winners')
            ).filter(Trade.is_closed == True).group_by(
                Trade.strategy_name
            ).all()

            return [{
                'strategy': r.strategy_name,
                'total_trades': r.total,
                'total_profit': r.total_profit or 0,
                'avg_profit': r.avg_profit or 0,
                'win_rate': (r.winners / r.total * 100) if r.total > 0 else 0
            } for r in results]

    def get_performance_by_symbol(self) -> List[dict]:
        """Get performance metrics grouped by symbol"""
        with self.SessionLocal() as session:
            from sqlalchemy import func

            results = session.query(
                Trade.symbol,
                func.count(Trade.id).label('total'),
                func.sum(Trade.profit).label('total_profit'),
                func.sum(Trade.profit_pips).label('total_pips')
            ).filter(Trade.is_closed == True).group_by(
                Trade.symbol
            ).all()

            return [{
                'symbol': r.symbol,
                'total_trades': r.total,
                'total_profit': r.total_profit or 0,
                'total_pips': r.total_pips or 0
            } for r in results]
```

---

## 5.3 Error Recovery & Resilience

### Skills to Learn:
- Circuit breaker pattern
- Retry logic with exponential backoff
- Health check systems
- Graceful degradation

### Tasks Checklist:

- [ ] **Automatic Reconnection**
  - [ ] Detect MT5 disconnections
  - [ ] Auto-reconnect with exponential backoff
  - [ ] Queue orders during disconnection
  - [ ] Replay queued orders after reconnection

- [ ] **Circuit Breaker Pattern**
  - [ ] Stop trading after consecutive failures
  - [ ] Gradual recovery mode (half-open state)
  - [ ] Automatic reset after timeout
  - [ ] Alert on circuit breaker activation

- [ ] **Health Check System**
  - [ ] System status API endpoint
  - [ ] Check connector health
  - [ ] Verify strategy availability
  - [ ] Monitor resource usage

### Files to Create:

```
src/resilience/
├── __init__.py
├── circuit_breaker.py        # Circuit breaker implementation
├── retry_handler.py          # Retry logic with backoff
└── health_check.py           # System health monitoring
```

### Implementation:

#### 1. Circuit Breaker

```python
# src/resilience/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "CLOSED"          # Normal operation
    OPEN = "OPEN"              # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"    # Testing if recovered

class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance

    Prevents cascading failures by stopping requests to failing services
    """

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            print(f"✅ Circuit breaker CLOSED - service recovered")

    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"🚨 Circuit breaker OPEN - {self.failure_count} consecutive failures")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to attempt recovery"""
        return (self.last_failure_time and
                datetime.now() - self.last_failure_time >
                timedelta(seconds=self.recovery_timeout))

# Usage example
trade_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=300  # 5 minutes
)

def execute_trade_with_protection(symbol, action, volume):
    """Execute trade with circuit breaker protection"""
    return trade_circuit_breaker.call(
        connector.send_order,
        TradeRequest(symbol=symbol, action=action, volume=volume)
    )
```

#### 2. Retry Handler

```python
# src/resilience/retry_handler.py
import time
from typing import Callable, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class RetryHandler:
    """Retry failed operations with exponential backoff"""

    @staticmethod
    def retry(max_attempts: int = 3,
              delay: float = 1.0,
              backoff: float = 2.0,
              exceptions: tuple = (Exception,)):
        """
        Decorator for retrying functions

        Args:
            max_attempts: Maximum retry attempts
            delay: Initial delay between retries (seconds)
            backoff: Multiplier for delay after each retry
            exceptions: Tuple of exceptions to catch
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                current_delay = delay

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        if attempt == max_attempts - 1:
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                            raise e

                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}"
                        )
                        logger.info(f"Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff

                return None

            return wrapper
        return decorator

# Usage example
@RetryHandler.retry(max_attempts=3, delay=2.0, backoff=2.0)
def connect_to_mt5(login, password, server):
    """Connect to MT5 with automatic retry"""
    if not mt5.initialize(login=login, password=password, server=server):
        raise ConnectionError(f"MT5 connection failed: {mt5.last_error()}")
    return True
```

---

## Integration with Main System

### Update main.py:

```python
# Add to main.py
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.performance_tracker import PerformanceTracker
from src.database.repository import TradeRepository
from src.resilience.circuit_breaker import CircuitBreaker

# Initialize components
metrics = MetricsCollector()
performance = PerformanceTracker()
db = TradeRepository()
circuit_breaker = CircuitBreaker()

# In trading loop:
cycle_start = time.time()

# ... trading logic ...

# Record metrics
metrics.record_cycle(cycle_start, trades_executed, signals_generated)

# Save trade to database
if trade_result.success:
    db.save_trade({
        'ticket': trade_result.order_ticket,
        'symbol': symbol,
        'direction': action.value,
        'volume': volume,
        'entry_price': trade_result.price,
        'entry_time': datetime.now(),
        'strategy_name': strategy.name
    })

# Export metrics every hour
if cycle_count % 120 == 0:  # Every 2 hours at 30s cycles
    metrics.export_to_json('logs/metrics.json')
    summary = metrics.get_summary()
    print(f"Performance Summary: {summary}")
```

---

## Testing Checklist

- [ ] Test metrics collection over 24 hours
- [ ] Verify database saves all trades correctly
- [ ] Test circuit breaker with simulated failures
- [ ] Verify retry logic works with MT5 disconnection
- [ ] Check memory usage doesn't grow over time
- [ ] Validate structured logs are parseable
- [ ] Test health check endpoint
- [ ] Verify performance queries are fast (<100ms)

---

## Expected Outcomes

After completing Phase 5, you will have:

1. **Full Observability**
   - JSON structured logs for easy analysis
   - Performance metrics exported every hour
   - Real-time monitoring of system health

2. **Persistent Storage**
   - All trades stored in database
   - Historical performance analysis
   - Queryable trade history

3. **Production Resilience**
   - Automatic reconnection on failures
   - Circuit breaker prevents cascading failures
   - Graceful degradation under load

4. **Better Debugging**
   - Correlation IDs track requests
   - Detailed error messages
   - Performance bottleneck identification

---

## Next Steps

After Phase 5, proceed to:
- **Phase 6:** Advanced Analytics & Reporting
- **Phase 7:** Web Dashboard & REST API

Or jump to any phase that interests you!

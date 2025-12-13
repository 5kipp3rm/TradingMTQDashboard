# TradingMTQ Database Layer

## Overview

The database layer provides persistent storage for trading operations using SQLAlchemy ORM, Alembic migrations, and the Repository pattern.

**Phase 0 Patterns:**
- Custom exceptions (DatabaseError, ConnectionError)
- Structured JSON logging with correlation IDs
- Error handler decorators with automatic retry
- Type-safe models and operations

## Database Models

### Trade
Complete trade lifecycle tracking from signal to closure.

**Key Fields:**
- `ticket`: MT5 ticket number (unique)
- `symbol`: Trading pair (e.g., "EURUSD")
- `trade_type`: BUY, SELL, HOLD
- `status`: PENDING, OPEN, CLOSED, CANCELLED, FAILED
- `entry_price`, `entry_time`, `volume`
- `stop_loss`, `take_profit`
- `exit_price`, `exit_time`, `profit`
- `ml_enhanced`, `ai_approved`: ML/AI flags

### Signal
All generated trading signals (executed or not).

**Key Fields:**
- `symbol`, `signal_type`, `timestamp`
- `price`, `stop_loss`, `take_profit`
- `confidence`: Signal quality (0.0-1.0)
- `strategy_name`, `timeframe`
- `ml_enhanced`, `ml_confidence`
- `executed`: Whether signal was acted upon
- `trade_id`: Foreign key to Trade (if executed)

### AccountSnapshot
Periodic snapshots of account balance and equity.

**Key Fields:**
- `account_number`, `server`, `broker`
- `balance`, `equity`, `profit`
- `margin`, `margin_free`, `margin_level`
- `open_positions`, `total_volume`
- `snapshot_time`: When snapshot was taken

### DailyPerformance
Aggregated daily trading statistics.

**Key Fields:**
- `date`: Trading date (unique)
- `total_trades`, `winning_trades`, `losing_trades`
- `gross_profit`, `gross_loss`, `net_profit`
- `win_rate`, `profit_factor`
- `average_win`, `average_loss`
- `end_balance`, `end_equity`

## Repository Pattern

### TradeRepository

```python
from src.database.repository import TradeRepository
from src.database.connection import get_session

repo = TradeRepository()

# Create trade
with get_session() as session:
    trade = repo.create(
        session,
        ticket=123456,
        symbol="EURUSD",
        trade_type="buy",
        entry_price=1.0850,
        entry_time=datetime.now(),
        volume=0.1,
        status="open"
    )

# Update on close
with get_session() as session:
    trade = repo.update_on_close(
        session,
        ticket=123456,
        exit_price=1.0900,
        exit_time=datetime.now(),
        profit=50.00
    )

# Get statistics
with get_session() as session:
    stats = repo.get_trade_statistics(session)
    print(f"Win rate: {stats['win_rate']:.2f}%")
```

### SignalRepository

```python
from src.database.repository import SignalRepository

repo = SignalRepository()

# Create signal
with get_session() as session:
    signal = repo.create(
        session,
        symbol="EURUSD",
        signal_type="buy",
        timestamp=datetime.now(),
        price=1.0850,
        confidence=0.85,
        strategy_name="MovingAverageCrossover",
        timeframe="H1"
    )

# Mark as executed
with get_session() as session:
    signal = repo.mark_executed(
        session,
        signal_id=signal.id,
        trade_id=trade.id,
        execution_reason="High confidence signal"
    )
```

## Database Configuration

### Environment Variable (Recommended for Production)

```bash
export TRADING_MTQ_DATABASE_URL="postgresql://user:password@localhost:5432/tradingmtq"
```

### alembic.ini (Development Default)

```ini
sqlalchemy.url = sqlite:///./tradingmtq.db
```

### Programmatic Configuration

```python
from src.database.connection import init_db

# Initialize with custom URL
engine = init_db(
    database_url="postgresql://user:password@localhost:5432/tradingmtq",
    echo=True  # Enable SQL logging
)
```

## Database Migrations

### Using Python API

```python
from src.database.migration_utils import (
    initialize_database,
    upgrade_database,
    downgrade_database,
    get_current_revision
)

# Initialize database (applies all migrations)
initialize_database()

# Upgrade to latest
upgrade_database()

# Downgrade one revision
downgrade_database(revision="-1")

# Check current revision
revision = get_current_revision()
print(f"Current: {revision}")
```

### Using CLI Script

```bash
# Initialize database
python src/database/migration_utils.py init

# Upgrade to latest
python src/database/migration_utils.py upgrade

# Downgrade one revision
python src/database/migration_utils.py downgrade --revision -1

# Check current revision
python src/database/migration_utils.py current

# Create new migration
python src/database/migration_utils.py create --message "Add new column"
```

### Using Alembic Directly

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Create new migration (auto-generate from model changes)
alembic revision --autogenerate -m "Add new column"

# Create empty migration
alembic revision -m "Custom migration"

# Show current revision
alembic current

# Show migration history
alembic history
```

## Connection Management

### Connection Pooling

The database layer uses SQLAlchemy's QueuePool for efficient connection management:

```python
# Configured in connection.py
pool_size=5          # Maintain 5 connections
max_overflow=10      # Allow 10 additional connections
pool_pre_ping=True   # Health check before using connection
pool_recycle=3600    # Recycle connections after 1 hour
```

### Session Management

Always use context manager for automatic commit/rollback:

```python
from src.database.connection import get_session

# Recommended pattern
with get_session() as session:
    # Operations here
    trade = repo.create(session, ...)
    # Automatic commit on success
    # Automatic rollback on exception
```

### Health Checks

```python
from src.database.connection import check_db_health

# Returns True if database is healthy
if check_db_health():
    print("Database is healthy")
else:
    print("Database connection issues")
```

## Error Handling

All database operations use Phase 0 error handling:

```python
from src.exceptions import DatabaseError, ConnectionError

try:
    with get_session() as session:
        trade = repo.create(session, ...)
except DatabaseError as e:
    # Handle database errors
    logger.error("Database error", error=str(e), context=e.context)
except ConnectionError as e:
    # Handle connection errors (automatic retry already attempted)
    logger.error("Connection error", error=str(e), context=e.context)
```

## Logging

All database operations include structured logging:

```json
{
  "timestamp": "2025-12-13T11:49:25Z",
  "level": "INFO",
  "correlation_id": "a1b2c3",
  "message": "Trade created",
  "trade_id": 1,
  "symbol": "EURUSD",
  "trade_type": "buy"
}
```

## Testing

### SQLite for Development

```python
# Uses in-memory database for tests
engine = init_db("sqlite:///:memory:")
```

### PostgreSQL for Production

```bash
# Set environment variable
export TRADING_MTQ_DATABASE_URL="postgresql://user:password@localhost:5432/tradingmtq"

# Initialize and run
python src/main.py
```

## Best Practices

1. **Always use repositories** - Never query models directly
2. **Use context managers** - Ensures proper session cleanup
3. **Check health** - Verify database connectivity before critical operations
4. **Log everything** - Structured logging already built in
5. **Handle errors** - Custom exceptions provide rich context
6. **Test migrations** - Always test downgrade paths
7. **Use connection pooling** - Already configured for production

## Migration History

### 001_initial_schema (2025-12-13)
- Created trades table with all trade lifecycle fields
- Created signals table with strategy and ML features
- Created account_snapshots table for balance tracking
- Created daily_performance table for aggregated statistics
- Added all indexes and foreign keys
- Supports both PostgreSQL and SQLite

## Next Steps

1. **Phase 5.1 Integration**: Wire up CurrencyTrader and Orchestrator to save data
2. **Performance Monitoring**: Track query performance and optimize as needed
3. **Backup Strategy**: Implement automated database backups
4. **Data Retention**: Define policies for archiving old data

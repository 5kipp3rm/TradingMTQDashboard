# Unified Logger Migration Guide

## Overview

The new `unified_logger.py` consolidates both `structured_logger.py` and `logger.py` into a single OOP-based logging system that provides:

✅ **JSON structured logging** (for production/monitoring tools)
✅ **Colored console output** (for development/debugging)
✅ **Correlation ID tracking** (thread-safe with ContextVar)
✅ **Multiple output formats** (JSON, Colored, Plain)
✅ **Multiple log files** (main, errors, trades)
✅ **Helper methods** (trade, signal, connection, etc.)
✅ **Backward compatibility** (drop-in replacement)

## Quick Start

### 1. Configure at Application Startup

**File**: `src/api/app.py`

```python
# OLD (logger.py)
from src.utils.logger import setup_logging
setup_logging(log_dir="logs", log_level="INFO", console_output=True, file_output=True)

# NEW (unified_logger.py)
from src.utils.unified_logger import UnifiedLogger, OutputFormat
UnifiedLogger.configure(
    log_dir="logs",
    log_level="INFO",
    console_output=True,
    console_format=OutputFormat.COLORED,  # Colored console for dev
    file_output=True,
    file_format=OutputFormat.JSON          # JSON files for production
)
```

### 2. Get Logger Instance

```python
# OLD (both logger.py and structured_logger.py)
from src.utils.logger import get_logger
# OR
from src.utils.structured_logger import StructuredLogger

logger = get_logger(__name__)
# OR
logger = StructuredLogger(__name__)

# NEW (unified_logger.py) - Works with both patterns!
from src.utils.unified_logger import UnifiedLogger

logger = UnifiedLogger.get_logger(__name__)
```

### 3. Use Logger

```python
# Simple logging (works with all three systems)
logger.info("Processing started")

# With structured fields (NEW unified approach)
logger.info("Trade executed", symbol="EURUSD", action="BUY", volume=0.1)

# With correlation tracking (NEW unified approach)
from src.utils.unified_logger import LogContext

with LogContext() as ctx:
    logger.info("Starting operation", operation_id=123)
    # All logs within this context will have same correlation_id
```

## Migration Steps

### Step 1: Update Application Startup

**File**: `src/api/app.py` (Line 42)

```python
# BEFORE
from src.utils.logger import setup_logging
setup_logging(log_dir="logs", log_level="INFO", console_output=True, file_output=True)

# AFTER
from src.utils.unified_logger import UnifiedLogger, OutputFormat
UnifiedLogger.configure(
    log_dir="logs",
    log_level="INFO",
    console_output=True,
    console_format=OutputFormat.COLORED,
    file_output=True,
    file_format=OutputFormat.JSON
)
```

### Step 2: Update Import Statements (Automatic with Aliases)

The unified logger provides **backward compatibility aliases**, so you can update imports gradually:

#### Option A: Update to New Unified Logger (Recommended)

```python
# Change this:
from src.utils.logger import get_logger
from src.utils.structured_logger import StructuredLogger, CorrelationContext

# To this:
from src.utils.unified_logger import UnifiedLogger, LogContext

logger = UnifiedLogger.get_logger(__name__)
```

#### Option B: Use Backward Compatibility Aliases (No Code Changes)

```python
# Keep existing imports - they work via aliases!
from src.utils.unified_logger import get_logger  # Alias for backward compat
from src.utils.unified_logger import StructuredLogger  # Alias
from src.utils.unified_logger import CorrelationContext  # Alias for LogContext

# Old code continues to work without changes
logger = get_logger(__name__)
# OR
logger = StructuredLogger(__name__)
```

### Step 3: Update Helper Function Calls

The unified logger combines helper functions from both systems:

```python
# OLD (logger.py)
from src.utils.logger import log_trade, log_signal, log_connection

log_trade(logger, "EURUSD", "BUY", 0.1, 1.0850, 12345)
log_signal(logger, "EURUSD", "BUY", 1.0850, 0.85)
log_connection(logger, "connect", "Account connected")

# NEW (unified_logger.py) - Methods on logger object!
logger.log_trade("EURUSD", "BUY", 0.1, 1.0850, 12345)
logger.log_signal("EURUSD", "BUY", 1.0850, 0.85)
logger.log_connection("connect", login=12345, server="ICMarkets", success=True)
```

```python
# OLD (structured_logger.py)
from src.utils.structured_logger import log_trade_execution, log_signal_generation

log_trade_execution(logger, "EURUSD", "BUY", 0.1, 1.0850, 12345, sl=1.08, tp=1.09)
log_signal_generation(logger, "EURUSD", "BUY", 0.85, "RSI_Strategy", indicators={'rsi': 30})

# NEW (unified_logger.py) - Same methods with shorter names
logger.log_trade("EURUSD", "BUY", 0.1, 1.0850, 12345, sl=1.08, tp=1.09)
logger.log_signal("EURUSD", "BUY", 1.0850, 0.85, strategy="RSI_Strategy", indicators={'rsi': 30})
```

## File-by-File Migration Examples

### Example 1: API Route (`src/api/routes/accounts.py`)

**BEFORE** (using `logger.py`):
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

@router.put("/accounts/{account_id}/config")
async def update_account_configuration(account_id: int, ...):
    logger.info(f"Configuration saved for account {account_id}")
    logger.info(f"Config source: {account.config_source}")
```

**AFTER** (using `unified_logger.py`):
```python
from src.utils.unified_logger import UnifiedLogger

logger = UnifiedLogger.get_logger(__name__)

@router.put("/accounts/{account_id}/config")
async def update_account_configuration(account_id: int, ...):
    # Structured logging with context fields
    logger.info(
        "Configuration saved for account",
        account_id=account_id,
        config_source=account.config_source,
        config_path=account.config_path
    )
```

### Example 2: Trading Logic (`src/trading/orchestrator.py`)

**BEFORE** (using `structured_logger.py`):
```python
from src.utils.structured_logger import StructuredLogger, CorrelationContext, log_trade_execution

logger = StructuredLogger(__name__)

async def execute_trade(symbol: str, action: str, volume: float):
    with CorrelationContext() as ctx:
        logger.info("Starting trade execution", symbol=symbol, action=action)
        # ... execute trade
        log_trade_execution(logger, symbol, action, volume, price, ticket)
```

**AFTER** (using `unified_logger.py`):
```python
from src.utils.unified_logger import UnifiedLogger, LogContext

logger = UnifiedLogger.get_logger(__name__)

async def execute_trade(symbol: str, action: str, volume: float):
    with LogContext() as ctx:
        logger.info("Starting trade execution", symbol=symbol, action=action)
        # ... execute trade
        logger.log_trade(symbol, action, volume, price, ticket)
```

### Example 3: Service Layer (`src/services/position_service.py`)

**BEFORE** (using `logger.py`):
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def get_open_positions(self, account_id: Optional[int], ...):
    logger.info(f"Getting open positions - account_id={account_id}")
    try:
        # ... logic
        logger.error(f"Error getting open positions: {str(e)}")
```

**AFTER** (using `unified_logger.py`):
```python
from src.utils.unified_logger import UnifiedLogger

logger = UnifiedLogger.get_logger(__name__)

async def get_open_positions(self, account_id: Optional[int], ...):
    logger.info("Getting open positions", account_id=account_id, symbol=symbol)
    try:
        # ... logic
    except Exception as e:
        logger.log_error_with_context(e, context={'account_id': account_id})
```

## Configuration Options

### Development Mode (Colored Console + JSON Files)

```python
UnifiedLogger.configure(
    log_dir="logs",
    log_level="DEBUG",
    console_output=True,
    console_format=OutputFormat.COLORED,  # Colors + emojis for terminal
    file_output=True,
    file_format=OutputFormat.JSON         # JSON for analysis tools
)
```

### Production Mode (JSON Everything)

```python
UnifiedLogger.configure(
    log_dir="/var/log/tradingmtq",
    log_level="INFO",
    console_output=True,
    console_format=OutputFormat.JSON,     # JSON to stdout for containers
    file_output=True,
    file_format=OutputFormat.JSON         # JSON files for ELK/Splunk
)
```

### Testing Mode (Plain Text, No Files)

```python
UnifiedLogger.configure(
    log_dir="logs",
    log_level="DEBUG",
    console_output=True,
    console_format=OutputFormat.PLAIN,    # Plain text for test output
    file_output=False                      # No files during tests
)
```

## Output Format Comparison

### JSON Format (OutputFormat.JSON)

```json
{
  "timestamp": "2025-12-28T16:30:45.123Z",
  "level": "INFO",
  "logger": "trading.orchestrator",
  "message": "Trade executed",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event_type": "trade_execution",
  "symbol": "EURUSD",
  "action": "BUY",
  "volume": 0.1,
  "price": 1.0850,
  "ticket": 12345,
  "stop_loss": 1.0800,
  "take_profit": 1.0900
}
```

### Colored Format (OutputFormat.COLORED)

```
16:30:45 [I] INFO 💰 [EURUSD] Trade executed: BUY 0.1 EURUSD @ 1.08500 - Ticket #12345
```

### Plain Format (OutputFormat.PLAIN)

```
2025-12-28 16:30:45 | INFO     | trading.orchestrator | Trade executed: BUY 0.1 EURUSD @ 1.08500 - Ticket #12345
```

## Complete Migration Checklist

### Phase 1: Setup (5 minutes)

- [ ] Update `src/api/app.py` startup to use `UnifiedLogger.configure()`
- [ ] Test application starts without errors
- [ ] Verify log files are created in `logs/` directory

### Phase 2: API Routes (30 minutes)

Files to update:
- [ ] `src/api/routes/accounts.py`
- [ ] `src/api/routes/positions.py`
- [ ] `src/api/routes/websocket.py`
- [ ] `src/api/websocket.py`

**Pattern**: Change `from src.utils.logger import get_logger` to `from src.utils.unified_logger import UnifiedLogger`

### Phase 3: Services (45 minutes)

Files to update:
- [ ] `src/services/trading_bot_service.py`
- [ ] `src/services/bot_service.py`
- [ ] `src/services/session_manager.py`
- [ ] `src/services/position_service.py`
- [ ] `src/services/analytics_service.py`
- [ ] `src/services/config_service.py`

**Pattern**: Use `logger.info("message", key=value)` instead of f-strings

### Phase 4: Trading Core (60 minutes)

Files to update:
- [ ] `src/trading/orchestrator.py`
- [ ] `src/trading/currency_trader.py`
- [ ] `src/trading/position_manager.py`
- [ ] `src/connectors/mt5_connector.py`

**Pattern**: Keep `LogContext` for correlation tracking, update helper functions to methods

### Phase 5: Database & Analytics (30 minutes)

Files to update:
- [ ] `src/database/connection.py`
- [ ] `src/database/repository.py`
- [ ] `src/database/migration_utils.py`
- [ ] `src/analytics/daily_aggregator.py`
- [ ] `src/analytics/scheduler.py`

### Phase 6: Miscellaneous (30 minutes)

Files to update:
- [ ] `src/api/routes/alerts.py`
- [ ] `src/api/routes/charts.py`
- [ ] `src/api/routes/reports.py`
- [ ] `src/notifications/alert_manager.py`
- [ ] `src/notifications/email_service.py`
- [ ] `src/reports/generator.py`
- [ ] `src/reports/email_service.py`
- [ ] `src/reports/scheduler.py`
- [ ] `src/ml/model_loader.py`

### Phase 7: Testing & Cleanup (30 minutes)

- [ ] Run full test suite
- [ ] Verify log output format (console + files)
- [ ] Check correlation IDs work correctly
- [ ] Test all helper methods (log_trade, log_signal, etc.)
- [ ] Backup old logger files: `logger.py.bak`, `structured_logger.py.bak`
- [ ] Update documentation and type hints

## Rollback Plan

If issues arise during migration:

1. **Keep old loggers**: Don't delete `logger.py` or `structured_logger.py` yet
2. **Gradual migration**: Update one module at a time, test thoroughly
3. **Backward compatibility**: Old imports continue to work via aliases
4. **Quick revert**: Change import back to old logger if needed

## Benefits of Unified Logger

✅ **Single source of truth** - One logging system instead of two
✅ **Flexible output** - JSON for production, colored for development
✅ **Better organization** - OOP design with clear methods
✅ **Backward compatible** - Existing code works without changes
✅ **Feature complete** - Combines best of both old systems
✅ **Future proof** - Easy to extend with new features
✅ **Type safe** - Better IDE autocomplete and type checking

## Support

For questions or issues during migration, refer to:

- [Unified Logger Source](../src/utils/unified_logger.py) - Full implementation
- [Logger Comparison](./LOGGER_COMPARISON.md) - Detailed comparison of old systems
- [Example Usage](../src/utils/unified_logger.py#L500) - Working examples at end of file

## Migration Timeline

- **Week 1**: Phase 1-2 (Setup + API routes)
- **Week 2**: Phase 3-4 (Services + Trading core)
- **Week 3**: Phase 5-6 (Database + Miscellaneous)
- **Week 4**: Phase 7 (Testing + Cleanup)

Total estimated time: **4 weeks** with thorough testing at each phase.

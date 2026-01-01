# Phase 4.5: MT5Connector Refactoring Example

This document shows how to refactor the MT5Connector to use custom exceptions, structured logging, and error handlers from Phase 0.

## Before & After Comparison

### BEFORE (Current Implementation)

```python
# src/connectors/mt5_connector.py (BEFORE)
import logging

logger = logging.getLogger(__name__)

class MT5Connector(BaseMetaTraderConnector):
    def connect(self, login: int, password: str, server: str,
                timeout: int = 60000, portable: bool = False, **kwargs) -> bool:
        """Connect to MT5 terminal"""
        try:
            self.status = ConnectionStatus.CONNECTING
            logger.info(f"[{self.instance_id}] Connecting to MT5 - Server: {server}")

            if not self._initialized:
                if not mt5.initialize(login=login, password=password, server=server):
                    error = mt5.last_error()
                    logger.error(f"[{self.instance_id}] MT5 initialization failed: {error}")
                    self.status = ConnectionStatus.ERROR
                    return False  # ❌ Returns bool instead of raising exception

                self._initialized = True

            account = mt5.account_info()
            if account is None:
                logger.error(f"[{self.instance_id}] Failed to get account info")
                self.status = ConnectionStatus.ERROR
                return False  # ❌ Returns bool

            self.status = ConnectionStatus.CONNECTED
            logger.info(f"[{self.instance_id}] Connected successfully")
            return True

        except Exception as e:  # ❌ Catches ALL exceptions
            logger.error(f"[{self.instance_id}] Connection error: {e}", exc_info=True)
            self.status = ConnectionStatus.ERROR
            return False  # ❌ Returns bool
```

**Problems:**
1. Returns `bool` instead of raising exceptions
2. Catches broad `Exception` without specificity
3. Uses unstructured logging (no JSON, no correlation IDs)
4. No automatic retry logic
5. Error context lost (no error codes, no context dict)

---

### AFTER (Refactored with Phase 0 Patterns)

```python
# src/connectors/mt5_connector.py (AFTER REFACTORING)
from src.exceptions import (
    ConnectionError, AuthenticationError, build_connection_context
)
from src.utils.structured_logger import StructuredLogger, CorrelationContext
from src.utils.error_handlers import handle_mt5_errors

logger = StructuredLogger(__name__)


class MT5Connector(BaseMetaTraderConnector):

    @handle_mt5_errors(retry_count=3, retry_delay=2.0)
    def connect(self, login: int, password: str, server: str,
                timeout: int = 60000, portable: bool = False, **kwargs) -> bool:
        """
        Connect to MT5 terminal

        Args:
            login: Account number
            password: Account password
            server: Broker server
            timeout: Connection timeout in milliseconds
            portable: Use portable mode

        Returns:
            True if connected successfully

        Raises:
            ConnectionError: If MT5 initialization fails
            AuthenticationError: If credentials are invalid
        """
        with CorrelationContext():  # ✅ Automatic correlation ID
            self.status = ConnectionStatus.CONNECTING

            logger.info(
                "Connecting to MT5",
                server=server,
                login=login,
                timeout=timeout,
                instance_id=self.instance_id
            )  # ✅ Structured logging

            if not self._initialized:
                if not mt5.initialize(
                    login=login,
                    password=password,
                    server=server,
                    timeout=timeout,
                    portable=portable
                ):
                    error = mt5.last_error()
                    error_code = error[0] if isinstance(error, tuple) else error

                    # ✅ Raise specific exception with context
                    if error_code == 10004:  # Invalid credentials
                        raise AuthenticationError(
                            f"Invalid MT5 credentials for server {server}",
                            error_code=error_code,
                            context=build_connection_context(login, server)
                        )
                    else:
                        raise ConnectionError(
                            f"MT5 initialization failed: {error}",
                            error_code=error_code,
                            context=build_connection_context(login, server)
                        )

                self._initialized = True

            # Store connection parameters for reconnection
            self._connection_params = {
                'login': login,
                'password': password,
                'server': server,
                'timeout': timeout,
                'portable': portable
            }

            # Verify connection
            account = mt5.account_info()
            if account is None:
                # ✅ Raise specific exception
                raise ConnectionError(
                    "Failed to get account info after connection",
                    context=build_connection_context(login, server, attempt=1)
                )

            self.status = ConnectionStatus.CONNECTED

            logger.info(
                "Connected to MT5 successfully",
                account_login=account.login,
                account_balance=account.balance,
                server=server,
                instance_id=self.instance_id
            )  # ✅ Structured logging with details

            return True

    def disconnect(self) -> None:
        """Disconnect from MT5"""
        with CorrelationContext():
            try:
                if self._initialized:
                    mt5.shutdown()
                    self._initialized = False
                    self.status = ConnectionStatus.DISCONNECTED

                    logger.info(
                        "Disconnected from MT5",
                        instance_id=self.instance_id
                    )
            except Exception as e:
                logger.error(
                    "Error during disconnect",
                    exc_info=True,
                    instance_id=self.instance_id
                )
                raise ConnectionError(
                    f"Failed to disconnect: {e}",
                    context={'instance_id': self.instance_id}
                )

    @handle_mt5_errors(retry_count=2, fallback_return=None)
    def get_account_info(self) -> Optional[AccountInfo]:
        """
        Get account information

        Returns:
            AccountInfo object or None if not available

        Raises:
            ConnectionError: If MT5 is not connected
        """
        with CorrelationContext():
            if not self._initialized:
                raise ConnectionError(
                    "MT5 not initialized",
                    context={'instance_id': self.instance_id}
                )

            account = mt5.account_info()
            if account is None:
                logger.warning(
                    "Failed to get account info",
                    instance_id=self.instance_id
                )
                raise ConnectionError(
                    "MT5 returned no account info",
                    context={'instance_id': self.instance_id}
                )

            logger.debug(
                "Retrieved account info",
                account_login=account.login,
                balance=account.balance,
                equity=account.equity,
                instance_id=self.instance_id
            )

            return AccountInfo(
                login=account.login,
                server=account.server,
                name=account.name,
                company=account.company,
                currency=account.currency,
                balance=account.balance,
                equity=account.equity,
                profit=account.profit,
                margin=account.margin,
                margin_free=account.margin_free,
                margin_level=account.margin_level if account.margin > 0 else 0,
                leverage=account.leverage,
                trade_allowed=account.trade_allowed
            )
```

---

## Key Improvements

### 1. Custom Exceptions Instead of Return Values

**BEFORE:**
```python
if not mt5.initialize(...):
    return False  # Caller must check bool
```

**AFTER:**
```python
if not mt5.initialize(...):
    raise ConnectionError(...)  # Caller gets specific exception
```

**Benefits:**
- ✅ Caller knows exactly what went wrong
- ✅ Can catch specific exception types
- ✅ Stack trace preserved
- ✅ Error context included

---

### 2. Structured JSON Logging

**BEFORE:**
```python
logger.info(f"[{self.instance_id}] Connecting to MT5 - Server: {server}")
```

**AFTER:**
```python
logger.info(
    "Connecting to MT5",
    server=server,
    login=login,
    timeout=timeout,
    instance_id=self.instance_id
)
```

**Output (JSON):**
```json
{
  "timestamp": "2025-12-13T10:30:45Z",
  "level": "INFO",
  "logger": "mt5_connector",
  "message": "Connecting to MT5",
  "correlation_id": "a1b2c3d4-...",
  "server": "MetaQuotes-Demo",
  "login": 12345,
  "timeout": 60000,
  "instance_id": "default"
}
```

**Benefits:**
- ✅ Machine-parseable (ELK, Splunk compatible)
- ✅ Correlation IDs for request tracking
- ✅ Queryable structured fields
- ✅ Easy to filter/aggregate

---

### 3. Automatic Retry Logic

**BEFORE:**
```python
def connect(...) -> bool:
    # Manual retry would need to be implemented by caller
    if not mt5.initialize(...):
        return False
```

**AFTER:**
```python
@handle_mt5_errors(retry_count=3, retry_delay=2.0)
def connect(...) -> bool:
    # Automatic retry with exponential backoff
    if not mt5.initialize(...):
        raise ConnectionError(...)
```

**Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: After 2 seconds
- Attempt 3: After 4 seconds (2 * 2)
- Attempt 4: After 8 seconds (4 * 2)

**Benefits:**
- ✅ Automatic recovery from transient failures
- ✅ Exponential backoff prevents flooding
- ✅ Configurable retry count and delay
- ✅ No boilerplate retry code needed

---

### 4. Correlation ID Propagation

**BEFORE:**
```python
def connect(...):
    logger.info("Connecting...")
    account = mt5.account_info()
    logger.info("Connected")
    # No way to correlate these log entries
```

**AFTER:**
```python
def connect(...):
    with CorrelationContext():  # Same ID for all logs in this context
        logger.info("Connecting...")
        account = mt5.account_info()
        logger.info("Connected")
```

**Log Output:**
```json
{"timestamp":"...","correlation_id":"a1b2c3d4","message":"Connecting..."}
{"timestamp":"...","correlation_id":"a1b2c3d4","message":"Connected"}
```

**Benefits:**
- ✅ Track entire request flow
- ✅ Find all logs related to a single operation
- ✅ Essential for debugging multi-threaded execution
- ✅ Works across function calls

---

## Complete Refactoring Checklist

### Phase 4.5 HIGH Priority Tasks

- [ ] **MT5Connector Refactoring**
  - [ ] Replace `return False` with `raise ConnectionError`
  - [ ] Replace `return None` with `raise DataNotAvailableError`
  - [ ] Add `@handle_mt5_errors` to all public methods
  - [ ] Wrap all methods with `CorrelationContext()`
  - [ ] Replace `logger.info()` with structured logging
  - [ ] Add error context to all exceptions

- [ ] **Orchestrator Refactoring**
  - [ ] Use `StructuredLogger` instead of standard logger
  - [ ] Add correlation IDs for each trading cycle
  - [ ] Replace broad `except Exception` with specific exceptions
  - [ ] Add structured logging for all operations

- [ ] **Strategy Refactoring**
  - [ ] Raise `IndicatorCalculationError` on indicator failures
  - [ ] Raise `SignalGenerationError` on signal failures
  - [ ] Use structured logging for signal generation
  - [ ] Add `@handle_mt5_errors` where applicable

- [ ] **Config Loader Refactoring**
  - [ ] Use Pydantic schemas for validation
  - [ ] Raise `ConfigurationError` on validation failure
  - [ ] Add structured logging for config loading
  - [ ] Validate config on load, fail fast

---

## Testing the Refactored Code

```python
# Test script: test_refactored_connector.py
from src.connectors.mt5_connector import MT5Connector
from src.exceptions import ConnectionError, AuthenticationError
from src.utils.structured_logger import StructuredLogger, CorrelationContext
import logging

# Setup logging to see JSON output
logging.basicConfig(level=logging.INFO)

logger = StructuredLogger(__name__)

def test_connection():
    """Test MT5 connector with new patterns"""
    connector = MT5Connector("test-instance")

    with CorrelationContext() as ctx:
        logger.info("Starting connection test", test_name="mt5_connect")

        try:
            # This will automatically retry 3 times if it fails
            success = connector.connect(
                login=12345,
                password="test",
                server="MetaQuotes-Demo"
            )

            if success:
                logger.info("Connection successful", account=connector.get_account_info())

        except AuthenticationError as e:
            logger.error(
                "Authentication failed",
                error_code=e.error_code,
                context=e.context,
                exc_info=True
            )

        except ConnectionError as e:
            logger.error(
                "Connection error",
                error_code=e.error_code,
                context=e.context,
                exc_info=True
            )

        finally:
            connector.disconnect()

if __name__ == '__main__':
    test_connection()
```

---

## Benefits Summary

### For Development
- ✅ **Clearer error handling** - Know exactly what went wrong
- ✅ **Less boilerplate** - Decorators handle retry logic
- ✅ **Better debugging** - Correlation IDs track requests
- ✅ **Type safety** - Specific exception types

### For Production
- ✅ **Machine-parseable logs** - ELK/Splunk integration ready
- ✅ **Automatic recovery** - Transient failures handled automatically
- ✅ **Better observability** - Structured fields enable dashboards
- ✅ **Incident response** - Correlation IDs find related logs instantly

### For Testing
- ✅ **Specific exceptions** - Can test exact failure scenarios
- ✅ **Mockable dependencies** - DI makes testing easier
- ✅ **Reproducible** - Correlation IDs help reproduce issues

---

## Migration Strategy

### Option 1: Big Bang (1 week)
1. Refactor all MT5Connector methods at once
2. Update all callers to handle new exceptions
3. Test thoroughly
4. Deploy

**Pros:** Clean break, complete immediately
**Cons:** Risky, requires full regression testing

### Option 2: Gradual Migration (2-3 weeks)
1. Week 1: Refactor MT5Connector, maintain backward compatibility
2. Week 2: Update Orchestrator and Strategies
3. Week 3: Remove compatibility layer, full migration

**Pros:** Lower risk, incremental testing
**Cons:** Longer timeline, temporary complexity

### Option 3: Hybrid (Recommended)
1. Refactor critical paths first (connect, send_order, get_positions)
2. Leave non-critical methods for gradual migration
3. Update callers as you encounter them during other work

**Pros:** Balance of speed and safety
**Cons:** Temporary inconsistency in codebase

---

## Next Steps

1. **Review this example** - Understand the patterns
2. **Pick a migration strategy** - Big bang vs. gradual
3. **Start with MT5Connector.connect()** - Most critical method
4. **Write tests** - Verify refactored code works
5. **Update callers** - Orchestrator, Strategies, etc.
6. **Document changes** - Update API documentation

---

**Status:** Example complete, ready for implementation
**Estimated Effort:** 1-2 weeks for full MT5Connector refactoring
**Risk Level:** Low (backward compatible approach possible)
**Impact:** High (foundation for all trading operations)


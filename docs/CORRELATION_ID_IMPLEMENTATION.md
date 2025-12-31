# Correlation ID Implementation

## Date: December 28, 2025

## Overview

Implemented automatic correlation ID tracking for all API requests using the unified logger's `LogContext` feature. This enables request tracing across the entire application stack.

## What Was Done

### 1. Added LogContext to FastAPI Middleware ✅

**File**: `src/api/app.py`

**Changes**:
1. **Import Update** (Line 28):
   ```python
   # Before
   from src.utils.unified_logger import UnifiedLogger, OutputFormat

   # After
   from src.utils.unified_logger import UnifiedLogger, OutputFormat, LogContext
   ```

2. **Middleware Update** (Lines 91-121):
   ```python
   @app.middleware("http")
   async def log_requests(request: Request, call_next):
       # Create correlation context for this request
       with LogContext() as ctx:
           start_time = time.time()

           # Log request with correlation_id
           logger.info(
               f"→ {request.method} {request.url.path}",
               method=request.method,
               path=request.url.path,
               client=request.client.host if request.client else None,
               correlation_id=ctx.correlation_id
           )

           # Process request
           response = await call_next(request)

           # Log response with correlation_id
           duration = time.time() - start_time
           logger.info(
               f"← {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
               method=request.method,
               path=request.url.path,
               status_code=response.status_code,
               duration=duration,
               correlation_id=ctx.correlation_id
           )

           return response
   ```

## How Correlation IDs Work

### Automatic Generation

Every API request now automatically gets a unique UUID correlation_id:

```python
with LogContext() as ctx:
    # ctx.correlation_id is a UUID like: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    # All logs within this context will have this same correlation_id
```

### Context Propagation

The `LogContext` uses Python's `ContextVar` for thread-safe correlation ID storage. This means:

1. **Request Scope**: Each API request gets its own correlation_id
2. **Thread-Safe**: Works correctly with FastAPI's async/await and threading
3. **Automatic Propagation**: All logs within the request context share the same ID

### Log Output Examples

#### JSON Format (File Output)

```json
{
  "timestamp": "2025-12-28T20:30:45.123Z",
  "level": "INFO",
  "logger": "src.api.app",
  "message": "→ GET /api/accounts",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "GET",
  "path": "/api/accounts",
  "client": "127.0.0.1"
}
```

```json
{
  "timestamp": "2025-12-28T20:30:45.456Z",
  "level": "INFO",
  "logger": "src.api.routes.accounts",
  "message": "Fetching accounts list",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "account_count": 5
}
```

```json
{
  "timestamp": "2025-12-28T20:30:45.789Z",
  "level": "INFO",
  "logger": "src.api.app",
  "message": "← GET /api/accounts - 200 (0.333s)",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "GET",
  "path": "/api/accounts",
  "status_code": 200,
  "duration": 0.333
}
```

#### Colored Console Format (Development)

```
20:30:45 [I] INFO → GET /api/accounts [correlation_id: a1b2c3d4-e5f6-7890]
20:30:45 [I] INFO Fetching accounts list [correlation_id: a1b2c3d4-e5f6-7890]
20:30:45 [I] INFO ← GET /api/accounts - 200 (0.333s) [correlation_id: a1b2c3d4-e5f6-7890]
```

## Benefits

### 1. Request Tracing ✅

Track a single request's entire journey through the application:

```bash
# Search logs for specific correlation_id
grep "a1b2c3d4-e5f6-7890" logs/trading_*.log

# In JSON logs, use jq
jq 'select(.correlation_id == "a1b2c3d4-e5f6-7890")' logs/trading_*.log
```

### 2. Error Debugging ✅

When an error occurs, you can trace back to the original request:

```json
{
  "timestamp": "2025-12-28T20:30:45.789Z",
  "level": "ERROR",
  "logger": "src.services.position_service",
  "message": "Error getting open positions: Account not found",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "account_id": 1,
  "exception": {
    "type": "ValueError",
    "message": "Account 1 not found"
  }
}
```

Search for this `correlation_id` to see the entire request flow that led to the error.

### 3. Performance Analysis ✅

Track request duration and identify bottlenecks:

```bash
# Find slow requests
jq 'select(.duration > 1.0)' logs/trading_*.log

# Group by endpoint
jq -r '[.correlation_id, .path, .duration] | @csv' logs/trading_*.log | sort -t, -k3 -n
```

### 4. Distributed System Readiness ✅

When you scale to multiple services:
- Pass `correlation_id` in HTTP headers between services
- Maintain tracing across microservices
- Build distributed tracing systems (Zipkin, Jaeger)

## Usage Patterns

### Pattern 1: Automatic (API Requests) ✅ IMPLEMENTED

All API requests automatically get correlation IDs via middleware - **no code changes needed**.

```python
# In any route handler
@router.get("/accounts")
async def get_accounts():
    # Correlation ID is automatically set by middleware
    logger.info("Fetching accounts")  # Will include correlation_id
    return accounts
```

### Pattern 2: Manual (Background Tasks)

For background tasks or operations outside HTTP requests:

```python
from src.utils.unified_logger import UnifiedLogger, LogContext

logger = UnifiedLogger.get_logger(__name__)

async def background_job():
    with LogContext() as ctx:
        logger.info("Starting background job")
        # All logs here will share ctx.correlation_id
        process_data()
        logger.info("Background job completed")
```

### Pattern 3: Nested Operations

LogContext can be nested for sub-operations:

```python
async def main_operation():
    with LogContext() as main_ctx:
        logger.info("Main operation started")  # correlation_id: main_ctx

        # Sub-operation with its own correlation_id
        with LogContext() as sub_ctx:
            logger.info("Sub-operation started")  # correlation_id: sub_ctx
            do_sub_work()
            logger.info("Sub-operation completed")  # correlation_id: sub_ctx

        logger.info("Main operation completed")  # correlation_id: main_ctx
```

### Pattern 4: Propagate Correlation ID

Pass correlation_id between functions:

```python
async def handle_request():
    with LogContext() as ctx:
        await process_data(correlation_id=ctx.correlation_id)

async def process_data(correlation_id: str):
    # Reuse the same correlation_id
    with LogContext(correlation_id=correlation_id):
        logger.info("Processing data")  # Same correlation_id as parent
```

## Before and After

### Before: Logs Without Correlation IDs

```json
{"timestamp": "2025-12-28T20:30:45.123Z", "level": "INFO", "logger": "src.api.app", "message": "→ GET /api/accounts", "correlation_id": "none"}
{"timestamp": "2025-12-28T20:30:45.456Z", "level": "INFO", "logger": "src.api.routes.accounts", "message": "Fetching accounts", "correlation_id": "none"}
{"timestamp": "2025-12-28T20:30:45.789Z", "level": "INFO", "logger": "src.api.app", "message": "← GET /api/accounts - 200", "correlation_id": "none"}
{"timestamp": "2025-12-28T20:30:46.123Z", "level": "ERROR", "logger": "src.services.position_service", "message": "Account not found", "correlation_id": "none"}
```

**Problem**: Can't trace which request caused the error - all correlation_ids are "none".

### After: Logs With Correlation IDs ✅

```json
{"timestamp": "2025-12-28T20:30:45.123Z", "level": "INFO", "logger": "src.api.app", "message": "→ GET /api/accounts", "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
{"timestamp": "2025-12-28T20:30:45.456Z", "level": "INFO", "logger": "src.api.routes.accounts", "message": "Fetching accounts", "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
{"timestamp": "2025-12-28T20:30:45.789Z", "level": "INFO", "logger": "src.api.app", "message": "← GET /api/accounts - 200", "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
{"timestamp": "2025-12-28T20:30:46.123Z", "level": "ERROR", "logger": "src.services.position_service", "message": "Account not found", "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
```

**Solution**: All logs from the same request share the same correlation_id - easy to trace!

## Testing

### Manual Testing

1. **Start the server**:
   ```bash
   uvicorn src.api.app:app --reload
   ```

2. **Make an API request**:
   ```bash
   curl http://localhost:8000/api/accounts
   ```

3. **Check the logs**:
   ```bash
   # Console output (colored)
   tail -f logs/trading_*.log

   # JSON file output
   tail -f logs/trading_*.log | jq '.'
   ```

4. **Verify correlation_id**:
   - Each request should have a unique UUID correlation_id
   - All logs within a single request should share the same correlation_id
   - Different requests should have different correlation_ids

### Expected Log Output

```
20:30:45 [I] INFO → GET /api/accounts
20:30:45 [I] INFO Fetching accounts list
20:30:45 [I] INFO ← GET /api/accounts - 200 (0.333s)
```

In JSON files:
```json
{"correlation_id": "550e8400-e29b-41d4-a716-446655440000", ...}
{"correlation_id": "550e8400-e29b-41d4-a716-446655440000", ...}
{"correlation_id": "550e8400-e29b-41d4-a716-446655440000", ...}
```

## Troubleshooting

### Issue: Still Seeing "correlation_id": "none"

**Cause**: Logs outside of `LogContext` will have "none" as correlation_id.

**Solution**:
- For API requests: Already fixed via middleware
- For background tasks: Wrap with `with LogContext(): ...`
- For standalone scripts: Add `with LogContext(): ...` around main logic

### Issue: Different correlation_ids Within Same Request

**Cause**: Creating multiple `LogContext()` instances within the same request.

**Solution**: Use the same `LogContext` instance or pass `correlation_id` parameter:
```python
with LogContext(correlation_id=existing_id):
    ...
```

### Issue: Correlation ID Not Propagating to Child Functions

**Cause**: `ContextVar` is thread-local - not propagated to new threads/processes.

**Solution**: Pass correlation_id as parameter when crossing thread boundaries:
```python
async def parent():
    with LogContext() as ctx:
        await child(correlation_id=ctx.correlation_id)

async def child(correlation_id: str):
    with LogContext(correlation_id=correlation_id):
        logger.info("Child operation")
```

## Related Documentation

- [Unified Logger Implementation Summary](./UNIFIED_LOGGER_IMPLEMENTATION_SUMMARY.md)
- [Unified Logger Migration Guide](./UNIFIED_LOGGER_MIGRATION.md)
- [Logger Comparison](./LOGGER_COMPARISON.md)

## Statistics

- **Files Modified**: 1 file (`src/api/app.py`)
- **Lines Changed**: ~5 lines
- **Time Investment**: ~10 minutes
- **Impact**: ✅ High - All API requests now have automatic correlation tracking

## Status

✅ **IMPLEMENTATION COMPLETE**

All API requests now automatically include unique correlation IDs for request tracing and debugging.

## Credits

**Implementation Date**: December 28, 2025
**Unified Logger**: Based on `src/utils/unified_logger.py`
**Correlation ID Storage**: Python `ContextVar` (thread-safe)
**UUID Generation**: Python `uuid.uuid4()`

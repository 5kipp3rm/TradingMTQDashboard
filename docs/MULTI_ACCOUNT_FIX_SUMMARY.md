# Multi-Account Support - Issue Analysis & Fix Summary

## Overview

This document summarizes the multi-account issues reported by the user and the fixes applied.

**User Report**: "once I have started the UI, and I have 2 account I see that its not running another instance of MT only disconnect the first account, another thing I dont see that the MT when I have connected starting to trade do we have button in the UI to start trade or it's starting automatically?"

---

## Issue #1: MT5 Portable Mode Path ✅ **FIXED**

### Problem
When starting multiple accounts, only one MT5 instance ran and the first account got disconnected when the second account connected.

### Root Cause
The MT5Connector used portable mode (`portable=True`) but **did not provide a unique path** for each MT5 instance. According to MetaTrader5 API documentation:

> When `portable=True`, you **must** provide a `path` parameter pointing to a unique directory for each instance. Without unique paths, all instances share the same MT5 terminal files.

### Solution Implemented

**Commit**: `cb685e9 - fix: Add portable mode path support for multi-account MT5 instances`

**Changes Made**:

1. **MT5Connector** ([src/connectors/mt5_connector.py](../src/connectors/mt5_connector.py)):
   - Added `path: Optional[str] = None` parameter to `connect()` method
   - Auto-generates unique paths when `portable=True` and `path=None`
   - Path format:
     - Windows: `%APPDATA%\TradingMTQ\MT5_Instances\{account_id}\`
     - Unix/Mac: `~/.tradingmtq/mt5_instances/{account_id}/`
   - Creates directories automatically if they don't exist

2. **ConnectCommand** ([src/workers/commands.py](../src/workers/commands.py)):
   - Added `path: Optional[str] = None` field
   - Updated `to_dict()` and `from_dict()` methods

3. **MT5Worker** ([src/workers/mt5_worker.py](../src/workers/mt5_worker.py)):
   - Updated `_handle_connect()` to pass `path` to connector

4. **WorkerPoolManager** ([src/workers/pool.py](../src/workers/pool.py)):
   - Added `path: Optional[str] = None` parameter to `start_worker()`
   - Auto-generates unique paths per account when `portable=True`
   - Logs generated paths for visibility
   - Passes `path` in `ConnectCommand`

5. **WorkerCreationRequest** ([src/services/worker_manager/models.py](../src/services/worker_manager/models.py)):
   - Added `path: Optional[str] = None` field
   - Updated `to_dict()` method

6. **WorkerManagerService** ([src/services/worker_manager/service.py](../src/services/worker_manager/service.py)):
   - Updated `start_worker_from_config()` to pass `path` parameter

### Expected Behavior After Fix

✅ **Multiple Accounts Can Run Simultaneously**:
- Account 1 starts → MT5 instance in `{base_dir}/account-001/`
- Account 2 starts → MT5 instance in `{base_dir}/account-002/`
- Both accounts remain connected without interference

✅ **Process Isolation**:
- On Windows: 2 separate `terminal64.exe` processes
- On macOS/Linux: 2 separate wine processes

✅ **Backwards Compatible**:
- If `path` not provided, it's auto-generated
- Existing code works without modification

### Testing Steps

1. Start first account via UI → verify it connects
2. Start second account via UI → verify both remain connected
3. Check Task Manager (Windows) or Activity Monitor (Mac):
   - Should see 2 separate MT5 terminal processes
4. Verify both accounts can execute trades independently

---

## Issue #2: Trading Bot Not Seeing Workers ⚠️ **REQUIRES FIX**

### Problem
The automated trading bot service doesn't execute trades on workers started via the WorkerManagerService (Phase 4).

### Root Cause
The `TradingBotService` checks for connected accounts using:

```python
connected_account_ids = session_manager.list_active_sessions()
```

**However**, when you start a worker via `WorkerManagerService`, it **does NOT register** the session with `session_manager`. The two systems operate independently:

- **Old System**: `SessionManager` (used by trading bot)
- **New System**: `WorkerManagerService` (Phase 4)

### Current Behavior

1. User starts worker via UI → calls `WorkerManagerService.start_worker_from_config()`
2. Worker starts and connects to MT5 ✅
3. Worker tracked in `WorkerManagerService._worker_info` ✅
4. **BUT**: `session_manager` doesn't know about it ❌
5. Trading bot checks `session_manager.list_active_sessions()` → returns empty ❌
6. **Result**: No automated trading occurs even though worker is connected

### Trading Bot Code

From [src/services/trading_bot_service.py:99](../src/services/trading_bot_service.py#L99):

```python
async def _execute_trading_cycle(self):
    """Execute one trading cycle for all connected accounts."""
    # Get all connected account IDs
    connected_account_ids = session_manager.list_active_sessions()  # ❌ Doesn't see workers!

    if not connected_account_ids:
        logger.debug("No connected accounts, skipping trading cycle")
        return

    logger.info(f"Executing trading cycle for {len(connected_account_ids)} connected accounts")
    # ...
```

### Solution Options

#### Option A: Quick Fix - Register Sessions in WorkerManagerService

**Pros**: Minimal code changes, preserves existing architecture
**Cons**: Creates coupling between two systems

**Implementation**:

```python
# In WorkerManagerService.start_worker_from_config()
def start_worker_from_config(...) -> WorkerInfo:
    # ... existing code ...

    worker_id = self.worker_pool.start_worker(...)

    # ✅ Register session with session_manager
    from src.services.session_manager import session_manager

    # Get connector instance from worker pool
    worker_handle = self.worker_pool.get_worker(worker_id)
    connector = worker_handle.worker._connector  # Access connector

    session_manager.create_session(
        account_id=account_id,
        connector=connector,
        config=config
    )

    # ... rest of code ...
```

**Also need to unregister on stop**:

```python
# In WorkerManagerService.stop_worker()
def stop_worker(self, account_id: str, timeout: Optional[float] = None) -> bool:
    # ... existing code ...

    # ✅ Unregister session
    session_manager.close_session(account_id)

    # ... rest of code ...
```

#### Option B: Better Architecture - Create Integration Bridge

**Pros**: Clean separation of concerns, scalable, maintainable
**Cons**: More code changes required

**Implementation**:

Create `src/services/worker_session_bridge.py`:

```python
"""
Worker-Session Bridge Service

Keeps WorkerManagerService and SessionManager in sync automatically.
"""

class WorkerSessionBridge:
    def __init__(self, worker_manager_service, session_manager):
        self.worker_manager = worker_manager_service
        self.session_manager = session_manager

        # Listen for worker lifecycle events
        self.worker_manager.on_worker_started(self._handle_worker_started)
        self.worker_manager.on_worker_stopped(self._handle_worker_stopped)

    def _handle_worker_started(self, worker_info: WorkerInfo):
        """Automatically register session when worker starts"""
        # Get connector from worker
        # Register with session_manager
        pass

    def _handle_worker_stopped(self, worker_info: WorkerInfo):
        """Automatically unregister session when worker stops"""
        self.session_manager.close_session(worker_info.account_id)
```

### Recommendation

**Use Option A for now** (quick fix) to get multi-account trading working immediately. Later, refactor to Option B for better architecture.

---

## Issue #3: Trading Bot Auto-Start ✅ **ALREADY WORKING**

### Question
"do we have button in the UI to start trade or it's starting automatically?"

### Answer

**Trading starts automatically!** The trading bot service is **already configured** to start automatically when the API server starts.

From [src/api/app.py:46-50](../src/api/app.py#L46-L50):

```python
# Startup: Start trading bot service
await trading_bot_service.start()

logger = logging.getLogger("src.api.app")
logger.info("Trading bot service started - will auto-trade on connected accounts")
```

### How It Works

1. **API Server Starts** → `trading_bot_service.start()` is called automatically
2. **Trading Bot Loop Runs** → every 60 seconds (configurable)
3. **Checks for Connected Accounts** → `session_manager.list_active_sessions()`
4. **Executes Trading Logic** → for each connected account
   - Loads currency configurations
   - Runs strategy analysis
   - Generates signals
   - Executes trades

### The Problem

The trading bot **IS running**, but it's **not seeing your workers** because of Issue #2 above (session manager integration).

Once Issue #2 is fixed, the trading bot will automatically:
- Detect connected workers
- Execute trading cycles
- Generate and execute trades based on strategies

### No Button Needed

You don't need a "Start Trading" button because:
- ✅ Trading bot starts automatically with API server
- ✅ Monitors connected accounts every 60 seconds
- ✅ Executes trades based on currency configurations
- ✅ No manual intervention required

**The UI can add**:
- Trading bot status indicator (running/stopped)
- Trade execution logs
- Button to manually trigger a trading cycle (optional)

---

## Summary & Next Steps

### ✅ Fixed (Priority 1)
- **Multi-Instance MT5 Support** - Commit `cb685e9`
- Each account gets unique MT5 terminal directory
- Multiple accounts can connect simultaneously

### ⚠️ Requires Fix (Priority 2)
- **Session Manager Integration** - Need to implement Option A or B
- Without this, trading bot won't see connected workers
- Recommended: Implement Option A first for quick fix

### ✅ Already Working (Info)
- **Trading Bot Auto-Start** - No changes needed
- Starts automatically with API server
- Executes trading cycles every 60 seconds

### Testing Checklist

After implementing Issue #2 fix:

- [ ] Start 2 accounts via UI
- [ ] Verify 2 MT5 instances running (Task Manager/Activity Monitor)
- [ ] Verify both accounts remain connected
- [ ] Check logs for "Executing trading cycle for 2 connected accounts"
- [ ] Verify trades are executed on both accounts
- [ ] Verify positions appear in UI for both accounts

---

## Implementation Priority

1. **Done** ✅: MT5 portable mode path support
2. **Next**: Session manager integration (Issue #2)
3. **Test**: Multi-account trading with 2+ accounts

Once Issue #2 is fixed, the complete multi-account automated trading system will be fully operational!

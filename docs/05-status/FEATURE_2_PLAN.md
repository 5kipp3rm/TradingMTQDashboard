# Feature 2: Multi-Account MT Login and Unified UI View - Implementation Plan

**Status:** Planning Complete
**Start Date:** 2024-12-15
**Estimated Effort:** 3-4 days
**Priority:** High

---

## Overview

Feature 2 will enable simultaneous MT5 account logins with a unified dashboard showing aggregated data across all connected accounts. This builds on existing multi-account infrastructure to add real-time connection management and cross-account analytics.

---

## Current Infrastructure Analysis

### ✅ What Already Exists (90% Complete)

#### Database Layer (100% Complete)
- **[src/database/models.py:57-118](../src/database/models.py#L57-L118)** - `TradingAccount` model
  - Stores account credentials, broker, server, login
  - Tracks `is_active`, `is_default`, `is_demo` flags
  - Records `last_connected` timestamp
  - Has audit trail (created_at, updated_at)
  - Foreign key relationships: `trades`, `account_snapshots`, `daily_performance`

#### API Layer (100% Complete)
- **[src/api/routes/accounts.py](../src/api/routes/accounts.py)** - Full CRUD endpoints
  - `GET /api/accounts` - List all accounts (with active_only filter)
  - `GET /api/accounts/{id}` - Get specific account
  - `POST /api/accounts` - Create account (auto-sets first as default)
  - `PUT /api/accounts/{id}` - Update account
  - `DELETE /api/accounts/{id}` - Delete account (reassigns default)
  - `POST /api/accounts/{id}/set-default` - Set default account
  - `POST /api/accounts/{id}/activate` - Activate account
  - `POST /api/accounts/{id}/deactivate` - Deactivate account

#### Frontend Layer (80% Complete)
- **[dashboard/js/account-manager.js](../dashboard/js/account-manager.js)** - Account switching
  - `AccountManager` class with account loading
  - `loadAccounts()` - Fetches accounts from API
  - `setSelectedAccountId()` - Persists selection to localStorage
  - `renderAccountSelector()` - Renders account dropdown
  - `dispatchEvent('accountChanged')` - Notifies components
- **[dashboard/index.html:18](../dashboard/index.html#L18)** - Account selector container
- **[dashboard/js/dashboard.js:26-37](../dashboard/js/dashboard.js#L26-L37)** - Account manager integration
  - Initializes account manager on page load
  - Listens for `accountChanged` event
  - Reloads dashboard data on account switch

#### MT5 Connector Layer (100% Complete)
- **[src/connectors/mt5_connector.py](../src/connectors/mt5_connector.py)** - MT5 connection management
  - `connect()` - Connects to MT5 with credentials
  - `disconnect()` - Disconnects from MT5
  - `is_connected()` - Checks connection status
  - `reconnect()` - Reconnects using stored parameters
  - Supports multiple instances via `instance_id` parameter

---

## ❌ What's Missing (10% Remaining)

### 1. Multi-Session Management (~20% of work)
**Problem:** Current system can only connect to ONE MT5 account at a time.

**Required Changes:**
- Session storage for multiple active MT5 connections
- Connection state tracking per account
- Session lifecycle management (connect/disconnect/reconnect)

### 2. MT5 Login/Connection API (~30% of work)
**Problem:** No API endpoints to connect/disconnect MT5 accounts from UI.

**Required Changes:**
- `POST /api/accounts/{id}/connect` - Initiate MT5 connection
- `POST /api/accounts/{id}/disconnect` - Disconnect MT5 session
- `GET /api/accounts/{id}/status` - Get connection status
- Connection state broadcasting via WebSocket

### 3. Aggregated Analytics (~30% of work)
**Problem:** Dashboard shows data for ONE selected account only.

**Required Changes:**
- Aggregation endpoints for cross-account metrics
- `GET /api/analytics/aggregate` - Combined metrics
- Support filtering: "all accounts" vs "selected account"
- Update dashboard to show aggregated view

### 4. Account Management UI Page (~10% of work)
**Problem:** No UI for CRUD operations (must use API directly).

**Required Changes:**
- `dashboard/accounts.html` - Account management page
- Create/edit/delete account functionality
- Visual connection status indicators
- Connect/disconnect buttons per account

### 5. WebSocket Events (~5% of work)
**Problem:** No real-time notifications for account events.

**Required Changes:**
- Broadcast account connection/disconnection events
- Broadcast account CRUD events
- Update dashboard in real-time

### 6. Testing (~5% of work)
**Problem:** No tests for multi-account features.

**Required Changes:**
- Unit tests for session manager
- API endpoint tests
- Integration tests for multi-account workflows

---

## Implementation Plan

### Phase 1: Multi-Session Management (Day 1)

#### 1.1 Create Session Manager Service
**File:** `src/services/session_manager.py` (NEW - ~300 lines)

```python
class MT5SessionManager:
    """
    Manages multiple MT5 account connections simultaneously.
    """
    def __init__(self):
        self._sessions: Dict[int, MT5Connector] = {}  # account_id -> connector
        self._connection_states: Dict[int, ConnectionState] = {}

    async def connect_account(self, account: TradingAccount) -> bool:
        """Connect to MT5 account and store session"""

    async def disconnect_account(self, account_id: int) -> bool:
        """Disconnect MT5 account and cleanup session"""

    def get_session(self, account_id: int) -> Optional[MT5Connector]:
        """Get active MT5 connector for account"""

    def get_connection_state(self, account_id: int) -> ConnectionState:
        """Get connection status for account"""

    def list_active_sessions(self) -> List[int]:
        """List all connected account IDs"""

    async def reconnect_all(self) -> Dict[int, bool]:
        """Reconnect all previously connected accounts"""
```

**Dependencies:**
- Uses existing `MT5Connector` class
- Manages multiple connector instances
- Thread-safe operation with locks

#### 1.2 Add Connection State Model
**File:** `src/database/models.py` (MODIFY - add ~50 lines)

```python
class AccountConnectionState(Base):
    """Tracks real-time connection status"""
    __tablename__ = 'account_connection_states'

    account_id: Mapped[int] = mapped_column(ForeignKey('trading_accounts.id'))
    is_connected: Mapped[bool] = mapped_column(default=False)
    last_connected_at: Mapped[Optional[datetime]]
    last_disconnected_at: Mapped[Optional[datetime]]
    connection_error: Mapped[Optional[str]]
    retry_count: Mapped[int] = mapped_column(default=0)
```

**Migration:** `alembic revision --autogenerate -m "Add account connection state tracking"`

---

### Phase 2: MT5 Login/Connection API (Day 1-2)

#### 2.1 Add Connection Endpoints
**File:** `src/api/routes/accounts.py` (MODIFY - add ~200 lines)

**New Endpoints:**

1. **POST /api/accounts/{account_id}/connect**
   - Initiates MT5 connection for account
   - Returns connection status
   - Broadcasts WebSocket event: `account_connected`

2. **POST /api/accounts/{account_id}/disconnect**
   - Disconnects MT5 session
   - Updates database state
   - Broadcasts WebSocket event: `account_disconnected`

3. **GET /api/accounts/{account_id}/status**
   - Returns real-time connection status
   - Includes: connected, last_connected, error_message

4. **POST /api/accounts/connect-all**
   - Connects all active accounts
   - Returns list of successes/failures

5. **POST /api/accounts/disconnect-all**
   - Disconnects all accounts
   - Cleanup all sessions

**Example Response:**
```json
{
  "account_id": 123,
  "is_connected": true,
  "last_connected": "2024-12-15T10:30:00Z",
  "connection_status": "active",
  "account_info": {
    "balance": 10000.00,
    "equity": 10250.50,
    "margin_level": 1500.00
  }
}
```

#### 2.2 Add WebSocket Events
**File:** `src/api/websocket.py` (MODIFY - add ~30 lines)

```python
async def broadcast_account_connection_event(
    self,
    event_type: str,  # connected, disconnected, error
    account_data: Dict[str, Any]
):
    """Broadcast account connection event"""
    message = {
        "type": "account_connection",
        "event": event_type,
        "data": account_data
    }
    await self.broadcast(message)
```

**Integration:** Add broadcasts to all connection endpoints

---

### Phase 3: Aggregated Analytics (Day 2)

#### 3.1 Add Analytics Service
**File:** `src/services/analytics_service.py` (NEW - ~400 lines)

```python
class AggregatedAnalyticsService:
    """
    Provides cross-account aggregated metrics.
    """

    async def get_aggregate_performance(
        self,
        account_ids: List[int],
        days: int = 30
    ) -> AggregatePerformance:
        """Get combined performance across accounts"""

    async def get_aggregate_trades(
        self,
        account_ids: List[int],
        limit: int = 100
    ) -> List[Trade]:
        """Get trades from multiple accounts"""

    async def get_account_comparison(
        self,
        account_ids: List[int],
        days: int = 30
    ) -> Dict[int, PerformanceMetrics]:
        """Compare performance across accounts"""
```

#### 3.2 Add Analytics Endpoints
**File:** `src/api/routes/analytics.py` (NEW - ~300 lines)

**New Endpoints:**

1. **GET /api/analytics/aggregate**
   - Query params: `account_ids` (comma-separated), `days`
   - Returns combined metrics across accounts
   - Includes: total trades, net profit, win rate, etc.

2. **GET /api/analytics/comparison**
   - Query params: `account_ids`, `days`
   - Returns side-by-side comparison
   - Includes: per-account breakdown

3. **GET /api/analytics/summary**
   - Returns summary of all accounts
   - Includes: connected count, total balance, total equity

**Example Response:**
```json
{
  "aggregate": {
    "total_accounts": 3,
    "connected_accounts": 2,
    "total_trades": 150,
    "net_profit": 5250.75,
    "win_rate": 65.5,
    "total_balance": 30000.00,
    "total_equity": 31250.75
  },
  "by_account": [
    {
      "account_id": 1,
      "account_name": "Demo 1",
      "trades": 50,
      "profit": 1250.50,
      "win_rate": 68.0
    }
  ]
}
```

---

### Phase 4: Account Management UI (Day 3)

#### 4.1 Create Account Management Page
**File:** `dashboard/accounts.html` (NEW - ~350 lines)

**Features:**
- Account list table with columns:
  - Account Number
  - Account Name
  - Broker / Server
  - Status (Active/Inactive)
  - Connection (Connected/Disconnected with icon)
  - Actions (Connect, Disconnect, Edit, Delete)
- Add Account button → modal form
- Edit Account → modal form (pre-filled)
- Delete Account → confirmation dialog
- Real-time connection status updates via WebSocket

#### 4.2 Account Management JS
**File:** `dashboard/js/accounts.js` (NEW - ~600 lines)

```javascript
class AccountsManager {
    constructor() {
        this.accounts = [];
        this.init();
    }

    async init() {
        await this.loadAccounts();
        this.renderAccounts();
        this.attachEventListeners();
        this.initializeWebSocket();
    }

    async connectAccount(accountId) {
        // POST /api/accounts/{id}/connect
    }

    async disconnectAccount(accountId) {
        // POST /api/accounts/{id}/disconnect
    }

    async createAccount(formData) {
        // POST /api/accounts
    }

    async updateAccount(accountId, formData) {
        // PUT /api/accounts/{id}
    }

    async deleteAccount(accountId) {
        // DELETE /api/accounts/{id}
    }

    renderAccounts() {
        // Render table with accounts
    }

    handleWebSocketEvent(event) {
        // Update UI on connection state changes
    }
}
```

#### 4.3 Account Management CSS
**File:** `dashboard/css/accounts.css` (NEW - ~400 lines)

**Styling:**
- Dark theme matching existing design
- Connection status indicators (green dot = connected, red = disconnected)
- Action buttons (Connect, Disconnect, Edit, Delete)
- Modal forms for add/edit

---

### Phase 5: Dashboard Enhancements (Day 3)

#### 5.1 Add Account Filter to Dashboard
**File:** `dashboard/index.html` (MODIFY - add account filter dropdown)

**Changes:**
- Add filter dropdown: "All Accounts" vs individual accounts
- Update summary cards to show aggregated data
- Add account breakdown section (expandable)

#### 5.2 Update Dashboard JS
**File:** `dashboard/js/dashboard.js` (MODIFY - add ~100 lines)

**Changes:**
- Add `currentAccountFilter` state ("all" or account_id)
- Fetch data from `/api/analytics/aggregate` when filter is "all"
- Fetch data from existing endpoints when specific account selected
- Update charts to show aggregated data
- Add account comparison chart (optional)

#### 5.3 Add Multi-Account Summary Section
**Example:**
```html
<section class="account-summary-section">
    <div class="card">
        <div class="card-header">
            <h3>Account Overview</h3>
        </div>
        <div class="card-body">
            <div class="account-cards">
                <div class="account-card" data-account-id="1">
                    <h4>Demo 1</h4>
                    <div class="status connected">● Connected</div>
                    <div class="metrics">
                        <span>Balance: $10,000</span>
                        <span>Profit: +$250</span>
                    </div>
                </div>
                <!-- Repeat for each account -->
            </div>
        </div>
    </div>
</section>
```

---

### Phase 6: Testing (Day 4)

#### 6.1 Session Manager Tests
**File:** `tests/test_session_manager.py` (NEW - ~400 lines)

**Test Cases:**
- Test connecting single account
- Test connecting multiple accounts
- Test disconnecting account
- Test reconnect on failure
- Test session cleanup
- Test concurrent connections

#### 6.2 Account Connection API Tests
**File:** `tests/test_accounts_connection_api.py` (NEW - ~500 lines)

**Test Cases:**
- Test POST /api/accounts/{id}/connect
- Test POST /api/accounts/{id}/disconnect
- Test GET /api/accounts/{id}/status
- Test connect-all endpoint
- Test disconnect-all endpoint
- Test WebSocket event broadcasting

#### 6.3 Analytics API Tests
**File:** `tests/test_analytics_api.py` (NEW - ~600 lines)

**Test Cases:**
- Test GET /api/analytics/aggregate with multiple accounts
- Test GET /api/analytics/comparison
- Test GET /api/analytics/summary
- Test filtering by date range
- Test handling of missing accounts

#### 6.4 Integration Tests
**File:** `tests/test_multi_account_integration.py` (NEW - ~700 lines)

**Test Cases:**
- Test end-to-end: create account → connect → trade → disconnect
- Test switching between accounts in UI
- Test aggregated analytics with real data
- Test WebSocket real-time updates

---

## File Structure Summary

### New Files to Create (7 files)
```
src/services/session_manager.py          (~300 lines)
src/services/analytics_service.py        (~400 lines)
src/api/routes/analytics.py              (~300 lines)
dashboard/accounts.html                  (~350 lines)
dashboard/js/accounts.js                 (~600 lines)
dashboard/css/accounts.css               (~400 lines)
docs/FEATURE_2_PLAN.md                   (this file)

tests/test_session_manager.py            (~400 lines)
tests/test_accounts_connection_api.py    (~500 lines)
tests/test_analytics_api.py              (~600 lines)
tests/test_multi_account_integration.py  (~700 lines)
```

### Files to Modify (5 files)
```
src/database/models.py                   (+50 lines)   - Add AccountConnectionState model
src/api/routes/accounts.py               (+200 lines)  - Add connect/disconnect endpoints
src/api/websocket.py                     (+30 lines)   - Add account connection events
dashboard/index.html                     (+50 lines)   - Add account filter UI
dashboard/js/dashboard.js                (+100 lines)  - Add aggregated view support
```

### Database Migration
```bash
alembic revision --autogenerate -m "Add account connection state tracking"
alembic upgrade head
```

---

## Code Metrics Estimate

### Production Code
- New Backend: ~1,200 lines (session manager, analytics service, endpoints)
- Modified Backend: ~280 lines (models, existing routes, websocket)
- New Frontend: ~1,350 lines (accounts page HTML/JS/CSS)
- Modified Frontend: ~150 lines (dashboard updates)
- **Total Production: ~2,980 lines**

### Test Code
- Unit Tests: ~900 lines (session manager, endpoints)
- Integration Tests: ~1,700 lines (workflows, analytics)
- **Total Tests: ~2,600 lines**

### Grand Total: ~5,580 lines

---

## Dependencies

### Existing Infrastructure Used
✅ TradingAccount model (src/database/models.py)
✅ Account CRUD API (src/api/routes/accounts.py)
✅ MT5Connector (src/connectors/mt5_connector.py)
✅ WebSocket infrastructure (src/api/websocket.py)
✅ AccountManager class (dashboard/js/account-manager.js)

### New Dependencies Required
- None (uses existing dependencies)

---

## Risk Assessment

### Low Risk ✅
- Database schema changes (additive only)
- API endpoint additions (backward compatible)
- Frontend additions (new pages)

### Medium Risk ⚠️
- MT5 multi-session management (complexity)
  - Mitigation: Thorough testing with multiple accounts
  - Fallback: Support single connection mode initially

- Session state synchronization
  - Mitigation: Use database as source of truth
  - Fallback: Manual reconnect if state mismatches

### High Risk ❌
- None identified

---

## Testing Strategy

### Unit Tests
- Test each service method independently
- Mock external dependencies (MT5 connector, database)
- Validate business logic

### API Tests
- Test each endpoint with valid/invalid inputs
- Test authentication and authorization
- Test WebSocket event broadcasting

### Integration Tests
- Test complete workflows end-to-end
- Test multi-account scenarios
- Test connection failure recovery

### Manual Testing Checklist
- [ ] Connect/disconnect single account
- [ ] Connect multiple accounts simultaneously
- [ ] Switch between accounts in UI
- [ ] View aggregated analytics
- [ ] Create/edit/delete account
- [ ] WebSocket real-time updates
- [ ] Connection failure recovery
- [ ] Session persistence across restarts

---

## Success Criteria

### Must Have ✅
1. Connect to multiple MT5 accounts simultaneously
2. View aggregated performance across all accounts
3. Switch between individual and aggregated views
4. Real-time connection status updates
5. Account management CRUD UI

### Should Have 🎯
1. Auto-reconnect on connection failure
2. Session persistence across server restarts
3. Account comparison charts
4. Connection health monitoring

### Nice to Have 🌟
1. Load balancing across accounts
2. Risk allocation across accounts
3. Account grouping/tagging
4. Historical connection logs

---

## Deployment Plan

### Phase 1: Database Migration
```bash
# Run migration
alembic revision --autogenerate -m "Add account connection state"
alembic upgrade head

# Verify migration
psql -d tradingmtq -c "SELECT * FROM account_connection_states LIMIT 1;"
```

### Phase 2: Backend Deployment
1. Deploy session manager service
2. Deploy analytics service
3. Deploy updated API routes
4. Restart API server

### Phase 3: Frontend Deployment
1. Upload accounts.html page
2. Upload accounts.js and accounts.css
3. Update dashboard.html and dashboard.js
4. Clear browser cache

### Phase 4: Verification
1. Health check: `curl http://localhost:8000/health`
2. Test connect endpoint: `POST /api/accounts/1/connect`
3. Test analytics endpoint: `GET /api/analytics/aggregate`
4. Verify WebSocket events in browser console

---

## Rollback Plan

If critical issues arise:

1. **Database Rollback:**
   ```bash
   alembic downgrade -1
   ```

2. **API Rollback:**
   - Restore previous API code
   - Restart server
   - Multi-account features will be unavailable

3. **Frontend Rollback:**
   - Restore previous HTML/JS files
   - Existing single-account functionality preserved

---

## Post-Implementation Tasks

### Documentation
- [ ] Update API documentation with new endpoints
- [ ] Update user guide with multi-account instructions
- [ ] Document session manager architecture
- [ ] Add analytics endpoint examples

### Monitoring
- [ ] Add metrics for connection success/failure rates
- [ ] Track number of active sessions
- [ ] Monitor aggregated analytics query performance
- [ ] Alert on connection failures

### Optimization Opportunities
- Connection pooling for MT5 sessions
- Caching for aggregated analytics
- Background session health checks
- Batch reconnection on startup

---

## Timeline

| Phase | Task | Duration | Cumulative |
|-------|------|----------|------------|
| 1 | Multi-Session Management | 8 hours | Day 1 |
| 2 | MT5 Connection API | 12 hours | Day 1-2 |
| 3 | Aggregated Analytics | 8 hours | Day 2 |
| 4 | Account Management UI | 10 hours | Day 3 |
| 5 | Dashboard Enhancements | 6 hours | Day 3 |
| 6 | Testing | 10 hours | Day 4 |
| **Total** | | **54 hours** | **~4 days** |

---

## Next Steps

1. ✅ Complete infrastructure analysis (DONE)
2. ⏳ Create implementation plan document (DONE)
3. ⏳ Begin Phase 1: Multi-Session Management
4. ⏳ Create database migration
5. ⏳ Implement session manager service

**Ready to begin implementation!** 🚀

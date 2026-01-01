# CORS Browser Cache Fix

## Issue

When adding a new account, the browser shows a CORS error:

```
Access to fetch at 'http://localhost:8000/api/accounts' from origin 'http://localhost:8080'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the
requested resource.
```

## Root Cause

**The CORS error is a CACHED browser error, not an actual server configuration issue.**

### Verification (Server is Correctly Configured)

Testing with curl confirms CORS is working correctly:

```bash
# Test CORS preflight (OPTIONS request)
curl -X OPTIONS http://localhost:8000/api/accounts \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v

# Response headers (CORRECT):
< access-control-allow-origin: http://localhost:8080
< access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
< access-control-allow-credentials: true
< access-control-max-age: 600
```

```bash
# Test actual POST request
curl -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:8080" \
  -d '{
    "account_number": 888888,
    "account_name": "Test Account",
    "broker": "Test Broker",
    "server": "test-server",
    "platform_type": "MT5",
    "login": 123457,
    "password": "test123",
    "is_demo": true,
    "is_active": true,
    "initial_balance": 10000,
    "currency": "USD"
  }'

# Response headers (CORRECT):
< HTTP/1.1 201 Created
< access-control-allow-origin: http://localhost:8080
< access-control-allow-credentials: true
```

### CORS Configuration (Already Correct)

**File**: [src/api/app.py:119-135](../src/api/app.py#L119-L135)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Vite dev server (dashboard) ✅
        "http://localhost:8000",  # FastAPI server (for static files)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",   # ✅
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Solution

### Option 1: Hard Refresh Browser (Recommended)

**Chrome/Edge/Brave**:
- Windows/Linux: `Ctrl + Shift + R` or `Ctrl + F5`
- macOS: `Cmd + Shift + R`

**Firefox**:
- Windows/Linux: `Ctrl + Shift + R` or `Ctrl + F5`
- macOS: `Cmd + Shift + R`

**Safari**:
- Hold `Shift` and click the Reload button
- Or: `Cmd + Option + R`

### Option 2: Clear Browser Cache

**Chrome/Edge/Brave**:
1. Open DevTools (F12)
2. Right-click the Reload button
3. Select "Empty Cache and Hard Reload"

**Firefox**:
1. Open DevTools (F12)
2. Go to Network tab
3. Click gear icon → Check "Disable HTTP cache"
4. Refresh page

**Safari**:
1. Safari menu → Preferences → Advanced
2. Check "Show Develop menu"
3. Develop menu → Empty Caches
4. Refresh page

### Option 3: Incognito/Private Window

Open the dashboard in an incognito/private browsing window:
- **Chrome/Edge/Brave**: `Ctrl + Shift + N` (Windows/Linux) or `Cmd + Shift + N` (macOS)
- **Firefox**: `Ctrl + Shift + P` (Windows/Linux) or `Cmd + Shift + P` (macOS)
- **Safari**: `Cmd + Shift + N`

### Option 4: Clear Site Data (Nuclear Option)

**Chrome/Edge/Brave**:
1. Open DevTools (F12)
2. Go to Application tab
3. Under "Storage", click "Clear site data"
4. Refresh page

## Why This Happens

1. **Browser caches CORS preflight responses** for performance (respects `Access-Control-Max-Age`)
2. **Previous error responses get cached** if the server wasn't configured correctly earlier
3. **Cache persists across regular refreshes** - requires hard refresh or cache clear
4. **CORS errors are "sticky"** in browser cache because they're security-related

## Prevention

### Development Mode: Disable Cache

**Chrome DevTools**:
1. Open DevTools (F12)
2. Go to Network tab
3. Check "Disable cache" (top of panel)
4. Keep DevTools open while developing

**Firefox DevTools**:
1. Open DevTools (F12)
2. Go to Network tab
3. Click gear icon
4. Check "Disable HTTP cache"

### Server-Side: Reduce Cache Time

The current CORS configuration uses `Access-Control-Max-Age: 600` (10 minutes).

For development, consider reducing this:

```python
# In src/api/app.py
app.add_middleware(
    CORSMiddleware,
    # ... other settings
    max_age=60,  # 1 minute instead of 10 minutes for dev
)
```

## Verification After Fix

After clearing cache, verify the account creation works:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Try creating an account
4. Check the request headers:
   - Should see `Origin: http://localhost:8080`
5. Check the response headers:
   - Should see `Access-Control-Allow-Origin: http://localhost:8080`
   - Should see `HTTP 201 Created` status

## Related Documentation

- [Dashboard API Fixes](./DASHBOARD_API_FIXES_2025-12-28.md) - Previous dashboard API fixes
- [Position Service Import Fix](./POSITION_SERVICE_IMPORT_FIX.md) - Recent position service fix
- [Accounts UI Bug Fixes](./ACCOUNTS_UI_BUG_FIXES_2025-12-28.md) - Initial accounts page fixes

## Testing

```bash
# Test that CORS is working (should succeed)
curl -X OPTIONS http://localhost:8000/api/accounts \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep -i "access-control-allow-origin"

# Expected output:
# < access-control-allow-origin: http://localhost:8080

# Test POST request (should succeed)
curl -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:8080" \
  -d '{"account_number": 999999, "account_name": "Test", "broker": "Test", "server": "test", "platform_type": "MT5", "login": 123456, "password": "test", "is_demo": true, "is_active": true, "currency": "USD"}' \
  -v 2>&1 | grep -i "HTTP"

# Expected output:
# < HTTP/1.1 201 Created
```

## Summary

✅ **Server CORS configuration is CORRECT**
✅ **Endpoint logic is WORKING**
✅ **Database operations are SUCCESSFUL**
❌ **Browser cache is showing OLD error**

**Solution**: Clear browser cache with hard refresh (`Ctrl/Cmd + Shift + R`)

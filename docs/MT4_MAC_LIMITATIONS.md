# MT4 on Mac - Known Limitations

## Issue: MT4 Socket Functions Don't Work on Mac

MT4 on Mac runs through Wine (Windows emulator), which has limitations with network socket functions used by the HTTP bridge EA.

### Why the Bridge EA Doesn't Work on Mac Wine:

1. **Socket Functions**: MQL4 `SocketCreate()`, `SocketBind()`, `SocketListen()` don't work properly in Wine
2. **Network Stack**: Wine's network layer doesn't fully support MT4's socket API
3. **Security**: macOS security may block Wine applications from opening ports

### Alternative Solutions for Mac Users:

## Option 1: Use MT5 Instead (RECOMMENDED)

MT5 has official Python API that works perfectly on Mac:

```bash
pip install MetaTrader5
```

**Advantages:**
- ✅ Official Python package
- ✅ Works natively on Mac  
- ✅ Better performance
- ✅ More modern platform
- ✅ Already implemented in TradingMTQ

**How to Switch:**
1. Download MT5 from MetaQuotes
2. Create MT5 account (or migrate from broker)
3. In TradingMTQ, set platform_type to "MT5"
4. Connect normally - it will just work!

## Option 2: File-Based Communication Bridge

Since sockets don't work, use file-based communication:

**How it works:**
1. MQL4 EA writes data to files in `MQL4/Files/` directory
2. Python connector reads/writes to same directory  
3. Communication via JSON files

**Advantages:**
- ✅ Works with Wine/Mac limitations
- ✅ No network/firewall issues
- ✅ Simple and reliable

**Disadvantages:**
- ❌ Slower (file I/O vs network)
- ❌ Not suitable for high-frequency trading
- ❌ Requires polling for updates

**Implementation:** Coming soon if there's demand

## Option 3: Run MT4 in Windows VM

Run MT4 in actual Windows environment:

**Options:**
- Parallels Desktop (paid)
- VMware Fusion (paid)
- VirtualBox (free)

**Setup:**
1. Install Windows in VM
2. Install MT4 in Windows
3. Set up network bridge between Mac and VM
4. Configure EA to accept connections from Mac IP
5. Update Python connector to use VM's IP address

**Advantages:**
- ✅ Full MT4 functionality
- ✅ Reliable socket support
- ✅ Best for serious trading

**Disadvantages:**
- ❌ Requires Windows license
- ❌ Resource intensive (RAM, CPU)
- ❌ More complex setup

## Option 4: FIX API (If Broker Supports)

Use FIX protocol instead of MT4 API:

See [MT4_INTEGRATION_GUIDE.md](MT4_INTEGRATION_GUIDE.md) for FIX API setup.

**Advantages:**
- ✅ Works from Mac directly
- ✅ Professional-grade
- ✅ No MT4 required (connects to broker)

**Disadvantages:**
- ❌ Requires broker FIX API access
- ❌ May have fees
- ❌ More complex setup

## Recommended Approach for Mac Users

### Short Term: Use MT5

Switch to MT5 which has full Mac support with official Python API.

### Long Term: Windows VM

If you must use MT4, set up Windows VM for proper functionality.

## Testing MT4 Socket Support

To test if your MT4 Wine installation supports sockets:

1. Open MT4
2. Tools → Options → Expert Advisors
3. Check "Allow DLL imports"
4. Attach a simple EA that tries to create a socket
5. Check Experts tab for errors

If you see errors like:
- "SocketCreate failed"
- "SocketBind failed"  
- "Access denied"

Then sockets are not supported in your Wine environment.

## Getting Help

If you're committed to MT4 on Mac:
1. Try updating Wine version (if possible)
2. Check MT4 build version (newer may have better Wine support)
3. Consider contacting broker for Mac-compatible solutions
4. Explore broker's web trading platforms

## Summary

**For Mac users, we strongly recommend using MT5 instead of MT4** due to Wine limitations with socket functionality. MT5 works perfectly on Mac with official Python API support.

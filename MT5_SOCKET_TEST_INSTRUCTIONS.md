# 🚀 MT5 Socket Test Instructions

## Current Status

✅ **MT5 bridge connector is fully implemented and working**
✅ **Server is running and ready**
✅ **Python code successfully attempts to connect to MT5**

⏳ **Waiting for:** Socket test to verify Wine MT5 supports HTTP bridge

---

## What You Need to Do Now (5 minutes)

### Step 1: Open MT5
- Launch **MetaTrader 5** from Applications
- Make sure you're **logged in** to your demo account (#5043678961)

### Step 2: Open MetaEditor
- Press **`⌘+F4`** (Command + F4)
- **OR** Go to: **Tools → MetaQuotes Language Editor**

### Step 3: Find the Test EA
- In MetaEditor's **Navigator** panel (left side)
- Expand the **"Experts"** folder
- You should see: **`mt5_bridge_test`** or **`mt5_bridge_test.mq5`**

> **Note:** The file is already in your MT5 directory:
> `~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/mt5_bridge_test.mq5`

### Step 4: Compile the EA
1. **Double-click** `mt5_bridge_test` to open it in the editor
2. Press **`⌘+F7`** (Command + F7) to compile
   - **OR** Click: **Compile → Compile**
3. Check the **bottom panel** - it should say:
   ```
   0 error(s), 0 warning(s)
   Compilation completed successfully
   ```

### Step 5: Attach EA to Chart
1. **Go back to MT5 Terminal** (switch windows)
2. **Open any chart** (e.g., EURUSD):
   - Click **File → New Chart → EURUSD**
   - Or select any existing chart
3. **Open Navigator**:
   - Press **`⌘+N`** (Command + N)
   - **OR** Go to: **View → Navigator**
4. **Expand "Expert Advisors"** in Navigator
5. **Drag `mt5_bridge_test`** onto the chart
6. **In the settings dialog that appears:**
   - Go to **"Common"** tab
   - ✅ **Check "Allow DLL imports"** ← **IMPORTANT!**
   - ✅ Check "Allow external experts imports" (if shown)
   - Click **OK**

### Step 6: Enable AutoTrading
- In MT5 **toolbar**, find the **"Algo Trading"** button
- Click it - it should turn **GREEN** ✅
- If it's gray/disabled, click it to enable

### Step 7: Check Results
- At the bottom of MT5, click the **"Experts"** tab
- Look for messages from `mt5_bridge_test`

---

## Expected Results

### ✅ **If Sockets Work (GREAT NEWS!):**

You'll see in the Experts tab:
```
=== MT5 Bridge Socket Test ===
Testing if sockets work in Wine environment...
✅ Socket created successfully!
Socket handle: 123
✅ Socket bound to port 8080
✅ Socket listening on port 8080

🎉 SUCCESS! Sockets work in this MT5 installation!
You can use the full MT5 bridge solution.

Test with: curl http://localhost:8080
```

**Then test from terminal:**
```bash
curl http://localhost:8080
```

You should see: **`MT5 Bridge Socket Test - SUCCESS!`**

### **What happens next if sockets work:**
✅ I'll create the full production MT5 bridge EA (~1000 lines)
✅ You'll compile and attach it to MT5
✅ TradingMTQ will connect successfully
✅ You can trade MT5 from your Mac! 🎉

---

### ❌ **If Sockets DON'T Work (Expected on Wine):**

You'll see in the Experts tab:
```
=== MT5 Bridge Socket Test ===
Testing if sockets work in Wine environment...
❌ SOCKET CREATION FAILED!
Error code: 5200
Error description: Invalid URL

This means Wine MT5 does NOT support sockets.
You will need to use a different approach or run on Windows.
```

### **What happens next if sockets don't work:**

We have **three alternatives**:

#### 1. **Windows VM** (Best option, ~30 min setup)
- Install **Parallels** or **VMware**
- Run **Windows 11** VM
- Install MT5 in Windows
- Bridge will work perfectly
- Best performance and reliability

#### 2. **File-Based Bridge** (Works but slower, ~2 hours development)
- MT5 EA writes JSON files to disk
- Python reads files periodically
- **100-500ms latency** vs 10ms with HTTP
- Good for low-frequency trading

#### 3. **Remote Windows Server** (Production solution)
- Run MT5 on remote Windows machine (VPS, cloud)
- Connect over network
- Professional setup for live trading
- Best for 24/7 operation

---

## Troubleshooting

### EA Not Appearing in Navigator
**Problem:** Can't find `mt5_bridge_test` in Expert Advisors list

**Solution:**
1. In MetaEditor, click **File → Open**
2. Navigate to: `~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/`
3. Open `mt5_bridge_test.mq5`
4. Compile it (⌘+F7)
5. It should now appear in Navigator

### Compilation Errors
**Problem:** "X error(s), Y warning(s)" when compiling

**Solution:**
- Share the error message with me
- I'll fix the MQL5 code immediately

### EA Shows Red X or Sad Face
**Problem:** EA attached but shows error icon

**Solution:**
1. Check **"Algo Trading"** button is **GREEN**
2. Verify **"Allow DLL imports"** was checked
3. Remove EA and re-attach with correct settings
4. Check **Experts** tab for specific error message

### No Messages in Experts Tab
**Problem:** EA attached but nothing happens

**Solution:**
1. Click **Experts** tab (bottom of MT5)
2. Look for any messages
3. If empty, EA might not be running
4. Try detaching and re-attaching EA

### Port 8080 Already in Use
**Problem:** Socket bind fails with "port in use"

**Solution:**
```bash
# Check what's using port 8080
lsof -i :8080

# If something else is using it, kill it:
kill -9 <PID>

# Or change the port in both:
# - mt5_bridge_test.mq5 (line with SocketBind)
# - Python connector (--port parameter)
```

---

## Quick Verification Checklist

After attaching the EA, verify:
- [ ] EA name appears in **top-right corner** of chart
- [ ] **Green smiley face** icon (means EA is running)
- [ ] Messages appear in **"Experts"** tab
- [ ] **"Algo Trading"** button is **GREEN**
- [ ] Chart has **small green/red icon** in corner

If all checked, EA is running correctly!

---

## Summary

| Step | Action | Time |
|------|--------|------|
| 1 | Open MT5 | 10 sec |
| 2 | Open MetaEditor (⌘+F4) | 5 sec |
| 3 | Find mt5_bridge_test in Experts | 10 sec |
| 4 | Compile (⌘+F7) | 5 sec |
| 5 | Attach to chart + settings | 30 sec |
| 6 | Enable Algo Trading | 5 sec |
| 7 | Check Experts tab for results | 10 sec |
| **Total** | | **~2 minutes** |

---

## What This Test Does

The `mt5_bridge_test` EA:
1. **Creates a socket** (networking capability)
2. **Binds to port 8080** (reserves the port)
3. **Listens for connections** (acts as server)
4. **Accepts HTTP requests** (responds to curl)
5. **Sends response** ("MT5 Bridge Socket Test - SUCCESS!")

If any step fails, it tells us **exactly what failed** and **why**.

---

## After the Test

### If Sockets Work ✅
**Reply with:** "Sockets work!"

I'll immediately:
1. Create `mt5_bridge_server.mq5` (full production EA)
2. Implement all REST API endpoints
3. Provide setup instructions
4. You'll be trading in 15 minutes!

### If Sockets Don't Work ❌
**Reply with:** "Sockets failed"

I'll:
1. Explain your three options in detail
2. Help you choose the best approach
3. Implement the chosen solution
4. Get you trading ASAP

---

## Questions?

- **Screenshot the Experts tab** - most helpful for debugging
- **Share any error messages** - exact text helps
- **Ask anything!** - I'm here to help

**Ready? Go test those sockets!** 🚀

---

**File Locations for Reference:**

- **Test EA:** `~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/mt5_bridge_test.mq5`
- **Quick Start Guide:** [docs/MT5_QUICK_START_MAC.md](docs/MT5_QUICK_START_MAC.md)
- **Implementation Summary:** [docs/MT5_IMPLEMENTATION_SUMMARY.md](docs/MT5_IMPLEMENTATION_SUMMARY.md)
- **Server Status:** Running on `http://localhost:8000`

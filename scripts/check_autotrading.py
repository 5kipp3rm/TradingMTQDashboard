#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check MT5 Auto-Trading Status
Quick check if algorithmic trading is enabled
"""
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

import MetaTrader5 as mt5
import subprocess
import time
import os
import winreg

def check_mt5_running():
    """Check if MT5 terminal is running"""
    try:
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        return 'terminal64.exe' in result.stdout.lower() or 'terminal.exe' in result.stdout.lower()
    except:
        return False

def find_mt5_executable():
    """Find MT5 installation path from registry"""
    paths_to_check = [
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    ]
    
    # Check registry
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\MetaQuotes\MetaTrader 5")
        install_path = winreg.QueryValueEx(key, "Install_Path")[0]
        winreg.CloseKey(key)
        paths_to_check.insert(0, os.path.join(install_path, "terminal64.exe"))
    except:
        pass
    
    for path in paths_to_check:
        if os.path.exists(path):
            return path
    return None

def start_mt5():
    """Start MT5 terminal if not running"""
    if check_mt5_running():
        print("✓ MT5 already running")
        return True
    
    print("⚠️  MT5 not running, attempting to start...")
    mt5_path = find_mt5_executable()
    
    if not mt5_path:
        print("❌ Could not find MT5 installation!")
        return False
    
    try:
        subprocess.Popen([mt5_path])
        print(f"✓ Starting MT5 from {mt5_path}")
        print("⏳ Waiting 5 seconds for MT5 to initialize...")
        time.sleep(5)
        return True
    except Exception as e:
        print(f"❌ Failed to start MT5: {e}")
        return False

print("\n" + "=" * 80)
print("  MT5 AUTO-TRADING STATUS CHECK")
print("=" * 80)

# Check/start MT5
print("\n🔍 Checking MT5 terminal...")
if not start_mt5():
    print("\n❌ Please start MetaTrader 5 manually and try again.")
    sys.exit(1)

print("\n📡 Connecting to MT5...")
if not mt5.initialize():
    print("\n❌ Could not connect to MT5")
    print("   Please ensure MT5 is running")
    exit(1)

terminal_info = mt5.terminal_info()

print(f"\nMT5 Terminal Information:")
print(f"  Path: {terminal_info.path}")
print(f"  Build: {terminal_info.build}")
print(f"  Trade Allowed: {terminal_info.trade_allowed}")
print(f"  Algo Trading: {terminal_info.algos_allowed if hasattr(terminal_info, 'algos_allowed') else 'N/A'}")

print("\n" + "-" * 80)

if terminal_info.trade_allowed:
    print("\n✅ AUTO-TRADING IS ENABLED!")
    print("\n   Your system is ready to place trades!")
    print("\n   Next step: python run.py")
else:
    print("\n❌ AUTO-TRADING IS DISABLED!")
    print("\n   📋 TO ENABLE AUTO-TRADING:")
    print("\n   Method 1: Toolbar Button")
    print("      - Look for 'AutoTrading' button in MT5 toolbar")
    print("      - Click it (should turn green/enabled)")
    print("\n   Method 2: Settings")
    print("      1. Open MT5")
    print("      2. Click Tools → Options")
    print("      3. Go to 'Expert Advisors' tab")
    print("      4. Check ✅ 'Allow algorithmic trading'")
    print("      5. Check ✅ 'Allow DLL imports' (if needed)")
    print("      6. Click OK")
    print("\n   Then run this script again to verify!")

print("\n" + "=" * 80 + "\n")

mt5.shutdown()

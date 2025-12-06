#!/usr/bin/env python
"""
Start MT5 Terminal
Utility to find and launch MetaTrader 5
"""
import os
import sys
import subprocess
import time
import winreg


def find_mt5_executable():
    """Find MT5 terminal executable"""
    print("🔍 Searching for MT5 installation...")
    
    # Common installation paths
    possible_paths = [
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        r"C:\Program Files\MetaTrader 5\terminal.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal.exe",
    ]
    
    # Try to find from registry
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\MetaQuotes\MetaTrader 5")
        install_path = winreg.QueryValueEx(key, "Install Path")[0]
        winreg.CloseKey(key)
        
        if install_path:
            print(f"  Found installation path in registry: {install_path}")
            possible_paths.insert(0, os.path.join(install_path, "terminal64.exe"))
            possible_paths.insert(1, os.path.join(install_path, "terminal.exe"))
    except:
        print("  Registry search: Not found")
    
    # Try HKEY_CURRENT_USER as well
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\MetaQuotes\MetaTrader 5")
        install_path = winreg.QueryValueEx(key, "Install Path")[0]
        winreg.CloseKey(key)
        
        if install_path:
            print(f"  Found installation path in user registry: {install_path}")
            possible_paths.insert(0, os.path.join(install_path, "terminal64.exe"))
            possible_paths.insert(1, os.path.join(install_path, "terminal.exe"))
    except:
        pass
    
    # Check which path exists
    print("\n  Checking possible locations:")
    for path in possible_paths:
        if os.path.exists(path):
            print(f"  ✓ Found: {path}")
            return path
        else:
            print(f"  ✗ Not found: {path}")
    
    return None


def is_mt5_running():
    """Check if MT5 is already running"""
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            mt5.shutdown()
            return True
        return False
    except:
        return False


def start_mt5():
    """Start MT5 terminal"""
    print("\n" + "=" * 80)
    print("  MT5 LAUNCHER")
    print("=" * 80)
    
    # Check if already running
    if is_mt5_running():
        print("\n✓ MT5 is already running!")
        print("\nYou can now run your trading scripts:")
        print("  $ python run.py")
        print("  $ python examples/quick_start.py")
        return True
    
    # Find MT5 executable
    mt5_path = find_mt5_executable()
    
    if not mt5_path:
        print("\n" + "=" * 80)
        print("❌ MT5 NOT FOUND")
        print("=" * 80)
        print("\n💡 SOLUTIONS:")
        print("\n1. Install MetaTrader 5:")
        print("   Download from: https://www.metatrader5.com/en/download")
        print("\n2. If already installed, specify the path:")
        print("   $ python start_mt5.py --path \"C:\\Path\\To\\terminal64.exe\"")
        print("\n" + "=" * 80)
        return False
    
    # Start MT5
    print("\n" + "-" * 80)
    print("🚀 Starting MT5...")
    print("-" * 80)
    
    try:
        # Start MT5 process
        process = subprocess.Popen(
            [mt5_path],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"\n✓ MT5 process started (PID: {process.pid})")
        print(f"  Executable: {mt5_path}")
        
        # Wait for MT5 to initialize
        print("\n⏳ Waiting for MT5 to initialize (this may take 5-10 seconds)...")
        
        max_wait = 15
        for i in range(max_wait):
            time.sleep(1)
            if is_mt5_running():
                print(f"\n✓ MT5 is ready! (took {i+1} seconds)")
                break
            print(f"  Waiting... {i+1}/{max_wait}", end='\r')
        else:
            print(f"\n⚠ MT5 started but initialization check timed out")
            print(f"  MT5 may still be loading. Give it a few more seconds.")
        
        print("\n" + "=" * 80)
        print("✓ MT5 TERMINAL STARTED")
        print("=" * 80)
        print("\n📋 NEXT STEPS:")
        print("  1. MT5 window should now be open")
        print("  2. Login to your account (or leave on login screen)")
        print("  3. Run your trading script:")
        print("     $ python run.py")
        print("     $ python examples/quick_start.py")
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to start MT5: {e}")
        print("\n💡 Try starting MT5 manually from Start Menu")
        return False


def main():
    """Main entry point"""
    # Check for custom path argument
    if len(sys.argv) > 2 and sys.argv[1] == '--path':
        custom_path = sys.argv[2]
        if os.path.exists(custom_path):
            print(f"Using custom MT5 path: {custom_path}")
            try:
                subprocess.Popen([custom_path], shell=True)
                print("✓ Started MT5 from custom path")
                return
            except Exception as e:
                print(f"✗ Failed: {e}")
                return
        else:
            print(f"✗ Path does not exist: {custom_path}")
            return
    
    start_mt5()


if __name__ == "__main__":
    main()

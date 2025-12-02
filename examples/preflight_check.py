"""
Pre-Flight Check
Verifies system is ready for live trading
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("\n" + "=" * 80)
print("  PRE-FLIGHT CHECK - LIVE TRADING READINESS")
print("=" * 80)

checks_passed = 0
checks_total = 0

# Check 1: MT5 Module
checks_total += 1
try:
    import MetaTrader5 as mt5
    version = mt5.__version__ if hasattr(mt5, '__version__') else "Unknown"
    print(f"\n✓ MetaTrader5 module installed (version: {version})")
    checks_passed += 1
except ImportError:
    print("\n✗ MetaTrader5 module NOT installed")
    print("  Install: pip install MetaTrader5")

# Check 2: Required packages
checks_total += 1
try:
    import numpy
    import pandas
    print(f"✓ NumPy and Pandas installed")
    checks_passed += 1
except ImportError as e:
    print(f"✗ Missing package: {e.name}")
    print("  Install: pip install numpy pandas")

# Check 3: Project imports
checks_total += 1
try:
    from src.connectors import MT5Connector, AccountUtils
    from src.strategies import SimpleMovingAverageStrategy
    print("✓ Project modules import successfully")
    checks_passed += 1
except ImportError as e:
    print(f"✗ Failed to import project modules: {e}")

# Check 4: Error descriptions
checks_total += 1
try:
    from src.connectors import trade_server_return_code_description, error_description
    test_desc = trade_server_return_code_description(10009)
    if "completed" in test_desc.lower():
        print("✓ Error descriptions working")
        checks_passed += 1
    else:
        print("✗ Error descriptions not returning expected values")
except Exception as e:
    print(f"✗ Error descriptions failed: {e}")

# Check 5: MT5 installation
checks_total += 1
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        terminal_info = mt5.terminal_info()
        if terminal_info:
            print(f"✓ MT5 terminal detected")
            print(f"  Path: {terminal_info.path}")
            print(f"  Build: {terminal_info.build}")
            checks_passed += 1
        else:
            print("✗ MT5 terminal info not available")
        mt5.shutdown()
    else:
        print("✗ MT5 terminal not running or not installed")
        print("  Please ensure MT5 is installed and running")
except Exception as e:
    print(f"✗ MT5 check failed: {e}")

# Check 6: Strategy test
checks_total += 1
try:
    from src.strategies import SimpleMovingAverageStrategy
    from src.connectors.base import OHLCBar
    from datetime import datetime
    
    strategy = SimpleMovingAverageStrategy({'fast_period': 10, 'slow_period': 20})
    
    # Create test bars
    test_bars = [
        OHLCBar(datetime.now(), 1.0850 + i*0.0001, 1.0852 + i*0.0001, 
                1.0848 + i*0.0001, 1.0851 + i*0.0001, 1000)
        for i in range(30)
    ]
    
    signal = strategy.analyze("EURUSD", "M5", test_bars)
    
    if signal:
        print("✓ Strategy generates signals correctly")
        checks_passed += 1
    else:
        print("✗ Strategy not generating signals")
except Exception as e:
    print(f"✗ Strategy test failed: {e}")

# Check 7: AccountUtils test
checks_total += 1
try:
    from src.connectors import AccountUtils
    import MetaTrader5 as mt5
    
    # Just verify the functions exist
    if hasattr(AccountUtils, 'risk_based_lot_size') and \
       hasattr(AccountUtils, 'margin_check'):
        print("✓ AccountUtils available with risk management functions")
        checks_passed += 1
    else:
        print("✗ AccountUtils missing required functions")
except Exception as e:
    print(f"✗ AccountUtils test failed: {e}")

# Check 8: Live trading script
checks_total += 1
import os.path
script_path = os.path.join(os.path.dirname(__file__), 'live_trading.py')
if os.path.exists(script_path):
    # Check if credentials are updated
    with open(script_path, 'r') as f:
        content = f.read()
        if 'MT5_LOGIN = 12345678' in content:
            print("⚠ Live trading script exists but credentials NOT updated")
            print("  Update MT5_LOGIN, MT5_PASSWORD, MT5_SERVER before running")
        else:
            print("✓ Live trading script exists and appears configured")
            checks_passed += 1
else:
    print("✗ live_trading.py not found")

# Summary
print("\n" + "=" * 80)
print(f"  RESULTS: {checks_passed}/{checks_total} checks passed")
print("=" * 80)

if checks_passed == checks_total:
    print("\n🎉 SYSTEM READY FOR LIVE TRADING!")
    print("\nNext steps:")
    print("  1. Update credentials in examples/live_trading.py")
    print("  2. Review LIVE_TRADING_GUIDE.md")
    print("  3. Start with DEMO account")
    print("  4. Run: python examples/live_trading.py")
elif checks_passed >= checks_total - 1:
    print("\n⚠ ALMOST READY - Minor issues detected")
    print("\nReview the failed checks above and fix them")
    print("Most issues can be resolved by:")
    print("  - Installing missing packages")
    print("  - Updating credentials in scripts")
    print("  - Ensuring MT5 is running")
else:
    print("\n✗ SYSTEM NOT READY - Multiple issues detected")
    print("\nPlease resolve the failed checks above before proceeding")
    print("\nCommon fixes:")
    print("  - pip install MetaTrader5 numpy pandas")
    print("  - Install MT5 from https://www.metatrader5.com/")
    print("  - Verify all project files are present")

print("\n" + "=" * 80 + "\n")

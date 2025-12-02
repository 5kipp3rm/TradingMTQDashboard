#!/usr/bin/env python
"""
TradingMTQ - Main Entry Point
Run this script to start the automated trading system

This script performs comprehensive system checks before launching:
- Verifies Python packages installed
- Tests MT5 terminal connection
- Validates project modules
- Checks configuration
- Offers multiple trading modes
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print("✓ Loaded .env file")
else:
    print("⚠ No .env file found (using .env.example as template)")

# Add project paths
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))


def print_header():
    """Print application header"""
    print("\n" + "=" * 80)
    print(" " * 25 + "TradingMTQ - Automated Trading System")
    print("=" * 80)


def check_dependencies():
    """Check required Python packages"""
    print("\n🔍 Checking dependencies...")
    
    required = {
        'MetaTrader5': 'MetaTrader5',
        'numpy': 'numpy',
        'pandas': 'pandas',
    }
    
    missing = []
    for package, import_name in required.items():
        try:
            __import__(import_name)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def find_mt5_executable():
    """Find MT5 terminal executable"""
    import winreg
    
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
            possible_paths.insert(0, os.path.join(install_path, "terminal64.exe"))
            possible_paths.insert(1, os.path.join(install_path, "terminal.exe"))
    except:
        pass
    
    # Check which path exists
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def start_mt5_terminal():
    """Start MT5 terminal if not running"""
    import subprocess
    
    print("  🚀 Attempting to start MT5 terminal...")
    
    mt5_path = find_mt5_executable()
    
    if not mt5_path:
        print(f"  ✗ Could not find MT5 installation")
        print(f"  📥 Download MT5 from: https://www.metatrader5.com/en/download")
        return False
    
    try:
        print(f"  Found MT5 at: {mt5_path}")
        
        # Start MT5 (don't wait for it to close)
        subprocess.Popen([mt5_path], 
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        
        print(f"  ✓ MT5 terminal started!")
        print(f"  ⏳ Waiting 5 seconds for MT5 to initialize...")
        
        import time
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to start MT5: {e}")
        return False


def check_mt5_terminal(auto_start=True):
    """Check if MT5 terminal is available, optionally auto-start it"""
    print("\n🔍 Checking MT5 terminal...")
    
    try:
        import MetaTrader5 as mt5
        
        if mt5.initialize():
            terminal_info = mt5.terminal_info()
            if terminal_info:
                print(f"  ✓ MT5 terminal found and running")
                print(f"    Path: {terminal_info.path}")
                print(f"    Build: {terminal_info.build}")
                mt5.shutdown()
                return True
            else:
                print(f"  ⚠ MT5 initialized but terminal info unavailable")
                mt5.shutdown()
                return True
        else:
            print(f"  ⚠ MT5 terminal not currently running")
            
            if auto_start:
                if start_mt5_terminal():
                    # Try to initialize again
                    if mt5.initialize():
                        print(f"  ✓ Successfully connected to MT5!")
                        mt5.shutdown()
                        return True
            
            print(f"\n  💡 MANUAL SOLUTION:")
            print(f"     1. Open MetaTrader 5 application manually")
            print(f"     2. Keep MT5 running, then run this script again")
            print(f"\n  📥 Don't have MT5? Download from: https://www.metatrader5.com/en/download")
            return False
    
    except Exception as e:
        print(f"  ✗ Error checking MT5: {e}")
        print(f"\n  💡 Install MetaTrader5 package: pip install MetaTrader5")
        return False


def check_project_modules():
    """Check project modules can be imported"""
    print("\n🔍 Checking project modules...")
    
    modules = [
        ('src.connectors', 'MT5 Connector'),
        ('src.strategies', 'Trading Strategies'),
        ('src.connectors.account_utils', 'Account Utilities'),
    ]
    
    for module, name in modules:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ✗ {name} - Import failed: {e}")
            return False
    
    return True


def get_credentials():
    """Get MT5 credentials from user or environment"""
    print("\n🔐 MT5 Credentials")
    print("-" * 80)
    
    # Try environment variables first
    login = os.getenv('MT5_LOGIN')
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')
    
    if login and password and server:
        print(f"  Using credentials from environment variables")
        print(f"  Server: {server}")
        print(f"  Login: {login}")
        
        use_env = input("\n  Use these credentials? (yes/no): ").strip().lower()
        if use_env in ['yes', 'y']:
            return int(login), password, server
    
    # Get from user input
    print("\n  Enter your MT5 credentials:")
    login = input("  Login: ").strip()
    password = input("  Password: ").strip()
    server = input("  Server: ").strip()
    
    if not login or not password or not server:
        print("\n❌ All credentials are required!")
        return None, None, None
    
    return int(login), password, server


def test_connection(login, password, server):
    """Test MT5 connection"""
    print("\n🔌 Testing MT5 connection...")
    
    try:
        from src.connectors import MT5Connector
        
        connector = MT5Connector("test")
        if connector.connect(login, password, server):
            print("  ✓ Connection successful!")
            
            account = connector.get_account_info()
            if account:
                print(f"\n  Account Information:")
                print(f"    Login: {account.login}")
                print(f"    Server: {account.server}")
                print(f"    Balance: ${account.balance:,.2f}")
                print(f"    Equity: ${account.equity:,.2f}")
                print(f"    Leverage: 1:{account.leverage}")
            
            connector.disconnect()
            return True
        else:
            print("  ✗ Connection failed!")
            return False
    
    except Exception as e:
        print(f"  ✗ Connection error: {e}")
        return False


def show_menu():
    """Show trading mode menu"""
    print("\n" + "=" * 80)
    print("  SELECT TRADING MODE")
    print("=" * 80)
    print("\n1. Quick Start Trading (Interactive)")
    print("   - Prompts for settings")
    print("   - Simple MA Crossover strategy")
    print("   - Risk-based position sizing")
    print("   - Recommended for beginners")
    
    print("\n2. Full Automated Bot")
    print("   - Comprehensive features")
    print("   - Multiple strategy options")
    print("   - Advanced risk management")
    print("   - Market analysis")
    
    print("\n3. Position Manager")
    print("   - View open positions")
    print("   - Close positions")
    print("   - No trading")
    
    print("\n4. Test Connection Only")
    print("   - Verify MT5 connection")
    print("   - Display account info")
    print("   - Safe - no trading")
    
    print("\n5. Exit")
    
    choice = input("\nChoice (1-5): ").strip()
    return choice


def run_quick_start(login, password, server):
    """Run quick start trading"""
    print("\n" + "=" * 80)
    print("  QUICK START TRADING")
    print("=" * 80)
    
    # Import here to avoid issues if not all modules available
    import MetaTrader5 as mt5
    from datetime import datetime
    import time
    from src.connectors import MT5Connector, OrderType, AccountUtils
    from src.strategies import SimpleMovingAverageStrategy, SignalType
    from src.connectors.base import TradeRequest
    
    # Get settings
    symbol = input("\nSymbol (default: EURUSD): ").strip() or "EURUSD"
    risk = input("Risk % per trade (default: 1.0): ").strip() or "1.0"
    risk_percent = float(risk)
    
    # Connect
    connector = MT5Connector()
    print(f"\nConnecting to {server}...")
    
    if not connector.connect(login, password, server):
        print("✗ Connection failed!")
        return
    
    print("✓ Connected!")
    
    # Verify symbol
    symbol_info = connector.get_symbol_info(symbol)
    if not symbol_info:
        print(f"✗ Symbol {symbol} not available!")
        connector.disconnect()
        return
    
    print(f"\nSymbol: {symbol}")
    print(f"Bid: {symbol_info.bid:.5f}, Ask: {symbol_info.ask:.5f}")
    
    # Create strategy
    strategy = SimpleMovingAverageStrategy({
        'fast_period': 10,
        'slow_period': 20,
        'sl_pips': 20,
        'tp_pips': 40
    })
    
    print(f"\nStrategy: {strategy.name}")
    print(f"Risk: {risk_percent}%")
    
    # Confirm
    print("\n" + "!" * 80)
    print("  WARNING: This will execute REAL trades!")
    print("!" * 80)
    confirm = input("\nType 'GO' to start: ").strip().upper()
    
    if confirm != 'GO':
        print("Cancelled")
        connector.disconnect()
        return
    
    print("\n" + "=" * 80)
    print("  TRADING ACTIVE - Press Ctrl+C to stop")
    print("=" * 80)
    
    last_signal_time = None
    
    try:
        while True:
            bars = connector.get_bars(symbol, 'M5', 100)
            
            if not bars:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to get data")
                time.sleep(30)
                continue
            
            signal = strategy.analyze(symbol, 'M5', bars)
            current_price = bars[-1].close
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
                  f"{symbol} @ {current_price:.5f} - "
                  f"Signal: {signal.type.name} ({signal.confidence:.0%})")
            
            if signal.type != SignalType.HOLD:
                if last_signal_time:
                    elapsed = (datetime.now() - last_signal_time).total_seconds()
                    if elapsed < 60:
                        print(f"  ⏭ Skipping (too soon: {elapsed:.0f}s)")
                        time.sleep(30)
                        continue
                
                # Convert signal type to MT5 order type for risk calculation
                mt5_order_type = mt5.ORDER_TYPE_BUY if signal.type == SignalType.BUY else mt5.ORDER_TYPE_SELL
                lot_size = AccountUtils.risk_based_lot_size(
                    symbol, mt5_order_type, signal.price, signal.stop_loss, risk_percent
                )
                
                if not lot_size:
                    lot_size = symbol_info.volume_min
                
                print(f"  📊 Executing {signal.type.name} - {lot_size:.2f} lots")
                
                # Convert to OrderType enum for TradeRequest
                action = OrderType.BUY if signal.type == SignalType.BUY else OrderType.SELL
                
                result = connector.send_order(
                    TradeRequest(
                        symbol=symbol,
                        action=action,
                        volume=lot_size,
                        price=signal.price,
                        sl=signal.stop_loss,
                        tp=signal.take_profit
                    )
                )
                
                if result.success:
                    print(f"  ✓ Order #{result.order_ticket} executed @ {result.price:.5f}")
                    last_signal_time = datetime.now()
                else:
                    print(f"  ✗ Failed: {result.error_message}")
            
            time.sleep(30)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Stopped by user")
    finally:
        positions = connector.get_positions(symbol=symbol)
        if positions:
            print(f"\n📍 Open positions: {len(positions)}")
            for pos in positions:
                print(f"   #{pos.ticket} - {'BUY' if pos.type == 0 else 'SELL'} "
                      f"{pos.volume:.2f} @ {pos.price_open:.5f} - P/L: ${pos.profit:.2f}")
        
        connector.disconnect()
        print("\n✓ Disconnected")


def run_position_manager(login, password, server):
    """Run position manager"""
    os.system(f'python examples/manage_positions.py')


def main():
    """Main entry point"""
    import sys
    
    print_header()
    
    # Pre-flight checks
    print("\n🚀 PRE-FLIGHT CHECKS")
    print("=" * 80)
    
    if not check_dependencies():
        print("\n❌ Dependency check failed!")
        print("Please install required packages and try again.")
        return 1
    
    if not check_mt5_terminal():
        print("\n⚠ MT5 terminal check failed!")
        print("Please ensure MT5 is installed and running.")
        return 1
    
    if not check_project_modules():
        print("\n❌ Project module check failed!")
        print("Please verify project structure is correct.")
        return 1
    
    print("\n✅ All checks passed!")
    
    # Get credentials (auto-load from .env)
    login, password, server = get_credentials()
    
    if not login:
        print("\n❌ Credentials required to continue!")
        return 1
    
    # Test connection
    if not test_connection(login, password, server):
        print("\n❌ Connection test failed!")
        print("Please check your credentials and try again.")
        return 1
    
    # Check for command-line mode selection
    mode = 'quick'  # Default mode
    
    if len(sys.argv) > 1:
        mode_arg = sys.argv[1].lower()
        if mode_arg in ['--full', '-f']:
            mode = 'full'
        elif mode_arg in ['--positions', '-p']:
            mode = 'positions'
        elif mode_arg in ['--test', '-t']:
            mode = 'test'
        elif mode_arg in ['--menu', '-m']:
            mode = 'menu'
        elif mode_arg in ['--help', '-h']:
            print("\nUsage: python run.py [OPTIONS]")
            print("\nOptions:")
            print("  (none)              Start Quick Trading (default)")
            print("  --full, -f          Full Automated Bot")
            print("  --positions, -p     Position Manager")
            print("  --test, -t          Test Connection Only")
            print("  --menu, -m          Show Interactive Menu")
            print("  --help, -h          Show this help")
            return 0
    
    # Execute based on mode
    if mode == 'menu':
        # Original menu behavior
        while True:
            choice = show_menu()
            
            if choice == '1':
                run_quick_start(login, password, server)
                break
            elif choice == '2':
                print("\n📝 Note: Edit examples/live_trading.py to configure the full bot")
                print("Then run: python examples/live_trading.py")
                break
            elif choice == '3':
                run_position_manager(login, password, server)
                break
            elif choice == '4':
                print("\n✓ Connection test already completed above!")
                break
            elif choice == '5':
                print("\nGoodbye!")
                return 0
            else:
                print("\n❌ Invalid choice. Please select 1-5.")
    
    elif mode == 'quick':
        # Direct Quick Start trading
        print("\n🚀 Starting Quick Trading Mode...")
        print("   (Use --help to see other options)")
        run_quick_start(login, password, server)
    
    elif mode == 'full':
        print("\n📝 Note: Edit examples/live_trading.py to configure the full bot")
        print("Then run: python examples/live_trading.py")
    
    elif mode == 'positions':
        run_position_manager(login, password, server)
    
    elif mode == 'test':
        print("\n✓ Connection test already completed above!")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

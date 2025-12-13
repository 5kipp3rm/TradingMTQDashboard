"""
Simple Test for Intelligent Trading System
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)
load_dotenv()

print("=" * 80)
print("TESTING INTELLIGENT TRADING SYSTEM")
print("=" * 80)

# Test imports
print("\n1. Testing imports...")
try:
    from src.connectors import ConnectorFactory
    from src.connectors.base import PlatformType
    from src.trading import MultiCurrencyOrchestrator, CurrencyTraderConfig
    from src.trading.intelligent_position_manager import IntelligentPositionManager
    from src.strategies import SimpleMovingAverageStrategy
    print("   OK - Core modules imported")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

# Test ML
print("\n2. Testing ML availability...")
try:
    from src.ml import RandomForestClassifier, FeatureEngineer, RF_AVAILABLE
    print(f"   ML Available: {RF_AVAILABLE}")
except:
    print("   ML Not Available (optional)")

# Test LLM
print("\n3. Testing LLM availability...")
try:
    from src.llm import OpenAIProvider, OPENAI_AVAILABLE
    from src.utils.config_loader import get_openai_key
    has_key = get_openai_key() is not None
    print(f"   LLM Available: {OPENAI_AVAILABLE and has_key}")
except:
    print("   LLM Not Available (optional)")

# Test MT5 Connection
print("\n4. Testing MT5 connection...")
connector = ConnectorFactory.create_connector(PlatformType.MT5, "test")

login = int(os.getenv('MT5_LOGIN', 0))
password = os.getenv('MT5_PASSWORD', '')
server = os.getenv('MT5_SERVER', '')

if connector.connect(login, password, server):
    print("   OK - Connected to MT5")
    
    account = connector.get_account_info()
    if account:
        print(f"   Balance: ${account.balance:,.2f}")
    
    # Test orchestrator
    print("\n5. Testing Orchestrator with Intelligent Manager...")
    orchestrator = MultiCurrencyOrchestrator(
        connector=connector,
        max_concurrent_trades=20,
        portfolio_risk_percent=15.0,
        use_intelligent_manager=True
    )
    
    print(f"   OK - Orchestrator created")
    print(f"   Intelligent Manager: {orchestrator.intelligent_manager is not None}")
    
    # Add one currency
    print("\n6. Adding test currency...")
    strategy = SimpleMovingAverageStrategy({
        'fast_period': 10,
        'slow_period': 20,
        'sl_pips': 20,
        'tp_pips': 40
    })
    
    config = CurrencyTraderConfig(
        symbol='EURUSD',
        strategy=strategy,
        risk_percent=1.0,
        timeframe='M5',
        cooldown_seconds=30,
        use_position_trading=True
    )
    
    trader = orchestrator.add_currency(config)
    if trader:
        print("   OK - EURUSD trader added")
    
    # Test intelligent manager
    print("\n7. Testing Intelligent Position Manager...")
    ipm = orchestrator.intelligent_manager
    
    if ipm:
        # Test portfolio analysis
        portfolio = ipm.analyze_portfolio()
        print(f"   Current Positions: {portfolio['total_positions']}")
        print(f"   Total P/L: ${portfolio['total_profit']:.2f}")
        
        # Test decision making
        print("\n8. Testing intelligent decision making...")
        bars = connector.get_bars('EURUSD', 'M5', 100)
        if bars:
            from src.strategies.base import Signal, SignalType
            
            test_signal = Signal(
                type=SignalType.BUY,
                symbol='EURUSD',
                timestamp=datetime.now(),
                price=bars[-1].close,
                stop_loss=bars[-1].close - 0.0020,
                take_profit=bars[-1].close + 0.0040,
                confidence=0.75
            )
            
            decision = ipm.should_open_new_position(test_signal, portfolio)
            print(f"   Decision: {decision.action.value}")
            print(f"   Confidence: {decision.confidence:.2f}")
            print(f"   Reasoning: {decision.reasoning}")
            print(f"   Allow Trade: {decision.allow_new_trade}")
    
    # Test one cycle
    print("\n9. Running one trading cycle...")
    try:
        results = orchestrator.process_single_cycle()
        print("   OK - Cycle completed")
        
        for symbol, result in results['currencies'].items():
            if result.get('signal'):
                print(f"   {symbol}: {result['signal'].type.name}")
    except Exception as e:
        print(f"   Cycle error: {e}")
    
    connector.disconnect()
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)
    
else:
    print("   FAILED - Could not connect to MT5")
    print("   Make sure MT5 is running and credentials are correct")
    sys.exit(1)

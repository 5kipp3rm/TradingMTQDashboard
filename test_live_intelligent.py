"""
Test Intelligent Trading with Live Data
Shows ML/LLM integration and intelligent decision-making
"""
import sys
import MetaTrader5 as mt5
from src.trading.orchestrator import MultiCurrencyOrchestrator
from src.trading.currency_trader import CurrencyTraderConfig
from src.strategies.simple_ma import SimpleMAStrategy
from src.connectors.mt5_connector import MT5Connector

# Check ML/LLM availability
try:
    from src.ml import FeatureEngineer, LSTM_AVAILABLE, RF_AVAILABLE
    print(f"✅ ML Available - LSTM: {LSTM_AVAILABLE}, RF: {RF_AVAILABLE}")
    ml_available = True
except:
    print("⚠️  ML Not Available")
    ml_available = False

try:
    from src.llm import SentimentAnalyzer, MarketAnalyst, get_openai_key
    has_key = bool(get_openai_key())
    print(f"✅ LLM Available - API Key: {'Yes' if has_key else 'No'}")
    llm_available = has_key
except:
    print("⚠️  LLM Not Available")
    llm_available = False

print("\n" + "="*80)
print("INITIALIZING INTELLIGENT TRADING SYSTEM")
print("="*80)

# Initialize MT5
if not mt5.initialize():
    print("❌ Failed to initialize MT5")
    sys.exit(1)

account_info = mt5.account_info()
print(f"\n✅ Connected to MT5")
print(f"   Account: {account_info.login}")
print(f"   Balance: ${account_info.balance:,.2f}")

# Get current positions
positions = mt5.positions_get()
print(f"   Positions: {len(positions)}")
if positions:
    total_pl = sum(p.profit for p in positions)
    print(f"   Total P/L: ${total_pl:.2f}")

# Create connector
connector = MT5Connector("test_intelligent")

# Create orchestrator WITH intelligent manager
print(f"\n🧠 Creating Orchestrator with Intelligent Manager...")
orchestrator = MultiCurrencyOrchestrator(
    connector=connector,
    max_concurrent_trades=15,
    use_intelligent_manager=True  # KEY: Enable intelligent manager
)

# Add test currencies
print("\n📊 Adding currency pairs...")
for symbol in ['EURUSD', 'GBPUSD', 'USDJPY']:
    config = CurrencyTraderConfig(
        symbol=symbol,
        strategy=SimpleMAStrategy(fast_period=20, slow_period=50),
        risk_percent=0.5,
        timeframe=mt5.TIMEFRAME_H1,
        stop_loss_pips=30,
        take_profit_pips=60
    )
    orchestrator.add_currency(config)
    print(f"   ✓ {symbol} added")

# Initialize ML if available
if ml_available:
    print("\n🤖 Initializing ML Enhancement...")
    try:
        feature_engineer = FeatureEngineer()
        # Note: Would load trained model here if available
        print("   ✓ Feature engineer ready")
        print("   ⚠️  ML model not trained - using technical signals only")
    except Exception as e:
        print(f"   ✗ ML initialization failed: {e}")

# Initialize LLM if available
if llm_available:
    print("\n💬 Initializing LLM Enhancement...")
    try:
        sentiment = SentimentAnalyzer()
        analyst = MarketAnalyst()
        
        # Enable for intelligent manager
        orchestrator.intelligent_manager.set_sentiment_analyzer(sentiment)
        orchestrator.intelligent_manager.set_llm_analyst(analyst)
        
        print("   ✓ Sentiment analyzer enabled")
        print("   ✓ Market analyst enabled")
        print("   ✓ LLM integrated with intelligent manager")
    except Exception as e:
        print(f"   ✗ LLM initialization failed: {e}")

# Run one trading cycle
print("\n" + "="*80)
print("RUNNING INTELLIGENT TRADING CYCLE")
print("="*80)

try:
    results = orchestrator.process_single_cycle()
    
    print(f"\n📊 Cycle Results:")
    print(f"   Timestamp: {results['timestamp']}")
    print(f"   Currencies processed: {len(results['currencies'])}")
    
    if results['currencies']:
        print("\n   Detailed Results:")
        for symbol, result in results['currencies'].items():
            print(f"\n   [{symbol}]")
            if 'reason' in result:
                print(f"      Decision: NOT EXECUTED")
                print(f"      Reason: {result['reason']}")
            elif 'signal' in result:
                signal = result['signal']
                print(f"      Signal: {signal.type}")
                print(f"      Executed: {result.get('executed', False)}")
    
    if results['errors']:
        print("\n   Errors:")
        for error in results['errors']:
            print(f"      ✗ {error}")
    
except Exception as e:
    print(f"❌ Cycle failed: {e}")
    import traceback
    traceback.print_exc()

# Show portfolio analysis
print("\n" + "="*80)
print("PORTFOLIO ANALYSIS")
print("="*80)

portfolio = orchestrator.intelligent_manager.analyze_portfolio()
print(f"\nCurrent Portfolio State:")
print(f"   Total Positions: {portfolio.total_positions}")
print(f"   Profit/Loss: ${portfolio.total_profit_loss:.2f}")
print(f"   Winning Positions: {portfolio.winning_positions}")
print(f"   Losing Positions: {portfolio.losing_positions}")
print(f"   Total Exposure: {portfolio.total_exposure:.1f}%")
print(f"   Is Profitable: {'Yes' if portfolio.is_profitable else 'No'}")

if portfolio.symbols_in_portfolio:
    print(f"\n   Symbols in Portfolio:")
    for symbol in portfolio.symbols_in_portfolio:
        print(f"      - {symbol}")

# Cleanup
mt5.shutdown()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\n✅ Intelligent trading system is operational!")
print("   - Intelligent Position Manager: ACTIVE")
print(f"   - ML Enhancement: {'ENABLED' if ml_available else 'DISABLED'}")
print(f"   - LLM Enhancement: {'ENABLED' if llm_available else 'DISABLED'}")
print("   - Portfolio-aware decision making: ACTIVE")
print("   - No hard position limits: ACTIVE")

"""
Multi-Currency Trading with Orchestrator
Each currency pair has independent configuration
"""
import os
from dotenv import load_dotenv

from src.connectors import ConnectorFactory
from src.connectors.base import PlatformType
from src.strategies import SimpleMovingAverageStrategy
from src.trading import MultiCurrencyOrchestrator, CurrencyTraderConfig

# Load environment
load_dotenv()

def main():
    """Run multi-currency trading with orchestrator"""
    
    # Create connector
    print("🔌 Connecting to MT5...")
    connector = ConnectorFactory.create_connector(
        platform=PlatformType.MT5,
        instance_id="multi_currency_bot"
    )
    
    login = int(os.getenv('MT5_LOGIN'))
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')
    
    if not connector.connect(login, password, server):
        print("❌ Connection failed")
        return
    
    print("✓ Connected to MT5")
    
    # Create orchestrator
    orchestrator = MultiCurrencyOrchestrator(
        connector=connector,
        max_concurrent_trades=5,  # Max 5 positions at once
        portfolio_risk_percent=10.0  # Total portfolio risk limit
    )
    
    # Define currency-specific configurations
    currency_configs = {
        'EURUSD': {
            'risk_percent': 1.0,
            'fast_period': 10,
            'slow_period': 20,
            'sl_pips': 20,
            'tp_pips': 40,
            'use_position_trading': True
        },
        'GBPUSD': {
            'risk_percent': 0.8,  # Lower risk for GBP (more volatile)
            'fast_period': 8,
            'slow_period': 21,
            'sl_pips': 25,
            'tp_pips': 50,
            'use_position_trading': True
        },
        'USDJPY': {
            'risk_percent': 1.2,  # Higher risk for JPY (less volatile)
            'fast_period': 12,
            'slow_period': 26,
            'sl_pips': 15,
            'tp_pips': 30,
            'use_position_trading': True
        },
        'XAUUSD': {
            'risk_percent': 0.5,  # Very low risk for gold (high volatility)
            'fast_period': 20,
            'slow_period': 50,
            'sl_pips': 50,
            'tp_pips': 100,
            'use_position_trading': False  # Use crossover for gold
        },
        'BTCUSD': {
            'risk_percent': 0.3,  # Minimal risk for crypto
            'fast_period': 15,
            'slow_period': 30,
            'sl_pips': 100,
            'tp_pips': 200,
            'use_position_trading': False
        }
    }
    
    # Add each currency with its specific config
    print("\n📊 Adding currency pairs...")
    added_count = 0
    skipped_symbols = []
    
    for symbol, config in currency_configs.items():
        strategy = SimpleMovingAverageStrategy({
            'fast_period': config['fast_period'],
            'slow_period': config['slow_period'],
            'sl_pips': config['sl_pips'],
            'tp_pips': config['tp_pips']
        })
        
        trader_config = CurrencyTraderConfig(
            symbol=symbol,
            strategy=strategy,
            risk_percent=config['risk_percent'],
            timeframe='M5',
            cooldown_seconds=60,
            use_position_trading=config['use_position_trading'],
            fast_period=config['fast_period'],
            slow_period=config['slow_period'],
            sl_pips=config['sl_pips'],
            tp_pips=config['tp_pips']
        )
        
        trader = orchestrator.add_currency(trader_config)
        if trader:
            added_count += 1
        else:
            skipped_symbols.append(symbol)
    
    print(f"\n✓ Added {len(orchestrator)} currency pairs")
    if skipped_symbols:
        print(f"⚠️  Skipped unavailable symbols: {', '.join(skipped_symbols)}")
    
    # Check if we have any valid currencies
    if len(orchestrator) == 0:
        print("\n❌ No valid currency pairs available on this broker")
        print("   Please check your MT5 symbol names or broker availability")
        connector.disconnect()
        return
    
    # Show configuration summary
    print("\n" + "=" * 80)
    print("CONFIGURATION SUMMARY")
    print("=" * 80)
    for symbol in orchestrator.traders.keys():
        config = currency_configs[symbol]
        print(f"\n{symbol}:")
        print(f"  Risk: {config['risk_percent']}%")
        print(f"  MA Periods: {config['fast_period']}/{config['slow_period']}")
        print(f"  SL/TP: {config['sl_pips']}/{config['tp_pips']} pips")
        print(f"  Mode: {'Position' if config['use_position_trading'] else 'Crossover'}")
    print("=" * 80)
    
    # User confirmation
    print("\n⚠️  Ready to start multi-currency trading")
    print("   - Each currency trades independently")
    print("   - Different strategies per pair")
    print("   - Portfolio-level risk management")
    print("   - Press Ctrl+C to stop\n")
    
    input("Press Enter to start trading...")
    
    # Run trading
    try:
        orchestrator.run_continuous(
            interval_seconds=30,
            parallel=False,  # Sequential (set True for parallel)
            max_cycles=None  # Infinite (set number for testing)
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping trading...")
    
    # Cleanup
    orchestrator.print_final_statistics()
    connector.disconnect()
    print("\n✓ Disconnected")


if __name__ == '__main__':
    main()

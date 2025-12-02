"""
TradingMTQ - Automated Trading System
Main entry point for the automated trading bot
"""
import sys
from typing import List

from .connectors import create_mt5_connector
from .strategies import SimpleMovingAverageStrategy
from .bot import TradingBot
from .analysis import MarketAnalyzer
from .analysis.ml_predictor import MLPredictor
from .utils import setup_logging, get_config, get_logger

logger = get_logger(__name__)


def main():
    """Main entry point for automated trading system"""
    # Setup logging
    setup_logging(log_level="INFO")
    
    print("\n" + "=" * 70)
    print(" " * 15 + "TradingMTQ - Automated Trading System")
    print("=" * 70)
    
    # Get configuration
    config = get_config()
    
    # Get MT5 credentials
    credentials = config.get_mt5_credentials()
    
    if not credentials['login'] or not credentials['password']:
        print("\n❌ ERROR: MT5 credentials not configured!")
        print("Please set MT5_LOGIN, MT5_PASSWORD, and MT5_SERVER in .env file")
        return 1
    
    print(f"\n🔄 Connecting to MT5...")
    print(f"   Server: {credentials['server']}")
    print(f"   Login: {credentials['login']}")
    
    # Create and connect to MT5
    try:
        connector = create_mt5_connector("main")
        success = connector.connect(**credentials)
        
        if not success:
            print("\n❌ Failed to connect to MT5")
            print("Please ensure:")
            print("  1. MT5 terminal is running")
            print("  2. You are logged into your account")
            print("  3. Credentials in .env are correct")
            return 1
        
        account = connector.get_account_info()
        if not account:
            print("\n❌ Failed to get account info")
            return 1
            
        print(f"\n✓ Connected successfully!")
        print(f"   Account: {account.login}")
        print(f"   Balance: ${account.balance:,.2f}")
        print(f"   Leverage: 1:{account.leverage}")
        
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        logger.error(f"Connection error: {e}", exc_info=True)
        return 1
    
    # Get trading symbols from config or use defaults
    symbols = config.get('symbols.forex', [
        'EURUSD',
        'GBPUSD',
        'USDJPY',
        'AUDUSD',
        'USDCAD',
        'NZDUSD',
        'EURGBP',
        'EURJPY',
        'GBPJPY',
        'AUDJPY',
        # Add more symbols here
    ])
    
    # ====================================================================
    # PRE-TRADING ANALYSIS: Learn market behavior before trading
    # ====================================================================
    print("\n" + "=" * 70)
    print(" " * 15 + "🔍 PRE-TRADING MARKET ANALYSIS")
    print("=" * 70)
    
    lookback_hours = 24  # Analyze last 24 hours
    print(f"\nAnalyzing {lookback_hours} hours of historical data for each symbol...")
    print("This helps identify abnormal market conditions and volatility patterns.\n")
    
    # Initialize analyzer and ML predictor
    analyzer = MarketAnalyzer(lookback_hours=lookback_hours)
    ml_predictor = MLPredictor()
    
    # Analyze each symbol
    for symbol in symbols:
        try:
            # Get historical data
            bars = connector.get_bars(
                symbol=symbol,
                timeframe="H1",  # 1-hour bars for analysis
                count=lookback_hours
            )
            
            if bars and len(bars) >= 10:
                # Analyze market profile
                profile = analyzer.analyze_symbol(symbol, bars)
                
                # ML prediction
                direction, confidence = ml_predictor.predict_movement(symbol, bars)
                
                print(f"✓ {symbol}: {profile.recommendation} "
                      f"(Volatility: {profile.avg_volatility:.2f}%, "
                      f"Anomaly: {profile.anomaly_score:.1f}%, "
                      f"ML: {direction} {confidence:.1%})")
            else:
                print(f"⚠ {symbol}: Insufficient data")
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            print(f"✗ {symbol}: Analysis failed")
    
    # Display comprehensive report
    analyzer.print_analysis_report()
    
    # Filter symbols based on analysis
    tradeable_symbols = [s for s in symbols if analyzer.should_trade_symbol(s)]
    
    if not tradeable_symbols:
        print("\n⚠️  WARNING: No symbols are suitable for trading!")
        print("All symbols show abnormal behavior or insufficient data.")
        print("Recommendation: Wait for market to normalize.\n")
        
        proceed = input("Continue anyway? (yes/no): ").strip().lower()
        if proceed not in ['yes', 'y']:
            connector.disconnect()
            return 0
        
        tradeable_symbols = symbols  # Use all if user insists
    else:
        avoided = set(symbols) - set(tradeable_symbols)
        if avoided:
            print(f"\n⚠️  Avoiding {len(avoided)} symbols due to abnormal conditions:")
            for s in avoided:
                profile = analyzer.get_profile(s)
                if profile:
                    print(f"   {s}: {profile.recommendation} "
                          f"(Anomaly: {profile.anomaly_score:.1f}%)")
    
    print(f"\n✓ Trading on {len(tradeable_symbols)} symbols: {', '.join(tradeable_symbols)}")
    
    # ====================================================================
    # START AUTOMATED TRADING
    # ====================================================================
    
    # Create strategy
    strategy = SimpleMovingAverageStrategy(params={
        'fast_period': 10,
        'slow_period': 20,
        'sl_pips': 20,
        'tp_pips': 40
    })
    
    print(f"\n📈 Strategy: {strategy.get_name()}")
    print(f"   Fast MA: {strategy.params['fast_period']} periods")
    print(f"   Slow MA: {strategy.params['slow_period']} periods")
    print(f"   Stop Loss: {strategy.params['sl_pips']} pips")
    print(f"   Take Profit: {strategy.params['tp_pips']} pips")
    
    # Get risk parameters from config
    risk_config = config.get_risk_config()
    volume = risk_config.get('default_lot_size', 0.01)
    max_positions = risk_config.get('max_positions', 3)
    
    print(f"\n⚙️  Settings:")
    print(f"   Volume: {volume} lots")
    print(f"   Max Positions: {max_positions}")
    print(f"   Symbols: {', '.join(symbols)}")
    
    # Create and start bot
    bot = TradingBot(
        connector=connector,
        strategy=strategy,
        symbols=tradeable_symbols,  # Use filtered symbols
        timeframe="M5",
        volume=volume,
        max_positions=max_positions,
        check_interval=60  # Check every 60 seconds
    )
    
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        if connector:
            connector.disconnect()
        print("\n✓ Disconnected from MT5")
        print("Goodbye!\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

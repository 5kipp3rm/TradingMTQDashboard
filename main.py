"""
TradingMTQ - Multi-Currency Trading Bot
Main entry point - launches CLI application

For legacy compatibility, this file can still be run directly.
New usage: Use 'tradingmtq' command after installation.
"""
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')


def main():
    """
    Legacy main function - launches CLI application
    
    For new usage, install package and use:
        pip install -e .
        tradingmtq trade
    """
    try:
        # Try to use the new CLI
        from src.cli import cli
        
        # If no arguments provided, run default trade command
        if len(sys.argv) == 1:
            sys.argv = ['main.py', 'trade']
        
        cli()
    
    except ImportError as e:
        # Fallback to old behavior if CLI dependencies not installed
        print("⚠️  CLI module not available")
        print(f"   Error: {e}")
        print("   Installing dependencies: pip install click")
        print("\n   Falling back to legacy mode...\n")
        _run_legacy_trading()


def _run_legacy_trading(enable_ml: bool = True, enable_llm: bool = True):
    """
    Legacy trading function for backward compatibility
    
    Args:
        enable_ml: Enable ML enhancement (default: True)
        enable_llm: Enable LLM sentiment analysis (default: True)
    """
    import os
    import time
    from datetime import datetime
    
    from src.connectors import ConnectorFactory
    from src.connectors.base import PlatformType
    from src.strategies import SimpleMovingAverageStrategy
    from src.trading import MultiCurrencyOrchestrator, CurrencyTraderConfig
    from src.config_manager import ConfigurationManager
    from src.utils.logger import setup_logging, get_logger, log_connection, log_config, log_cycle
    
    # Optional ML/LLM imports
    try:
        from src.ml import RandomForestClassifier, FeatureEngineer, ModelLoader, MLModelWrapper
        ML_AVAILABLE = True
    except ImportError:
        ML_AVAILABLE = False
        print("⚠️  ML libraries not available")
    
    try:
        from src.llm import OpenAIProvider, SentimentAnalyzer, MarketAnalyst
        from src.utils.config_loader import get_openai_key
        LLM_AVAILABLE = True
    except ImportError:
        LLM_AVAILABLE = False
    
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Run legacy trading (original main.py logic)
    
    logger.info("=" * 80)
    logger.info("  CONFIGURATION-BASED MULTI-CURRENCY TRADING")
    logger.info("=" * 80)
    
    # Load configuration
    log_config(logger, "Loading configuration from config/currencies.yaml")
    try:
        config_manager = ConfigurationManager("config/currencies.yaml")
        log_config(logger, "Configuration loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        return
    
    # Check emergency stop
    if config_manager.is_emergency_stop_active():
        logger.critical("EMERGENCY STOP IS ACTIVE!")
        logger.warning("Set emergency.emergency_stop to false in config to continue")
        return
    
    # Create connector
    log_connection(logger, "CONNECTING", "Initializing MT5 connection")
    connector = ConnectorFactory.create_connector(
        platform=PlatformType.MT5,
        instance_id="config_bot"
    )
    
    login = int(os.getenv('MT5_LOGIN', 0))
    password = os.getenv('MT5_PASSWORD', '')
    server = os.getenv('MT5_SERVER', '')
    
    if not connector.connect(login, password, server):
        log_connection(logger, "FAILED", "MT5 connection failed")
        return
    
    log_connection(logger, "ESTABLISHED", f"Server: {server}")
    
    # Create orchestrator with config values
    orchestrator = MultiCurrencyOrchestrator(
        connector=connector,
        max_concurrent_trades=config_manager.get_max_concurrent_trades(),
        portfolio_risk_percent=config_manager.get_portfolio_risk_percent()
    )
    
    # Clean up any leftover position tracking from previous runs
    logger.info("Cleaning up position tracking from previous runs...")
    orchestrator.position_manager.cleanup_closed_positions()
    logger.info(f"Position manager ready (tracking {orchestrator.position_manager.get_managed_count()} open positions)")
    
    # Add enabled currencies from config
    log_config(logger, "Loading currency pairs from configuration")
    enabled_currencies = config_manager.get_enabled_currencies()
    
    if not enabled_currencies:
        logger.error("No enabled currencies found in configuration")
        logger.warning("Set enabled: true for at least one currency in config/currencies.yaml")
        connector.disconnect()
        return
    
    logger.info(f"Found {len(enabled_currencies)} enabled currencies: {', '.join(enabled_currencies)}")
    
    # Initialize ML/LLM components (optional)
    # Override config with CLI flags
    use_ml = config_manager.config.get('global', {}).get('use_ml_enhancement', False) and enable_ml
    use_llm = config_manager.config.get('global', {}).get('use_sentiment_filter', False) and enable_llm
    
    # Log ML/LLM status
    if not enable_ml:
        logger.info("ML Enhancement: DISABLED (via CLI flag)")
    if not enable_llm:
        logger.info("LLM Sentiment: DISABLED (via CLI flag)")
    
    currency_models = {}
    if use_ml and ML_AVAILABLE:
        logger.info("=" * 80)
        logger.info("  INITIALIZING ML ENHANCEMENT")
        logger.info("=" * 80)
        
        # Load models for enabled currencies
        model_loader = ModelLoader("models")
        model_loader.print_available_models()
        
        # Load ensemble models (preferred) for all enabled currencies
        currency_models = model_loader.load_all_models(
            config_manager.config.get('currencies', {}),
            model_type='ensemble'  # Use ensemble models for best accuracy
        )
        
        if currency_models:
            logger.info(f"\n✅ Loaded {len(currency_models)} ML models for trading")
        else:
            logger.warning("⚠️  No ML models found")
            logger.info("   Train models using: python scripts/train_all.py")
            use_ml = False
    
    if use_llm and LLM_AVAILABLE:
        logger.info("=" * 80)
        logger.info("  INITIALIZING LLM SENTIMENT ANALYSIS")
        logger.info("=" * 80)
        
        api_key = get_openai_key()
        if api_key:
            try:
                llm_provider = OpenAIProvider(api_key=api_key)
                sentiment_analyzer = SentimentAnalyzer(llm_provider)
                market_analyst = MarketAnalyst(llm_provider)
                
                orchestrator.enable_llm_for_all(sentiment_analyzer, market_analyst)
                logger.info("✅ LLM sentiment analysis enabled")
            except Exception as e:
                logger.warning(f"⚠️  LLM initialization failed: {e}")
                use_llm = False
        else:
            logger.warning("⚠️  OpenAI API key not found")
            logger.info("   Set OPENAI_API_KEY in .env or config/api_keys.yaml")
            use_llm = False
    
    added_count = 0
    skipped_symbols = []
    
    for symbol in enabled_currencies:
        currency_config = config_manager.get_currency_config(symbol)
        
        # Create strategy with config parameters
        strategy = SimpleMovingAverageStrategy({
            'fast_period': currency_config['fast_period'],
            'slow_period': currency_config['slow_period'],
            'sl_pips': currency_config['sl_pips'],
            'tp_pips': currency_config['tp_pips']
        })
        
        # Create trader config
        trader_config = CurrencyTraderConfig(
            symbol=symbol,
            strategy=strategy,
            risk_percent=currency_config['risk_percent'],
            timeframe=currency_config['timeframe'],
            cooldown_seconds=currency_config['cooldown_seconds'],
            max_position_size=currency_config.get('max_position_size', 1.0),
            min_position_size=currency_config.get('min_position_size', 0.01),
            use_position_trading=currency_config['strategy_type'] == 'position',
            # Position stacking parameters
            allow_position_stacking=currency_config.get('allow_position_stacking', False),
            max_positions_same_direction=currency_config.get('max_positions_same_direction', 1),
            max_total_positions=currency_config.get('max_total_positions', 5),
            stacking_risk_multiplier=currency_config.get('stacking_risk_multiplier', 1.0),
            fast_period=currency_config['fast_period'],
            slow_period=currency_config['slow_period'],
            sl_pips=currency_config['sl_pips'],
            tp_pips=currency_config['tp_pips']
        )
        
        trader = orchestrator.add_currency(trader_config)
        if trader:
            added_count += 1
            
            # Enable ML for this specific currency if model available
            if use_ml and symbol in currency_models:
                wrapped_model = MLModelWrapper(currency_models[symbol])
                trader.enable_ml_enhancement(wrapped_model)
                logger.info(f"  \u2705 [{symbol}] ML enhancement enabled with ensemble model")
        else:
            skipped_symbols.append(symbol)
    
    logger.info(f"Successfully added {len(orchestrator)} currency pairs")
    if skipped_symbols:
        logger.warning(f"Skipped unavailable symbols: {', '.join(skipped_symbols)}")
    
    # Check if we have any valid currencies
    if len(orchestrator) == 0:
        logger.error("No valid currency pairs available")
        connector.disconnect()
        return
    
    # Show configuration summary
    logger.info("=" * 80)
    logger.info("CONFIGURATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Global Settings:")
    logger.info(f"  Max Concurrent Trades: {config_manager.get_max_concurrent_trades()}")
    logger.info(f"  Portfolio Risk: {config_manager.get_portfolio_risk_percent()}%")
    logger.info(f"  Interval: {config_manager.get_interval_seconds()}s")
    logger.info(f"  Parallel: {config_manager.get_parallel_execution()}")
    logger.info(f"  Auto-Reload: {config_manager.get_auto_reload_enabled()}")
    
    logger.info(f"Currency Pairs:")
    for symbol in orchestrator.traders.keys():
        currency_config = config_manager.get_currency_config(symbol)
        logger.info(f"  {symbol}:", extra={'symbol': symbol})
        logger.info(f"    Risk: {currency_config['risk_percent']}%", extra={'symbol': symbol})
        logger.info(f"    Strategy: {currency_config['strategy_type'].upper()}", extra={'symbol': symbol})
        logger.info(f"    Timeframe: {currency_config['timeframe']}", extra={'symbol': symbol})
        logger.info(f"    MA: {currency_config['fast_period']}/{currency_config['slow_period']}", extra={'symbol': symbol})
        logger.info(f"    SL/TP: {currency_config['sl_pips']}/{currency_config['tp_pips']} pips", extra={'symbol': symbol})
        logger.info(f"    Cooldown: {currency_config['cooldown_seconds']}s", extra={'symbol': symbol})
    
    logger.info(f"Modifications:")
    logger.info(f"  Trailing Stop: {config_manager.get_trailing_stop_enabled()}")
    if config_manager.get_trailing_stop_enabled():
        logger.info(f"    Distance: {config_manager.get_trailing_stop_pips()} pips")
    logger.info(f"  Breakeven: {config_manager.get_breakeven_enabled()}")
    if config_manager.get_breakeven_enabled():
        logger.info(f"    Trigger: {config_manager.get_breakeven_trigger()} pips")
        logger.info(f"    Offset: {config_manager.get_breakeven_offset()} pips")
    
    logger.info("=" * 80)
    
    # Check market hours
    try:
        from src.utils.market_hours import is_forex_market_open, get_next_market_open
        market_open, market_msg = is_forex_market_open()
        
        if not market_open:
            logger.warning("=" * 80)
            logger.warning(f"⚠️  {market_msg}")
            logger.warning(f"   Next market open: {get_next_market_open()}")
            logger.warning("   Bot will continue running but may not receive new data")
            logger.warning("   Existing positions will be monitored if any")
            logger.warning("=" * 80)
    except Exception as e:
        logger.debug(f"Market hours check skipped: {e}")
    
    # User confirmation
    logger.warning("Ready to start configuration-based trading")
    logger.info("   - All settings loaded from config/currencies.yaml")
    logger.info("   - Edit config file to modify SL/TP on the fly")
    if config_manager.get_auto_reload_enabled():
        logger.info(f"   - Config auto-reloads every {config_manager.get_reload_interval()}s")
    logger.info("   - Press Ctrl+C to stop")
    
    #input("Press Enter to start trading...")
    
    # Run trading with config hot-reload
    try:
        cycle_count = 0
        last_config_check = datetime.now()
        
        while True:
            # Check for emergency stop
            if config_manager.is_emergency_stop_active():
                logger.critical("EMERGENCY STOP ACTIVATED!")
                emergency_config = config_manager.get_emergency_config()
                if emergency_config.get('close_all_on_stop', True):
                    logger.warning("Closing all positions...")
                    orchestrator.connector.close_all_positions()
                break
            
            # Check for config reload
            if config_manager.get_auto_reload_enabled():
                elapsed = (datetime.now() - last_config_check).total_seconds()
                if elapsed >= config_manager.get_reload_interval():
                    if config_manager.check_and_reload():
                        log_config(logger, "Configuration reloaded - new settings will apply to new trades")
                        
                        # Show what changed
                        new_enabled = config_manager.get_enabled_currencies()
                        current_symbols = set(orchestrator.traders.keys())
                        
                        # Check for disabled currencies
                        for symbol in list(current_symbols):
                            if symbol not in new_enabled:
                                logger.warning(f"{symbol} disabled in config - will skip", extra={'symbol': symbol})
                        
                        # Note: New currencies would need orchestrator restart
                        # This is a design choice - could auto-add here
                    
                    last_config_check = datetime.now()
            
            # Run trading cycle
            log_cycle(logger, cycle_count + 1, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get position management config
            management_config = config_manager.config.get('modifications', {})
            
            if config_manager.get_parallel_execution():
                results = orchestrator.process_parallel_cycle(
                    max_workers=config_manager.get_max_workers()
                )
                # Apply position management after parallel cycle
                try:
                    orchestrator.position_manager.cleanup_closed_positions()
                    orchestrator.position_manager.process_all_positions(management_config)
                except Exception as e:
                    logger.warning(f"Position management error: {e}")
            else:
                results = orchestrator.process_single_cycle(management_config)
            
            # Show summary
            executed_count = sum(1 for r in results['currencies'].values() 
                               if r.get('executed'))
            if executed_count > 0:
                logger.info(f"Cycle Summary: {executed_count} trades executed", extra={'custom_icon': '📊'})
            
            cycle_count += 1
            
            # Wait before next cycle
            interval = config_manager.get_interval_seconds()
            logger.debug(f"Waiting {interval}s until next cycle...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.warning("Trading stopped by user")
        orchestrator.print_final_statistics()
    
    # Cleanup
    connector.disconnect()
    log_connection(logger, "DISCONNECTED", "MT5 connection closed")


if __name__ == '__main__':
    main()

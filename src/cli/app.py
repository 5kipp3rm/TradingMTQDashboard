"""
Main CLI Application
Built with Click framework for command-line interface
"""
import click
import sys
from pathlib import Path


@click.group()
@click.version_option(version='2.0.0', prog_name='TradingMTQ')
def cli():
    """
    TradingMTQ - Advanced Multi-Currency Trading Bot for MetaTrader 5
    
    A sophisticated algorithmic trading platform with ML enhancement,
    position stacking, and intelligent risk management.
    """
    pass


@cli.command()
@click.option('--config', '-c', default='config/currencies.yaml',
              help='Path to configuration file')
@click.option('--aggressive', '-a', is_flag=True,
              help='Use aggressive trading configuration')
@click.option('--demo', '-d', is_flag=True,
              help='Run in demo/paper trading mode')
@click.option('--interval', '-i', type=int,
              help='Override interval seconds from config')
@click.option('--max-concurrent', '-m', type=int,
              help='Override max concurrent trades')
@click.option('--enable-ml/--disable-ml', default=True,
              help='Enable/disable ML enhancement (default: enabled)')
@click.option('--enable-llm/--disable-llm', default=True,
              help='Enable/disable LLM sentiment analysis (default: enabled)')
def trade(config, aggressive, demo, interval, max_concurrent, enable_ml, enable_llm):
    """
    Start live trading with specified configuration
    
    Examples:
        tradingmtq trade                    # Use default config (ML & LLM enabled)
        tradingmtq trade --aggressive       # Use aggressive config
        tradingmtq trade -c custom.yaml     # Use custom config
        tradingmtq trade -i 30 -m 20        # Override settings
        tradingmtq trade --disable-ml       # Disable ML enhancement
        tradingmtq trade --disable-llm      # Disable LLM sentiment
        tradingmtq trade --disable-ml --disable-llm  # Disable both
    """
    try:
        from .commands import run_trading
        
        run_trading(
            config_file=config,
            aggressive=aggressive,
            demo=demo,
            interval=interval,
            max_concurrent=max_concurrent,
            enable_ml=enable_ml,
            enable_llm=enable_llm
        )
    except KeyboardInterrupt:
        click.echo("\n\nTrading stopped by user")
    except Exception as e:
        from ..utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Trading error: {e}", exc_info=True)
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
def version():
    """Show version information"""
    click.echo("\nTradingMTQ v2.0.0")
    click.echo("Advanced Multi-Currency Trading Bot")
    click.echo("\nFeatures:")
    click.echo("  • Multi-currency trading orchestration")
    click.echo("  • Position stacking during trends")
    click.echo("  • ML-enhanced signal generation")
    click.echo("  • Intelligent position management")
    click.echo("  • Configuration hot-reload")
    click.echo("\nRepository: https://github.com/5kipp3rm/TradingMTQ\n")


@cli.command()
def check():
    """Run system checks"""
    click.echo("\nSystem Check\n")
    click.echo(f"  Python Version: {sys.version.split()[0]}")
    
    # Check dependencies
    click.echo("\nDependencies:")
    
    dependencies = [
        ('MetaTrader5', 'MetaTrader5'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('yaml', 'pyyaml'),
        ('sklearn', 'scikit-learn'),
        ('click', 'click'),
    ]
    
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            click.echo(f"  [OK] {package_name}")
        except ImportError:
            click.echo(f"  [MISSING] {package_name} (not installed)")
    
    click.echo()


if __name__ == '__main__':
    cli()

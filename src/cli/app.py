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


@cli.command()
@click.option('--date', '-d', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Aggregate specific date (YYYY-MM-DD)')
@click.option('--start', '-s', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date for range aggregation (YYYY-MM-DD)')
@click.option('--end', '-e', type=click.DateTime(formats=['%Y-%m-%d']),
              help='End date for range aggregation (YYYY-MM-DD)')
@click.option('--backfill', '-b', is_flag=True,
              help='Backfill all historical trade data')
def aggregate(date, start, end, backfill):
    """
    Aggregate trade data into daily performance metrics

    Examples:
        tradingmtq aggregate --backfill              # Aggregate all historical data
        tradingmtq aggregate -d 2025-12-13           # Aggregate specific date
        tradingmtq aggregate -s 2025-12-01 -e 2025-12-13  # Aggregate date range
    """
    from datetime import date as dt_date
    from src.analytics import DailyAggregator
    from src.database.connection import init_db

    try:
        # Initialize database
        init_db()

        aggregator = DailyAggregator()

        if backfill:
            click.echo("\n🔄 Backfilling all historical trade data...")
            results = aggregator.backfill()

            if results:
                click.echo(f"✅ Aggregated {len(results)} days of data")
                click.echo(f"   Date range: {results[0].date} to {results[-1].date}")
            else:
                click.echo("ℹ️  No trade data found to aggregate")

        elif date:
            click.echo(f"\n🔄 Aggregating trades for {date.date()}...")
            result = aggregator.aggregate_day(date.date())

            if result:
                click.echo(f"✅ Aggregated {result.total_trades} trades")
                click.echo(f"   Net profit: ${result.net_profit:.2f}")
                click.echo(f"   Win rate: {result.win_rate:.1f}%")
            else:
                click.echo(f"ℹ️  No closed trades found for {date.date()}")

        elif start and end:
            click.echo(f"\n🔄 Aggregating trades from {start.date()} to {end.date()}...")
            results = aggregator.aggregate_range(start.date(), end.date())

            if results:
                click.echo(f"✅ Aggregated {len(results)} days of data")
                total_trades = sum(r.total_trades for r in results)
                total_profit = sum(r.net_profit for r in results)
                click.echo(f"   Total trades: {total_trades}")
                click.echo(f"   Total profit: ${total_profit:.2f}")
            else:
                click.echo("ℹ️  No trade data found in date range")

        else:
            click.echo("❌ Please specify --backfill, --date, or --start/--end")
            raise click.Abort()

        click.echo()

    except Exception as e:
        click.echo(f"\n❌ Aggregation error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--host', '-h', default='0.0.0.0',
              help='Host to bind the API server (default: 0.0.0.0)')
@click.option('--port', '-p', default=8000, type=int,
              help='Port to bind the API server (default: 8000)')
@click.option('--reload', '-r', is_flag=True,
              help='Enable auto-reload on code changes (development only)')
def serve(host, port, reload):
    """
    Start the analytics API server

    Examples:
        tradingmtq serve                    # Start on 0.0.0.0:8000
        tradingmtq serve -p 8080            # Use port 8080
        tradingmtq serve --reload           # Enable auto-reload for development
        tradingmtq serve -h localhost -p 3000  # Bind to localhost:3000
    """
    try:
        import uvicorn
        from src.database.connection import init_db

        # Initialize database
        init_db()

        click.echo(f"\n🚀 Starting TradingMTQ Analytics API")
        click.echo(f"   Host: {host}")
        click.echo(f"   Port: {port}")
        click.echo(f"   Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/api/docs")
        click.echo(f"   Auto-reload: {'enabled' if reload else 'disabled'}")
        click.echo(f"\n   Press Ctrl+C to stop\n")

        # Run uvicorn server
        uvicorn.run(
            "src.api.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )

    except ImportError:
        click.echo("❌ FastAPI or Uvicorn not installed", err=True)
        click.echo("   Install with: pip install fastapi uvicorn", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"\n❌ Server error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()

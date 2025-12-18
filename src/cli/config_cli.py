"""
Configuration CLI
Command-line interface for managing TradingMTQ configuration
"""

import click
import json
from pathlib import Path
from tabulate import tabulate
from typing import Optional

from src.services.config_manager import get_config_manager, CurrencyConfig


@click.group()
def config():
    """Manage TradingMTQ configuration"""
    pass


# Currency Commands

@config.group()
def currency():
    """Manage trading currencies"""
    pass


@currency.command('list')
@click.option('--enabled-only', is_flag=True, help='Show only enabled currencies')
@click.option('--category', type=str, help='Filter by category')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
def list_currencies(enabled_only, category, output_format):
    """List all currencies"""
    config_manager = get_config_manager()

    if category:
        currencies = config_manager.get_currencies_by_category(category, enabled_only)
    else:
        currencies = config_manager.get_all_currencies(enabled_only)

    if output_format == 'json':
        data = [curr.to_dict() for curr in currencies]
        click.echo(json.dumps(data, indent=2))
    else:
        headers = ['Symbol', 'Description', 'Category', 'Enabled', 'Custom']
        rows = [
            [
                curr.symbol,
                curr.description[:40] + '...' if len(curr.description) > 40 else curr.description,
                curr.category,
                '✓' if curr.enabled else '✗',
                '✓' if curr.custom else '✗'
            ]
            for curr in currencies
        ]
        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
        click.echo(f"\nTotal: {len(currencies)} currencies")


@currency.command('show')
@click.argument('symbol')
def show_currency(symbol):
    """Show detailed currency information"""
    config_manager = get_config_manager()
    curr = config_manager.get_currency(symbol.upper())

    if not curr:
        click.echo(f"❌ Currency not found: {symbol}", err=True)
        raise click.Abort()

    click.echo(f"\n📊 Currency: {curr.symbol}")
    click.echo("=" * 60)
    click.echo(f"Description:     {curr.description}")
    click.echo(f"Category:        {curr.category}")
    click.echo(f"Digits:          {curr.digits}")
    click.echo(f"Point:           {curr.point}")
    click.echo(f"Contract Size:   {curr.contract_size}")
    click.echo(f"Min Lot:         {curr.min_lot}")
    click.echo(f"Max Lot:         {curr.max_lot}")
    click.echo(f"Lot Step:        {curr.lot_step}")
    click.echo(f"Typical Spread:  {curr.spread_typical} pips")
    click.echo(f"Enabled:         {'✓ Yes' if curr.enabled else '✗ No'}")
    click.echo(f"Custom:          {'✓ Yes' if curr.custom else '✗ No (default)'}")
    if curr.created_at:
        click.echo(f"Created:         {curr.created_at}")
    if curr.updated_at:
        click.echo(f"Updated:         {curr.updated_at}")


@currency.command('add')
@click.argument('symbol')
@click.option('--description', required=True, help='Currency description')
@click.option('--category', required=True, help='Category (e.g., Forex Majors, Commodities)')
@click.option('--digits', type=int, default=5, help='Number of decimal places')
@click.option('--point', type=float, default=0.00001, help='Minimum price movement')
@click.option('--contract-size', type=int, default=100000, help='Standard lot size')
@click.option('--min-lot', type=float, default=0.01, help='Minimum volume')
@click.option('--max-lot', type=float, default=100.0, help='Maximum volume')
@click.option('--lot-step', type=float, default=0.01, help='Volume step')
@click.option('--spread', type=float, default=0.0, help='Typical spread in pips')
@click.option('--disabled', is_flag=True, help='Create disabled')
def add_currency(symbol, description, category, digits, point, contract_size,
                min_lot, max_lot, lot_step, spread, disabled):
    """Add a new currency"""
    config_manager = get_config_manager()

    currency = CurrencyConfig(
        symbol=symbol.upper(),
        description=description,
        category=category,
        digits=digits,
        point=point,
        contract_size=contract_size,
        min_lot=min_lot,
        max_lot=max_lot,
        lot_step=lot_step,
        spread_typical=spread,
        enabled=not disabled,
        custom=True
    )

    success = config_manager.add_currency(currency)
    if success:
        click.echo(f"✅ Added currency: {symbol}")
    else:
        click.echo(f"❌ Failed to add currency: {symbol}", err=True)
        raise click.Abort()


@currency.command('remove')
@click.argument('symbol')
@click.option('--force', is_flag=True, help='Skip confirmation')
def remove_currency(symbol, force):
    """Remove a custom currency"""
    config_manager = get_config_manager()

    currency = config_manager.get_currency(symbol.upper())
    if not currency:
        click.echo(f"❌ Currency not found: {symbol}", err=True)
        raise click.Abort()

    if not currency.custom:
        click.echo(f"❌ Cannot remove default currency: {symbol}", err=True)
        raise click.Abort()

    if not force:
        if not click.confirm(f"Remove currency {symbol}?"):
            click.echo("Cancelled")
            return

    success = config_manager.remove_currency(symbol.upper())
    if success:
        click.echo(f"✅ Removed currency: {symbol}")
    else:
        click.echo(f"❌ Failed to remove currency: {symbol}", err=True)
        raise click.Abort()


@currency.command('enable')
@click.argument('symbol')
def enable_currency(symbol):
    """Enable a currency"""
    config_manager = get_config_manager()

    success = config_manager.enable_currency(symbol.upper())
    if success:
        click.echo(f"✅ Enabled currency: {symbol}")
    else:
        click.echo(f"❌ Failed to enable currency: {symbol}", err=True)
        raise click.Abort()


@currency.command('disable')
@click.argument('symbol')
def disable_currency(symbol):
    """Disable a currency"""
    config_manager = get_config_manager()

    success = config_manager.disable_currency(symbol.upper())
    if success:
        click.echo(f"✅ Disabled currency: {symbol}")
    else:
        click.echo(f"❌ Failed to disable currency: {symbol}", err=True)
        raise click.Abort()


# Preferences Commands

@config.group()
def prefs():
    """Manage trading preferences"""
    pass


@prefs.command('show')
def show_preferences():
    """Show trading preferences"""
    config_manager = get_config_manager()
    prefs = config_manager.get_preferences()

    click.echo("\n⚙️  Trading Preferences")
    click.echo("=" * 60)
    click.echo(f"Default Volume:       {prefs.default_volume} lots")
    click.echo(f"Default SL:           {prefs.default_sl_pips or 'None'} pips")
    click.echo(f"Default TP:           {prefs.default_tp_pips or 'None'} pips")
    click.echo(f"Max Risk:             {prefs.max_risk_percent}%")
    click.echo(f"Max Daily Loss:       {prefs.max_daily_loss_percent}%")
    click.echo(f"Max Positions:        {prefs.max_positions}")
    click.echo(f"Favorite Symbols:     {len(prefs.favorite_symbols)}")
    if prefs.favorite_symbols:
        click.echo(f"  {', '.join(prefs.favorite_symbols)}")
    click.echo(f"Recent Symbols:       {len(prefs.recent_symbols)}")
    if prefs.recent_symbols:
        click.echo(f"  {', '.join(prefs.recent_symbols[:5])}")


@prefs.command('set')
@click.option('--default-volume', type=float, help='Default trading volume')
@click.option('--default-sl', type=float, help='Default stop loss in pips')
@click.option('--default-tp', type=float, help='Default take profit in pips')
@click.option('--max-risk', type=float, help='Maximum risk per trade (%)')
@click.option('--max-daily-loss', type=float, help='Maximum daily loss (%)')
@click.option('--max-positions', type=int, help='Maximum open positions')
def set_preferences(default_volume, default_sl, default_tp, max_risk, max_daily_loss, max_positions):
    """Update trading preferences"""
    config_manager = get_config_manager()

    updates = {}
    if default_volume is not None:
        updates['default_volume'] = default_volume
    if default_sl is not None:
        updates['default_sl_pips'] = default_sl
    if default_tp is not None:
        updates['default_tp_pips'] = default_tp
    if max_risk is not None:
        updates['max_risk_percent'] = max_risk
    if max_daily_loss is not None:
        updates['max_daily_loss_percent'] = max_daily_loss
    if max_positions is not None:
        updates['max_positions'] = max_positions

    if not updates:
        click.echo("❌ No preferences to update", err=True)
        return

    success = config_manager.update_preferences(**updates)
    if success:
        click.echo(f"✅ Updated {len(updates)} preference(s)")
        for key, value in updates.items():
            click.echo(f"  - {key}: {value}")
    else:
        click.echo("❌ Failed to update preferences", err=True)
        raise click.Abort()


# Favorites Commands

@config.group()
def favorites():
    """Manage favorite currencies"""
    pass


@favorites.command('list')
def list_favorites():
    """List favorite currencies"""
    config_manager = get_config_manager()
    favs = config_manager.get_favorites()

    if not favs:
        click.echo("No favorites yet")
        return

    headers = ['Symbol', 'Description', 'Category']
    rows = [[curr.symbol, curr.description, curr.category] for curr in favs]
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@favorites.command('add')
@click.argument('symbol')
def add_favorite(symbol):
    """Add currency to favorites"""
    config_manager = get_config_manager()

    currency = config_manager.get_currency(symbol.upper())
    if not currency:
        click.echo(f"❌ Currency not found: {symbol}", err=True)
        raise click.Abort()

    success = config_manager.add_favorite(symbol.upper())
    if success:
        click.echo(f"✅ Added {symbol} to favorites")
    else:
        click.echo(f"❌ Failed to add favorite", err=True)
        raise click.Abort()


@favorites.command('remove')
@click.argument('symbol')
def remove_favorite(symbol):
    """Remove currency from favorites"""
    config_manager = get_config_manager()

    success = config_manager.remove_favorite(symbol.upper())
    if success:
        click.echo(f"✅ Removed {symbol} from favorites")
    else:
        click.echo(f"❌ Failed to remove favorite", err=True)
        raise click.Abort()


# Statistics and Export/Import

@config.command('stats')
def show_stats():
    """Show configuration statistics"""
    config_manager = get_config_manager()
    stats = config_manager.get_stats()

    click.echo("\n📊 Configuration Statistics")
    click.echo("=" * 60)
    click.echo(f"Total Currencies:     {stats['total_currencies']}")
    click.echo(f"  Enabled:            {stats['enabled_currencies']}")
    click.echo(f"  Disabled:           {stats['disabled_currencies']}")
    click.echo(f"  Custom:             {stats['custom_currencies']}")
    click.echo(f"  Default:            {stats['default_currencies']}")
    click.echo(f"\nFavorites:            {stats['favorites_count']}")
    click.echo(f"Recent:               {stats['recent_count']}")

    click.echo(f"\nBy Category:")
    for category, data in sorted(stats['categories'].items()):
        click.echo(f"  {category:20} {data['enabled']}/{data['total']} enabled")


@config.command('export')
@click.argument('file_path', type=click.Path())
def export_config(file_path):
    """Export configuration to file"""
    config_manager = get_config_manager()

    path = Path(file_path)
    success = config_manager.export_config(path)

    if success:
        click.echo(f"✅ Configuration exported to {file_path}")
    else:
        click.echo(f"❌ Failed to export configuration", err=True)
        raise click.Abort()


@config.command('import')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--replace', is_flag=True, help='Replace instead of merge')
def import_config(file_path, replace):
    """Import configuration from file"""
    config_manager = get_config_manager()

    path = Path(file_path)
    success = config_manager.import_config(path, merge=not replace)

    if success:
        mode = "replaced" if replace else "merged"
        click.echo(f"✅ Configuration {mode} from {file_path}")
    else:
        click.echo(f"❌ Failed to import configuration", err=True)
        raise click.Abort()


@config.command('reset')
@click.option('--force', is_flag=True, help='Skip confirmation')
def reset_config(force):
    """Reset configuration to defaults"""
    if not force:
        if not click.confirm("⚠️  Reset all configuration to defaults? This will remove all custom currencies!"):
            click.echo("Cancelled")
            return

    config_manager = get_config_manager()
    config_manager.currencies.clear()
    config_manager._initialize_defaults()
    config_manager.save()

    click.echo("✅ Configuration reset to defaults")


@config.command('path')
def show_path():
    """Show configuration file path"""
    config_manager = get_config_manager()
    click.echo(f"Configuration file: {config_manager.config_file}")


if __name__ == '__main__':
    config()

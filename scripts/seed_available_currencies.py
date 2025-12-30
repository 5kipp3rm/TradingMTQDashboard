#!/usr/bin/env python3
"""
Seed Available Currencies

Populates the available_currencies table with common forex pairs, commodities, and indices.
Run this script after creating the available_currencies table.

Usage:
    python scripts/seed_available_currencies.py
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_session, AvailableCurrency, CurrencyCategory, init_db
from src.utils.unified_logger import UnifiedLogger

logger = UnifiedLogger.get_logger(__name__)

# Currency data: (symbol, description, base, quote, pip_value, decimal_places, typical_spread)
CURRENCY_DATA = {
    "major": [
        ("EURUSD", "Euro vs US Dollar", "EUR", "USD", "0.0001", 5, "0.8"),
        ("GBPUSD", "British Pound vs US Dollar", "GBP", "USD", "0.0001", 5, "1.2"),
        ("USDJPY", "US Dollar vs Japanese Yen", "USD", "JPY", "0.01", 3, "0.9"),
        ("USDCHF", "US Dollar vs Swiss Franc", "USD", "CHF", "0.0001", 5, "1.1"),
        ("AUDUSD", "Australian Dollar vs US Dollar", "AUD", "USD", "0.0001", 5, "1.0"),
        ("USDCAD", "US Dollar vs Canadian Dollar", "USD", "CAD", "0.0001", 5, "1.3"),
        ("NZDUSD", "New Zealand Dollar vs US Dollar", "NZD", "USD", "0.0001", 5, "1.5"),
    ],
    "cross": [
        ("EURJPY", "Euro vs Japanese Yen", "EUR", "JPY", "0.01", 3, "1.5"),
        ("GBPJPY", "British Pound vs Japanese Yen", "GBP", "JPY", "0.01", 3, "2.1"),
        ("EURGBP", "Euro vs British Pound", "EUR", "GBP", "0.0001", 5, "1.0"),
        ("AUDJPY", "Australian Dollar vs Japanese Yen", "AUD", "JPY", "0.01", 3, "1.8"),
        ("EURAUD", "Euro vs Australian Dollar", "EUR", "AUD", "0.0001", 5, "2.0"),
        ("EURCHF", "Euro vs Swiss Franc", "EUR", "CHF", "0.0001", 5, "1.5"),
        ("AUDNZD", "Australian Dollar vs NZ Dollar", "AUD", "NZD", "0.0001", 5, "2.5"),
        ("NZDJPY", "New Zealand Dollar vs Yen", "NZD", "JPY", "0.01", 3, "2.0"),
        ("GBPAUD", "British Pound vs Australian Dollar", "GBP", "AUD", "0.0001", 5, "3.0"),
        ("GBPCAD", "British Pound vs Canadian Dollar", "GBP", "CAD", "0.0001", 5, "2.5"),
        ("EURNZD", "Euro vs New Zealand Dollar", "EUR", "NZD", "0.0001", 5, "3.5"),
        ("AUDCAD", "Australian Dollar vs Canadian Dollar", "AUD", "CAD", "0.0001", 5, "2.0"),
        ("GBPCHF", "British Pound vs Swiss Franc", "GBP", "CHF", "0.0001", 5, "2.5"),
        ("EURCAD", "Euro vs Canadian Dollar", "EUR", "CAD", "0.0001", 5, "2.0"),
    ],
    "exotic": [
        ("USDTRY", "US Dollar vs Turkish Lira", "USD", "TRY", "0.0001", 5, "15.0"),
        ("USDZAR", "US Dollar vs South African Rand", "USD", "ZAR", "0.0001", 5, "25.0"),
        ("USDMXN", "US Dollar vs Mexican Peso", "USD", "MXN", "0.0001", 5, "20.0"),
        ("USDSEK", "US Dollar vs Swedish Krona", "USD", "SEK", "0.0001", 5, "8.0"),
        ("USDNOK", "US Dollar vs Norwegian Krone", "USD", "NOK", "0.0001", 5, "9.0"),
        ("USDDKK", "US Dollar vs Danish Krone", "USD", "DKK", "0.0001", 5, "7.0"),
        ("USDPLN", "US Dollar vs Polish Zloty", "USD", "PLN", "0.0001", 5, "12.0"),
        ("USDHUF", "US Dollar vs Hungarian Forint", "USD", "HUF", "0.01", 3, "10.0"),
        ("USDCZK", "US Dollar vs Czech Koruna", "USD", "CZK", "0.0001", 5, "8.0"),
        ("USDSGD", "US Dollar vs Singapore Dollar", "USD", "SGD", "0.0001", 5, "3.0"),
        ("USDHKD", "US Dollar vs Hong Kong Dollar", "USD", "HKD", "0.0001", 5, "2.0"),
    ],
    "commodity": [
        ("XAUUSD", "Gold vs US Dollar", "XAU", "USD", "0.01", 2, "0.3"),
        ("XAGUSD", "Silver vs US Dollar", "XAG", "USD", "0.001", 3, "0.025"),
        ("XPTUSD", "Platinum vs US Dollar", "XPT", "USD", "0.01", 2, "2.0"),
        ("XPDUSD", "Palladium vs US Dollar", "XPD", "USD", "0.01", 2, "3.0"),
        ("USOIL", "US Crude Oil (WTI)", "USO", "USD", "0.01", 2, "0.05"),
        ("UKOIL", "UK Brent Crude Oil", "UKO", "USD", "0.01", 2, "0.05"),
    ],
    "crypto": [
        ("BTCUSD", "Bitcoin vs US Dollar", "BTC", "USD", "1.0", 2, "10.0"),
        ("ETHUSD", "Ethereum vs US Dollar", "ETH", "USD", "0.1", 2, "2.0"),
    ],
    "index": [
        ("US30", "Dow Jones Industrial Average", "US30", "USD", "1.0", 2, "2.0"),
        ("US500", "S&P 500 Index", "US500", "USD", "0.1", 2, "0.5"),
        ("NAS100", "NASDAQ 100 Index", "NAS100", "USD", "1.0", 2, "1.0"),
        ("GER40", "German DAX Index", "GER40", "EUR", "1.0", 2, "2.0"),
        ("UK100", "UK FTSE 100 Index", "UK100", "GBP", "1.0", 2, "1.5"),
        ("JPN225", "Japanese Nikkei 225", "JPN225", "JPY", "1.0", 2, "5.0"),
    ],
}


def seed_currencies():
    """Seed the available_currencies table"""
    # Initialize database connection
    init_db()

    total_added = 0
    total_skipped = 0

    # Use context manager for session
    with get_session() as session:
        try:
            for category, currencies in CURRENCY_DATA.items():
                logger.info(f"Processing {category} currencies", category=category, count=len(currencies))

                for symbol, description, base, quote, pip_val, decimals, spread in currencies:
                    # Check if currency already exists
                    existing = session.query(AvailableCurrency).filter_by(symbol=symbol).first()

                    if existing:
                        logger.info(f"Currency {symbol} already exists, skipping", symbol=symbol)
                        total_skipped += 1
                        continue

                    # Create new currency
                    currency = AvailableCurrency(
                        symbol=symbol,
                        description=description,
                        category=CurrencyCategory[category.upper()],
                        base_currency=base,
                        quote_currency=quote,
                        pip_value=Decimal(pip_val),
                        decimal_places=decimals,
                        min_lot_size=Decimal('0.01'),
                        max_lot_size=Decimal('100.0'),
                        typical_spread=Decimal(spread),
                        is_active=True,
                    )

                    session.add(currency)
                    total_added += 1
                    logger.info(f"Added currency {symbol}", symbol=symbol, category=category)

            # Note: session.commit() is handled by the context manager

            logger.info(
                "Currency seeding completed",
                total_added=total_added,
                total_skipped=total_skipped,
                total_categories=len(CURRENCY_DATA)
            )

            print(f"\n✅ Successfully seeded {total_added} currencies")
            print(f"⏭️  Skipped {total_skipped} existing currencies")
            print(f"📊 Total categories: {len(CURRENCY_DATA)}")

            # Show summary by category
            print("\nSummary by category:")
            for category in CURRENCY_DATA.keys():
                count = session.query(AvailableCurrency).filter_by(
                    category=CurrencyCategory[category.upper()]
                ).count()
                print(f"  {category.capitalize()}: {count} pairs")

        except Exception as e:
            session.rollback()
            logger.error(f"Error seeding currencies: {str(e)}", exc_info=True)
            print(f"\n❌ Error: {str(e)}")
            raise


def main():
    """Main entry point"""
    print("=" * 60)
    print("Seeding Available Currencies")
    print("=" * 60)

    try:
        seed_currencies()
        print("\n✅ Seeding completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Seeding failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

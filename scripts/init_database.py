#!/usr/bin/env python3
"""
Initialize Database with Default Data

This script initializes the database structure and optionally seeds it with default data.

Usage:
    # Initialize tables only (no data seeding)
    python init_database.py

    # Initialize tables AND seed with default currencies
    python init_database.py --seed

    # Force re-seed (will skip existing records)
    python init_database.py --seed --force

Options:
    --seed      Populate database with default currency data
    --force     Show detailed seeding information
    --help      Show this help message
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import init_db, get_session
from src.database.seed_data import seed_all
from src.utils.unified_logger import UnifiedLogger

logger = UnifiedLogger.get_logger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Initialize TradingMTQ database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--seed',
        action='store_true',
        help='Seed database with default currency data'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Show detailed information (for debugging)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("TradingMTQ Database Initialization")
    print("=" * 60)

    try:
        # Initialize database (creates tables)
        print("\n📦 Initializing database...")
        init_db(seed=args.seed)

        if not args.seed:
            print("\n✅ Database initialized successfully!")
            print("\n💡 To populate with default currency data, run:")
            print("   python init_database.py --seed")
        else:
            print("\n✅ Database initialized and seeded successfully!")

            if args.force:
                # Show detailed currency information
                from src.database import CurrencyConfiguration, AvailableCurrency
                with get_session() as session:
                    print("\n📊 Currency Configurations:")
                    configs = session.query(CurrencyConfiguration).all()
                    for config in configs:
                        status = "✓ enabled" if config.enabled else "✗ disabled"
                        print(f"   {config.symbol}: {status} - {config.description}")

                    print(f"\n📊 Available Currencies: {session.query(AvailableCurrency).count()} total")
                    from src.database.models import CurrencyCategory
                    for category in CurrencyCategory:
                        count = session.query(AvailableCurrency).filter_by(category=category).count()
                        if count > 0:
                            print(f"   {category.value}: {count} pairs")

        print("\n" + "=" * 60)
        return 0

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Make sure your .env file is configured with MT5 credentials")
        return 1


if __name__ == "__main__":
    sys.exit(main())

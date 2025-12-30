#!/usr/bin/env python3
"""
Create Available Currencies Table

Creates the available_currencies table directly using SQL if alembic is not available.
This is a fallback script for when alembic migration can't be run.

Usage:
    python scripts/create_available_currencies_table.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.database import engine
    from sqlalchemy import text
    print("Database connection established.")
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please ensure SQLAlchemy and other dependencies are installed.")
    sys.exit(1)


def create_table():
    """Create available_currencies table if it doesn't exist"""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS available_currencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol VARCHAR(20) NOT NULL UNIQUE,
        description VARCHAR(200),
        category VARCHAR(20) NOT NULL,
        base_currency VARCHAR(10),
        quote_currency VARCHAR(10),
        pip_value DECIMAL(10, 5) NOT NULL,
        decimal_places INTEGER NOT NULL,
        min_lot_size DECIMAL(10, 2) NOT NULL,
        max_lot_size DECIMAL(10, 2) NOT NULL,
        typical_spread DECIMAL(10, 5),
        is_active BOOLEAN NOT NULL DEFAULT 1,
        trading_hours_start VARCHAR(5),
        trading_hours_end VARCHAR(5),
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_indices_sql = [
        "CREATE INDEX IF NOT EXISTS ix_available_currencies_symbol ON available_currencies (symbol);",
        "CREATE INDEX IF NOT EXISTS ix_available_currencies_category ON available_currencies (category);",
        "CREATE INDEX IF NOT EXISTS ix_available_currencies_is_active ON available_currencies (is_active);"
    ]

    try:
        with engine.begin() as conn:
            # Create table
            print("Creating available_currencies table...")
            conn.execute(text(create_table_sql))
            print("✅ Table created successfully")

            # Create indices
            print("Creating indices...")
            for index_sql in create_indices_sql:
                conn.execute(text(index_sql))
            print("✅ Indices created successfully")

        print("\n✅ Database setup completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Error creating table: {str(e)}")
        return False


def main():
    """Main entry point"""
    print("=" * 60)
    print("Creating Available Currencies Table")
    print("=" * 60)

    if create_table():
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python scripts/seed_available_currencies.py")
        print("2. Restart your API server")
        return 0
    else:
        print("\n❌ Setup failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

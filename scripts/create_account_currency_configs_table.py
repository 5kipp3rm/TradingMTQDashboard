#!/usr/bin/env python3
"""
Create Account Currency Configs Table

Creates the account_currency_configs table directly using SQL if alembic is not available.
This table stores per-account currency configuration overrides.

Usage:
    python scripts/create_account_currency_configs_table.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import engine
from sqlalchemy import text


def create_table():
    """Create account_currency_configs table if it doesn't exist"""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS account_currency_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        currency_symbol VARCHAR(20) NOT NULL,
        enabled BOOLEAN NOT NULL,
        risk_percent FLOAT,
        max_position_size FLOAT,
        min_position_size FLOAT,
        strategy_type VARCHAR(20),
        timeframe VARCHAR(10),
        fast_period INTEGER,
        slow_period INTEGER,
        sl_pips INTEGER,
        tp_pips INTEGER,
        cooldown_seconds INTEGER,
        trade_on_signal_change BOOLEAN,
        allow_position_stacking BOOLEAN,
        max_positions_same_direction INTEGER,
        max_total_positions INTEGER,
        stacking_risk_multiplier FLOAT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES trading_accounts(id) ON DELETE CASCADE,
        FOREIGN KEY (currency_symbol) REFERENCES currency_configurations(symbol) ON DELETE CASCADE,
        UNIQUE (account_id, currency_symbol)
    );
    """

    create_indices_sql = [
        "CREATE INDEX IF NOT EXISTS ix_account_currency_configs_account_id ON account_currency_configs (account_id);",
        "CREATE INDEX IF NOT EXISTS ix_account_currency_configs_currency_symbol ON account_currency_configs (currency_symbol);",
    ]

    try:
        with engine.begin() as conn:
            # Create table
            print("Creating account_currency_configs table...")
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
    print("Creating Account Currency Configs Table")
    print("=" * 60)

    if create_table():
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Restart your API server")
        print("2. Add currencies to your accounts via the dashboard")
        return 0
    else:
        print("\n❌ Setup failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

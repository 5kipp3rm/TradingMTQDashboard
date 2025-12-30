#!/bin/bash
# Create account_currency_configs table directly in SQLite

DB_PATH="trading_bot.db"

echo "============================================================"
echo "Creating Account Currency Configs Table"
echo "============================================================"

sqlite3 "$DB_PATH" <<EOF
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

CREATE INDEX IF NOT EXISTS ix_account_currency_configs_account_id ON account_currency_configs (account_id);
CREATE INDEX IF NOT EXISTS ix_account_currency_configs_currency_symbol ON account_currency_configs (currency_symbol);
EOF

if [ $? -eq 0 ]; then
    echo "✅ Table created successfully"
    echo ""
    echo "Verifying table structure..."
    sqlite3 "$DB_PATH" ".schema account_currency_configs"
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Restart your API server"
    echo "2. Add currencies to your accounts via the dashboard"
else
    echo "❌ Error creating table"
    exit 1
fi

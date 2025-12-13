"""Initial database schema with Trade, Signal, AccountSnapshot, DailyPerformance models

Revision ID: 001
Revises:
Create Date: 2025-12-13 11:49:25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables"""

    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticket', sa.Integer(), nullable=True),
        sa.Column('symbol', sa.String(length=12), nullable=False),
        sa.Column('magic_number', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('trade_type', sa.Enum('BUY', 'SELL', 'HOLD', name='signaltype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'OPEN', 'CLOSED', 'CANCELLED', 'FAILED', name='tradestatus'), nullable=False, server_default='PENDING'),
        sa.Column('entry_price', sa.Numeric(precision=10, scale=5), nullable=False),
        sa.Column('entry_time', sa.DateTime(), nullable=False),
        sa.Column('volume', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stop_loss', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('take_profit', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('exit_price', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('exit_time', sa.DateTime(), nullable=True),
        sa.Column('profit', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('commission', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.0'),
        sa.Column('swap', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.0'),
        sa.Column('pips', sa.Numeric(precision=10, scale=1), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('strategy_name', sa.String(length=50), nullable=True),
        sa.Column('signal_confidence', sa.Float(), nullable=True),
        sa.Column('signal_reason', sa.Text(), nullable=True),
        sa.Column('ml_enhanced', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ml_confidence', sa.Float(), nullable=True),
        sa.Column('ai_approved', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket')
    )
    op.create_index(op.f('ix_trades_ticket'), 'trades', ['ticket'], unique=True)
    op.create_index(op.f('ix_trades_symbol'), 'trades', ['symbol'], unique=False)
    op.create_index(op.f('ix_trades_status'), 'trades', ['status'], unique=False)
    op.create_index(op.f('ix_trades_entry_time'), 'trades', ['entry_time'], unique=False)
    op.create_index(op.f('ix_trades_exit_time'), 'trades', ['exit_time'], unique=False)
    op.create_index(op.f('ix_trades_strategy_name'), 'trades', ['strategy_name'], unique=False)

    # Create signals table
    op.create_table(
        'signals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=12), nullable=False),
        sa.Column('signal_type', sa.Enum('BUY', 'SELL', 'HOLD', name='signaltype'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=5), nullable=False),
        sa.Column('stop_loss', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('take_profit', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('strategy_name', sa.String(length=50), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('ml_enhanced', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ml_confidence', sa.Float(), nullable=True),
        sa.Column('ml_agreed', sa.Boolean(), nullable=True),
        sa.Column('executed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('execution_reason', sa.Text(), nullable=True),
        sa.Column('trade_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['trade_id'], ['trades.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signals_symbol'), 'signals', ['symbol'], unique=False)
    op.create_index(op.f('ix_signals_signal_type'), 'signals', ['signal_type'], unique=False)
    op.create_index(op.f('ix_signals_timestamp'), 'signals', ['timestamp'], unique=False)
    op.create_index(op.f('ix_signals_strategy_name'), 'signals', ['strategy_name'], unique=False)
    op.create_index(op.f('ix_signals_executed'), 'signals', ['executed'], unique=False)

    # Create account_snapshots table
    op.create_table(
        'account_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_number', sa.Integer(), nullable=False),
        sa.Column('server', sa.String(length=50), nullable=False),
        sa.Column('broker', sa.String(length=50), nullable=False),
        sa.Column('balance', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('equity', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('profit', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.0'),
        sa.Column('margin', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.0'),
        sa.Column('margin_free', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.0'),
        sa.Column('margin_level', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('open_positions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_volume', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.0'),
        sa.Column('snapshot_time', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_account_snapshots_account_number'), 'account_snapshots', ['account_number'], unique=False)
    op.create_index(op.f('ix_account_snapshots_snapshot_time'), 'account_snapshots', ['snapshot_time'], unique=False)

    # Create daily_performance table
    op.create_table(
        'daily_performance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('winning_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losing_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gross_profit', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.0'),
        sa.Column('gross_loss', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.0'),
        sa.Column('net_profit', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.0'),
        sa.Column('win_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('profit_factor', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('average_win', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('average_loss', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('largest_win', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('largest_loss', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('end_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('end_equity', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_index(op.f('ix_daily_performance_date'), 'daily_performance', ['date'], unique=True)


def downgrade() -> None:
    """Drop all tables"""

    op.drop_index(op.f('ix_daily_performance_date'), table_name='daily_performance')
    op.drop_table('daily_performance')

    op.drop_index(op.f('ix_account_snapshots_snapshot_time'), table_name='account_snapshots')
    op.drop_index(op.f('ix_account_snapshots_account_number'), table_name='account_snapshots')
    op.drop_table('account_snapshots')

    op.drop_index(op.f('ix_signals_executed'), table_name='signals')
    op.drop_index(op.f('ix_signals_strategy_name'), table_name='signals')
    op.drop_index(op.f('ix_signals_timestamp'), table_name='signals')
    op.drop_index(op.f('ix_signals_signal_type'), table_name='signals')
    op.drop_index(op.f('ix_signals_symbol'), table_name='signals')
    op.drop_table('signals')

    op.drop_index(op.f('ix_trades_strategy_name'), table_name='trades')
    op.drop_index(op.f('ix_trades_exit_time'), table_name='trades')
    op.drop_index(op.f('ix_trades_entry_time'), table_name='trades')
    op.drop_index(op.f('ix_trades_status'), table_name='trades')
    op.drop_index(op.f('ix_trades_symbol'), table_name='trades')
    op.drop_index(op.f('ix_trades_ticket'), table_name='trades')
    op.drop_table('trades')

    # Drop enums (PostgreSQL specific, will be ignored by SQLite)
    op.execute('DROP TYPE IF EXISTS tradestatus')
    op.execute('DROP TYPE IF EXISTS signaltype')

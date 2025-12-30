"""add_available_currencies_table

Revision ID: b7c8e9f1d2a3
Revises: 9f0df884bcb0
Create Date: 2025-12-28 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8e9f1d2a3'
down_revision: Union[str, None] = '9f0df884bcb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create available_currencies table"""
    op.create_table(
        'available_currencies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('category', sa.Enum('major', 'cross', 'exotic', 'commodity', 'crypto', 'index', name='currencycategory'), nullable=False),
        sa.Column('base_currency', sa.String(length=10), nullable=True),
        sa.Column('quote_currency', sa.String(length=10), nullable=True),
        sa.Column('pip_value', sa.Numeric(precision=10, scale=5), nullable=False),
        sa.Column('decimal_places', sa.Integer(), nullable=False),
        sa.Column('min_lot_size', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('max_lot_size', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('typical_spread', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('trading_hours_start', sa.String(length=5), nullable=True),
        sa.Column('trading_hours_end', sa.String(length=5), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )
    op.create_index(op.f('ix_available_currencies_symbol'), 'available_currencies', ['symbol'], unique=True)
    op.create_index(op.f('ix_available_currencies_category'), 'available_currencies', ['category'], unique=False)
    op.create_index(op.f('ix_available_currencies_is_active'), 'available_currencies', ['is_active'], unique=False)


def downgrade() -> None:
    """Drop available_currencies table"""
    op.drop_index(op.f('ix_available_currencies_is_active'), table_name='available_currencies')
    op.drop_index(op.f('ix_available_currencies_category'), table_name='available_currencies')
    op.drop_index(op.f('ix_available_currencies_symbol'), table_name='available_currencies')
    op.drop_table('available_currencies')
    # Drop the enum type
    sa.Enum('major', 'cross', 'exotic', 'commodity', 'crypto', 'index', name='currencycategory').drop(op.get_bind(), checkfirst=True)

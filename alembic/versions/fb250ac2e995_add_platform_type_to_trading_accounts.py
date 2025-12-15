"""add_platform_type_to_trading_accounts

Revision ID: fb250ac2e995
Revises: 756dae056c20
Create Date: 2025-12-15 16:56:24.879830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb250ac2e995'
down_revision: Union[str, None] = '756dae056c20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add platform_type column with default value MT5
    op.add_column('trading_accounts',
        sa.Column('platform_type',
                 sa.Enum('MT4', 'MT5', name='platformtype'),
                 nullable=False,
                 server_default='MT5'))


def downgrade() -> None:
    # Remove platform_type column
    op.drop_column('trading_accounts', 'platform_type')
    # Drop the enum type
    op.execute("DROP TYPE platformtype")

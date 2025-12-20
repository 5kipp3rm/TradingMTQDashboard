"""add_account_configuration_columns

Revision ID: a9392368ae24
Revises: fb250ac2e995
Create Date: 2025-12-20 08:58:41.288911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9392368ae24'
down_revision: Union[str, None] = 'fb250ac2e995'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add configuration columns to trading_accounts table
    op.add_column('trading_accounts', sa.Column('config_source', sa.String(length=20), nullable=True, server_default='hybrid'))
    op.add_column('trading_accounts', sa.Column('config_path', sa.String(length=255), nullable=True))
    op.add_column('trading_accounts', sa.Column('trading_config_json', sa.JSON(), nullable=True))
    op.add_column('trading_accounts', sa.Column('config_validated_at', sa.DateTime(), nullable=True))
    op.add_column('trading_accounts', sa.Column('config_validation_error', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove configuration columns from trading_accounts table
    op.drop_column('trading_accounts', 'config_validation_error')
    op.drop_column('trading_accounts', 'config_validated_at')
    op.drop_column('trading_accounts', 'trading_config_json')
    op.drop_column('trading_accounts', 'config_path')
    op.drop_column('trading_accounts', 'config_source')

"""
Alembic Environment Configuration for TradingMTQ

Uses Phase 0 patterns:
- Structured logging
- Error handling
- Configuration management
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models and Base
from src.database.models import Base
from src.utils.structured_logger import StructuredLogger

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use structured logger for migration operations
logger = StructuredLogger(__name__)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Override sqlalchemy.url from environment variable if set
database_url = os.getenv('TRADING_MTQ_DATABASE_URL')
if database_url:
    config.set_main_option('sqlalchemy.url', database_url)
    logger.info("Using database URL from environment", source="TRADING_MTQ_DATABASE_URL")
else:
    logger.info("Using database URL from alembic.ini", url=config.get_main_option('sqlalchemy.url'))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    logger.info("Running migrations in offline mode")

    with context.begin_transaction():
        context.run_migrations()

    logger.info("Offline migrations complete")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    logger.info("Running migrations in online mode")

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            logger.info("Starting migration transaction")
            context.run_migrations()
            logger.info("Migration transaction complete")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

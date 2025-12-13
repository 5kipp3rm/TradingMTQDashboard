"""
Database Migration Utilities for TradingMTQ

Provides helper functions for database initialization and migrations.

Uses Phase 0 patterns:
- Structured logging
- Custom exceptions
- Error context
"""
import os
import sys
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config

from src.utils.structured_logger import StructuredLogger, CorrelationContext
from src.exceptions import DatabaseError

logger = StructuredLogger(__name__)


def get_alembic_config(database_url: Optional[str] = None) -> Config:
    """
    Get Alembic configuration

    Args:
        database_url: Optional database URL override

    Returns:
        Alembic Config object
    """
    with CorrelationContext():
        # Get project root directory
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        if not alembic_ini.exists():
            raise DatabaseError(
                "Alembic configuration not found",
                context={'alembic_ini': str(alembic_ini)}
            )

        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini))

        # Override database URL if provided
        if database_url:
            alembic_cfg.set_main_option('sqlalchemy.url', database_url)
            logger.info("Using custom database URL", source="parameter")
        else:
            # Try environment variable
            env_url = os.getenv('TRADING_MTQ_DATABASE_URL')
            if env_url:
                alembic_cfg.set_main_option('sqlalchemy.url', env_url)
                logger.info("Using database URL from environment", source="TRADING_MTQ_DATABASE_URL")
            else:
                logger.info("Using database URL from alembic.ini")

        return alembic_cfg


def upgrade_database(database_url: Optional[str] = None, revision: str = "head") -> None:
    """
    Upgrade database to a specific revision

    Args:
        database_url: Optional database URL
        revision: Target revision (default: "head" for latest)

    Raises:
        DatabaseError: If upgrade fails
    """
    with CorrelationContext():
        try:
            alembic_cfg = get_alembic_config(database_url)

            logger.info("Starting database upgrade", revision=revision)
            command.upgrade(alembic_cfg, revision)
            logger.info("Database upgrade complete", revision=revision)

        except Exception as e:
            logger.error(
                "Database upgrade failed",
                revision=revision,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                f"Failed to upgrade database: {e}",
                context={'revision': revision}
            )


def downgrade_database(database_url: Optional[str] = None, revision: str = "-1") -> None:
    """
    Downgrade database to a specific revision

    Args:
        database_url: Optional database URL
        revision: Target revision (default: "-1" for previous)

    Raises:
        DatabaseError: If downgrade fails
    """
    with CorrelationContext():
        try:
            alembic_cfg = get_alembic_config(database_url)

            logger.info("Starting database downgrade", revision=revision)
            command.downgrade(alembic_cfg, revision)
            logger.info("Database downgrade complete", revision=revision)

        except Exception as e:
            logger.error(
                "Database downgrade failed",
                revision=revision,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                f"Failed to downgrade database: {e}",
                context={'revision': revision}
            )


def get_current_revision(database_url: Optional[str] = None) -> Optional[str]:
    """
    Get current database revision

    Args:
        database_url: Optional database URL

    Returns:
        Current revision string or None if no migrations applied
    """
    with CorrelationContext():
        try:
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext
            from sqlalchemy import create_engine

            alembic_cfg = get_alembic_config(database_url)

            # Get database URL from config
            db_url = alembic_cfg.get_main_option('sqlalchemy.url')

            # Create engine and get current revision
            engine = create_engine(db_url)
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()

            logger.info("Retrieved current database revision", revision=current_rev)
            return current_rev

        except Exception as e:
            logger.error(
                "Failed to get current revision",
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(f"Failed to get current revision: {e}")


def create_new_migration(message: str, database_url: Optional[str] = None, autogenerate: bool = True) -> None:
    """
    Create a new migration

    Args:
        message: Migration message
        database_url: Optional database URL
        autogenerate: Whether to auto-generate migration from model changes

    Raises:
        DatabaseError: If migration creation fails
    """
    with CorrelationContext():
        try:
            alembic_cfg = get_alembic_config(database_url)

            logger.info("Creating new migration", message=message, autogenerate=autogenerate)

            if autogenerate:
                command.revision(alembic_cfg, message=message, autogenerate=True)
            else:
                command.revision(alembic_cfg, message=message)

            logger.info("Migration created successfully", message=message)

        except Exception as e:
            logger.error(
                "Migration creation failed",
                message=message,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                f"Failed to create migration: {e}",
                context={'message': message}
            )


def initialize_database(database_url: Optional[str] = None) -> None:
    """
    Initialize database with all migrations

    This is a convenience function that:
    1. Creates the database schema
    2. Applies all migrations

    Args:
        database_url: Optional database URL

    Raises:
        DatabaseError: If initialization fails
    """
    with CorrelationContext():
        try:
            logger.info("Initializing database")

            # Apply all migrations
            upgrade_database(database_url, "head")

            logger.info("Database initialization complete")

        except Exception as e:
            logger.error(
                "Database initialization failed",
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(f"Failed to initialize database: {e}")


# CLI interface for direct script execution
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='TradingMTQ Database Migration Utility')
    parser.add_argument(
        'command',
        choices=['upgrade', 'downgrade', 'current', 'create', 'init'],
        help='Migration command to execute'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        help='Database URL (overrides environment and config)'
    )
    parser.add_argument(
        '--revision',
        type=str,
        default='head',
        help='Target revision (for upgrade/downgrade)'
    )
    parser.add_argument(
        '--message',
        type=str,
        help='Migration message (for create command)'
    )
    parser.add_argument(
        '--no-autogenerate',
        action='store_true',
        help='Disable autogenerate (for create command)'
    )

    args = parser.parse_args()

    try:
        if args.command == 'upgrade':
            upgrade_database(args.database_url, args.revision)
        elif args.command == 'downgrade':
            upgrade_database(args.database_url, args.revision)
        elif args.command == 'current':
            revision = get_current_revision(args.database_url)
            print(f"Current revision: {revision}")
        elif args.command == 'create':
            if not args.message:
                print("Error: --message required for create command")
                sys.exit(1)
            create_new_migration(args.message, args.database_url, not args.no_autogenerate)
        elif args.command == 'init':
            initialize_database(args.database_url)
    except DatabaseError as e:
        print(f"Error: {e}")
        sys.exit(1)

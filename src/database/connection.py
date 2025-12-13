"""
Database Connection Management for TradingMTQ

Uses Phase 0 patterns:
- Custom exceptions for database errors
- Structured logging with correlation IDs
- Automatic retry for transient failures
- Connection pooling for performance
"""
from typing import Optional, Generator
from contextlib import contextmanager
import os

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Phase 0 imports
from src.exceptions import DatabaseError, ConnectionError as TradingConnectionError
from src.utils.structured_logger import StructuredLogger, CorrelationContext
from src.utils.error_handlers import handle_mt5_errors

from .models import Base

logger = StructuredLogger(__name__)

# Global engine and session factory
_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def get_database_url(env: str = "development") -> str:
    """
    Get database URL from environment

    Args:
        env: Environment name (development, production, test)

    Returns:
        Database URL string

    Raises:
        DatabaseError: If DATABASE_URL not configured
    """
    if env == "test":
        # Use in-memory SQLite for testing
        return "sqlite:///:memory:"

    # Get from environment or default to SQLite file
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        if env == "production":
            raise DatabaseError(
                "DATABASE_URL environment variable required for production",
                context={'env': env}
            )
        else:
            # Development default: SQLite file
            db_path = os.path.join(os.getcwd(), "trading_mtq.db")
            db_url = f"sqlite:///{db_path}"
            logger.info("Using default SQLite database", db_path=db_path)

    return db_url


@handle_mt5_errors(retry_count=3, retry_delay=1.0)
def init_db(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    Initialize database connection

    Args:
        database_url: Database connection URL (optional, uses env if not provided)
        echo: Whether to echo SQL statements

    Returns:
        SQLAlchemy Engine instance

    Raises:
        DatabaseError: If database initialization fails
    """
    global _engine, _SessionFactory

    with CorrelationContext():
        if _engine is not None:
            logger.warning("Database already initialized", action="skip")
            return _engine

        # Get database URL
        if database_url is None:
            env = os.getenv("ENVIRONMENT", "development")
            database_url = get_database_url(env)

        logger.info("Initializing database", database_url=database_url.split('@')[-1])  # Hide credentials

        try:
            # Create engine with connection pooling
            _engine = create_engine(
                database_url,
                echo=echo,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
            )

            # Add connection event listeners
            @event.listens_for(_engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                logger.debug("New database connection established")

            @event.listens_for(_engine, "close")
            def receive_close(dbapi_conn, connection_record):
                logger.debug("Database connection closed")

            # Create all tables
            Base.metadata.create_all(_engine)
            logger.info("Database tables created/verified")

            # Create session factory
            _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)

            logger.info("Database initialized successfully", pool_size=5)
            return _engine

        except Exception as e:
            logger.error(
                "Database initialization failed",
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                f"Failed to initialize database: {e}",
                context={'database_url': database_url.split('@')[-1]}
            )


def close_db() -> None:
    """
    Close database connection and cleanup resources

    Safe to call multiple times
    """
    global _engine, _SessionFactory

    with CorrelationContext():
        if _engine is not None:
            logger.info("Closing database connection")
            _engine.dispose()
            _engine = None
            _SessionFactory = None
            logger.info("Database connection closed")
        else:
            logger.debug("Database not initialized, nothing to close")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get database session context manager

    Usage:
        with get_session() as session:
            trade = Trade(...)
            session.add(trade)
            session.commit()

    Yields:
        SQLAlchemy Session instance

    Raises:
        DatabaseError: If session creation fails
    """
    if _SessionFactory is None:
        raise DatabaseError(
            "Database not initialized. Call init_db() first.",
            context={'action': 'get_session'}
        )

    session: Session = _SessionFactory()

    try:
        with CorrelationContext():
            logger.debug("Database session started")
            yield session
            session.commit()
            logger.debug("Database session committed")

    except Exception as e:
        session.rollback()
        logger.error(
            "Database session error, rolling back",
            error=str(e),
            exc_info=True
        )
        raise DatabaseError(
            f"Database session error: {e}",
            context={'operation': 'session_transaction'}
        )

    finally:
        session.close()
        logger.debug("Database session closed")


def get_session_factory() -> sessionmaker:
    """
    Get session factory for manual session management

    Returns:
        SQLAlchemy sessionmaker

    Raises:
        DatabaseError: If database not initialized
    """
    if _SessionFactory is None:
        raise DatabaseError(
            "Database not initialized. Call init_db() first.",
            context={'action': 'get_session_factory'}
        )

    return _SessionFactory


def get_engine() -> Engine:
    """
    Get database engine

    Returns:
        SQLAlchemy Engine

    Raises:
        DatabaseError: If database not initialized
    """
    if _engine is None:
        raise DatabaseError(
            "Database not initialized. Call init_db() first.",
            context={'action': 'get_engine'}
        )

    return _engine


# Health check function
def check_database_health() -> bool:
    """
    Check database connection health

    Returns:
        True if database is healthy, False otherwise
    """
    from sqlalchemy import text

    try:
        with get_session() as session:
            # Simple query to test connection
            session.execute(text("SELECT 1"))
            logger.debug("Database health check passed")
            return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False

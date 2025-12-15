"""
MT5 Session Manager

Manages multiple MT5 account connections simultaneously.
Provides session lifecycle management (connect, disconnect, reconnect).
Thread-safe operation with proper resource cleanup.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from sqlalchemy import select, update

from src.connectors.mt5_connector import MT5Connector
from src.connectors.base import ConnectionStatus
from src.database.models import TradingAccount
from src.utils.logger import get_logger
from src.exceptions import ConnectionError, AuthenticationError


logger = get_logger(__name__)


class ConnectionState:
    """
    Connection state for a trading account.
    """
    def __init__(
        self,
        account_id: int,
        account_number: int,
        is_connected: bool = False,
        connector: Optional[MT5Connector] = None,
        last_connected_at: Optional[datetime] = None,
        last_disconnected_at: Optional[datetime] = None,
        connection_error: Optional[str] = None,
        retry_count: int = 0
    ):
        self.account_id = account_id
        self.account_number = account_number
        self.is_connected = is_connected
        self.connector = connector
        self.last_connected_at = last_connected_at
        self.last_disconnected_at = last_disconnected_at
        self.connection_error = connection_error
        self.retry_count = retry_count

    def to_dict(self) -> dict:
        """Convert state to dictionary"""
        return {
            "account_id": self.account_id,
            "account_number": self.account_number,
            "is_connected": self.is_connected,
            "last_connected_at": self.last_connected_at.isoformat() if self.last_connected_at else None,
            "last_disconnected_at": self.last_disconnected_at.isoformat() if self.last_disconnected_at else None,
            "connection_error": self.connection_error,
            "retry_count": self.retry_count,
            "connector_status": self.connector.status.value if self.connector else None
        }


class MT5SessionManager:
    """
    Manages multiple MT5 account connections simultaneously.

    Features:
    - Connect/disconnect multiple accounts
    - Track connection state per account
    - Auto-reconnect on failure
    - Thread-safe operations
    - Resource cleanup
    """

    def __init__(self):
        """Initialize session manager"""
        self._sessions: Dict[int, ConnectionState] = {}
        self._lock = asyncio.Lock()
        self._max_retry_attempts = 3
        self._retry_delay_seconds = 5

        logger.info("MT5SessionManager initialized")

    async def connect_account(
        self,
        account: TradingAccount,
        db: Session,
        force_reconnect: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Connect to MT5 account and store session.

        Args:
            account: TradingAccount model instance
            db: Database session
            force_reconnect: Force reconnect if already connected

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        async with self._lock:
            account_id = account.id
            account_number = account.account_number

            # Check if already connected
            if account_id in self._sessions:
                state = self._sessions[account_id]
                if state.is_connected and not force_reconnect:
                    logger.info(
                        "Account already connected",
                        account_id=account_id,
                        account_number=account_number
                    )
                    return True, None

                # Force reconnect - disconnect first
                if force_reconnect:
                    await self._disconnect_internal(account_id)

            logger.info(
                "Connecting to MT5 account",
                account_id=account_id,
                account_number=account_number,
                broker=account.broker,
                server=account.server
            )

            # Create new MT5 connector instance
            instance_id = f"account_{account_id}_{account_number}"
            connector = MT5Connector(instance_id=instance_id)

            # Initialize connection state
            state = ConnectionState(
                account_id=account_id,
                account_number=account_number,
                connector=connector
            )

            try:
                # Attempt connection
                success = connector.connect(
                    login=account.login,
                    password=account.password_encrypted,  # TODO: Decrypt password
                    server=account.server,
                    timeout=60000
                )

                if success:
                    # Update state
                    state.is_connected = True
                    state.last_connected_at = datetime.now(timezone.utc)
                    state.connection_error = None
                    state.retry_count = 0

                    # Store session
                    self._sessions[account_id] = state

                    # Update database
                    account.last_connected = state.last_connected_at
                    db.commit()

                    logger.info(
                        "Successfully connected to MT5 account",
                        account_id=account_id,
                        account_number=account_number
                    )

                    return True, None

                else:
                    error_msg = "Connection failed without exception"
                    state.connection_error = error_msg
                    logger.error(
                        "Failed to connect to MT5 account",
                        account_id=account_id,
                        account_number=account_number,
                        error=error_msg
                    )
                    return False, error_msg

            except AuthenticationError as e:
                error_msg = f"Authentication failed: {str(e)}"
                state.connection_error = error_msg
                state.last_disconnected_at = datetime.now(timezone.utc)
                self._sessions[account_id] = state

                logger.error(
                    "Authentication error connecting to MT5 account",
                    account_id=account_id,
                    account_number=account_number,
                    error=error_msg
                )
                return False, error_msg

            except ConnectionError as e:
                error_msg = f"Connection error: {str(e)}"
                state.connection_error = error_msg
                state.last_disconnected_at = datetime.now(timezone.utc)
                self._sessions[account_id] = state

                logger.error(
                    "Connection error connecting to MT5 account",
                    account_id=account_id,
                    account_number=account_number,
                    error=error_msg
                )
                return False, error_msg

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                state.connection_error = error_msg
                state.last_disconnected_at = datetime.now(timezone.utc)
                self._sessions[account_id] = state

                logger.error(
                    "Unexpected error connecting to MT5 account",
                    account_id=account_id,
                    account_number=account_number,
                    error=error_msg,
                    exc_info=True
                )
                return False, error_msg

    async def disconnect_account(
        self,
        account_id: int,
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """
        Disconnect MT5 account and cleanup session.

        Args:
            account_id: TradingAccount ID
            db: Database session

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        async with self._lock:
            return await self._disconnect_internal(account_id)

    async def _disconnect_internal(self, account_id: int) -> Tuple[bool, Optional[str]]:
        """
        Internal disconnect method (assumes lock is held).

        Args:
            account_id: TradingAccount ID

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if account_id not in self._sessions:
            logger.warning("Account not found in sessions", account_id=account_id)
            return False, "Account not found in sessions"

        state = self._sessions[account_id]

        logger.info(
            "Disconnecting MT5 account",
            account_id=account_id,
            account_number=state.account_number
        )

        try:
            if state.connector:
                state.connector.disconnect()

            # Update state
            state.is_connected = False
            state.last_disconnected_at = datetime.now(timezone.utc)
            state.connector = None

            # Remove from sessions
            del self._sessions[account_id]

            logger.info(
                "Successfully disconnected MT5 account",
                account_id=account_id,
                account_number=state.account_number
            )

            return True, None

        except Exception as e:
            error_msg = f"Disconnect error: {str(e)}"
            logger.error(
                "Error disconnecting MT5 account",
                account_id=account_id,
                error=error_msg,
                exc_info=True
            )
            return False, error_msg

    def get_session(self, account_id: int) -> Optional[MT5Connector]:
        """
        Get active MT5 connector for account.

        Args:
            account_id: TradingAccount ID

        Returns:
            MT5Connector instance or None if not connected
        """
        state = self._sessions.get(account_id)
        if state and state.is_connected and state.connector:
            return state.connector
        return None

    def get_connection_state(self, account_id: int) -> Optional[ConnectionState]:
        """
        Get connection state for account.

        Args:
            account_id: TradingAccount ID

        Returns:
            ConnectionState or None if not found
        """
        return self._sessions.get(account_id)

    def list_active_sessions(self) -> List[int]:
        """
        List all connected account IDs.

        Returns:
            List of account IDs with active sessions
        """
        return [
            account_id
            for account_id, state in self._sessions.items()
            if state.is_connected
        ]

    def get_all_connection_states(self) -> Dict[int, ConnectionState]:
        """
        Get all connection states.

        Returns:
            Dictionary of account_id -> ConnectionState
        """
        return self._sessions.copy()

    async def reconnect_account(
        self,
        account_id: int,
        account: TradingAccount,
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """
        Reconnect a disconnected account.

        Args:
            account_id: TradingAccount ID
            account: TradingAccount model instance
            db: Database session

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        logger.info("Reconnecting MT5 account", account_id=account_id)

        # Disconnect if currently connected
        if account_id in self._sessions:
            await self.disconnect_account(account_id, db)

        # Wait before reconnecting
        await asyncio.sleep(2)

        # Attempt connection
        return await self.connect_account(account, db)

    async def reconnect_all(
        self,
        db: Session
    ) -> Dict[int, Tuple[bool, Optional[str]]]:
        """
        Reconnect all previously connected accounts.

        Args:
            db: Database session

        Returns:
            Dictionary of account_id -> (success, error_message)
        """
        logger.info("Reconnecting all MT5 accounts")

        results = {}

        # Get all accounts that were previously connected
        account_ids = list(self._sessions.keys())

        for account_id in account_ids:
            # Get account from database
            account = db.get(TradingAccount, account_id)
            if not account or not account.is_active:
                logger.warning(
                    "Skipping reconnect for inactive account",
                    account_id=account_id
                )
                continue

            # Attempt reconnection
            success, error = await self.reconnect_account(account_id, account, db)
            results[account_id] = (success, error)

        logger.info(
            "Reconnect all completed",
            total=len(results),
            successful=sum(1 for s, _ in results.values() if s)
        )

        return results

    async def disconnect_all(self, db: Session) -> Dict[int, Tuple[bool, Optional[str]]]:
        """
        Disconnect all connected accounts.

        Args:
            db: Database session

        Returns:
            Dictionary of account_id -> (success, error_message)
        """
        logger.info("Disconnecting all MT5 accounts")

        results = {}
        account_ids = list(self._sessions.keys())

        for account_id in account_ids:
            success, error = await self.disconnect_account(account_id, db)
            results[account_id] = (success, error)

        logger.info(
            "Disconnect all completed",
            total=len(results),
            successful=sum(1 for s, _ in results.values() if s)
        )

        return results

    def is_connected(self, account_id: int) -> bool:
        """
        Check if account is connected.

        Args:
            account_id: TradingAccount ID

        Returns:
            True if connected, False otherwise
        """
        state = self._sessions.get(account_id)
        return state is not None and state.is_connected

    def get_stats(self) -> dict:
        """
        Get session manager statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "total_sessions": len(self._sessions),
            "connected_sessions": sum(1 for s in self._sessions.values() if s.is_connected),
            "sessions": [
                {
                    "account_id": state.account_id,
                    "account_number": state.account_number,
                    "is_connected": state.is_connected,
                    "last_connected_at": state.last_connected_at.isoformat() if state.last_connected_at else None,
                    "retry_count": state.retry_count
                }
                for state in self._sessions.values()
            ]
        }


# Global session manager instance
session_manager = MT5SessionManager()

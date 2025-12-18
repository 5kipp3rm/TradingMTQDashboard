"""
Account Connection Management Endpoints

Provides REST endpoints for connecting/disconnecting MT5 accounts.
Supports individual and bulk operations with WebSocket event broadcasting.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import get_db_dependency, TradingAccount
from src.services.session_manager import session_manager
from src.api.websocket import connection_manager


router = APIRouter()


# Pydantic Models for Request/Response

class ConnectionStatusResponse(BaseModel):
    """Response model for connection status"""
    account_id: int
    account_number: int
    is_connected: bool
    last_connected_at: Optional[str]
    last_disconnected_at: Optional[str]
    connection_error: Optional[str]
    retry_count: int
    account_info: Optional[dict] = None

    class Config:
        from_attributes = True


class BulkConnectionResponse(BaseModel):
    """Response model for bulk connection operations"""
    total: int
    successful: int
    failed: int
    results: List[dict]


# ============================================================================
# MT5 CONNECTION MANAGEMENT ENDPOINTS
# ============================================================================


@router.post("/accounts/{account_id}/connect", response_model=ConnectionStatusResponse)
async def connect_account(
    account_id: int,
    force_reconnect: bool = Query(False, description="Force reconnect if already connected"),
    db: Session = Depends(get_db_dependency)
):
    """
    Connect to MT5 account.

    Establishes MT5 connection for the specified account and stores the session.
    Broadcasts WebSocket event on successful connection.
    """
    # Get account
    account = db.get(TradingAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    if not account.is_active:
        raise HTTPException(status_code=400, detail="Cannot connect to inactive account")

    # Attempt connection
    success, error = await session_manager.connect_account(account, db, force_reconnect=force_reconnect)

    if not success:
        raise HTTPException(status_code=500, detail=f"Connection failed: {error}")

    # Get connection state
    state = session_manager.get_connection_state(account_id)
    if not state:
        raise HTTPException(status_code=500, detail="Failed to retrieve connection state")

    # Get account info from MT5
    connector = session_manager.get_session(account_id)
    account_info_dict = None
    if connector:
        try:
            account_info = connector.get_account_info()
            if account_info:
                account_info_dict = {
                    "balance": account_info.balance,
                    "equity": account_info.equity,
                    "profit": account_info.profit,
                    "margin": account_info.margin,
                    "margin_free": account_info.margin_free,
                    "margin_level": account_info.margin_level
                }
        except Exception as e:
            # Log error but don't fail the connection
            pass

    # Broadcast WebSocket event
    await connection_manager.broadcast_account_connection_event(
        "connected",
        {
            "account_id": account_id,
            "account_number": account.account_number,
            "account_name": account.account_name,
            "is_connected": True
        }
    )

    return ConnectionStatusResponse(
        account_id=state.account_id,
        account_number=state.account_number,
        is_connected=state.is_connected,
        last_connected_at=state.last_connected_at.isoformat() if state.last_connected_at else None,
        last_disconnected_at=state.last_disconnected_at.isoformat() if state.last_disconnected_at else None,
        connection_error=state.connection_error,
        retry_count=state.retry_count,
        account_info=account_info_dict
    )


@router.post("/accounts/{account_id}/disconnect", response_model=ConnectionStatusResponse)
async def disconnect_account(
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Disconnect from MT5 account.

    Terminates MT5 connection and cleanup session.
    Broadcasts WebSocket event on successful disconnection.
    """
    # Get account
    account = db.get(TradingAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    # Attempt disconnection
    success, error = await session_manager.disconnect_account(account_id, db)

    if not success:
        raise HTTPException(status_code=500, detail=f"Disconnection failed: {error}")

    # Broadcast WebSocket event
    await connection_manager.broadcast_account_connection_event(
        "disconnected",
        {
            "account_id": account_id,
            "account_number": account.account_number,
            "account_name": account.account_name,
            "is_connected": False
        }
    )

    return ConnectionStatusResponse(
        account_id=account_id,
        account_number=account.account_number,
        is_connected=False,
        last_connected_at=None,
        last_disconnected_at=None,
        connection_error=None,
        retry_count=0,
        account_info=None
    )


@router.get("/accounts/{account_id}/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    account_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get real-time connection status for account.

    Returns current connection state including last connected time, errors, and MT5 account info.
    """
    # Get account
    account = db.get(TradingAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    # Get connection state
    state = session_manager.get_connection_state(account_id)

    # Get account info if connected
    account_info_dict = None
    if state and state.is_connected:
        connector = session_manager.get_session(account_id)
        if connector:
            try:
                account_info = connector.get_account_info()
                if account_info:
                    account_info_dict = {
                        "balance": account_info.balance,
                        "equity": account_info.equity,
                        "profit": account_info.profit,
                        "margin": account_info.margin,
                        "margin_free": account_info.margin_free,
                        "margin_level": account_info.margin_level
                    }
            except Exception:
                pass

    if not state:
        # No connection state - never connected
        return ConnectionStatusResponse(
            account_id=account_id,
            account_number=account.account_number,
            is_connected=False,
            last_connected_at=account.last_connected.isoformat() if account.last_connected else None,
            last_disconnected_at=None,
            connection_error=None,
            retry_count=0,
            account_info=None
        )

    return ConnectionStatusResponse(
        account_id=state.account_id,
        account_number=state.account_number,
        is_connected=state.is_connected,
        last_connected_at=state.last_connected_at.isoformat() if state.last_connected_at else None,
        last_disconnected_at=state.last_disconnected_at.isoformat() if state.last_disconnected_at else None,
        connection_error=state.connection_error,
        retry_count=state.retry_count,
        account_info=account_info_dict
    )


@router.post("/accounts/connect-all", response_model=BulkConnectionResponse)
async def connect_all_accounts(
    db: Session = Depends(get_db_dependency)
):
    """
    Connect all active accounts.

    Attempts to connect to all active trading accounts simultaneously.
    Returns summary of successes and failures.
    """
    # Get all active accounts
    query = select(TradingAccount).where(TradingAccount.is_active == True)
    result = db.execute(query)
    accounts = result.scalars().all()

    if not accounts:
        return BulkConnectionResponse(
            total=0,
            successful=0,
            failed=0,
            results=[]
        )

    results = []
    successful = 0
    failed = 0

    for account in accounts:
        success, error = await session_manager.connect_account(account, db)

        if success:
            successful += 1
            # Broadcast WebSocket event
            await connection_manager.broadcast_account_connection_event(
                "connected",
                {
                    "account_id": account.id,
                    "account_number": account.account_number,
                    "account_name": account.account_name,
                    "is_connected": True
                }
            )
        else:
            failed += 1

        results.append({
            "account_id": account.id,
            "account_number": account.account_number,
            "account_name": account.account_name,
            "success": success,
            "error": error
        })

    return BulkConnectionResponse(
        total=len(accounts),
        successful=successful,
        failed=failed,
        results=results
    )


@router.post("/accounts/disconnect-all", response_model=BulkConnectionResponse)
async def disconnect_all_accounts(
    db: Session = Depends(get_db_dependency)
):
    """
    Disconnect all connected accounts.

    Terminates all active MT5 connections and cleanup sessions.
    Returns summary of successes and failures.
    """
    # Get all connected account IDs
    connected_ids = session_manager.list_active_sessions()

    if not connected_ids:
        return BulkConnectionResponse(
            total=0,
            successful=0,
            failed=0,
            results=[]
        )

    results = []
    successful = 0
    failed = 0

    for account_id in connected_ids:
        account = db.get(TradingAccount, account_id)
        if not account:
            continue

        success, error = await session_manager.disconnect_account(account_id, db)

        if success:
            successful += 1
            # Broadcast WebSocket event
            await connection_manager.broadcast_account_connection_event(
                "disconnected",
                {
                    "account_id": account_id,
                    "account_number": account.account_number,
                    "account_name": account.account_name,
                    "is_connected": False
                }
            )
        else:
            failed += 1

        results.append({
            "account_id": account_id,
            "account_number": account.account_number,
            "account_name": account.account_name,
            "success": success,
            "error": error
        })

    return BulkConnectionResponse(
        total=len(connected_ids),
        successful=successful,
        failed=failed,
        results=results
    )

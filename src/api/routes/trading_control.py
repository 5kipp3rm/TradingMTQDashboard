"""
Trading Control API Endpoints

Provides REST API for controlling trading operations.

Design Pattern: Controller Layer (thin API layer)
- Delegates to TradingControlService
- Handles HTTP concerns (routing, validation, responses)
- Minimal business logic

SOLID: Single Responsibility - only handles HTTP routing
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from src.services.trading_control import (
    TradingControlService,
    get_trading_control_service,
)


router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class StartTradingRequest(BaseModel):
    """Request model for starting trading"""
    currency_symbols: Optional[List[str]] = None
    check_autotrading: bool = True


class TradingControlResponse(BaseModel):
    """Response model for trading control operations"""
    success: bool
    message: str
    account_id: str
    status: str
    timestamp: str
    error: Optional[str] = None
    metadata: Optional[dict] = None


class AutoTradingStatusResponse(BaseModel):
    """Response model for AutoTrading status"""
    autotrading_enabled: bool
    account_id: str
    checked_at: str
    instructions: Optional[dict] = None
    error: Optional[str] = None


# =============================================================================
# Dependency Injection
# =============================================================================

def get_service() -> TradingControlService:
    """
    Get trading control service instance

    FastAPI dependency injection.
    """
    return get_trading_control_service()


# =============================================================================
# API Endpoints
# =============================================================================

@router.post(
    "/accounts/{account_id}/trading/start",
    response_model=TradingControlResponse,
    summary="Start trading for account",
    description="""
    Start automated trading for the specified account.

    This will:
    1. Verify AutoTrading is enabled in MT5 (if check_autotrading=true)
    2. Execute a trading cycle to begin trading
    3. Return the current trading status

    **Note**: Account must be connected (worker running) before calling this endpoint.
    """
)
async def start_trading(
    account_id: str,
    request: StartTradingRequest = StartTradingRequest(),
    service: TradingControlService = Depends(get_service)
) -> TradingControlResponse:
    """
    Start trading for account

    Args:
        account_id: Account identifier
        request: Start trading request
        service: Trading control service (injected)

    Returns:
        Trading control response

    Raises:
        HTTPException: If operation fails
    """
    try:
        result = service.start_trading(
            account_id=account_id,
            currency_symbols=request.currency_symbols,
            check_autotrading=request.check_autotrading
        )

        return TradingControlResponse(**result.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start trading: {str(e)}"
        )


@router.post(
    "/accounts/{account_id}/trading/stop",
    response_model=TradingControlResponse,
    summary="Stop trading for account",
    description="""
    Stop automated trading for the specified account.

    This will:
    1. Stop opening new positions
    2. Return the current trading status

    **Note**: This does NOT close existing positions. Use position management
    endpoints to close positions if needed.
    """
)
async def stop_trading(
    account_id: str,
    service: TradingControlService = Depends(get_service)
) -> TradingControlResponse:
    """
    Stop trading for account

    Args:
        account_id: Account identifier
        service: Trading control service (injected)

    Returns:
        Trading control response

    Raises:
        HTTPException: If operation fails
    """
    try:
        result = service.stop_trading(account_id=account_id)

        return TradingControlResponse(**result.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop trading: {str(e)}"
        )


@router.get(
    "/accounts/{account_id}/trading/status",
    response_model=TradingControlResponse,
    summary="Get trading status",
    description="""
    Get current trading status for the account.

    Returns information about whether trading is active, stopped, or in error state.
    """
)
async def get_trading_status(
    account_id: str,
    service: TradingControlService = Depends(get_service)
) -> TradingControlResponse:
    """
    Get trading status for account

    Args:
        account_id: Account identifier
        service: Trading control service (injected)

    Returns:
        Trading control response

    Raises:
        HTTPException: If operation fails
    """
    try:
        result = service.get_trading_status(account_id=account_id)

        return TradingControlResponse(**result.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trading status: {str(e)}"
        )


@router.get(
    "/accounts/{account_id}/autotrading/status",
    response_model=AutoTradingStatusResponse,
    summary="Check AutoTrading status",
    description="""
    Check if AutoTrading is enabled in the MT5 terminal for this account.

    If AutoTrading is disabled, the response will include step-by-step
    instructions for enabling it.

    **Common reasons for disabled AutoTrading**:
    - AutoTrading button not clicked in MT5 toolbar
    - Algo Trading disabled in Tools -> Options -> Expert Advisors
    - MT5 terminal not running
    """
)
async def check_autotrading_status(
    account_id: str,
    service: TradingControlService = Depends(get_service)
) -> AutoTradingStatusResponse:
    """
    Check AutoTrading status for account

    Args:
        account_id: Account identifier
        service: Trading control service (injected)

    Returns:
        AutoTrading status response

    Raises:
        HTTPException: If check fails
    """
    try:
        status = service.check_autotrading(account_id=account_id)

        return AutoTradingStatusResponse(**status.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check AutoTrading status: {str(e)}"
        )

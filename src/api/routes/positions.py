"""
Position Execution API Endpoints

Provides REST API for position execution and management.
Supports opening, closing, modifying, and previewing positions.

Features:
- Position opening with validation
- Position closing (single and bulk)
- Real-time SL/TP modification
- Position preview with risk calculation
- Get open positions
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.connection import get_session as get_db
from src.services.position_service import position_service
from src.api.websocket import connection_manager
from src.utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/positions", tags=["positions"])


# Request Models

class PositionOpenRequest(BaseModel):
    """Request model for opening a new position"""
    account_id: int = Field(..., description="Trading account ID")
    symbol: str = Field(..., description="Trading symbol (e.g., 'EURUSD')", min_length=1, max_length=20)
    order_type: str = Field(..., description="Order type: 'BUY' or 'SELL'", pattern="^(BUY|SELL)$")
    volume: float = Field(..., description="Position volume in lots", gt=0, le=100)
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    comment: Optional[str] = Field(None, description="Order comment", max_length=250)
    magic: int = Field(234000, description="Magic number for order identification")
    deviation: int = Field(20, description="Maximum price deviation in points", ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": 1,
                "symbol": "EURUSD",
                "order_type": "BUY",
                "volume": 0.1,
                "stop_loss": 1.0930,
                "take_profit": 1.0990,
                "comment": "Scalping trade",
                "magic": 234000,
                "deviation": 20
            }
        }


class PositionModifyRequest(BaseModel):
    """Request model for modifying position SL/TP"""
    stop_loss: Optional[float] = Field(None, description="New stop loss price")
    take_profit: Optional[float] = Field(None, description="New take profit price")

    class Config:
        json_schema_extra = {
            "example": {
                "stop_loss": 1.0920,
                "take_profit": 1.1000
            }
        }


class PositionPreviewRequest(BaseModel):
    """Request model for position preview"""
    account_id: int = Field(..., description="Trading account ID")
    symbol: str = Field(..., description="Trading symbol", min_length=1, max_length=20)
    order_type: str = Field(..., description="Order type: 'BUY' or 'SELL'", pattern="^(BUY|SELL)$")
    volume: float = Field(..., description="Position volume in lots", gt=0, le=100)
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": 1,
                "symbol": "EURUSD",
                "order_type": "BUY",
                "volume": 0.1,
                "stop_loss": 1.0930,
                "take_profit": 1.0990
            }
        }


class BulkCloseRequest(BaseModel):
    """Request model for bulk closing positions"""
    account_id: int = Field(..., description="Trading account ID")
    symbol: Optional[str] = Field(None, description="Filter by symbol (closes all if not provided)", max_length=20)

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": 1,
                "symbol": "EURUSD"
            }
        }


# Response Models

class PositionOpenResponse(BaseModel):
    """Response model for position opening"""
    success: bool = Field(..., description="Whether the operation succeeded")
    ticket: Optional[int] = Field(None, description="Position ticket number")
    message: Optional[str] = Field(None, description="Success or error message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticket": 123456789,
                "message": None
            }
        }


class PositionCloseResponse(BaseModel):
    """Response model for position closing"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: Optional[str] = Field(None, description="Success or error message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": None
            }
        }


class PositionModifyResponse(BaseModel):
    """Response model for position modification"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: Optional[str] = Field(None, description="Success or error message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": None
            }
        }


class PositionPreviewResponse(BaseModel):
    """Response model for position preview"""
    symbol: str = Field(..., description="Trading symbol")
    order_type: str = Field(..., description="Order type")
    volume: float = Field(..., description="Position volume")
    entry_price: float = Field(..., description="Expected entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    risk_pips: float = Field(..., description="Risk in pips")
    reward_pips: float = Field(..., description="Reward in pips")
    risk_reward_ratio: float = Field(..., description="Risk/reward ratio")
    risk_amount: float = Field(..., description="Risk amount in account currency")
    potential_profit: float = Field(..., description="Potential profit in account currency")
    margin_required: float = Field(..., description="Margin required for position")
    account_balance: float = Field(..., description="Current account balance")
    account_equity: float = Field(..., description="Current account equity")
    margin_free: float = Field(..., description="Free margin available")
    margin_sufficient: bool = Field(..., description="Whether margin is sufficient")
    spread: float = Field(..., description="Current spread")
    contract_size: float = Field(..., description="Contract size")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "EURUSD",
                "order_type": "BUY",
                "volume": 0.1,
                "entry_price": 1.0950,
                "stop_loss": 1.0930,
                "take_profit": 1.0990,
                "risk_pips": 20.0,
                "reward_pips": 40.0,
                "risk_reward_ratio": 2.0,
                "risk_amount": 20.0,
                "potential_profit": 40.0,
                "margin_required": 109.50,
                "account_balance": 10000.0,
                "account_equity": 10000.0,
                "margin_free": 9890.50,
                "margin_sufficient": True,
                "spread": 1.5,
                "contract_size": 100000.0
            }
        }


class BulkCloseResult(BaseModel):
    """Individual result for bulk close operation"""
    ticket: int = Field(..., description="Position ticket")
    symbol: str = Field(..., description="Position symbol")
    volume: float = Field(..., description="Position volume")
    profit: float = Field(..., description="Position profit")
    success: bool = Field(..., description="Whether close succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


class BulkCloseResponse(BaseModel):
    """Response model for bulk close operation"""
    successful_count: int = Field(..., description="Number of successfully closed positions")
    failed_count: int = Field(..., description="Number of failed closes")
    results: List[BulkCloseResult] = Field(..., description="Detailed results for each position")

    class Config:
        json_schema_extra = {
            "example": {
                "successful_count": 2,
                "failed_count": 0,
                "results": [
                    {
                        "ticket": 123456789,
                        "symbol": "EURUSD",
                        "volume": 0.1,
                        "profit": 25.50,
                        "success": True,
                        "error": None
                    },
                    {
                        "ticket": 123456790,
                        "symbol": "EURUSD",
                        "volume": 0.2,
                        "profit": 15.30,
                        "success": True,
                        "error": None
                    }
                ]
            }
        }


class PositionInfo(BaseModel):
    """Position information model"""
    ticket: int = Field(..., description="Position ticket")
    symbol: str = Field(..., description="Position symbol")
    type: str = Field(..., description="Position type (BUY/SELL)")
    volume: float = Field(..., description="Position volume")
    price_open: float = Field(..., description="Opening price")
    price_current: float = Field(..., description="Current price")
    sl: float = Field(..., description="Stop loss price")
    tp: float = Field(..., description="Take profit price")
    profit: float = Field(..., description="Current profit/loss")


# API Endpoints

@router.post("/open", response_model=PositionOpenResponse, status_code=status.HTTP_201_CREATED)
async def open_position(
    request: PositionOpenRequest,
    db: Session = Depends(get_db)
):
    """
    Open a new trading position.

    Opens a market order position with specified parameters after validation.
    Returns the position ticket number on success.

    ## Request Body
    - **account_id**: Trading account ID
    - **symbol**: Trading symbol (e.g., 'EURUSD')
    - **order_type**: 'BUY' or 'SELL'
    - **volume**: Position volume in lots
    - **stop_loss**: Stop loss price (optional)
    - **take_profit**: Take profit price (optional)
    - **comment**: Order comment (optional)
    - **magic**: Magic number (optional, default: 234000)
    - **deviation**: Max price deviation in points (optional, default: 20)

    ## Returns
    - **success**: Whether the operation succeeded
    - **ticket**: Position ticket number (if successful)
    - **message**: Error message (if failed)
    """
    logger.info(
        "API: Open position request",
        account_id=request.account_id,
        symbol=request.symbol,
        order_type=request.order_type,
        volume=request.volume
    )

    try:
        success, ticket, error_msg = await position_service.open_position(
            account_id=request.account_id,
            db=db,
            symbol=request.symbol,
            order_type=request.order_type,
            volume=request.volume,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            comment=request.comment,
            magic=request.magic,
            deviation=request.deviation
        )

        if success:
            # Broadcast position opened event via WebSocket
            await connection_manager.broadcast_position_event(
                "position_opened",
                {
                    "account_id": request.account_id,
                    "ticket": ticket,
                    "symbol": request.symbol,
                    "order_type": request.order_type,
                    "volume": request.volume,
                    "stop_loss": request.stop_loss,
                    "take_profit": request.take_profit
                }
            )

            return PositionOpenResponse(
                success=True,
                ticket=ticket,
                message=None
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Failed to open position"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in open_position endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{ticket}/close", response_model=PositionCloseResponse)
async def close_position(
    ticket: int,
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Close an open trading position.

    Closes the position identified by ticket number.

    ## Path Parameters
    - **ticket**: Position ticket number

    ## Query Parameters
    - **account_id**: Trading account ID

    ## Returns
    - **success**: Whether the operation succeeded
    - **message**: Error message (if failed)
    """
    logger.info(
        "API: Close position request",
        ticket=ticket,
        account_id=account_id
    )

    try:
        success, error_msg = await position_service.close_position(
            account_id=account_id,
            db=db,
            ticket=ticket
        )

        if success:
            # Broadcast position closed event via WebSocket
            await connection_manager.broadcast_position_event(
                "position_closed",
                {
                    "account_id": account_id,
                    "ticket": ticket
                }
            )

            return PositionCloseResponse(
                success=True,
                message=None
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Failed to close position"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in close_position endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{ticket}/modify", response_model=PositionModifyResponse)
async def modify_position(
    ticket: int,
    account_id: int,
    request: PositionModifyRequest,
    db: Session = Depends(get_db)
):
    """
    Modify SL/TP on an open position.

    Modifies stop loss and/or take profit for the position identified by ticket number.

    ## Path Parameters
    - **ticket**: Position ticket number

    ## Query Parameters
    - **account_id**: Trading account ID

    ## Request Body
    - **stop_loss**: New stop loss price (optional)
    - **take_profit**: New take profit price (optional)

    At least one of stop_loss or take_profit must be provided.

    ## Returns
    - **success**: Whether the operation succeeded
    - **message**: Error message (if failed)
    """
    logger.info(
        "API: Modify position request",
        ticket=ticket,
        account_id=account_id,
        new_sl=request.stop_loss,
        new_tp=request.take_profit
    )

    try:
        success, error_msg = await position_service.modify_position(
            account_id=account_id,
            db=db,
            ticket=ticket,
            new_sl=request.stop_loss,
            new_tp=request.take_profit
        )

        if success:
            # Broadcast position modified event via WebSocket
            await connection_manager.broadcast_position_event(
                "position_modified",
                {
                    "account_id": account_id,
                    "ticket": ticket,
                    "stop_loss": request.stop_loss,
                    "take_profit": request.take_profit
                }
            )

            return PositionModifyResponse(
                success=True,
                message=None
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Failed to modify position"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in modify_position endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/close-all", response_model=BulkCloseResponse)
async def bulk_close_positions(
    request: BulkCloseRequest,
    db: Session = Depends(get_db)
):
    """
    Close all positions for an account (optionally filtered by symbol).

    Closes all open positions for the specified account. If symbol is provided,
    only positions for that symbol are closed.

    ## Request Body
    - **account_id**: Trading account ID
    - **symbol**: Filter by symbol (optional, closes all if not provided)

    ## Returns
    - **successful_count**: Number of successfully closed positions
    - **failed_count**: Number of failed closes
    - **results**: Detailed results for each position
    """
    logger.info(
        "API: Bulk close positions request",
        account_id=request.account_id,
        symbol=request.symbol
    )

    try:
        successful_count, failed_count, results = await position_service.bulk_close_positions(
            account_id=request.account_id,
            db=db,
            symbol=request.symbol
        )

        return BulkCloseResponse(
            successful_count=successful_count,
            failed_count=failed_count,
            results=[
                BulkCloseResult(
                    ticket=r["ticket"],
                    symbol=r["symbol"],
                    volume=r["volume"],
                    profit=r["profit"],
                    success=r["success"],
                    error=r["error"]
                )
                for r in results
            ]
        )

    except Exception as e:
        logger.error(f"Unexpected error in bulk_close_positions endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/preview", response_model=PositionPreviewResponse)
async def preview_position(
    request: PositionPreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Preview position before execution with risk calculation.

    Calculates risk metrics, margin requirements, and potential profit/loss
    without actually opening the position.

    ## Request Body
    - **account_id**: Trading account ID
    - **symbol**: Trading symbol
    - **order_type**: 'BUY' or 'SELL'
    - **volume**: Position volume in lots
    - **stop_loss**: Stop loss price (optional)
    - **take_profit**: Take profit price (optional)

    ## Returns
    Detailed position preview including:
    - Entry price, SL/TP prices
    - Risk and reward in pips
    - Risk/reward ratio
    - Risk amount and potential profit
    - Margin requirements
    - Account balance and margin info
    - Whether margin is sufficient
    """
    logger.info(
        "API: Preview position request",
        account_id=request.account_id,
        symbol=request.symbol,
        order_type=request.order_type,
        volume=request.volume
    )

    try:
        preview = await position_service.preview_position(
            account_id=request.account_id,
            db=db,
            symbol=request.symbol,
            order_type=request.order_type,
            volume=request.volume,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit
        )

        if "error" in preview:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=preview["error"]
            )

        return PositionPreviewResponse(**preview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in preview_position endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/open", response_model=List[PositionInfo])
async def get_open_positions(
    account_id: int,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all open positions for an account.

    Returns list of all open positions for the specified account.
    Optionally filter by symbol.

    ## Query Parameters
    - **account_id**: Trading account ID
    - **symbol**: Filter by symbol (optional)

    ## Returns
    List of open positions with details:
    - Ticket number
    - Symbol
    - Position type (BUY/SELL)
    - Volume
    - Opening and current prices
    - SL/TP prices
    - Current profit/loss
    """
    logger.info(
        "API: Get open positions request",
        account_id=account_id,
        symbol=symbol
    )

    try:
        positions = await position_service.get_open_positions(
            account_id=account_id,
            db=db,
            symbol=symbol
        )

        return [PositionInfo(**pos) for pos in positions]

    except Exception as e:
        logger.error(f"Unexpected error in get_open_positions endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

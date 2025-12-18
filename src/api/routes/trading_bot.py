"""
Trading Bot Control Endpoints

Provides REST API endpoints for controlling the automated trading bot service.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from src.services.trading_bot_service import trading_bot_service


router = APIRouter()


class TradingBotStatusResponse(BaseModel):
    """Response model for trading bot status"""
    is_running: bool
    check_interval: int
    connected_accounts: int
    account_ids: List[int]
    active_traders: int


class TradingBotActionResponse(BaseModel):
    """Response model for trading bot actions"""
    success: bool
    message: str
    status: TradingBotStatusResponse


@router.get("/trading-bot/status", response_model=TradingBotStatusResponse)
async def get_trading_bot_status():
    """
    Get current status of the trading bot service.

    Returns:
        Current trading bot status including running state and connected accounts
    """
    status = trading_bot_service.get_status()

    return TradingBotStatusResponse(
        is_running=status["is_running"],
        check_interval=status["check_interval"],
        connected_accounts=status["connected_accounts"],
        account_ids=status["account_ids"],
        active_traders=status["active_traders"]
    )


@router.post("/trading-bot/start", response_model=TradingBotActionResponse)
async def start_trading_bot():
    """
    Start the trading bot service.

    The trading bot will begin monitoring connected accounts and executing trades
    based on currency configurations.

    Returns:
        Action result with updated status
    """
    if trading_bot_service.is_running:
        return TradingBotActionResponse(
            success=False,
            message="Trading bot is already running",
            status=TradingBotStatusResponse(**trading_bot_service.get_status())
        )

    try:
        await trading_bot_service.start()

        return TradingBotActionResponse(
            success=True,
            message="Trading bot started successfully",
            status=TradingBotStatusResponse(**trading_bot_service.get_status())
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start trading bot: {str(e)}"
        )


@router.post("/trading-bot/stop", response_model=TradingBotActionResponse)
async def stop_trading_bot():
    """
    Stop the trading bot service.

    The trading bot will stop monitoring accounts and executing trades.
    This does not close existing positions.

    Returns:
        Action result with updated status
    """
    if not trading_bot_service.is_running:
        return TradingBotActionResponse(
            success=False,
            message="Trading bot is not running",
            status=TradingBotStatusResponse(**trading_bot_service.get_status())
        )

    try:
        await trading_bot_service.stop()

        return TradingBotActionResponse(
            success=True,
            message="Trading bot stopped successfully",
            status=TradingBotStatusResponse(**trading_bot_service.get_status())
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop trading bot: {str(e)}"
        )


@router.post("/trading-bot/restart", response_model=TradingBotActionResponse)
async def restart_trading_bot():
    """
    Restart the trading bot service.

    Stops and then starts the trading bot service.

    Returns:
        Action result with updated status
    """
    try:
        if trading_bot_service.is_running:
            await trading_bot_service.stop()

        await trading_bot_service.start()

        return TradingBotActionResponse(
            success=True,
            message="Trading bot restarted successfully",
            status=TradingBotStatusResponse(**trading_bot_service.get_status())
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart trading bot: {str(e)}"
        )

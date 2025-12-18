"""
Aggregated Analytics API Endpoints

Provides REST endpoints for cross-account aggregated metrics and performance analysis.
Supports filtering by account IDs and date ranges for flexible reporting.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database import get_db_dependency
from src.services.analytics_service import analytics_service


router = APIRouter()


# Pydantic Models for Response

class AggregatePerformanceResponse(BaseModel):
    """Response model for aggregate performance metrics"""
    period_days: int
    account_count: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    gross_profit: float
    gross_loss: float
    net_profit: float
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    average_daily_profit: float


class AccountComparisonItem(BaseModel):
    """Individual account in comparison response"""
    account_id: int
    account_number: int
    account_name: str
    broker: str
    is_demo: bool
    total_trades: int
    winning_trades: int
    losing_trades: int
    net_profit: float
    win_rate: float
    profit_factor: float
    gross_profit: float
    gross_loss: float


class AccountComparisonResponse(BaseModel):
    """Response model for account comparison"""
    period_days: int
    total_accounts: int
    accounts: List[AccountComparisonItem]


class AggregateSummaryResponse(BaseModel):
    """Response model for aggregate summary"""
    total_accounts: int
    active_accounts: int
    demo_accounts: int
    live_accounts: int
    total_initial_balance: float
    last_30_days: dict
    today: dict


class AggregateTradesResponse(BaseModel):
    """Response model for aggregate trades list"""
    trades: List[dict]
    total: int
    limit: int
    offset: int
    has_more: bool


# ============================================================================
# AGGREGATED ANALYTICS ENDPOINTS
# ============================================================================


@router.get("/analytics/aggregate", response_model=AggregatePerformanceResponse)
async def get_aggregate_performance(
    account_ids: Optional[str] = Query(None, description="Comma-separated list of account IDs (e.g., '1,2,3'). If not provided, aggregates all accounts."),
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    db: Session = Depends(get_db_dependency)
):
    """
    Get aggregated performance metrics across multiple accounts.

    Returns comprehensive performance statistics including:
    - Trade counts (total, winning, losing)
    - Profit metrics (gross profit, gross loss, net profit)
    - Performance ratios (win rate, profit factor)
    - Average metrics (average win, average loss, daily profit)
    - Extremes (largest win, largest loss)

    Query Parameters:
    - account_ids: Optional comma-separated account IDs (e.g., "1,2,3")
    - days: Number of days to look back (default: 30, max: 365)

    Example:
    - /api/analytics/aggregate?days=30 (all accounts, last 30 days)
    - /api/analytics/aggregate?account_ids=1,2,3&days=7 (specific accounts, last 7 days)
    """
    # Parse account IDs if provided
    account_ids_list = None
    if account_ids:
        try:
            account_ids_list = [int(id_str.strip()) for id_str in account_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_ids format. Expected comma-separated integers (e.g., '1,2,3')"
            )

    # Get aggregate performance
    result = analytics_service.get_aggregate_performance(
        db=db,
        account_ids=account_ids_list,
        days=days
    )

    return AggregatePerformanceResponse(**result)


@router.get("/analytics/comparison", response_model=AccountComparisonResponse)
async def get_account_comparison(
    account_ids: Optional[str] = Query(None, description="Comma-separated list of account IDs (e.g., '1,2,3'). If not provided, compares all accounts."),
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    db: Session = Depends(get_db_dependency)
):
    """
    Get side-by-side comparison of performance across accounts.

    Returns per-account performance breakdown including:
    - Account information (ID, number, name, broker, demo status)
    - Trade statistics (total, winning, losing)
    - Profit metrics (net, gross profit, gross loss)
    - Performance ratios (win rate, profit factor)

    Accounts are sorted by net profit in descending order.

    Query Parameters:
    - account_ids: Optional comma-separated account IDs (e.g., "1,2,3")
    - days: Number of days to look back (default: 30, max: 365)

    Example:
    - /api/analytics/comparison?days=30 (all accounts, last 30 days)
    - /api/analytics/comparison?account_ids=1,2,3&days=7 (specific accounts, last 7 days)
    """
    # Parse account IDs if provided
    account_ids_list = None
    if account_ids:
        try:
            account_ids_list = [int(id_str.strip()) for id_str in account_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_ids format. Expected comma-separated integers (e.g., '1,2,3')"
            )

    # Get account comparison
    result = analytics_service.get_account_comparison(
        db=db,
        account_ids=account_ids_list,
        days=days
    )

    return AccountComparisonResponse(**result)


@router.get("/analytics/summary", response_model=AggregateSummaryResponse)
async def get_aggregate_summary(
    db: Session = Depends(get_db_dependency)
):
    """
    Get high-level summary across all accounts.

    Returns system-wide overview including:
    - Account counts (total, active, demo, live)
    - Total initial balance across all accounts
    - Last 30 days performance (trades, profit)
    - Today's performance (trades, profit)

    This endpoint provides a quick snapshot of overall trading system status.

    Example:
    - /api/analytics/summary
    """
    result = analytics_service.get_aggregate_summary(db=db)

    return AggregateSummaryResponse(**result)


@router.get("/analytics/trades", response_model=AggregateTradesResponse)
async def get_aggregate_trades(
    account_ids: Optional[str] = Query(None, description="Comma-separated list of account IDs (e.g., '1,2,3'). If not provided, includes all accounts."),
    limit: int = Query(100, description="Maximum number of trades to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of trades to skip", ge=0),
    db: Session = Depends(get_db_dependency)
):
    """
    Get trades from multiple accounts with pagination.

    Returns list of closed trades across specified accounts, ordered by entry time (most recent first).
    Each trade includes account information (name, number) for context.

    Query Parameters:
    - account_ids: Optional comma-separated account IDs (e.g., "1,2,3")
    - limit: Maximum trades to return (default: 100, max: 1000)
    - offset: Number of trades to skip for pagination (default: 0)

    Returns:
    - trades: List of trade objects with account info
    - total: Total number of trades matching criteria
    - limit: Applied limit
    - offset: Applied offset
    - has_more: Boolean indicating if more trades are available

    Example:
    - /api/analytics/trades?limit=50&offset=0 (first 50 trades, all accounts)
    - /api/analytics/trades?account_ids=1,2&limit=100&offset=100 (next 100 trades, accounts 1 and 2)
    """
    # Parse account IDs if provided
    account_ids_list = None
    if account_ids:
        try:
            account_ids_list = [int(id_str.strip()) for id_str in account_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_ids format. Expected comma-separated integers (e.g., '1,2,3')"
            )

    # Get aggregate trades
    result = analytics_service.get_aggregate_trades(
        db=db,
        account_ids=account_ids_list,
        limit=limit,
        offset=offset
    )

    return AggregateTradesResponse(**result)

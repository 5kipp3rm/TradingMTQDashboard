"""
Analytics Endpoints

API endpoints for retrieving performance analytics and daily aggregation data.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.database.connection import get_session
from src.database.repository import DailyPerformanceRepository
from src.database.models import DailyPerformance
from src.analytics import DailyAggregator

router = APIRouter()


@router.get("/summary")
async def get_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get summary analytics for the specified number of days.

    Args:
        days: Number of days to include (default: 30, max: 365)
        account_id: Optional account ID to filter by

    Returns:
        Summary analytics including total trades, profit, win rate, etc.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    with get_session() as session:
        repo = DailyPerformanceRepository()

        # Use existing get_performance_summary method
        summary = repo.get_performance_summary(session, start_date, end_date, account_id=account_id)

        if not summary:
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
                "account_id": account_id,
                "total_days": 0,
                "total_trades": 0,
                "net_profit": 0.0,
                "message": "No data available for this period"
            }

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days,
            "account_id": account_id,
            **summary
        }


@router.get("/daily")
async def get_daily_performance(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(default=30, ge=1, le=365, description="Max number of records"),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get daily performance records.

    Args:
        start_date: Start date (optional, defaults to 30 days ago)
        end_date: End date (optional, defaults to today)
        limit: Maximum number of records to return
        account_id: Optional account ID to filter by

    Returns:
        List of daily performance records
    """
    if end_date is None:
        end_date = date.today()

    if start_date is None:
        start_date = end_date - timedelta(days=limit)

    with get_session() as session:
        # Query directly using SQLAlchemy
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        query = session.query(DailyPerformance).filter(
            DailyPerformance.date >= start_dt,
            DailyPerformance.date <= end_dt
        )

        # Add account filter if provided
        if account_id is not None:
            query = query.filter(DailyPerformance.account_id == account_id)

        records = query.order_by(DailyPerformance.date.desc()).limit(limit).all()

        # Convert to dict
        results = []
        for record in records:
            results.append(record.to_dict())

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "account_id": account_id,
            "count": len(results),
            "records": results
        }


@router.get("/daily/{target_date}")
async def get_daily_performance_by_date(target_date: date):
    """
    Get performance metrics for a specific date.

    Args:
        target_date: Date in YYYY-MM-DD format

    Returns:
        Daily performance metrics for the specified date
    """
    with get_session() as session:
        repo = DailyPerformanceRepository()
        record = repo.get_by_date(session, target_date)

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"No performance data found for {target_date.isoformat()}"
            )

        return record.to_dict()


@router.post("/aggregate")
async def trigger_aggregation(target_date: Optional[date] = None):
    """
    Manually trigger aggregation for a specific date.

    Args:
        target_date: Date to aggregate (defaults to yesterday)

    Returns:
        Aggregation result
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    aggregator = DailyAggregator()
    result = aggregator.aggregate_day(target_date)

    if result:
        return {
            "success": True,
            "message": f"Successfully aggregated data for {target_date.isoformat()}",
            **result.to_dict()
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No closed trades found for {target_date.isoformat()}"
        )


@router.get("/metrics")
async def get_performance_metrics(
    days: int = Query(default=30, ge=1, le=365),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get key performance metrics for charting.

    Args:
        days: Number of days to include
        account_id: Optional account ID to filter by

    Returns:
        Time series data for key metrics
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    with get_session() as session:
        # Query directly using SQLAlchemy
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        query = session.query(DailyPerformance).filter(
            DailyPerformance.date >= start_dt,
            DailyPerformance.date <= end_dt
        )

        # Add account filter if provided
        if account_id is not None:
            query = query.filter(DailyPerformance.account_id == account_id)

        records = query.order_by(DailyPerformance.date.asc()).all()

        # Prepare time series data
        dates = []
        profits = []
        win_rates = []
        trade_counts = []

        cumulative_profit = 0.0

        for record in records:
            cumulative_profit += float(record.net_profit)

            dates.append(record.date.date().isoformat() if isinstance(record.date, datetime) else record.date.isoformat())
            profits.append(round(cumulative_profit, 2))
            win_rates.append(float(record.win_rate) if record.win_rate else 0)
            trade_counts.append(record.total_trades)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "period_days": days,
            "account_id": account_id,
            "dates": dates,
            "cumulative_profit": profits,
            "win_rates": win_rates,
            "trade_counts": trade_counts
        }

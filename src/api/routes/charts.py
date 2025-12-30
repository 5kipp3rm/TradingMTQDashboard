"""
Advanced Charts API Endpoints

Provides data for advanced visualizations:
- Equity curve
- Trade distribution heatmaps
- Win/loss analysis
- Symbol performance comparison
- Time-based patterns
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from src.database.connection import get_async_session
from src.database.models import Trade, TradeStatus, SignalType, DailyPerformance, AccountSnapshot
from sqlalchemy import func, and_, extract
from src.utils.unified_logger import UnifiedLogger

logger = UnifiedLogger.get_logger(__name__)
router = APIRouter()


@router.get("/equity-curve")
async def get_equity_curve(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    granularity: str = Query("daily", description="Granularity: daily, trade, hourly"),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get equity curve data showing account balance over time.

    Args:
        start_date: Start date (defaults to 90 days ago)
        end_date: End date (defaults to today)
        granularity: Data granularity (daily, trade, hourly)
        account_id: Optional account ID to filter by

    Returns:
        Equity curve data points with timestamps and balance
    """
    if end_date is None:
        end_date = date.today()

    if start_date is None:
        start_date = end_date - timedelta(days=90)

    try:
        async with get_async_session() as session:
            if granularity == "daily":
                # Use daily performance data
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.max.time())

                query = session.query(DailyPerformance).filter(
                    DailyPerformance.date >= start_dt,
                    DailyPerformance.date <= end_dt
                )

                if account_id is not None:
                    query = query.filter(DailyPerformance.account_id == account_id)

                records = query.order_by(DailyPerformance.date).all()

                # Calculate cumulative equity
                equity_data = []
                cumulative_profit = 0.0

                for record in records:
                    cumulative_profit += float(record.net_profit or 0)
                    equity_data.append({
                        "date": record.date.date().isoformat(),
                        "balance": float(record.end_balance or 0),
                        "equity": float(record.end_equity or 0),
                        "cumulative_profit": cumulative_profit,
                        "trades": record.total_trades
                    })

                return {
                    "granularity": "daily",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "data": equity_data
                }

            elif granularity == "trade":
                # Build equity from individual trades
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.max.time())

                query = session.query(Trade).filter(
                    Trade.status == TradeStatus.CLOSED,
                    Trade.exit_time >= start_dt,
                    Trade.exit_time <= end_dt
                )

                if account_id is not None:
                    query = query.filter(Trade.account_id == account_id)

                trades = query.order_by(Trade.exit_time).all()

                equity_data = []
                cumulative_profit = 0.0
                initial_balance = 10000.0  # Default starting balance

                for trade in trades:
                    cumulative_profit += float(trade.profit or 0)
                    equity_data.append({
                        "date": trade.exit_time.isoformat(),
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "profit": float(trade.profit or 0),
                        "cumulative_profit": cumulative_profit,
                        "balance": initial_balance + cumulative_profit
                    })

                return {
                    "granularity": "trade",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_trades": len(equity_data),
                    "data": equity_data
                }

            else:
                raise HTTPException(status_code=400, detail=f"Invalid granularity: {granularity}")

    except Exception as e:
        logger.error("Failed to generate equity curve", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade-distribution")
async def get_trade_distribution(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get trade distribution by hour of day and day of week.

    Returns heatmap data showing when trades are most profitable.
    """
    if end_date is None:
        end_date = date.today()

    if start_date is None:
        start_date = end_date - timedelta(days=90)

    try:
        async with get_async_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            # Query trades with time extraction
            query = session.query(
                extract('dow', Trade.entry_time).label('day_of_week'),
                extract('hour', Trade.entry_time).label('hour'),
                func.count(Trade.id).label('trade_count'),
                func.sum(Trade.profit).label('total_profit'),
                func.avg(Trade.profit).label('avg_profit')
            ).filter(
                Trade.status == TradeStatus.CLOSED,
                Trade.entry_time >= start_dt,
                Trade.entry_time <= end_dt
            )

            if account_id is not None:
                query = query.filter(Trade.account_id == account_id)

            trades = query.group_by(
                'day_of_week', 'hour'
            ).all()

            # Build heatmap matrix (7 days x 24 hours)
            heatmap_data = []
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

            for trade in trades:
                heatmap_data.append({
                    "day": day_names[int(trade.day_of_week)],
                    "day_num": int(trade.day_of_week),
                    "hour": int(trade.hour),
                    "trade_count": int(trade.trade_count),
                    "total_profit": float(trade.total_profit or 0),
                    "avg_profit": float(trade.avg_profit or 0)
                })

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "data": heatmap_data
            }

    except Exception as e:
        logger.error("Failed to generate trade distribution", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbol-performance")
async def get_symbol_performance(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(10, ge=1, le=50, description="Max symbols to return"),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get performance comparison across different symbols.

    Returns metrics for each symbol including win rate, avg profit, trade count.
    """
    if end_date is None:
        end_date = date.today()

    if start_date is None:
        start_date = end_date - timedelta(days=90)

    try:
        async with get_async_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            # Aggregate by symbol
            query = session.query(
                Trade.symbol,
                func.count(Trade.id).label('total_trades'),
                func.sum(func.case((Trade.profit > 0, 1), else_=0)).label('winning_trades'),
                func.sum(func.case((Trade.profit < 0, 1), else_=0)).label('losing_trades'),
                func.sum(Trade.profit).label('net_profit'),
                func.avg(Trade.profit).label('avg_profit'),
                func.max(Trade.profit).label('max_profit'),
                func.min(Trade.profit).label('min_profit')
            ).filter(
                Trade.status == TradeStatus.CLOSED,
                Trade.exit_time >= start_dt,
                Trade.exit_time <= end_dt
            )

            if account_id is not None:
                query = query.filter(Trade.account_id == account_id)

            results = query.group_by(
                Trade.symbol
            ).order_by(
                func.sum(Trade.profit).desc()
            ).limit(limit).all()

            symbol_data = []
            for row in results:
                total = int(row.total_trades)
                winning = int(row.winning_trades or 0)
                win_rate = (winning / total * 100) if total > 0 else 0

                symbol_data.append({
                    "symbol": row.symbol,
                    "total_trades": total,
                    "winning_trades": winning,
                    "losing_trades": int(row.losing_trades or 0),
                    "win_rate": round(win_rate, 2),
                    "net_profit": float(row.net_profit or 0),
                    "avg_profit": float(row.avg_profit or 0),
                    "max_profit": float(row.max_profit or 0),
                    "min_profit": float(row.min_profit or 0)
                })

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "symbols": symbol_data
            }

    except Exception as e:
        logger.error("Failed to generate symbol performance", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/win-loss-analysis")
async def get_win_loss_analysis(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get detailed win/loss analysis including:
    - Profit distribution histogram
    - Win/loss streaks
    - Trade duration analysis
    """
    if end_date is None:
        end_date = date.today()

    if start_date is None:
        start_date = end_date - timedelta(days=90)

    try:
        async with get_async_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            # Get all closed trades
            query = session.query(Trade).filter(
                Trade.status == TradeStatus.CLOSED,
                Trade.exit_time >= start_dt,
                Trade.exit_time <= end_dt
            )

            if account_id is not None:
                query = query.filter(Trade.account_id == account_id)

            trades = query.order_by(Trade.exit_time).all()

            # Profit distribution (histogram)
            profit_ranges = [-1000, -500, -250, -100, -50, -25, 0, 25, 50, 100, 250, 500, 1000]
            profit_histogram = {f"{profit_ranges[i]} to {profit_ranges[i+1]}": 0
                               for i in range(len(profit_ranges)-1)}
            profit_histogram["< -1000"] = 0
            profit_histogram["> 1000"] = 0

            # Calculate streaks
            current_streak = 0
            max_win_streak = 0
            max_loss_streak = 0
            streaks = []

            # Duration analysis
            duration_buckets = defaultdict(int)

            for trade in trades:
                profit = float(trade.profit or 0)

                # Histogram
                if profit < -1000:
                    profit_histogram["< -1000"] += 1
                elif profit > 1000:
                    profit_histogram["> 1000"] += 1
                else:
                    for i in range(len(profit_ranges)-1):
                        if profit_ranges[i] <= profit < profit_ranges[i+1]:
                            profit_histogram[f"{profit_ranges[i]} to {profit_ranges[i+1]}"] += 1
                            break

                # Streaks
                if profit > 0:
                    if current_streak > 0:
                        current_streak += 1
                    else:
                        if current_streak < 0:
                            max_loss_streak = min(max_loss_streak, current_streak)
                        current_streak = 1
                elif profit < 0:
                    if current_streak < 0:
                        current_streak -= 1
                    else:
                        if current_streak > 0:
                            max_win_streak = max(max_win_streak, current_streak)
                        current_streak = -1

                # Duration (in hours)
                if trade.duration_seconds:
                    hours = trade.duration_seconds / 3600
                    if hours < 1:
                        duration_buckets["< 1 hour"] += 1
                    elif hours < 4:
                        duration_buckets["1-4 hours"] += 1
                    elif hours < 24:
                        duration_buckets["4-24 hours"] += 1
                    elif hours < 168:
                        duration_buckets["1-7 days"] += 1
                    else:
                        duration_buckets["> 7 days"] += 1

            # Final streak check
            if current_streak > 0:
                max_win_streak = max(max_win_streak, current_streak)
            elif current_streak < 0:
                max_loss_streak = min(max_loss_streak, current_streak)

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "profit_distribution": profit_histogram,
                "streaks": {
                    "max_win_streak": max_win_streak,
                    "max_loss_streak": abs(max_loss_streak)
                },
                "duration_analysis": dict(duration_buckets),
                "total_trades_analyzed": len(trades)
            }

    except Exception as e:
        logger.error("Failed to generate win/loss analysis", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly-comparison")
async def get_monthly_comparison(
    months: int = Query(12, ge=1, le=24, description="Number of months to compare"),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get month-over-month performance comparison.

    Returns metrics for each month for trend analysis.
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 31)

        async with get_async_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            # Aggregate by month
            query = session.query(
                extract('year', DailyPerformance.date).label('year'),
                extract('month', DailyPerformance.date).label('month'),
                func.sum(DailyPerformance.total_trades).label('total_trades'),
                func.sum(DailyPerformance.winning_trades).label('winning_trades'),
                func.sum(DailyPerformance.losing_trades).label('losing_trades'),
                func.sum(DailyPerformance.net_profit).label('net_profit'),
                func.avg(DailyPerformance.win_rate).label('avg_win_rate')
            ).filter(
                DailyPerformance.date >= start_dt,
                DailyPerformance.date <= end_dt
            )

            if account_id is not None:
                query = query.filter(DailyPerformance.account_id == account_id)

            results = query.group_by(
                'year', 'month'
            ).order_by(
                'year', 'month'
            ).all()

            monthly_data = []
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            for row in results:
                year = int(row.year)
                month = int(row.month)
                monthly_data.append({
                    "year": year,
                    "month": month,
                    "month_name": f"{month_names[month-1]} {year}",
                    "total_trades": int(row.total_trades or 0),
                    "winning_trades": int(row.winning_trades or 0),
                    "losing_trades": int(row.losing_trades or 0),
                    "net_profit": float(row.net_profit or 0),
                    "avg_win_rate": float(row.avg_win_rate or 0)
                })

            return {
                "months": months,
                "data": monthly_data
            }

    except Exception as e:
        logger.error("Failed to generate monthly comparison", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-reward-scatter")
async def get_risk_reward_scatter(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(500, ge=1, le=1000, description="Max trades to include"),
    account_id: Optional[int] = Query(None, description="Filter by specific account ID")
):
    """
    Get risk/reward scatter plot data.

    Returns trade data for plotting risk vs reward.
    """
    if end_date is None:
        end_date = date.today()

    if start_date is None:
        start_date = end_date - timedelta(days=90)

    try:
        async with get_async_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            query = session.query(Trade).filter(
                Trade.status == TradeStatus.CLOSED,
                Trade.exit_time >= start_dt,
                Trade.exit_time <= end_dt,
                Trade.stop_loss.isnot(None),
                Trade.take_profit.isnot(None)
            )

            if account_id is not None:
                query = query.filter(Trade.account_id == account_id)

            trades = query.order_by(Trade.exit_time.desc()).limit(limit).all()

            scatter_data = []
            for trade in trades:
                # Calculate risk and reward
                entry = float(trade.entry_price)
                sl = float(trade.stop_loss)
                tp = float(trade.take_profit)

                if trade.trade_type.value == 'buy':
                    risk = abs(entry - sl)
                    reward = abs(tp - entry)
                else:  # sell
                    risk = abs(sl - entry)
                    reward = abs(entry - tp)

                risk_reward_ratio = reward / risk if risk > 0 else 0

                scatter_data.append({
                    "trade_id": trade.id,
                    "symbol": trade.symbol,
                    "profit": float(trade.profit or 0),
                    "pips": float(trade.pips or 0),
                    "risk": risk,
                    "reward": reward,
                    "risk_reward_ratio": round(risk_reward_ratio, 2),
                    "outcome": "win" if (trade.profit or 0) > 0 else "loss"
                })

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_trades": len(scatter_data),
                "data": scatter_data
            }

    except Exception as e:
        logger.error("Failed to generate risk/reward scatter", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

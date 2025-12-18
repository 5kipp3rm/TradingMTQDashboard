"""
Trades Endpoints

API endpoints for retrieving individual trade data and history.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date, datetime, timedelta

from src.database.connection import get_async_session
from src.database.repository import TradeRepository
from src.database.models import TradeStatus

router = APIRouter()


@router.get("/")
async def get_trades(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., EURUSD)"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, CLOSED)"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max number of trades")
):
    """
    Get trades with optional filtering.

    Args:
        symbol: Filter by trading symbol
        status: Filter by trade status (OPEN or CLOSED)
        start_date: Start date for filtering
        end_date: End date for filtering
        limit: Maximum number of trades to return

    Returns:
        List of trades matching the filters
    """
    async with get_async_session() as session:
        repo = TradeRepository()

        # Parse status if provided
        trade_status = None
        if status:
            try:
                trade_status = TradeStatus[status.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}. Must be OPEN or CLOSED"
                )

        # Get trades based on filters
        if start_date and end_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            trades = repo.get_trades_by_date(
                session=session,
                start_date=start_datetime,
                end_date=end_datetime,
                status=trade_status
            )
        else:
            # Use get_trades_by_date_range for recent trades
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=30)  # Last 30 days

            trades = repo.get_trades_by_date_range(
                session=session,
                start_date=start_dt,
                end_date=end_dt,
                symbol=symbol
            )

        # Convert to dict
        results = []
        for trade in trades[:limit]:
            results.append({
                "ticket": trade.ticket,
                "symbol": trade.symbol,
                "trade_type": trade.trade_type,
                "volume": float(trade.volume),
                "entry_price": float(trade.entry_price),
                "exit_price": float(trade.exit_price) if trade.exit_price else None,
                "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
                "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
                "profit": float(trade.profit) if trade.profit else 0,
                "pips": float(trade.pips) if trade.pips else 0,
                "status": trade.status.value,
                "stop_loss": float(trade.stop_loss) if trade.stop_loss else None,
                "take_profit": float(trade.take_profit) if trade.take_profit else None
            })

        return {
            "count": len(results),
            "trades": results
        }


@router.get("/{ticket}")
async def get_trade_by_ticket(ticket: int):
    """
    Get a specific trade by ticket number.

    Args:
        ticket: MT5 ticket number

    Returns:
        Trade details
    """
    async with get_async_session() as session:
        repo = TradeRepository()
        trade = repo.get_by_ticket(session, ticket)

        if not trade:
            raise HTTPException(
                status_code=404,
                detail=f"Trade with ticket {ticket} not found"
            )

        return {
            "ticket": trade.ticket,
            "symbol": trade.symbol,
            "trade_type": trade.trade_type,
            "volume": float(trade.volume),
            "entry_price": float(trade.entry_price),
            "exit_price": float(trade.exit_price) if trade.exit_price else None,
            "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
            "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
            "profit": float(trade.profit) if trade.profit else 0,
            "pips": float(trade.pips) if trade.pips else 0,
            "status": trade.status.value,
            "stop_loss": float(trade.stop_loss) if trade.stop_loss else None,
            "take_profit": float(trade.take_profit) if trade.take_profit else None,
            "strategy_name": trade.strategy_name,
            "ml_enhanced": trade.ml_enhanced,
            "created_at": trade.created_at.isoformat() if trade.created_at else None,
            "updated_at": trade.updated_at.isoformat() if trade.updated_at else None
        }


@router.get("/stats/by-symbol")
async def get_stats_by_symbol(days: int = Query(default=30, ge=1, le=365)):
    """
    Get trade statistics grouped by symbol.

    Args:
        days: Number of days to include

    Returns:
        Statistics for each symbol
    """
    end_date = datetime.combine(date.today(), datetime.max.time())
    start_date = end_date - timedelta(days=days)

    async with get_async_session() as session:
        repo = TradeRepository()
        trades = repo.get_trades_by_date(
            session=session,
            start_date=start_date,
            end_date=end_date,
            status=TradeStatus.CLOSED
        )

        # Group by symbol
        symbol_stats = {}
        for trade in trades:
            if trade.symbol not in symbol_stats:
                symbol_stats[trade.symbol] = {
                    "symbol": trade.symbol,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "net_profit": 0.0,
                    "total_volume": 0.0
                }

            stats = symbol_stats[trade.symbol]
            stats["total_trades"] += 1
            stats["net_profit"] += float(trade.profit)
            stats["total_volume"] += float(trade.volume)

            if trade.profit > 0:
                stats["winning_trades"] += 1
            elif trade.profit < 0:
                stats["losing_trades"] += 1

        # Calculate win rates
        for stats in symbol_stats.values():
            if stats["total_trades"] > 0:
                stats["win_rate"] = round(
                    (stats["winning_trades"] / stats["total_trades"]) * 100,
                    2
                )
            else:
                stats["win_rate"] = 0

            stats["net_profit"] = round(stats["net_profit"], 2)
            stats["total_volume"] = round(stats["total_volume"], 2)

        return {
            "period_days": days,
            "symbols": list(symbol_stats.values())
        }

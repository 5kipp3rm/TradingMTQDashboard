"""
Aggregated Analytics Service

Provides cross-account aggregated metrics and performance analysis.
Supports filtering by account IDs and date ranges.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from src.database.models import Trade, TradingAccount, DailyPerformance, TradeStatus
from src.utils.logger import get_logger


logger = get_logger(__name__)


class AggregatedAnalyticsService:
    """
    Service for aggregated analytics across multiple trading accounts.

    Provides:
    - Cross-account performance metrics
    - Account comparisons
    - Aggregated trade statistics
    """

    def __init__(self):
        pass

    def get_aggregate_performance(
        self,
        db: Session,
        account_ids: Optional[List[int]] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get aggregated performance metrics across multiple accounts.

        Args:
            db: Database session
            account_ids: List of account IDs to aggregate (None = all accounts)
            days: Number of days to look back

        Returns:
            Dictionary with aggregated metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Build base query
        query = select(Trade).where(
            and_(
                Trade.entry_time >= start_date,
                Trade.status == TradeStatus.CLOSED
            )
        )

        # Filter by account IDs if specified
        if account_ids:
            query = query.where(Trade.account_id.in_(account_ids))

        # Execute query
        result = db.execute(query)
        trades = result.scalars().all()

        if not trades:
            return self._empty_aggregate_response(account_ids, days)

        # Calculate metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.profit and t.profit > 0)
        losing_trades = sum(1 for t in trades if t.profit and t.profit <= 0)

        gross_profit = sum(t.profit for t in trades if t.profit and t.profit > 0) or Decimal(0)
        gross_loss = abs(sum(t.profit for t in trades if t.profit and t.profit < 0)) or Decimal(0)
        net_profit = sum(t.profit for t in trades if t.profit) or Decimal(0)

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

        average_win = (gross_profit / winning_trades) if winning_trades > 0 else Decimal(0)
        average_loss = (gross_loss / losing_trades) if losing_trades > 0 else Decimal(0)

        largest_win = max((t.profit for t in trades if t.profit and t.profit > 0), default=Decimal(0))
        largest_loss = min((t.profit for t in trades if t.profit and t.profit < 0), default=Decimal(0))

        # Average daily profit
        avg_daily_profit = net_profit / days if days > 0 else Decimal(0)

        # Get account info
        account_count = len(set(t.account_id for t in trades if t.account_id))

        return {
            "period_days": days,
            "account_count": account_count,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "gross_profit": float(gross_profit),
            "gross_loss": float(gross_loss),
            "net_profit": float(net_profit),
            "win_rate": round(win_rate, 2),
            "profit_factor": float(round(profit_factor, 2)),
            "average_win": float(average_win),
            "average_loss": float(average_loss),
            "largest_win": float(largest_win),
            "largest_loss": float(largest_loss),
            "average_daily_profit": float(avg_daily_profit)
        }

    def get_account_comparison(
        self,
        db: Session,
        account_ids: Optional[List[int]] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get side-by-side comparison of performance across accounts.

        Args:
            db: Database session
            account_ids: List of account IDs to compare (None = all accounts)
            days: Number of days to look back

        Returns:
            Dictionary with per-account breakdown
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get accounts
        account_query = select(TradingAccount)
        if account_ids:
            account_query = account_query.where(TradingAccount.id.in_(account_ids))

        accounts = db.execute(account_query).scalars().all()

        if not accounts:
            return {"accounts": [], "total_accounts": 0}

        comparison = []

        for account in accounts:
            # Get trades for this account
            trades_query = select(Trade).where(
                and_(
                    Trade.account_id == account.id,
                    Trade.entry_time >= start_date,
                    Trade.status == TradeStatus.CLOSED
                )
            )
            trades = db.execute(trades_query).scalars().all()

            # Calculate metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.profit and t.profit > 0)
            losing_trades = sum(1 for t in trades if t.profit and t.profit <= 0)

            gross_profit = sum(t.profit for t in trades if t.profit and t.profit > 0) or Decimal(0)
            gross_loss = abs(sum(t.profit for t in trades if t.profit and t.profit < 0)) or Decimal(0)
            net_profit = sum(t.profit for t in trades if t.profit) or Decimal(0)

            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

            comparison.append({
                "account_id": account.id,
                "account_number": account.account_number,
                "account_name": account.account_name,
                "broker": account.broker,
                "is_demo": account.is_demo,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "net_profit": float(net_profit),
                "win_rate": round(win_rate, 2),
                "profit_factor": float(round(profit_factor, 2)),
                "gross_profit": float(gross_profit),
                "gross_loss": float(gross_loss)
            })

        # Sort by net profit descending
        comparison.sort(key=lambda x: x["net_profit"], reverse=True)

        return {
            "period_days": days,
            "total_accounts": len(comparison),
            "accounts": comparison
        }

    def get_aggregate_summary(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get high-level summary across all accounts.

        Args:
            db: Database session

        Returns:
            Dictionary with summary metrics
        """
        # Get all accounts
        accounts = db.execute(select(TradingAccount)).scalars().all()

        total_accounts = len(accounts)
        active_accounts = sum(1 for a in accounts if a.is_active)
        demo_accounts = sum(1 for a in accounts if a.is_demo)
        live_accounts = sum(1 for a in accounts if not a.is_demo)

        # Get total balance (from initial_balance - this is a placeholder)
        total_initial_balance = sum(
            (a.initial_balance or Decimal(0)) for a in accounts
        )

        # Get recent trades (last 30 days)
        start_date = datetime.utcnow() - timedelta(days=30)
        recent_trades_query = select(Trade).where(
            and_(
                Trade.entry_time >= start_date,
                Trade.status == TradeStatus.CLOSED
            )
        )
        recent_trades = db.execute(recent_trades_query).scalars().all()

        total_recent_trades = len(recent_trades)
        recent_net_profit = sum(t.profit for t in recent_trades if t.profit) or Decimal(0)

        # Get today's trades
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades_query = select(Trade).where(
            and_(
                Trade.entry_time >= today_start,
                Trade.status == TradeStatus.CLOSED
            )
        )
        today_trades = db.execute(today_trades_query).scalars().all()

        today_trades_count = len(today_trades)
        today_profit = sum(t.profit for t in today_trades if t.profit) or Decimal(0)

        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "demo_accounts": demo_accounts,
            "live_accounts": live_accounts,
            "total_initial_balance": float(total_initial_balance),
            "last_30_days": {
                "total_trades": total_recent_trades,
                "net_profit": float(recent_net_profit)
            },
            "today": {
                "total_trades": today_trades_count,
                "net_profit": float(today_profit)
            }
        }

    def get_aggregate_trades(
        self,
        db: Session,
        account_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get trades from multiple accounts with pagination.

        Args:
            db: Database session
            account_ids: List of account IDs (None = all accounts)
            limit: Maximum number of trades to return
            offset: Number of trades to skip

        Returns:
            Dictionary with trades and pagination info
        """
        # Build query
        query = select(Trade).where(Trade.status == TradeStatus.CLOSED)

        if account_ids:
            query = query.where(Trade.account_id.in_(account_ids))

        # Order by entry time descending
        query = query.order_by(Trade.entry_time.desc())

        # Get total count
        count_query = select(func.count()).select_from(Trade).where(Trade.status == TradeStatus.CLOSED)
        if account_ids:
            count_query = count_query.where(Trade.account_id.in_(account_ids))
        total_count = db.execute(count_query).scalar()

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        trades = db.execute(query).scalars().all()

        # Get account info for trades
        account_ids_in_trades = list(set(t.account_id for t in trades if t.account_id))
        accounts_dict = {}
        if account_ids_in_trades:
            accounts = db.execute(
                select(TradingAccount).where(TradingAccount.id.in_(account_ids_in_trades))
            ).scalars().all()
            accounts_dict = {a.id: a for a in accounts}

        # Format trades
        trades_list = []
        for trade in trades:
            account = accounts_dict.get(trade.account_id)
            trade_dict = trade.to_dict()
            trade_dict["account_name"] = account.account_name if account else "Unknown"
            trade_dict["account_number"] = account.account_number if account else None
            trades_list.append(trade_dict)

        return {
            "trades": trades_list,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }

    def _empty_aggregate_response(
        self,
        account_ids: Optional[List[int]],
        days: int
    ) -> Dict[str, Any]:
        """Return empty aggregate response when no trades found."""
        return {
            "period_days": days,
            "account_count": len(account_ids) if account_ids else 0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "net_profit": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "average_daily_profit": 0.0
        }


# Global service instance
analytics_service = AggregatedAnalyticsService()

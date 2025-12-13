"""
Daily Performance Aggregator

Calculates daily trading performance metrics from trade data and populates
the daily_performance table for analytics and reporting.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional, List
from decimal import Decimal

from src.database.models import Trade, TradeStatus, DailyPerformance
from src.database.repository import TradeRepository, DailyPerformanceRepository
from src.database.connection import get_session
from src.utils.structured_logger import StructuredLogger, CorrelationContext

logger = StructuredLogger(__name__)


class DailyAggregator:
    """
    Aggregates trade data into daily performance metrics.

    Usage:
        aggregator = DailyAggregator()

        # Aggregate specific date
        aggregator.aggregate_day(date(2025, 12, 13))

        # Aggregate date range
        aggregator.aggregate_range(start_date, end_date)

        # Backfill all historical data
        aggregator.backfill()
    """

    def __init__(self):
        self.trade_repo = TradeRepository()
        self.perf_repo = DailyPerformanceRepository()

    def aggregate_day(self, target_date: date) -> Optional[DailyPerformance]:
        """
        Aggregate trade data for a specific date.

        Args:
            target_date: The date to aggregate

        Returns:
            DailyPerformance object if trades exist, None otherwise
        """
        logger.info(
            "Starting daily aggregation",
            extra={"target_date": target_date.isoformat()}
        )

        with get_session() as session:
            # Get all closed trades for the target date
            trades = self.trade_repo.get_trades_by_date(
                session=session,
                start_date=datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                end_date=datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc),
                status=TradeStatus.CLOSED
            )

            if not trades:
                logger.info(
                    "No closed trades found for date",
                    extra={"target_date": target_date.isoformat()}
                )
                return None

            # Calculate metrics
            metrics = self._calculate_metrics(trades, target_date)

            # Create or update daily performance record
            performance = self.perf_repo.create_or_update(
                session=session,
                target_date=target_date,
                **metrics
            )

            logger.info(
                "Daily aggregation completed",
                extra={
                    "target_date": target_date.isoformat(),
                    "total_trades": metrics["total_trades"],
                    "net_profit": float(metrics["net_profit"]),
                    "win_rate": float(metrics["win_rate"])
                }
            )

            return performance

    def aggregate_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[DailyPerformance]:
        """
        Aggregate trade data for a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of DailyPerformance objects created
        """
        logger.info(
            "Starting range aggregation",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )

        results = []
        current_date = start_date

        while current_date <= end_date:
            performance = self.aggregate_day(current_date)
            if performance:
                results.append(performance)
            current_date += timedelta(days=1)

        logger.info(
            "Range aggregation completed",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_aggregated": len(results)
            }
        )

        return results

    def backfill(self) -> List[DailyPerformance]:
        """
        Backfill all historical trade data into daily performance.

        Finds the earliest trade date and aggregates all days up to today.

        Returns:
            List of DailyPerformance objects created
        """
        logger.info("Starting backfill aggregation")

        with get_session() as session:
            # Find earliest trade
            earliest_trade = self.trade_repo.get_earliest_trade(session)

            if not earliest_trade:
                logger.info("No trades found for backfill")
                return []

            # Get date range
            start_date = earliest_trade.entry_time.date()
            end_date = date.today()

            logger.info(
                "Backfill date range determined",
                extra={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_days": (end_date - start_date).days + 1
                }
            )

            # Aggregate the range
            return self.aggregate_range(start_date, end_date)

    def _calculate_metrics(self, trades: List[Trade], target_date: date) -> dict:
        """
        Calculate daily performance metrics from trades.

        Args:
            trades: List of closed trades for the day
            target_date: The date being aggregated

        Returns:
            Dictionary of calculated metrics
        """
        total_trades = len(trades)

        # Separate winning and losing trades
        winning_trades = [t for t in trades if t.profit > 0]
        losing_trades = [t for t in trades if t.profit < 0]
        breakeven_trades = [t for t in trades if t.profit == 0]

        winning_count = len(winning_trades)
        losing_count = len(losing_trades)

        # Calculate profit metrics
        gross_profit = sum(t.profit for t in winning_trades)
        gross_loss = abs(sum(t.profit for t in losing_trades))
        net_profit = sum(t.profit for t in trades)

        # Calculate rates
        win_rate = Decimal(winning_count / total_trades * 100) if total_trades > 0 else Decimal(0)
        profit_factor = Decimal(gross_profit / gross_loss) if gross_loss > 0 else Decimal(0)

        # Calculate averages
        avg_win = Decimal(gross_profit / winning_count) if winning_count > 0 else Decimal(0)
        avg_loss = Decimal(gross_loss / losing_count) if losing_count > 0 else Decimal(0)
        avg_trade_profit = Decimal(net_profit / total_trades) if total_trades > 0 else Decimal(0)

        # Find best and worst trades
        best_trade_profit = max(t.profit for t in trades) if trades else Decimal(0)
        worst_trade_loss = min(t.profit for t in trades) if trades else Decimal(0)

        # Calculate average trade duration (in minutes)
        total_duration_minutes = 0
        for trade in trades:
            if trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 60
                total_duration_minutes += duration

        avg_trade_duration_minutes = int(total_duration_minutes / total_trades) if total_trades > 0 else 0

        # Count symbols traded
        symbols_traded = len(set(t.symbol for t in trades))

        # Calculate max consecutive wins/losses
        max_consecutive_wins = self._calculate_max_consecutive(trades, winning=True)
        max_consecutive_losses = self._calculate_max_consecutive(trades, winning=False)

        return {
            "total_trades": total_trades,
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "net_profit": net_profit,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "largest_win": best_trade_profit,
            "largest_loss": worst_trade_loss
        }

    def _calculate_max_consecutive(self, trades: List[Trade], winning: bool) -> int:
        """
        Calculate maximum consecutive wins or losses.

        Args:
            trades: List of trades (should be sorted by exit_time)
            winning: True to count wins, False to count losses

        Returns:
            Maximum consecutive count
        """
        if not trades:
            return 0

        # Sort by exit time to get correct sequence
        sorted_trades = sorted(trades, key=lambda t: t.exit_time if t.exit_time else datetime.now(timezone.utc))

        max_consecutive = 0
        current_consecutive = 0

        for trade in sorted_trades:
            if winning:
                is_match = trade.profit > 0
            else:
                is_match = trade.profit < 0

            if is_match:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

"""
Background Job Scheduler for Analytics

Implements automated daily aggregation using APScheduler.
Runs aggregation jobs at configured times to ensure daily performance
metrics are calculated without manual intervention.
"""

from datetime import date, datetime, timedelta
from typing import Optional
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from src.analytics.daily_aggregator import DailyAggregator
from src.database.connection import init_db, get_session
from src.utils.structured_logger import StructuredLogger, CorrelationContext

logger = StructuredLogger(__name__)


class AnalyticsScheduler:
    """
    Manages scheduled analytics jobs for automated daily aggregation.

    Usage:
        scheduler = AnalyticsScheduler()
        scheduler.start()

        # Scheduler runs in background
        # Aggregation happens daily at configured time

        scheduler.stop()  # Clean shutdown
    """

    def __init__(self, aggregation_hour: int = 0, aggregation_minute: int = 5):
        """
        Initialize scheduler with configuration.

        Args:
            aggregation_hour: Hour of day to run aggregation (0-23, default: 0 = midnight)
            aggregation_minute: Minute of hour to run aggregation (0-59, default: 5)
        """
        self.scheduler = BackgroundScheduler()
        self.aggregator = DailyAggregator()
        self.aggregation_hour = aggregation_hour
        self.aggregation_minute = aggregation_minute

        # Add event listeners for job monitoring
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )

        # Register shutdown handler
        atexit.register(self.stop)

        logger.info(
            "Analytics scheduler initialized",
            extra={
                "aggregation_time": f"{aggregation_hour:02d}:{aggregation_minute:02d}"
            }
        )

    def start(self):
        """Start the scheduler and register jobs."""
        try:
            # Ensure database is initialized
            init_db()

            # Schedule daily aggregation job
            self.scheduler.add_job(
                func=self._run_daily_aggregation,
                trigger=CronTrigger(
                    hour=self.aggregation_hour,
                    minute=self.aggregation_minute
                ),
                id='daily_aggregation',
                name='Daily Performance Aggregation',
                replace_existing=True,
                max_instances=1  # Prevent overlapping runs
            )

            # Start scheduler
            self.scheduler.start()

            logger.info(
                "Analytics scheduler started",
                extra={
                    "jobs": len(self.scheduler.get_jobs()),
                    "next_run": self._get_next_run_time()
                }
            )

        except Exception as e:
            logger.error(
                "Failed to start analytics scheduler",
                exc_info=True,
                extra={"error": str(e)}
            )
            raise

    def stop(self):
        """Stop the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Analytics scheduler stopped")

    def _run_daily_aggregation(self):
        """
        Run daily aggregation for yesterday's trades.

        This job runs at the configured time each day to aggregate
        the previous day's trading performance.
        """
        with CorrelationContext():
            try:
                # Aggregate yesterday's trades
                yesterday = date.today() - timedelta(days=1)

                logger.info(
                    "Starting scheduled daily aggregation",
                    extra={"target_date": yesterday.isoformat()}
                )

                result = self.aggregator.aggregate_day(yesterday)

                if result:
                    logger.info(
                        "Scheduled daily aggregation completed",
                        extra={
                            "target_date": yesterday.isoformat(),
                            "total_trades": result.total_trades,
                            "net_profit": float(result.net_profit),
                            "win_rate": float(result.win_rate)
                        }
                    )
                else:
                    logger.info(
                        "No trades found for scheduled aggregation",
                        extra={"target_date": yesterday.isoformat()}
                    )

            except Exception as e:
                logger.error(
                    "Scheduled daily aggregation failed",
                    exc_info=True,
                    extra={
                        "target_date": yesterday.isoformat(),
                        "error": str(e)
                    }
                )
                raise

    def trigger_aggregation_now(self, target_date: Optional[date] = None):
        """
        Manually trigger aggregation job for testing or catch-up.

        Args:
            target_date: Date to aggregate (default: yesterday)
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        with CorrelationContext():
            logger.info(
                "Manual aggregation triggered",
                extra={"target_date": target_date.isoformat()}
            )

            result = self.aggregator.aggregate_day(target_date)

            if result:
                logger.info(
                    "Manual aggregation completed",
                    extra={
                        "target_date": target_date.isoformat(),
                        "total_trades": result.total_trades,
                        "net_profit": float(result.net_profit)
                    }
                )
            else:
                logger.info(
                    "No trades found for manual aggregation",
                    extra={"target_date": target_date.isoformat()}
                )

            return result

    def _get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time as ISO string."""
        jobs = self.scheduler.get_jobs()
        if jobs:
            next_run = jobs[0].next_run_time
            return next_run.isoformat() if next_run else None
        return None

    def _job_executed_listener(self, event):
        """Log successful job execution."""
        logger.info(
            "Scheduled job executed successfully",
            extra={
                "job_id": event.job_id,
                "scheduled_time": event.scheduled_run_time.isoformat(),
                "execution_time": datetime.now().isoformat()
            }
        )

    def _job_error_listener(self, event):
        """Log job execution errors."""
        logger.error(
            "Scheduled job failed",
            extra={
                "job_id": event.job_id,
                "exception": str(event.exception),
                "traceback": event.traceback
            }
        )

    def get_status(self) -> dict:
        """
        Get scheduler status information.

        Returns:
            Dictionary with scheduler status details
        """
        return {
            "running": self.scheduler.running,
            "jobs_count": len(self.scheduler.get_jobs()),
            "next_run": self._get_next_run_time(),
            "aggregation_time": f"{self.aggregation_hour:02d}:{self.aggregation_minute:02d}"
        }


# Global scheduler instance
_scheduler_instance: Optional[AnalyticsScheduler] = None


def get_scheduler(
    aggregation_hour: int = 0,
    aggregation_minute: int = 5
) -> AnalyticsScheduler:
    """
    Get or create the global scheduler instance.

    Args:
        aggregation_hour: Hour of day to run aggregation (0-23)
        aggregation_minute: Minute of hour to run aggregation (0-59)

    Returns:
        AnalyticsScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = AnalyticsScheduler(
            aggregation_hour=aggregation_hour,
            aggregation_minute=aggregation_minute
        )

    return _scheduler_instance

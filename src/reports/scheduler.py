"""
Report Scheduler Service

Manages scheduled report generation using APScheduler.
Handles daily, weekly, monthly, and custom report schedules.
"""

from typing import Optional, List
from datetime import datetime, date, timedelta, time as datetime_time
from pathlib import Path
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job

from src.database import get_session
from src.database.report_models import (
    ReportConfiguration,
    ReportHistory,
    ReportFrequency,
    ReportFormat
)
from src.reports.generator import ReportGenerator
from src.reports.email_service import EmailService, EmailConfiguration
from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class ReportScheduler:
    """
    Manages scheduled report generation with APScheduler.
    """

    def __init__(
        self,
        report_generator: Optional[ReportGenerator] = None,
        email_service: Optional[EmailService] = None
    ):
        """
        Initialize report scheduler.

        Args:
            report_generator: Report generator instance (creates default if None)
            email_service: Email service instance (optional)
        """
        self.scheduler = BackgroundScheduler()
        self.report_generator = report_generator or ReportGenerator()
        self.email_service = email_service
        self._job_map = {}  # Maps config_id to job_id

    def start(self):
        """
        Start the scheduler and load all active report configurations.
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Report scheduler started")

            # Load and schedule all active reports
            self.reload_schedules()

    def stop(self):
        """
        Stop the scheduler and clear all jobs.
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Report scheduler stopped")

    def reload_schedules(self):
        """
        Reload all active report configurations and reschedule them.
        """
        logger.info("Reloading report schedules")

        # Remove all existing jobs
        self.scheduler.remove_all_jobs()
        self._job_map.clear()

        # Load active configurations
        with get_session() as session:
            configs = session.query(ReportConfiguration).filter(
                ReportConfiguration.is_active == True
            ).all()

            for config in configs:
                try:
                    self.schedule_report(config.id)
                    logger.info(
                        "Scheduled report",
                        config_id=config.id,
                        name=config.name,
                        frequency=config.frequency.value
                    )
                except Exception as e:
                    logger.error(
                        "Failed to schedule report",
                        config_id=config.id,
                        error=str(e)
                    )

    def schedule_report(self, config_id: int):
        """
        Schedule a specific report configuration.

        Args:
            config_id: Report configuration ID
        """
        with get_session() as session:
            config = session.get(ReportConfiguration, config_id)

            if not config:
                raise ValueError(f"Report configuration {config_id} not found")

            if not config.is_active:
                logger.warning(
                    "Attempted to schedule inactive report",
                    config_id=config_id
                )
                return

            # Create trigger based on frequency
            trigger = self._create_trigger(config)

            # Schedule the job
            job = self.scheduler.add_job(
                func=self._generate_scheduled_report,
                trigger=trigger,
                args=[config_id],
                id=f"report_{config_id}",
                name=config.name,
                replace_existing=True,
                misfire_grace_time=3600  # 1 hour grace period
            )

            self._job_map[config_id] = job.id

            # Update next_run time
            config.next_run = job.next_run_time
            session.commit()

            logger.info(
                "Report scheduled",
                config_id=config_id,
                next_run=job.next_run_time.isoformat() if job.next_run_time else None
            )

    def unschedule_report(self, config_id: int):
        """
        Remove a scheduled report.

        Args:
            config_id: Report configuration ID
        """
        job_id = self._job_map.get(config_id)
        if job_id:
            try:
                self.scheduler.remove_job(job_id)
                del self._job_map[config_id]
                logger.info("Report unscheduled", config_id=config_id)
            except Exception as e:
                logger.error(
                    "Failed to unschedule report",
                    config_id=config_id,
                    error=str(e)
                )

    def _create_trigger(self, config: ReportConfiguration):
        """
        Create APScheduler trigger based on report configuration.

        Args:
            config: Report configuration

        Returns:
            APScheduler trigger object
        """
        # Parse time of day
        hour, minute = 9, 0  # Default to 9:00 AM
        if config.time_of_day:
            try:
                time_parts = config.time_of_day.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
            except (ValueError, IndexError):
                logger.warning(
                    "Invalid time_of_day format, using default 09:00",
                    config_id=config.id,
                    time_of_day=config.time_of_day
                )

        if config.frequency == ReportFrequency.DAILY:
            # Daily at specified time
            return CronTrigger(hour=hour, minute=minute)

        elif config.frequency == ReportFrequency.WEEKLY:
            # Weekly on specified day at specified time
            day_of_week = config.day_of_week if config.day_of_week is not None else 0  # Monday
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)

        elif config.frequency == ReportFrequency.MONTHLY:
            # Monthly on specified day at specified time
            day = config.day_of_month if config.day_of_month is not None else 1
            return CronTrigger(day=day, hour=hour, minute=minute)

        elif config.frequency == ReportFrequency.CUSTOM:
            # Custom interval (default to daily if no specific schedule)
            logger.warning(
                "Custom frequency not fully implemented, defaulting to daily",
                config_id=config.id
            )
            return CronTrigger(hour=hour, minute=minute)

        else:
            raise ValueError(f"Unknown frequency: {config.frequency}")

    def _generate_scheduled_report(self, config_id: int):
        """
        Generate report for a scheduled configuration.

        This is the job function called by APScheduler.

        Args:
            config_id: Report configuration ID
        """
        start_time = datetime.now()
        logger.info("Starting scheduled report generation", config_id=config_id)

        try:
            with get_session() as session:
                config = session.get(ReportConfiguration, config_id)

                if not config:
                    logger.error("Report configuration not found", config_id=config_id)
                    return

                if not config.is_active:
                    logger.warning("Report configuration is inactive", config_id=config_id)
                    return

                # Calculate date range based on days_lookback
                end_date = date.today()
                start_date = end_date - timedelta(days=config.days_lookback)

                # Generate report
                report_path = self.report_generator.generate_performance_report(
                    start_date=start_date,
                    end_date=end_date,
                    account_id=config.account_id,
                    include_trades=config.include_trades,
                    include_charts=config.include_charts
                )

                # Send email if configured
                email_sent = False
                if self.email_service and config.recipients:
                    recipients = config.recipients.split(',')
                    cc_recipients = config.cc_recipients.split(',') if config.cc_recipients else None

                    subject = config.email_subject or f"Trading Performance Report - {end_date}"
                    body_html = config.email_body

                    email_sent = self.email_service.send_report(
                        to_emails=recipients,
                        subject=subject,
                        report_path=report_path,
                        body_html=body_html,
                        cc_emails=cc_recipients
                    )

                # Calculate execution time
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

                # Record success in history
                history = ReportHistory(
                    config_id=config_id,
                    generated_at=datetime.now(),
                    report_start_date=start_date,
                    report_end_date=end_date,
                    success=True,
                    file_path=str(report_path),
                    file_size=report_path.stat().st_size,
                    email_sent=email_sent,
                    email_recipients=config.recipients,
                    execution_time_ms=execution_time
                )
                session.add(history)

                # Update configuration status
                config.last_run = datetime.now()
                config.last_success = datetime.now()
                config.run_count += 1
                config.last_error = None

                # Update next_run time
                job = self.scheduler.get_job(f"report_{config_id}")
                if job:
                    config.next_run = job.next_run_time

                session.commit()

                logger.info(
                    "Scheduled report generated successfully",
                    config_id=config_id,
                    report_path=str(report_path),
                    execution_time_ms=execution_time,
                    email_sent=email_sent
                )

        except Exception as e:
            # Record failure in history
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            error_message = str(e)
            error_trace = traceback.format_exc()

            logger.error(
                "Failed to generate scheduled report",
                config_id=config_id,
                error=error_message,
                exc_info=True
            )

            try:
                with get_session() as session:
                    config = session.get(ReportConfiguration, config_id)

                    if config:
                        # Calculate date range
                        end_date = date.today()
                        start_date = end_date - timedelta(days=config.days_lookback)

                        # Record failure
                        history = ReportHistory(
                            config_id=config_id,
                            generated_at=datetime.now(),
                            report_start_date=start_date,
                            report_end_date=end_date,
                            success=False,
                            error_message=error_message[:500],  # Limit error message length
                            email_sent=False,
                            execution_time_ms=execution_time
                        )
                        session.add(history)

                        # Update configuration status
                        config.last_run = datetime.now()
                        config.last_error = error_message[:500]
                        config.run_count += 1

                        session.commit()
            except Exception as db_error:
                logger.error(
                    "Failed to record report failure in database",
                    config_id=config_id,
                    error=str(db_error),
                    exc_info=True
                )

    def get_scheduled_jobs(self) -> List[dict]:
        """
        Get information about all scheduled jobs.

        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs

    def get_job_status(self, config_id: int) -> Optional[dict]:
        """
        Get status of a specific scheduled report.

        Args:
            config_id: Report configuration ID

        Returns:
            Job status dictionary or None if not found
        """
        job_id = self._job_map.get(config_id)
        if not job_id:
            return None

        job = self.scheduler.get_job(job_id)
        if not job:
            return None

        return {
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger),
            'pending': job.pending
        }

    def trigger_report_now(self, config_id: int):
        """
        Manually trigger a report generation immediately.

        Args:
            config_id: Report configuration ID
        """
        logger.info("Manually triggering report generation", config_id=config_id)
        self._generate_scheduled_report(config_id)

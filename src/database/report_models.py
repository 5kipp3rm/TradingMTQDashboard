"""
Report Configuration Database Models

Models for managing scheduled reports and report configurations.
"""

from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models import Base


class ReportFrequency(PyEnum):
    """Report frequency enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportFormat(PyEnum):
    """Report format enumeration"""
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


class ReportConfiguration(Base):
    """
    Report Configuration Model

    Stores scheduled report configurations including recipients, frequency,
    and report parameters.
    """
    __tablename__ = 'report_configurations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Configuration
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Schedule
    frequency: Mapped[ReportFrequency] = mapped_column(
        Enum(ReportFrequency),
        nullable=False,
        default=ReportFrequency.DAILY
    )
    day_of_week: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="For weekly reports: 0=Monday, 6=Sunday"
    )
    day_of_month: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="For monthly reports: 1-31"
    )
    time_of_day: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="Time in HH:MM format (24-hour)"
    )

    # Report Parameters
    report_format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat),
        nullable=False,
        default=ReportFormat.PDF
    )
    include_trades: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_charts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    days_lookback: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="Number of days to include in report"
    )

    # Account Filter
    account_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('trading_accounts.id'),
        nullable=True,
        index=True,
        comment="Filter by specific account, NULL for all accounts"
    )

    # Email Configuration
    recipients: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Comma-separated email addresses"
    )
    cc_recipients: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated CC email addresses"
    )
    email_subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_success: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'frequency': self.frequency.value,
            'day_of_week': self.day_of_week,
            'day_of_month': self.day_of_month,
            'time_of_day': self.time_of_day,
            'report_format': self.report_format.value,
            'include_trades': self.include_trades,
            'include_charts': self.include_charts,
            'days_lookback': self.days_lookback,
            'account_id': self.account_id,
            'recipients': self.recipients.split(',') if self.recipients else [],
            'cc_recipients': self.cc_recipients.split(',') if self.cc_recipients else [],
            'email_subject': self.email_subject,
            'is_active': self.is_active,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'last_error': self.last_error,
            'run_count': self.run_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ReportHistory(Base):
    """
    Report Generation History

    Tracks historical report generation attempts with success/failure status.
    """
    __tablename__ = 'report_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Configuration Reference
    config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('report_configurations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Generation Details
    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    report_start_date: Mapped[date] = mapped_column(DateTime, nullable=False)
    report_end_date: Mapped[date] = mapped_column(DateTime, nullable=False)

    # Status
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Output
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Email Status
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_recipients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Execution Time
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Execution time in milliseconds"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'config_id': self.config_id,
            'generated_at': self.generated_at.isoformat(),
            'report_start_date': self.report_start_date.isoformat() if isinstance(self.report_start_date, (date, datetime)) else self.report_start_date,
            'report_end_date': self.report_end_date.isoformat() if isinstance(self.report_end_date, (date, datetime)) else self.report_end_date,
            'success': self.success,
            'error_message': self.error_message,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'email_sent': self.email_sent,
            'email_recipients': self.email_recipients,
            'execution_time_ms': self.execution_time_ms,
        }

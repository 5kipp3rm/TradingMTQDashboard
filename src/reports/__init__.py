"""
Performance Report Generation System

Provides automated PDF report generation and email delivery for trading performance analytics.
"""

from .generator import ReportGenerator
from .email_service import EmailService
from .scheduler import ReportScheduler

__all__ = [
    'ReportGenerator',
    'EmailService',
    'ReportScheduler',
]

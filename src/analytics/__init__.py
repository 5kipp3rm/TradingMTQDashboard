"""
Analytics Module

Provides performance analytics, aggregation, and reporting capabilities.

Components:
- DailyAggregator: Calculates daily performance metrics from trade data
- AnalyticsScheduler: Automated background job system for daily aggregation
- PerformanceAnalyzer: Advanced performance analysis and statistics (future)
- ReportGenerator: Generates performance reports (future)
"""

from src.analytics.daily_aggregator import DailyAggregator
from src.analytics.scheduler import AnalyticsScheduler, get_scheduler

__all__ = ["DailyAggregator", "AnalyticsScheduler", "get_scheduler"]

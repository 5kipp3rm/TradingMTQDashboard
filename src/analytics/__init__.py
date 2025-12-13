"""
Analytics Module

Provides performance analytics, aggregation, and reporting capabilities.

Components:
- DailyAggregator: Calculates daily performance metrics from trade data
- PerformanceAnalyzer: Advanced performance analysis and statistics
- ReportGenerator: Generates performance reports
"""

from src.analytics.daily_aggregator import DailyAggregator

__all__ = ["DailyAggregator"]

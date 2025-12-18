"""
Database package for TradingMTQ
Provides SQLAlchemy models, repositories, and connection management
"""
from .models import (
    Base, Trade, Signal, AccountSnapshot, DailyPerformance,
    AlertConfiguration, AlertHistory, AlertType, NotificationChannel,
    TradingAccount, AccountConnectionState, PlatformType
)
from .report_models import (
    ReportConfiguration, ReportHistory, ReportFrequency, ReportFormat
)
from .currency_models import (
    CurrencyConfiguration, StrategyType, Timeframe
)
from .bot_models import (
    BotState, BotStatus
)
from .repository import TradeRepository, SignalRepository, AccountSnapshotRepository
from .connection import get_session, get_db_dependency, init_db, close_db

__all__ = [
    'Base',
    'Trade',
    'Signal',
    'AccountSnapshot',
    'DailyPerformance',
    'AlertConfiguration',
    'AlertHistory',
    'AlertType',
    'NotificationChannel',
    'TradingAccount',
    'AccountConnectionState',
    'PlatformType',
    'ReportConfiguration',
    'ReportHistory',
    'ReportFrequency',
    'ReportFormat',
    'CurrencyConfiguration',
    'StrategyType',
    'Timeframe',
    'BotState',
    'BotStatus',
    'TradeRepository',
    'SignalRepository',
    'AccountSnapshotRepository',
    'get_session',
    'get_db_dependency',
    'init_db',
    'close_db',
]

"""
Trading Control Service - Phase 3

Provides service layer for controlling trading operations via API.

Design Patterns:
- Service Layer: Business logic separated from API layer
- Strategy Pattern: Pluggable AutoTrading checkers
- Decorator Pattern: Caching decorator for status checks
- Dependency Injection: Services injected via constructor

SOLID Principles:
- Single Responsibility: Each service has one purpose
- Open/Closed: Extensible through interfaces
- Dependency Inversion: Depend on abstractions

Usage:
    from src.services.trading_control import (
        TradingControlService,
        get_trading_control_service
    )

    # Get service (singleton)
    service = get_trading_control_service()

    # Start trading for account
    result = service.start_trading("account-001")

    # Check AutoTrading status
    status = service.check_autotrading("account-001")

    # Stop trading
    result = service.stop_trading("account-001")
"""

from src.services.trading_control.models import (
    TradingControlResult,
    TradingStatus,
    AutoTradingStatus,
)

from src.services.trading_control.interfaces import (
    IAutoTradingChecker,
)

from src.services.trading_control.service import (
    TradingControlService,
)

from src.services.trading_control.checker import (
    WorkerBasedAutoTradingChecker,
    CachedAutoTradingChecker,
)

from src.services.trading_control.factory import (
    get_trading_control_service,
    reset_trading_control_service,
)

__all__ = [
    # Models
    "TradingControlResult",
    "TradingStatus",
    "AutoTradingStatus",
    # Interfaces
    "IAutoTradingChecker",
    # Service
    "TradingControlService",
    # Checkers
    "WorkerBasedAutoTradingChecker",
    "CachedAutoTradingChecker",
    # Factory
    "get_trading_control_service",
    "reset_trading_control_service",
]

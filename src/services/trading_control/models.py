"""
Trading Control Models - Value Objects

Immutable value objects for trading control service.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class TradingStatus(str, Enum):
    """Trading status enumeration"""
    ACTIVE = "active"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TradingControlResult:
    """
    Value object for trading control operation results

    Immutable to prevent accidental modification.
    """
    success: bool
    message: str
    account_id: str
    status: TradingStatus
    timestamp: datetime
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "success": self.success,
            "message": self.message,
            "account_id": self.account_id,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
            "metadata": self.metadata or {},
        }


@dataclass(frozen=True)
class AutoTradingStatus:
    """
    Value object for AutoTrading status

    Contains status and instructions for enabling if disabled.
    """
    enabled: bool
    account_id: str
    checked_at: datetime
    instructions: Optional[Dict[str, str]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "autotrading_enabled": self.enabled,
            "account_id": self.account_id,
            "checked_at": self.checked_at.isoformat(),
        }

        if not self.enabled and self.instructions:
            result["instructions"] = self.instructions

        if self.error:
            result["error"] = self.error

        return result

    @staticmethod
    def get_enable_instructions() -> Dict[str, str]:
        """Get standard instructions for enabling AutoTrading"""
        return {
            "step1": "Open MetaTrader 5 terminal",
            "step2": "Click the 'AutoTrading' button in the toolbar (or press Alt+A)",
            "step3": "Ensure 'Algo Trading' is enabled in Tools -> Options -> Expert Advisors",
            "step4": "Verify the AutoTrading indicator is green in the terminal status bar",
        }

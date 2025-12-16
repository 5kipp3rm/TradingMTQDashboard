"""
MT5 Connector - MetaTrader 5 Integration

This is a routing module that directs to the appropriate MT5 connector implementation.

Available MT5 Connector Implementations:
==========================================

1. MT5ConnectorBridge (RECOMMENDED - Works on Mac/Windows/Linux)
   - Bridge solution using MQL5 Expert Advisor
   - Works with any broker
   - No Python package dependencies
   - File: src/connectors/mt5_connector_bridge.py
   - Setup: See mql5/README.md

2. MT5ConnectorDirect (Python Package - Windows/Linux Only)
   - Uses MetaTrader5 Python package
   - Only available on Windows and Linux
   - File: src/connectors/mt5_connector_direct.py
   - Install: pip install MetaTrader5

For detailed comparison and setup instructions, see:
    docs/MT5_INTEGRATION_GUIDE.md

To use a specific implementation, import directly:
    from src.connectors.mt5_connector_bridge import MT5ConnectorBridge
    from src.connectors.mt5_connector_direct import MT5ConnectorDirect
"""
from typing import Optional, List
import logging
from .base import (
    BaseMetaTraderConnector, PlatformType,
    TickData, OHLCBar, SymbolInfo, Position, AccountInfo,
    TradeRequest, TradeResult
)

# Import recommended implementation (bridge solution)
try:
    from .mt5_connector_bridge import MT5ConnectorBridge
    DEFAULT_IMPLEMENTATION = MT5ConnectorBridge
    IMPLEMENTATION_NAME = "MT5ConnectorBridge"
except ImportError:
    DEFAULT_IMPLEMENTATION = None
    IMPLEMENTATION_NAME = "None"


logger = logging.getLogger(__name__)


class MT5Connector(BaseMetaTraderConnector):
    """
    MetaTrader 5 connector - Routes to appropriate implementation

    This class automatically uses the best available MT5 connector implementation.
    By default, it uses MT5ConnectorBridge (MQL5 bridge solution).

    To use a different implementation, import directly:
        from src.connectors.mt5_connector_bridge import MT5ConnectorBridge
        from src.connectors.mt5_connector_direct import MT5ConnectorDirect

    For setup instructions, see:
        - docs/MT5_INTEGRATION_GUIDE.md
        - mql5/README.md (for bridge solution)
    """

    def __init__(self, instance_id: str = "default"):
        """
        Initialize MT5 connector

        This will automatically select and initialize the best available implementation.
        For most users, this uses MT5ConnectorBridge.
        """
        super().__init__(instance_id, PlatformType.MT5)

        if DEFAULT_IMPLEMENTATION is None:
            logger.error(
                f"[{self.instance_id}] No MT5 connector implementation available. "
                "Please ensure mt5_connector_bridge is available. "
                "See docs/MT5_INTEGRATION_GUIDE.md for details."
            )
            self._impl = None
        else:
            logger.info(
                f"[{self.instance_id}] Using {IMPLEMENTATION_NAME} for MT5 connection"
            )
            self._impl = DEFAULT_IMPLEMENTATION(instance_id=instance_id)

    def connect(self, login: int, password: str, server: str, **kwargs) -> bool:
        """
        Connect to MT5

        For MT5ConnectorBridge (default):
            Requires MQL5 Expert Advisor to be running in MT5.
            See mql5/README.md for setup instructions.

        Args:
            login: MT5 account number
            password: Account password
            server: Broker server
            **kwargs: Implementation-specific parameters

        Returns:
            True if connection successful
        """
        if self._impl is None:
            logger.error(
                f"[{self.instance_id}] No MT5 connector implementation available. "
                "See docs/MT5_INTEGRATION_GUIDE.md for setup instructions."
            )
            return False

        return self._impl.connect(login, password, server, **kwargs)

    def disconnect(self) -> None:
        """Disconnect from MT5"""
        if self._impl:
            self._impl.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        if self._impl:
            return self._impl.is_connected()
        return False

    def reconnect(self) -> bool:
        """Reconnect to MT5"""
        if self._impl:
            return self._impl.reconnect()
        return False

    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        if self._impl:
            return self._impl.get_account_info()
        return None

    def get_symbols(self, group: str = "*") -> List[str]:
        """Get available symbols"""
        if self._impl:
            return self._impl.get_symbols(group)
        return []

    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get symbol information"""
        if self._impl:
            return self._impl.get_symbol_info(symbol)
        return None

    def select_symbol(self, symbol: str, enable: bool = True) -> bool:
        """Select symbol in Market Watch"""
        if self._impl:
            return self._impl.select_symbol(symbol, enable)
        return False

    def get_tick(self, symbol: str) -> Optional[TickData]:
        """Get last tick for symbol"""
        if self._impl:
            return self._impl.get_tick(symbol)
        return None

    def get_bars(self, symbol: str, timeframe: str, count: int,
                 start_pos: int = 0) -> List[OHLCBar]:
        """Get historical bars"""
        if self._impl:
            return self._impl.get_bars(symbol, timeframe, count, start_pos)
        return []

    def send_order(self, request: TradeRequest) -> TradeResult:
        """Send trading order"""
        if self._impl:
            return self._impl.send_order(request)
        return TradeResult(
            success=False,
            error_message="No MT5 connector implementation available"
        )

    def close_position(self, ticket: int) -> TradeResult:
        """Close position by ticket"""
        if self._impl:
            return self._impl.close_position(ticket)
        return TradeResult(
            success=False,
            error_message="No MT5 connector implementation available"
        )

    def modify_position(self, ticket: int, sl: Optional[float] = None,
                       tp: Optional[float] = None) -> TradeResult:
        """Modify position SL/TP"""
        if self._impl:
            return self._impl.modify_position(ticket, sl, tp)
        return TradeResult(
            success=False,
            error_message="No MT5 connector implementation available"
        )

    def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """Get open positions"""
        if self._impl:
            return self._impl.get_positions(symbol)
        return []

    def get_position_by_ticket(self, ticket: int) -> Optional[Position]:
        """Get position by ticket"""
        if self._impl:
            return self._impl.get_position_by_ticket(ticket)
        return None

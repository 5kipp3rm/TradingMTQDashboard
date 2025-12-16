"""
MT4 Connector - MetaTrader 4 Integration

This is a routing module that directs to the appropriate MT4 connector implementation.

Available MT4 Connector Implementations:
==========================================

1. MT4ConnectorV3Bridge (RECOMMENDED for Mac/Most Users)
   - Bridge solution using MQL4 Expert Advisor
   - Works with any broker
   - No broker approval needed
   - File: src/connectors/mt4_connector_v3_bridge.py
   - Setup: See mql4/README.md

2. MT4ConnectorV1 (Python Package)
   - Uses MetaTrader4 Python package
   - Limited broker support
   - File: src/connectors/mt4_connector_v1.py
   - Install: pip install MetaTrader4

3. MT4ConnectorV2FIX (FIX API)
   - Professional FIX protocol
   - Requires broker FIX API access
   - File: src/connectors/mt4_connector_v2_fix.py
   - Install: pip install simplefix

For detailed comparison and setup instructions, see:
    docs/MT4_INTEGRATION_GUIDE.md

To use a specific implementation, import directly:
    from src.connectors.mt4_connector_v3_bridge import MT4ConnectorV3Bridge
"""
from typing import Optional, List
from datetime import datetime
import logging
from .base import (
    BaseMetaTraderConnector, PlatformType, OrderType, ConnectionStatus,
    TickData, OHLCBar, SymbolInfo, Position, AccountInfo,
    TradeRequest, TradeResult
)

# Import recommended implementation
try:
    from .mt4_connector_v3_bridge import MT4ConnectorV3Bridge
    DEFAULT_IMPLEMENTATION = MT4ConnectorV3Bridge
    IMPLEMENTATION_NAME = "MT4ConnectorV3Bridge"
except ImportError:
    DEFAULT_IMPLEMENTATION = None
    IMPLEMENTATION_NAME = "None"


logger = logging.getLogger(__name__)


class MT4Connector(BaseMetaTraderConnector):
    """
    MetaTrader 4 connector - Routes to appropriate implementation

    This class automatically uses the best available MT4 connector implementation.
    By default, it uses MT4ConnectorV3Bridge (MQL4 bridge solution).

    To use a different implementation, import directly:
        from src.connectors.mt4_connector_v1 import MT4ConnectorV1
        from src.connectors.mt4_connector_v2_fix import MT4ConnectorV2FIX
        from src.connectors.mt4_connector_v3_bridge import MT4ConnectorV3Bridge

    For setup instructions, see:
        - docs/MT4_INTEGRATION_GUIDE.md
        - mql4/README.md (for bridge solution)
    """

    def __init__(self, instance_id: str = "default"):
        """
        Initialize MT4 connector

        This will automatically select and initialize the best available implementation.
        For Mac users and most scenarios, this uses MT4ConnectorV3Bridge.
        """
        super().__init__(instance_id, PlatformType.MT4)

        if DEFAULT_IMPLEMENTATION is None:
            logger.error(
                f"[{self.instance_id}] No MT4 connector implementation available. "
                "Please install one of: mt4_connector_v3_bridge (recommended), "
                "mt4_connector_v1, or mt4_connector_v2_fix. "
                "See docs/MT4_INTEGRATION_GUIDE.md for details."
            )
            self._impl = None
        else:
            logger.info(
                f"[{self.instance_id}] Using {IMPLEMENTATION_NAME} for MT4 connection"
            )
            self._impl = DEFAULT_IMPLEMENTATION(instance_id=instance_id)

    def connect(self, login: int, password: str, server: str, **kwargs) -> bool:
        """
        Connect to MT4

        For MT4ConnectorV3Bridge (default):
            Requires MQL4 Expert Advisor to be running in MT4.
            See mql4/README.md for setup instructions.

        Args:
            login: MT4 account number
            password: Account password
            server: Broker server
            **kwargs: Implementation-specific parameters

        Returns:
            True if connection successful
        """
        if self._impl is None:
            logger.error(
                f"[{self.instance_id}] No MT4 connector implementation available. "
                "See docs/MT4_INTEGRATION_GUIDE.md for setup instructions."
            )
            return False

        return self._impl.connect(login, password, server, **kwargs)
    
    def disconnect(self) -> None:
        """Disconnect from MT4"""
        if self._impl:
            self._impl.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to MT4"""
        if self._impl:
            return self._impl.is_connected()
        return False

    def reconnect(self) -> bool:
        """Reconnect to MT4"""
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
            error_message="No MT4 connector implementation available"
        )

    def close_position(self, ticket: int) -> TradeResult:
        """Close position by ticket"""
        if self._impl:
            return self._impl.close_position(ticket)
        return TradeResult(
            success=False,
            error_message="No MT4 connector implementation available"
        )

    def modify_position(self, ticket: int, sl: Optional[float] = None,
                       tp: Optional[float] = None) -> TradeResult:
        """Modify position SL/TP"""
        if self._impl:
            return self._impl.modify_position(ticket, sl, tp)
        return TradeResult(
            success=False,
            error_message="No MT4 connector implementation available"
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

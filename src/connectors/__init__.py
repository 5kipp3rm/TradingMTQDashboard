"""
Connectors package - MetaTrader integration
Supports both MT4 and MT5 with multiple instances
"""
from .base import (
    BaseMetaTraderConnector,
    PlatformType,
    OrderType,
    ConnectionStatus,
    TickData,
    OHLCBar,
    SymbolInfo,
    Position,
    AccountInfo,
    TradeRequest,
    TradeResult
)
from .mt5_connector import MT5Connector
from .mt4_connector import MT4Connector
from .factory import (
    ConnectorFactory,
    create_mt5_connector,
    create_mt4_connector,
    get_connector
)
from .account_utils import AccountUtils
from .error_descriptions import trade_server_return_code_description, error_description


__all__ = [
    # Base classes and enums
    'BaseMetaTraderConnector',
    'PlatformType',
    'OrderType',
    'ConnectionStatus',
    
    # Data classes
    'TickData',
    'OHLCBar',
    'SymbolInfo',
    'Position',
    'AccountInfo',
    'TradeRequest',
    'TradeResult',
    
    # Connector implementations
    'MT5Connector',
    'MT4Connector',
    
    # Factory
    'ConnectorFactory',
    'create_mt5_connector',
    'create_mt4_connector',
    'get_connector',
    
    # Utilities
    'AccountUtils',
    'trade_server_return_code_description',
    'error_description',
]

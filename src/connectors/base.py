"""
TradingMTQ - Base classes for MetaTrader connectors
Supports both MT4 and MT5 with multiple instances
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PlatformType(Enum):
    """MetaTrader platform types"""
    MT4 = "MT4"
    MT5 = "MT5"


class OrderType(Enum):
    """Order types (compatible with both MT4 and MT5)"""
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


class ConnectionStatus(Enum):
    """Connection states"""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


@dataclass
class TickData:
    """Real-time tick data"""
    symbol: str
    time: datetime
    bid: float
    ask: float
    last: float
    volume: int
    spread: float
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price"""
        return (self.bid + self.ask) / 2


@dataclass
class OHLCBar:
    """OHLC candlestick data"""
    symbol: str
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    real_volume: float = 0.0
    spread: int = 0


@dataclass
class SymbolInfo:
    """Symbol information"""
    name: str
    description: str
    base_currency: str
    quote_currency: str
    digits: int
    point: float
    volume_min: float
    volume_max: float
    volume_step: float
    contract_size: float
    bid: float
    ask: float
    spread: float
    trade_allowed: bool


@dataclass
class Position:
    """Open position"""
    ticket: int
    symbol: str
    type: OrderType
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    swap: float = 0.0
    commission: float = 0.0
    magic: int = 0
    comment: str = ""
    time_open: Optional[datetime] = None
    
    @property
    def pnl_pips(self) -> float:
        """Calculate P&L in pips (simplified)"""
        if self.type == OrderType.BUY:
            return (self.price_current - self.price_open) * 10000
        else:
            return (self.price_open - self.price_current) * 10000


@dataclass
class AccountInfo:
    """Account information"""
    login: int
    server: str
    name: str
    company: str
    currency: str
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    leverage: int
    trade_allowed: bool
    
    @property
    def margin_used_percent(self) -> float:
        """Percentage of margin used"""
        return (self.margin / self.equity * 100) if self.equity > 0 else 0
    
    @property
    def available_for_trading(self) -> float:
        """Available margin for new trades"""
        return self.margin_free


@dataclass
class TradeRequest:
    """Trade order request"""
    symbol: str
    action: OrderType
    volume: float
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: int = 20
    magic: int = 234000
    comment: str = ""


@dataclass
class TradeResult:
    """Trade execution result"""
    success: bool
    order_ticket: Optional[int] = None
    deal_ticket: Optional[int] = None
    volume: float = 0.0
    price: float = 0.0
    comment: str = ""
    error_code: int = 0
    error_message: str = ""


class BaseMetaTraderConnector(ABC):
    """
    Abstract base class for MetaTrader connectors
    Supports both MT4 and MT5 with common interface
    """
    
    def __init__(self, instance_id: str, platform: PlatformType):
        """
        Initialize connector
        
        Args:
            instance_id: Unique identifier for this instance
            platform: Platform type (MT4 or MT5)
        """
        self.instance_id = instance_id
        self.platform = platform
        self.status = ConnectionStatus.DISCONNECTED
        self._connection_params = {}
    
    # Connection Management
    
    @abstractmethod
    def connect(self, login: int, password: str, server: str, **kwargs) -> bool:
        """
        Establish connection to MetaTrader
        
        Args:
            login: Account number
            password: Account password
            server: Broker server name
            **kwargs: Additional platform-specific parameters
            
        Returns:
            True if connected successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to MetaTrader"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected"""
        pass
    
    @abstractmethod
    def reconnect(self) -> bool:
        """Attempt to reconnect using stored credentials"""
        pass
    
    # Account Information
    
    @abstractmethod
    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        pass
    
    # Symbol Operations
    
    @abstractmethod
    def get_symbols(self, group: str = "*") -> List[str]:
        """Get list of available symbols"""
        pass
    
    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get detailed symbol information"""
        pass
    
    @abstractmethod
    def select_symbol(self, symbol: str, enable: bool = True) -> bool:
        """Enable/disable symbol in Market Watch"""
        pass
    
    # Market Data
    
    @abstractmethod
    def get_tick(self, symbol: str) -> Optional[TickData]:
        """Get latest tick for symbol"""
        pass
    
    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str, count: int, 
                 start_pos: int = 0) -> List[OHLCBar]:
        """Get historical OHLC bars"""
        pass
    
    # Trading Operations
    
    @abstractmethod
    def send_order(self, request: TradeRequest) -> TradeResult:
        """Send trade order"""
        pass
    
    @abstractmethod
    def close_position(self, ticket: int) -> TradeResult:
        """Close open position"""
        pass
    
    @abstractmethod
    def modify_position(self, ticket: int, sl: Optional[float] = None, 
                       tp: Optional[float] = None) -> TradeResult:
        """Modify position SL/TP"""
        pass
    
    # Position Management
    
    @abstractmethod
    def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """Get open positions"""
        pass
    
    @abstractmethod
    def get_position_by_ticket(self, ticket: int) -> Optional[Position]:
        """Get specific position by ticket"""
        pass
    
    # Utility Methods
    
    def get_platform_type(self) -> PlatformType:
        """Get platform type"""
        return self.platform
    
    def get_instance_id(self) -> str:
        """Get instance identifier"""
        return self.instance_id
    
    def get_status(self) -> ConnectionStatus:
        """Get current connection status"""
        return self.status
    
    def __str__(self) -> str:
        return f"{self.platform.value}Connector(instance={self.instance_id}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return self.__str__()

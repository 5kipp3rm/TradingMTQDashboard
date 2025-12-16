"""
MT4 Connector - Bridge Implementation via HTTP

This connector communicates with an MQL4 Expert Advisor running inside MT4.
The EA exposes an HTTP server that the Python connector calls.

Installation:
    1. Copy mt4_bridge_server.mq4 to MT4's Experts folder
    2. Compile the EA in MetaEditor
    3. Attach the EA to any chart in MT4
    4. Ensure AutoTrading is enabled

Configuration:
    - Default port: 8080
    - Default host: localhost
    - Configure in EA settings

Requirements:
    pip install requests
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .base import (
    BaseMetaTraderConnector, PlatformType, OrderType, ConnectionStatus,
    TickData, OHLCBar, SymbolInfo, Position, AccountInfo,
    TradeRequest, TradeResult
)


logger = logging.getLogger(__name__)


class MT4ConnectorV3Bridge(BaseMetaTraderConnector):
    """
    MetaTrader 4 connector using HTTP bridge to MQL4 Expert Advisor

    This implementation communicates with an MT4 Expert Advisor via HTTP.
    The EA must be running in MT4 for this connector to work.

    Recommended for Mac users and situations where direct API access is not available.
    """

    def __init__(self, instance_id: str = "default", host: str = "localhost", port: int = 8080):
        """
        Initialize MT4 bridge connector

        Args:
            instance_id: Unique identifier for this connector instance
            host: Host where MT4 EA is running (default: localhost)
            port: Port where MT4 EA is listening (default: 8080)
        """
        super().__init__(instance_id, PlatformType.MT4)

        if not REQUESTS_AVAILABLE:
            logger.error(
                f"[{self.instance_id}] requests package not installed. "
                "Install with: pip install requests"
            )
            self.status = ConnectionStatus.ERROR

        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}"
        self._session = requests.Session() if REQUESTS_AVAILABLE else None
        self._timeout = 10  # Request timeout in seconds

        # Account credentials
        self._login: Optional[int] = None
        self._password: Optional[str] = None
        self._server: Optional[str] = None

        logger.info(
            f"[{self.instance_id}] MT4ConnectorV3Bridge initialized",
            extra={'base_url': self._base_url}
        )

    def connect(self, login: int, password: str, server: str, **kwargs) -> bool:
        """
        Connect to MT4 via bridge

        Note: The EA must already be connected to MT4. This method verifies
        that the bridge is accessible and that MT4 is connected.

        Args:
            login: MT4 account number
            password: Account password (stored for potential reconnection)
            server: Broker server (stored for reference)
            **kwargs: Additional parameters
                - timeout: Request timeout in seconds (default: 10)

        Returns:
            True if bridge is accessible and MT4 is connected
        """
        if not REQUESTS_AVAILABLE:
            logger.error(f"[{self.instance_id}] requests package not available")
            self.status = ConnectionStatus.ERROR
            return False

        self._timeout = kwargs.get('timeout', 10)
        self._login = login
        self._password = password
        self._server = server

        logger.info(
            f"[{self.instance_id}] Connecting to MT4 bridge",
            extra={
                'login': login,
                'server': server,
                'base_url': self._base_url
            }
        )

        try:
            # Check if bridge is accessible
            response = self._request('GET', '/ping')

            if not response or not response.get('success'):
                logger.error(
                    f"[{self.instance_id}] MT4 bridge not accessible. "
                    "Ensure EA is running in MT4."
                )
                self.status = ConnectionStatus.ERROR
                return False

            # Check if MT4 is connected
            status_response = self._request('GET', '/status')

            if not status_response or not status_response.get('success'):
                logger.error(f"[{self.instance_id}] Failed to get MT4 status")
                self.status = ConnectionStatus.ERROR
                return False

            is_connected = status_response.get('data', {}).get('is_connected', False)

            if not is_connected:
                logger.error(
                    f"[{self.instance_id}] MT4 is not connected. "
                    "Please connect MT4 to your broker first."
                )
                self.status = ConnectionStatus.DISCONNECTED
                return False

            # Verify account matches
            account_info = status_response.get('data', {}).get('account', {})
            mt4_login = account_info.get('login')

            if mt4_login and mt4_login != login:
                logger.warning(
                    f"[{self.instance_id}] Account mismatch: "
                    f"Expected {login}, MT4 shows {mt4_login}"
                )

            self.status = ConnectionStatus.CONNECTED

            logger.info(
                f"[{self.instance_id}] Successfully connected to MT4 bridge",
                extra={
                    'login': mt4_login,
                    'server': account_info.get('server'),
                    'balance': account_info.get('balance')
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"[{self.instance_id}] MT4 bridge connection error: {str(e)}",
                exc_info=True
            )
            self.status = ConnectionStatus.ERROR
            return False

    def disconnect(self) -> None:
        """
        Disconnect from MT4 bridge

        Note: This doesn't disconnect MT4 itself, just closes the Python connection.
        """
        logger.info(f"[{self.instance_id}] Disconnecting from MT4 bridge")
        self.status = ConnectionStatus.DISCONNECTED

        if self._session:
            self._session.close()
            self._session = requests.Session() if REQUESTS_AVAILABLE else None

        logger.info(f"[{self.instance_id}] Successfully disconnected from MT4 bridge")

    def is_connected(self) -> bool:
        """Check if connected to MT4 bridge"""
        if self.status != ConnectionStatus.CONNECTED:
            return False

        try:
            response = self._request('GET', '/ping', timeout=2)
            return response is not None and response.get('success', False)
        except Exception:
            return False

    def reconnect(self) -> bool:
        """Reconnect to MT4 bridge"""
        logger.info(f"[{self.instance_id}] Reconnecting to MT4 bridge")
        self.disconnect()
        time.sleep(1)

        if self._login and self._password and self._server:
            return self.connect(self._login, self._password, self._server)

        return False

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                 timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to MT4 bridge

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/account/info')
            data: Request data (for POST/PUT)
            timeout: Request timeout (default: self._timeout)

        Returns:
            Response JSON or None if request failed
        """
        if not self._session:
            return None

        timeout = timeout or self._timeout
        url = f"{self._base_url}{endpoint}"

        try:
            if method == 'GET':
                response = self._session.get(url, timeout=timeout, params=data)
            elif method == 'POST':
                response = self._session.post(url, timeout=timeout, json=data)
            elif method == 'PUT':
                response = self._session.put(url, timeout=timeout, json=data)
            elif method == 'DELETE':
                response = self._session.delete(url, timeout=timeout, json=data)
            else:
                logger.error(f"[{self.instance_id}] Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            logger.error(
                f"[{self.instance_id}] Connection refused. "
                f"Ensure MT4 EA is running and listening on {self._base_url}"
            )
            return None
        except requests.exceptions.Timeout:
            logger.error(f"[{self.instance_id}] Request timeout")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"[{self.instance_id}] HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Request error: {str(e)}",
                exc_info=True
            )
            return None

    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        if not self.is_connected():
            return None

        try:
            response = self._request('GET', '/account/info')

            if not response or not response.get('success'):
                return None

            data = response.get('data', {})

            return AccountInfo(
                login=data.get('login', 0),
                server=data.get('server', ''),
                name=data.get('name', ''),
                balance=float(data.get('balance', 0.0)),
                equity=float(data.get('equity', 0.0)),
                margin=float(data.get('margin', 0.0)),
                margin_free=float(data.get('margin_free', 0.0)),
                margin_level=float(data.get('margin_level', 0.0)),
                profit=float(data.get('profit', 0.0)),
                currency=data.get('currency', 'USD'),
                leverage=int(data.get('leverage', 0)),
                company=data.get('company', '')
            )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error getting account info: {str(e)}",
                exc_info=True
            )
            return None

    def get_symbols(self, group: str = "*") -> List[str]:
        """Get available symbols"""
        if not self.is_connected():
            return []

        try:
            response = self._request('GET', '/symbols', data={'group': group})

            if not response or not response.get('success'):
                return []

            return response.get('data', {}).get('symbols', [])
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error getting symbols: {str(e)}",
                exc_info=True
            )
            return []

    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get symbol information"""
        if not self.is_connected():
            return None

        try:
            response = self._request('GET', f'/symbols/{symbol}')

            if not response or not response.get('success'):
                return None

            data = response.get('data', {})

            return SymbolInfo(
                name=data.get('name', symbol),
                description=data.get('description', ''),
                point=float(data.get('point', 0.0)),
                digits=int(data.get('digits', 0)),
                trade_contract_size=float(data.get('contract_size', 0.0)),
                trade_tick_value=float(data.get('tick_value', 0.0)),
                trade_tick_size=float(data.get('tick_size', 0.0)),
                min_volume=float(data.get('min_volume', 0.01)),
                max_volume=float(data.get('max_volume', 100.0)),
                volume_step=float(data.get('volume_step', 0.01)),
                bid=float(data.get('bid', 0.0)),
                ask=float(data.get('ask', 0.0)),
                spread=int(data.get('spread', 0))
            )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error getting symbol info: {str(e)}",
                exc_info=True
            )
            return None

    def select_symbol(self, symbol: str, enable: bool = True) -> bool:
        """Select symbol in Market Watch"""
        if not self.is_connected():
            return False

        try:
            response = self._request('POST', f'/symbols/{symbol}/select', data={'enable': enable})
            return response is not None and response.get('success', False)
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error selecting symbol: {str(e)}",
                exc_info=True
            )
            return False

    def get_tick(self, symbol: str) -> Optional[TickData]:
        """Get last tick for symbol"""
        if not self.is_connected():
            return None

        try:
            response = self._request('GET', f'/ticks/{symbol}')

            if not response or not response.get('success'):
                return None

            data = response.get('data', {})

            return TickData(
                time=datetime.fromisoformat(data.get('time')) if data.get('time') else datetime.now(),
                bid=float(data.get('bid', 0.0)),
                ask=float(data.get('ask', 0.0)),
                last=float(data.get('last', 0.0)),
                volume=int(data.get('volume', 0))
            )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error getting tick: {str(e)}",
                exc_info=True
            )
            return None

    def get_bars(self, symbol: str, timeframe: str, count: int,
                 start_pos: int = 0) -> List[OHLCBar]:
        """Get historical bars"""
        if not self.is_connected():
            return []

        try:
            response = self._request('GET', f'/bars/{symbol}', data={
                'timeframe': timeframe,
                'count': count,
                'start_pos': start_pos
            })

            if not response or not response.get('success'):
                return []

            bars_data = response.get('data', {}).get('bars', [])

            return [
                OHLCBar(
                    time=datetime.fromisoformat(bar['time']) if bar.get('time') else datetime.now(),
                    open=float(bar.get('open', 0.0)),
                    high=float(bar.get('high', 0.0)),
                    low=float(bar.get('low', 0.0)),
                    close=float(bar.get('close', 0.0)),
                    tick_volume=int(bar.get('tick_volume', 0)),
                    spread=int(bar.get('spread', 0)),
                    real_volume=int(bar.get('real_volume', 0))
                )
                for bar in bars_data
            ]
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error getting bars: {str(e)}",
                exc_info=True
            )
            return []

    def send_order(self, request: TradeRequest) -> TradeResult:
        """Send trading order"""
        if not self.is_connected():
            return TradeResult(
                success=False,
                error_message="Not connected to MT4 bridge"
            )

        try:
            order_data = {
                'symbol': request.symbol,
                'order_type': request.order_type.name,
                'volume': request.volume,
                'price': request.price or 0.0,
                'sl': request.sl or 0.0,
                'tp': request.tp or 0.0,
                'deviation': request.deviation or 10,
                'magic': request.magic or 0,
                'comment': request.comment or ''
            }

            response = self._request('POST', '/orders', data=order_data)

            if not response or not response.get('success'):
                return TradeResult(
                    success=False,
                    error_message=response.get('message', 'Order failed') if response else 'Request failed'
                )

            data = response.get('data', {})

            return TradeResult(
                success=True,
                order=data.get('order'),
                deal=data.get('deal'),
                volume=data.get('volume'),
                price=data.get('price'),
                comment=data.get('comment')
            )

        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error sending order: {str(e)}",
                exc_info=True
            )
            return TradeResult(
                success=False,
                error_message=str(e)
            )

    def close_position(self, ticket: int) -> TradeResult:
        """Close position by ticket"""
        if not self.is_connected():
            return TradeResult(
                success=False,
                error_message="Not connected to MT4 bridge"
            )

        try:
            response = self._request('DELETE', f'/positions/{ticket}')

            if not response or not response.get('success'):
                return TradeResult(
                    success=False,
                    error_message=response.get('message', 'Close failed') if response else 'Request failed'
                )

            return TradeResult(success=True)

        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error closing position: {str(e)}",
                exc_info=True
            )
            return TradeResult(
                success=False,
                error_message=str(e)
            )

    def modify_position(self, ticket: int, sl: Optional[float] = None,
                       tp: Optional[float] = None) -> TradeResult:
        """Modify position SL/TP"""
        if not self.is_connected():
            return TradeResult(
                success=False,
                error_message="Not connected to MT4 bridge"
            )

        try:
            modify_data = {}
            if sl is not None:
                modify_data['sl'] = sl
            if tp is not None:
                modify_data['tp'] = tp

            response = self._request('PUT', f'/positions/{ticket}', data=modify_data)

            if not response or not response.get('success'):
                return TradeResult(
                    success=False,
                    error_message=response.get('message', 'Modify failed') if response else 'Request failed'
                )

            return TradeResult(success=True)

        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error modifying position: {str(e)}",
                exc_info=True
            )
            return TradeResult(
                success=False,
                error_message=str(e)
            )

    def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """Get open positions"""
        if not self.is_connected():
            return []

        try:
            params = {'symbol': symbol} if symbol else None
            response = self._request('GET', '/positions', data=params)

            if not response or not response.get('success'):
                return []

            positions_data = response.get('data', {}).get('positions', [])

            return [
                Position(
                    ticket=int(pos.get('ticket', 0)),
                    symbol=pos.get('symbol', ''),
                    type=OrderType[pos.get('type', 'BUY')] if pos.get('type') else OrderType.BUY,
                    volume=float(pos.get('volume', 0.0)),
                    price_open=float(pos.get('price_open', 0.0)),
                    price_current=float(pos.get('price_current', 0.0)),
                    sl=float(pos.get('sl', 0.0)),
                    tp=float(pos.get('tp', 0.0)),
                    profit=float(pos.get('profit', 0.0)),
                    swap=float(pos.get('swap', 0.0)),
                    commission=float(pos.get('commission', 0.0)),
                    magic=int(pos.get('magic', 0)),
                    comment=pos.get('comment', ''),
                    time=datetime.fromisoformat(pos.get('time')) if pos.get('time') else datetime.now()
                )
                for pos in positions_data
            ]
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error getting positions: {str(e)}",
                exc_info=True
            )
            return []

    def get_position_by_ticket(self, ticket: int) -> Optional[Position]:
        """Get position by ticket"""
        positions = self.get_positions()
        return next((p for p in positions if p.ticket == ticket), None)

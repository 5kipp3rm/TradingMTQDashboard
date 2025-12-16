"""
MT5 Connector Bridge - HTTP Bridge Solution for MetaTrader 5

This connector communicates with MT5 via HTTP REST API exposed by an MQL5 Expert Advisor.
This approach works on any platform (Windows, Mac, Linux) and doesn't require the
MetaTrader5 Python package.

Setup:
1. Copy mql5/mt5_bridge_server.mq5 to your MT5 Experts folder
2. Compile the EA in MetaEditor
3. Attach EA to any chart in MT5
4. EA will start HTTP server on localhost:8080 (configurable)
5. Python connector connects via HTTP

See: mql5/README.md for detailed setup instructions
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

from .base import (
    BaseMetaTraderConnector, PlatformType, OrderType, ConnectionStatus,
    TickData, OHLCBar, SymbolInfo, Position, AccountInfo,
    TradeRequest, TradeResult
)


logger = logging.getLogger(__name__)


class MT5ConnectorBridge(BaseMetaTraderConnector):
    """
    MetaTrader 5 connector using HTTP bridge (MQL5 EA)

    This implementation communicates with MT5 via HTTP REST API.
    Requires MT5 Expert Advisor (mt5_bridge_server.mq5) to be running.

    Advantages:
    - Works on any platform (Windows, Mac, Linux)
    - No Python package dependencies
    - Simple HTTP communication
    - Easy to debug with curl/browser
    - No broker restrictions

    Requirements:
    - MT5 terminal must be running
    - mt5_bridge_server.mq5 EA must be attached to a chart
    - EA must have AutoTrading enabled
    - Python requests package (pip install requests)
    """

    def __init__(self, instance_id: str = "default", host: str = "localhost", port: int = 8080):
        """
        Initialize MT5 bridge connector

        Args:
            instance_id: Unique identifier for this connector instance
            host: MT5 bridge server host (default: localhost)
            port: MT5 bridge server port (default: 8080)
        """
        super().__init__(instance_id, PlatformType.MT5)
        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}"
        self._session = requests.Session()
        self._session.timeout = 5  # 5 second timeout for HTTP requests

        logger.info(
            f"[{self.instance_id}] MT5ConnectorBridge initialized for {self._base_url}"
        )

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to MT5 bridge server

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint (e.g., '/ping', '/account/info')
            data: Optional request data for POST requests

        Returns:
            Response JSON as dictionary

        Raises:
            ConnectionError: If cannot connect to MT5 bridge
            RequestException: If request fails
        """
        url = f"{self._base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = self._session.get(url, timeout=5)
            elif method.upper() == 'POST':
                response = self._session.post(url, json=data, timeout=5)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except ConnectionError as e:
            logger.error(
                f"[{self.instance_id}] Connection refused. "
                f"Ensure MT5 EA is running and listening on {self._base_url}"
            )
            raise ConnectionError(
                f"Cannot connect to MT5 bridge at {self._base_url}. "
                "Ensure MT5 is running and mt5_bridge_server.mq5 EA is attached to a chart."
            ) from e
        except Timeout as e:
            logger.error(
                f"[{self.instance_id}] Request timeout to {url}"
            )
            raise Timeout(f"Request to MT5 bridge timed out: {url}") from e
        except RequestException as e:
            logger.error(
                f"[{self.instance_id}] Request failed: {url} - {str(e)}"
            )
            raise

    def connect(self, login: int, password: str, server: str, **kwargs) -> bool:
        """
        Connect to MT5 via bridge

        The bridge doesn't handle MT5 login - MT5 must already be logged in.
        This method verifies the bridge is accessible and MT5 is connected.

        Args:
            login: MT5 account number (not used by bridge, for logging only)
            password: Account password (not used by bridge)
            server: Broker server (not used by bridge, for logging only)
            **kwargs: Additional parameters (host, port can override defaults)

        Returns:
            True if bridge is accessible and MT5 is connected
        """
        try:
            # Override host/port if provided
            if 'host' in kwargs:
                self._host = kwargs['host']
                self._base_url = f"http://{self._host}:{self._port}"
            if 'port' in kwargs:
                self._port = kwargs['port']
                self._base_url = f"http://{self._host}:{self._port}"

            logger.info(
                f"[{self.instance_id}] Connecting to MT5 bridge at {self._base_url} "
                f"for account #{login}"
            )

            # Ping the bridge
            ping_response = self._request('GET', '/ping')
            if not ping_response.get('success'):
                logger.error(
                    f"[{self.instance_id}] Bridge ping failed"
                )
                self._status = ConnectionStatus.DISCONNECTED
                return False

            logger.info(
                f"[{self.instance_id}] Bridge is accessible"
            )

            # Check MT5 terminal status
            status_response = self._request('GET', '/status')
            if not status_response.get('success'):
                logger.error(
                    f"[{self.instance_id}] MT5 status check failed"
                )
                self._status = ConnectionStatus.DISCONNECTED
                return False

            status_data = status_response.get('data', {})
            terminal_connected = status_data.get('terminal_connected', False)

            if not terminal_connected:
                logger.error(
                    f"[{self.instance_id}] MT5 terminal is not connected to broker. "
                    "Please login to MT5 first."
                )
                self._status = ConnectionStatus.DISCONNECTED
                return False

            # Verify account matches
            account_info_response = self._request('GET', '/account/info')
            if account_info_response.get('success'):
                account_data = account_info_response.get('data', {})
                bridge_login = account_data.get('login', 0)

                if bridge_login != login:
                    logger.warning(
                        f"[{self.instance_id}] Account mismatch: "
                        f"Expected #{login}, but MT5 is logged in as #{bridge_login}"
                    )

                logger.info(
                    f"[{self.instance_id}] Connected to MT5 account #{bridge_login} "
                    f"on {account_data.get('server', 'unknown')}"
                )

            self._status = ConnectionStatus.CONNECTED
            logger.info(
                f"[{self.instance_id}] Successfully connected to MT5 via bridge"
            )
            return True

        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Connection failed: {str(e)}"
            )
            self._status = ConnectionStatus.DISCONNECTED
            return False

    def disconnect(self) -> None:
        """
        Disconnect from MT5 bridge

        Note: This doesn't log out of MT5, just closes the HTTP session.
        """
        logger.info(
            f"[{self.instance_id}] Disconnecting from MT5 bridge"
        )
        self._session.close()
        self._status = ConnectionStatus.DISCONNECTED

    def is_connected(self) -> bool:
        """
        Check if connected to MT5 bridge

        Returns:
            True if bridge is accessible and MT5 is connected
        """
        if self._status != ConnectionStatus.CONNECTED:
            return False

        try:
            response = self._request('GET', '/status')
            if response.get('success'):
                status_data = response.get('data', {})
                return status_data.get('terminal_connected', False)
            return False
        except Exception:
            self._status = ConnectionStatus.DISCONNECTED
            return False

    def reconnect(self) -> bool:
        """
        Reconnect to MT5 bridge

        Returns:
            True if reconnection successful
        """
        logger.info(
            f"[{self.instance_id}] Reconnecting to MT5 bridge"
        )
        self.disconnect()
        # Bridge doesn't need login credentials to reconnect
        return self.connect(0, "", "")

    def get_account_info(self) -> Optional[AccountInfo]:
        """
        Get MT5 account information

        Returns:
            AccountInfo object or None if request fails
        """
        try:
            response = self._request('GET', '/account/info')
            if not response.get('success'):
                return None

            data = response.get('data', {})

            return AccountInfo(
                login=data.get('login', 0),
                server=data.get('server', ''),
                balance=data.get('balance', 0.0),
                equity=data.get('equity', 0.0),
                margin=data.get('margin', 0.0),
                margin_free=data.get('margin_free', 0.0),
                margin_level=data.get('margin_level', 0.0),
                profit=data.get('profit', 0.0),
                leverage=data.get('leverage', 0),
                currency=data.get('currency', 'USD'),
                name=data.get('name', ''),
                trade_allowed=data.get('trade_allowed', False),
                trade_expert=data.get('trade_expert', False)
            )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to get account info: {str(e)}"
            )
            return None

    def get_symbols(self, group: str = "*") -> List[str]:
        """
        Get available symbols

        Args:
            group: Symbol group filter (e.g., "*", "EURUSD*", "Major*")

        Returns:
            List of symbol names
        """
        try:
            response = self._request('GET', f'/symbols?group={group}')
            if response.get('success'):
                return response.get('data', {}).get('symbols', [])
            return []
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to get symbols: {str(e)}"
            )
            return []

    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Get symbol information

        Args:
            symbol: Symbol name (e.g., "EURUSD")

        Returns:
            SymbolInfo object or None if request fails
        """
        try:
            response = self._request('GET', f'/symbol/info?symbol={symbol}')
            if not response.get('success'):
                return None

            data = response.get('data', {})

            return SymbolInfo(
                name=data.get('name', symbol),
                description=data.get('description', ''),
                point=data.get('point', 0.00001),
                digits=data.get('digits', 5),
                spread=data.get('spread', 0),
                trade_contract_size=data.get('trade_contract_size', 100000.0),
                trade_tick_value=data.get('trade_tick_value', 1.0),
                trade_tick_size=data.get('trade_tick_size', 0.00001),
                volume_min=data.get('volume_min', 0.01),
                volume_max=data.get('volume_max', 100.0),
                volume_step=data.get('volume_step', 0.01),
                currency_base=data.get('currency_base', ''),
                currency_profit=data.get('currency_profit', ''),
                currency_margin=data.get('currency_margin', ''),
                trade_mode=data.get('trade_mode', 0),
                visible=data.get('visible', True),
                select=data.get('select', True)
            )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to get symbol info for {symbol}: {str(e)}"
            )
            return None

    def select_symbol(self, symbol: str, enable: bool = True) -> bool:
        """
        Add/remove symbol in Market Watch

        Args:
            symbol: Symbol name
            enable: True to add, False to remove

        Returns:
            True if successful
        """
        try:
            response = self._request('POST', '/symbol/select', {
                'symbol': symbol,
                'enable': enable
            })
            return response.get('success', False)
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to select symbol {symbol}: {str(e)}"
            )
            return False

    def get_tick(self, symbol: str) -> Optional[TickData]:
        """
        Get last tick for symbol

        Args:
            symbol: Symbol name

        Returns:
            TickData object or None if request fails
        """
        try:
            response = self._request('GET', f'/tick?symbol={symbol}')
            if not response.get('success'):
                return None

            data = response.get('data', {})

            return TickData(
                time=datetime.fromtimestamp(data.get('time', 0)),
                bid=data.get('bid', 0.0),
                ask=data.get('ask', 0.0),
                last=data.get('last', 0.0),
                volume=data.get('volume', 0)
            )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to get tick for {symbol}: {str(e)}"
            )
            return None

    def get_bars(self, symbol: str, timeframe: str, count: int,
                 start_pos: int = 0) -> List[OHLCBar]:
        """
        Get historical bars

        Args:
            symbol: Symbol name
            timeframe: Timeframe (e.g., "M1", "M5", "H1", "D1")
            count: Number of bars
            start_pos: Starting position (0 = most recent)

        Returns:
            List of OHLCBar objects
        """
        try:
            response = self._request('GET',
                f'/bars?symbol={symbol}&timeframe={timeframe}&count={count}&start_pos={start_pos}'
            )
            if not response.get('success'):
                return []

            bars_data = response.get('data', {}).get('bars', [])
            bars = []

            for bar_data in bars_data:
                bars.append(OHLCBar(
                    time=datetime.fromtimestamp(bar_data.get('time', 0)),
                    open=bar_data.get('open', 0.0),
                    high=bar_data.get('high', 0.0),
                    low=bar_data.get('low', 0.0),
                    close=bar_data.get('close', 0.0),
                    tick_volume=bar_data.get('tick_volume', 0),
                    real_volume=bar_data.get('real_volume', 0),
                    spread=bar_data.get('spread', 0)
                ))

            return bars
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to get bars for {symbol}: {str(e)}"
            )
            return []

    def send_order(self, request: TradeRequest) -> TradeResult:
        """
        Send trading order

        Args:
            request: TradeRequest object with order parameters

        Returns:
            TradeResult with execution details
        """
        try:
            order_data = {
                'action': 'DEAL',
                'symbol': request.symbol,
                'volume': request.volume,
                'type': request.order_type.name,
                'price': request.price,
                'sl': request.sl,
                'tp': request.tp,
                'deviation': request.deviation,
                'magic': request.magic,
                'comment': request.comment
            }

            response = self._request('POST', '/order/send', order_data)

            if response.get('success'):
                data = response.get('data', {})
                return TradeResult(
                    success=True,
                    order=data.get('order', 0),
                    deal=data.get('deal', 0),
                    volume=data.get('volume', 0.0),
                    price=data.get('price', 0.0),
                    comment=data.get('comment', ''),
                    request_id=data.get('request_id', 0),
                    retcode=data.get('retcode', 0)
                )
            else:
                return TradeResult(
                    success=False,
                    error_message=response.get('message', 'Order failed'),
                    retcode=response.get('data', {}).get('retcode', 0)
                )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to send order: {str(e)}"
            )
            return TradeResult(
                success=False,
                error_message=f"Exception: {str(e)}"
            )

    def close_position(self, ticket: int) -> TradeResult:
        """
        Close position by ticket

        Args:
            ticket: Position ticket number

        Returns:
            TradeResult with execution details
        """
        try:
            response = self._request('POST', '/position/close', {
                'ticket': ticket
            })

            if response.get('success'):
                data = response.get('data', {})
                return TradeResult(
                    success=True,
                    order=data.get('order', 0),
                    deal=data.get('deal', 0),
                    volume=data.get('volume', 0.0),
                    price=data.get('price', 0.0),
                    comment=data.get('comment', ''),
                    retcode=data.get('retcode', 0)
                )
            else:
                return TradeResult(
                    success=False,
                    error_message=response.get('message', 'Close failed'),
                    retcode=response.get('data', {}).get('retcode', 0)
                )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to close position: {str(e)}"
            )
            return TradeResult(
                success=False,
                error_message=f"Exception: {str(e)}"
            )

    def modify_position(self, ticket: int, sl: Optional[float] = None,
                       tp: Optional[float] = None) -> TradeResult:
        """
        Modify position SL/TP

        Args:
            ticket: Position ticket number
            sl: New stop loss (None = don't change)
            tp: New take profit (None = don't change)

        Returns:
            TradeResult with execution details
        """
        try:
            modify_data = {'ticket': ticket}
            if sl is not None:
                modify_data['sl'] = sl
            if tp is not None:
                modify_data['tp'] = tp

            response = self._request('POST', '/position/modify', modify_data)

            if response.get('success'):
                data = response.get('data', {})
                return TradeResult(
                    success=True,
                    order=data.get('order', 0),
                    retcode=data.get('retcode', 0)
                )
            else:
                return TradeResult(
                    success=False,
                    error_message=response.get('message', 'Modify failed'),
                    retcode=response.get('data', {}).get('retcode', 0)
                )
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to modify position: {str(e)}"
            )
            return TradeResult(
                success=False,
                error_message=f"Exception: {str(e)}"
            )

    def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """
        Get open positions

        Args:
            symbol: Optional symbol filter

        Returns:
            List of Position objects
        """
        try:
            endpoint = '/positions'
            if symbol:
                endpoint += f'?symbol={symbol}'

            response = self._request('GET', endpoint)
            if not response.get('success'):
                return []

            positions_data = response.get('data', {}).get('positions', [])
            positions = []

            for pos_data in positions_data:
                positions.append(Position(
                    ticket=pos_data.get('ticket', 0),
                    time=datetime.fromtimestamp(pos_data.get('time', 0)),
                    symbol=pos_data.get('symbol', ''),
                    type=OrderType[pos_data.get('type', 'BUY')],
                    volume=pos_data.get('volume', 0.0),
                    price_open=pos_data.get('price_open', 0.0),
                    price_current=pos_data.get('price_current', 0.0),
                    sl=pos_data.get('sl', 0.0),
                    tp=pos_data.get('tp', 0.0),
                    profit=pos_data.get('profit', 0.0),
                    swap=pos_data.get('swap', 0.0),
                    commission=pos_data.get('commission', 0.0),
                    magic=pos_data.get('magic', 0),
                    comment=pos_data.get('comment', '')
                ))

            return positions
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Failed to get positions: {str(e)}"
            )
            return []

    def get_position_by_ticket(self, ticket: int) -> Optional[Position]:
        """
        Get position by ticket

        Args:
            ticket: Position ticket number

        Returns:
            Position object or None if not found
        """
        positions = self.get_positions()
        for position in positions:
            if position.ticket == ticket:
                return position
        return None

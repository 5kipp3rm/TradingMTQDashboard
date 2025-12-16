"""
MT5 Connector - MetaTrader 5 implementation
Production-ready with error handling and connection pooling

Refactored to use Phase 0 patterns:
- Custom exceptions for specific error types
- Structured JSON logging with correlation IDs
- Automatic retry decorators
- Error context preservation
"""
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    # MetaTrader5 is Windows-only, mock it for development on macOS/Linux
    MT5_AVAILABLE = False
    import sys
    from types import ModuleType

    # Create a mock MT5 module for development
    mt5 = ModuleType('MetaTrader5')
    # Timeframes
    mt5.TIMEFRAME_M1 = 1
    mt5.TIMEFRAME_M5 = 5
    mt5.TIMEFRAME_M15 = 15
    mt5.TIMEFRAME_M30 = 30
    mt5.TIMEFRAME_H1 = 60
    mt5.TIMEFRAME_H4 = 240
    mt5.TIMEFRAME_D1 = 1440
    mt5.TIMEFRAME_W1 = 10080
    mt5.TIMEFRAME_MN1 = 43200
    # Order types
    mt5.ORDER_TYPE_BUY = 0
    mt5.ORDER_TYPE_SELL = 1
    mt5.ORDER_TYPE_BUY_LIMIT = 2
    mt5.ORDER_TYPE_SELL_LIMIT = 3
    mt5.ORDER_TYPE_BUY_STOP = 4
    mt5.ORDER_TYPE_SELL_STOP = 5
    # Trade actions
    mt5.TRADE_ACTION_DEAL = 1
    mt5.TRADE_ACTION_PENDING = 5
    mt5.TRADE_ACTION_SLTP = 2
    mt5.TRADE_ACTION_MODIFY = 3
    mt5.TRADE_ACTION_REMOVE = 4
    # Order filling types
    mt5.ORDER_FILLING_FOK = 0
    mt5.ORDER_FILLING_IOC = 1
    mt5.ORDER_FILLING_RETURN = 2
    # Order time types
    mt5.ORDER_TIME_GTC = 0
    mt5.ORDER_TIME_SPECIFIED = 2
    mt5.ORDER_TIME_SPECIFIED_DAY = 3
    # Trade return codes
    mt5.TRADE_RETCODE_DONE = 10009
    sys.modules['MetaTrader5'] = mt5
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

# Phase 0 imports - NEW
from src.exceptions import (
    ConnectionError, AuthenticationError, InvalidSymbolError,
    OrderExecutionError, OrderTimeoutError, DataNotAvailableError,
    build_connection_context, build_order_context
)
from src.utils.structured_logger import StructuredLogger, CorrelationContext
from src.utils.error_handlers import handle_mt5_errors

from .base import (
    BaseMetaTraderConnector, PlatformType, OrderType, ConnectionStatus,
    TickData, OHLCBar, SymbolInfo, Position, AccountInfo,
    TradeRequest, TradeResult
)
from .error_descriptions import trade_server_return_code_description, error_description


logger = StructuredLogger(__name__)


class MT5Connector(BaseMetaTraderConnector):
    """
    MetaTrader 5 connector implementation
    Supports multiple instances with proper resource management

    Uses Phase 0 patterns:
    - Raises specific exceptions instead of returning False/None
    - Structured logging with correlation IDs
    - Automatic retry for transient failures
    """

    # MT5 Timeframe mapping
    TIMEFRAMES = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1,
        'W1': mt5.TIMEFRAME_W1,
        'MN1': mt5.TIMEFRAME_MN1,
    }

    # MT5 Order type mapping
    ORDER_TYPE_MAP = {
        OrderType.BUY: mt5.ORDER_TYPE_BUY,
        OrderType.SELL: mt5.ORDER_TYPE_SELL,
        OrderType.BUY_LIMIT: mt5.ORDER_TYPE_BUY_LIMIT,
        OrderType.SELL_LIMIT: mt5.ORDER_TYPE_SELL_LIMIT,
        OrderType.BUY_STOP: mt5.ORDER_TYPE_BUY_STOP,
        OrderType.SELL_STOP: mt5.ORDER_TYPE_SELL_STOP,
    }

    def __init__(self, instance_id: str = "default"):
        """
        Initialize MT5 connector

        Args:
            instance_id: Unique identifier for this instance
        """
        super().__init__(instance_id, PlatformType.MT5)
        self._initialized = False
        self._no_bars_count = {}  # Track consecutive no-bar warnings per symbol
        logger.info("MT5Connector initialized", instance_id=instance_id)

    @handle_mt5_errors(retry_count=3, retry_delay=2.0)
    def connect(self, login: int, password: str, server: str,
                timeout: int = 60000, portable: bool = False, **kwargs) -> bool:
        """
        Connect to MT5 terminal

        Args:
            login: Account number
            password: Account password
            server: Broker server
            timeout: Connection timeout in milliseconds
            portable: Use portable mode

        Returns:
            True if connected successfully

        Raises:
            ConnectionError: If MT5 initialization fails
            AuthenticationError: If credentials are invalid
        """
        with CorrelationContext():
            self.status = ConnectionStatus.CONNECTING
            logger.info(
                "Connecting to MT5",
                server=server,
                login=login,
                timeout=timeout,
                instance_id=self.instance_id
            )

            # Initialize MT5
            if not self._initialized:
                if not mt5.initialize(
                    login=login,
                    password=password,
                    server=server,
                    timeout=timeout,
                    portable=portable
                ):
                    error = mt5.last_error()
                    error_code = error[0] if isinstance(error, tuple) else error

                    # Check for authentication errors
                    if error_code == 10004:  # Invalid credentials
                        raise AuthenticationError(
                            f"Invalid MT5 credentials for server {server}",
                            error_code=error_code,
                            context=build_connection_context(login, server)
                        )
                    else:
                        raise ConnectionError(
                            f"MT5 initialization failed: {error}",
                            error_code=error_code,
                            context=build_connection_context(login, server)
                        )

                self._initialized = True

            # Store connection parameters for reconnection
            self._connection_params = {
                'login': login,
                'password': password,
                'server': server,
                'timeout': timeout,
                'portable': portable
            }

            # Verify connection
            account = mt5.account_info()
            if account is None:
                raise ConnectionError(
                    "Failed to get account info after connection",
                    context=build_connection_context(login, server, attempt=1)
                )

            self.status = ConnectionStatus.CONNECTED
            logger.info(
                "Connected to MT5 successfully",
                account_login=account.login,
                account_balance=account.balance,
                server=server,
                instance_id=self.instance_id
            )

            return True

    def disconnect(self) -> None:
        """
        Disconnect from MT5

        Raises:
            ConnectionError: If disconnect fails
        """
        with CorrelationContext():
            try:
                if self._initialized:
                    mt5.shutdown()
                    self._initialized = False
                    self.status = ConnectionStatus.DISCONNECTED
                    logger.info("Disconnected from MT5", instance_id=self.instance_id)
            except Exception as e:
                logger.error("Error during disconnect", exc_info=True, instance_id=self.instance_id)
                raise ConnectionError(
                    f"Failed to disconnect: {e}",
                    context={'instance_id': self.instance_id}
                )

    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        if not self._initialized:
            return False

        try:
            account = mt5.account_info()
            return account is not None
        except:
            return False

    @handle_mt5_errors(retry_count=2, retry_delay=1.0)
    def reconnect(self) -> bool:
        """
        Reconnect using stored credentials

        Returns:
            True if reconnected successfully

        Raises:
            ConnectionError: If no connection parameters stored or reconnection fails
        """
        with CorrelationContext():
            if not self._connection_params:
                raise ConnectionError(
                    "No connection parameters stored for reconnection",
                    context={'instance_id': self.instance_id}
                )

            logger.info("Attempting to reconnect", instance_id=self.instance_id)
            self.disconnect()
            return self.connect(**self._connection_params)

    @handle_mt5_errors(retry_count=2, fallback_return=None)
    def get_account_info(self) -> Optional[AccountInfo]:
        """
        Get account information

        Returns:
            AccountInfo object or None if not available

        Raises:
            ConnectionError: If MT5 is not connected
        """
        with CorrelationContext():
            if not self._initialized:
                raise ConnectionError(
                    "MT5 not initialized",
                    context={'instance_id': self.instance_id}
                )

            account = mt5.account_info()
            if account is None:
                logger.warning("Failed to get account info", instance_id=self.instance_id)
                raise ConnectionError(
                    "MT5 returned no account info",
                    context={'instance_id': self.instance_id}
                )

            logger.debug(
                "Retrieved account info",
                account_login=account.login,
                balance=account.balance,
                equity=account.equity,
                instance_id=self.instance_id
            )

            return AccountInfo(
                login=account.login,
                server=account.server,
                name=account.name,
                company=account.company,
                currency=account.currency,
                balance=account.balance,
                equity=account.equity,
                profit=account.profit,
                margin=account.margin,
                margin_free=account.margin_free,
                margin_level=account.margin_level if account.margin > 0 else 0,
                leverage=account.leverage,
                trade_allowed=account.trade_allowed
            )

    @handle_mt5_errors(retry_count=2, fallback_return=[])
    def get_symbols(self, group: str = "*") -> List[str]:
        """
        Get list of symbols

        Args:
            group: Symbol group filter

        Returns:
            List of symbol names
        """
        with CorrelationContext():
            symbols = mt5.symbols_get(group=group)
            if symbols is None:
                logger.warning("No symbols found", group=group, instance_id=self.instance_id)
                raise DataNotAvailableError(
                    f"No symbols found for group: {group}",
                    context={'group': group, 'instance_id': self.instance_id}
                )

            symbol_names = [s.name for s in symbols]
            logger.debug("Retrieved symbols", count=len(symbol_names), group=group)
            return symbol_names

    @handle_mt5_errors(retry_count=2, fallback_return=None)
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Get symbol information

        Args:
            symbol: Trading symbol

        Returns:
            SymbolInfo object or None

        Raises:
            InvalidSymbolError: If symbol not found
        """
        with CorrelationContext():
            info = mt5.symbol_info(symbol)
            if info is None:
                raise InvalidSymbolError(
                    f"Symbol not found: {symbol}",
                    context={'symbol': symbol, 'instance_id': self.instance_id}
                )

            return SymbolInfo(
                name=info.name,
                description=info.description,
                base_currency=info.currency_base,
                quote_currency=info.currency_profit,
                digits=info.digits,
                point=info.point,
                volume_min=info.volume_min,
                volume_max=info.volume_max,
                volume_step=info.volume_step,
                contract_size=info.trade_contract_size,
                bid=info.bid,
                ask=info.ask,
                spread=info.spread * info.point,
                trade_allowed=info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL
            )

    @handle_mt5_errors(retry_count=1, fallback_return=False)
    def select_symbol(self, symbol: str, enable: bool = True) -> bool:
        """
        Enable/disable symbol in Market Watch

        Args:
            symbol: Trading symbol
            enable: True to enable, False to disable

        Returns:
            True if successful

        Raises:
            InvalidSymbolError: If symbol selection fails
        """
        with CorrelationContext():
            result = mt5.symbol_select(symbol, enable)
            if not result:
                raise InvalidSymbolError(
                    f"Failed to {'enable' if enable else 'disable'} symbol: {symbol}",
                    context={'symbol': symbol, 'enable': enable}
                )
            return result

    def _get_filling_mode(self, mt5_symbol_info) -> int:
        """
        Detect the supported filling mode for a symbol

        Args:
            mt5_symbol_info: MT5 symbol info object (from mt5.symbol_info())

        Returns:
            MT5 filling mode constant
        """
        filling_modes = mt5_symbol_info.filling_mode

        logger.debug(
            "Detecting filling mode",
            symbol=mt5_symbol_info.name,
            filling_modes=filling_modes
        )

        # Priority order: RETURN > FOK > IOC
        if filling_modes & 4:  # SYMBOL_FILLING_RETURN
            logger.debug("Using ORDER_FILLING_RETURN")
            return mt5.ORDER_FILLING_RETURN
        elif filling_modes & 2:  # SYMBOL_FILLING_FOK
            logger.debug("Using ORDER_FILLING_FOK")
            return mt5.ORDER_FILLING_FOK
        elif filling_modes & 1:  # SYMBOL_FILLING_IOC
            logger.debug("Using ORDER_FILLING_IOC")
            return mt5.ORDER_FILLING_IOC
        else:
            logger.warning("No filling mode detected, defaulting to FOK")
            return mt5.ORDER_FILLING_FOK

    @handle_mt5_errors(retry_count=2, fallback_return=None)
    def get_tick(self, symbol: str) -> Optional[TickData]:
        """
        Get latest tick

        Args:
            symbol: Trading symbol

        Returns:
            TickData object or None

        Raises:
            DataNotAvailableError: If tick data not available
        """
        with CorrelationContext():
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                raise DataNotAvailableError(
                    f"No tick data available for {symbol}",
                    context={'symbol': symbol, 'instance_id': self.instance_id}
                )

            return TickData(
                symbol=symbol,
                time=datetime.fromtimestamp(tick.time),
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                spread=tick.ask - tick.bid
            )

    @handle_mt5_errors(retry_count=2, fallback_return=[])
    def get_bars(self, symbol: str, timeframe: str, count: int,
                 start_pos: int = 0) -> List[OHLCBar]:
        """
        Get historical bars

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string (M1, M5, H1, etc.)
            count: Number of bars to retrieve
            start_pos: Starting position (0 = most recent)

        Returns:
            List of OHLCBar objects

        Raises:
            DataNotAvailableError: If bars not available
        """
        with CorrelationContext():
            tf = self.TIMEFRAMES.get(timeframe.upper())
            if tf is None:
                raise DataNotAvailableError(
                    f"Invalid timeframe: {timeframe}",
                    context={'symbol': symbol, 'timeframe': timeframe}
                )

            rates = mt5.copy_rates_from_pos(symbol, tf, start_pos, count)
            if rates is None or len(rates) == 0:
                # Track consecutive failures
                key = f"{symbol}_{timeframe}"
                self._no_bars_count[key] = self._no_bars_count.get(key, 0) + 1

                # Only warn on specific cycles to reduce noise
                if self._no_bars_count[key] == 1:
                    logger.warning(
                        "No bars available - market may be closed",
                        symbol=symbol,
                        timeframe=timeframe,
                        instance_id=self.instance_id
                    )
                elif self._no_bars_count[key] == 20:
                    logger.warning(
                        "Still no data after 20 attempts - check market hours and MT5 connection",
                        symbol=symbol,
                        timeframe=timeframe,
                        attempts=20
                    )

                raise DataNotAvailableError(
                    f"No bars available for {symbol} {timeframe}",
                    context={'symbol': symbol, 'timeframe': timeframe, 'attempts': self._no_bars_count[key]}
                )
            else:
                # Reset counter on successful data retrieval
                key = f"{symbol}_{timeframe}"
                if key in self._no_bars_count:
                    del self._no_bars_count[key]

            bars = []
            for rate in rates:
                bars.append(OHLCBar(
                    symbol=symbol,
                    timeframe=timeframe,
                    time=datetime.fromtimestamp(rate['time']),
                    open=rate['open'],
                    high=rate['high'],
                    low=rate['low'],
                    close=rate['close'],
                    tick_volume=rate['tick_volume'],
                    real_volume=rate['real_volume'],
                    spread=rate['spread']
                ))

            logger.debug("Retrieved bars", symbol=symbol, timeframe=timeframe, count=len(bars))
            return bars

    @handle_mt5_errors(retry_count=2)
    def send_order(self, request: TradeRequest) -> TradeResult:
        """
        Send trade order

        Args:
            request: TradeRequest object with order parameters

        Returns:
            TradeResult object

        Raises:
            InvalidSymbolError: If symbol not found
            OrderExecutionError: If order execution fails
        """
        with CorrelationContext():
            logger.info(
                "Sending order",
                symbol=request.symbol,
                action=request.action.value,
                volume=request.volume,
                instance_id=self.instance_id
            )

            # Get MT5 symbol info for validation and filling mode
            mt5_symbol_info = mt5.symbol_info(request.symbol)
            if mt5_symbol_info is None:
                raise InvalidSymbolError(
                    f"Symbol {request.symbol} not found",
                    context=build_order_context(request.symbol, request.action.value, request.volume)
                )

            # Get our SymbolInfo for other validations
            symbol_info = self.get_symbol_info(request.symbol)
            if not symbol_info:
                raise InvalidSymbolError(
                    f"Symbol {request.symbol} not available",
                    context=build_order_context(request.symbol, request.action.value, request.volume)
                )

            # Validate volume
            if request.volume < symbol_info.volume_min or request.volume > symbol_info.volume_max:
                raise OrderExecutionError(
                    f"Invalid volume: {request.volume} (min: {symbol_info.volume_min}, max: {symbol_info.volume_max})",
                    error_code=2,
                    context=build_order_context(request.symbol, request.action.value, request.volume)
                )

            # Prepare order request
            order_type = self.ORDER_TYPE_MAP.get(request.action)
            if order_type is None:
                raise OrderExecutionError(
                    f"Invalid order type: {request.action}",
                    error_code=3,
                    context=build_order_context(request.symbol, request.action.value, request.volume)
                )

            # Determine price for market orders
            price = request.price
            if price is None:
                if request.action in [OrderType.BUY, OrderType.BUY_LIMIT, OrderType.BUY_STOP]:
                    price = symbol_info.ask
                else:
                    price = symbol_info.bid

            # Detect supported filling mode for the symbol
            filling_type = self._get_filling_mode(mt5_symbol_info)

            # Build MT5 request
            mt5_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": request.symbol,
                "volume": request.volume,
                "type": order_type,
                "price": price,
                "deviation": request.deviation,
                "magic": request.magic,
                "comment": request.comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_type,
            }

            # Add SL/TP if provided
            if request.sl is not None:
                mt5_request["sl"] = request.sl
            if request.tp is not None:
                mt5_request["tp"] = request.tp

            # Try to send order with detected filling mode
            result = mt5.order_send(mt5_request)

            # If filling mode error, try other modes
            if result and result.retcode == 10030:  # Unsupported filling mode
                logger.warning("Filling mode rejected, trying alternatives", filling_type=filling_type)

                # Try all filling modes in order
                filling_modes_to_try = [
                    mt5.ORDER_FILLING_RETURN,
                    mt5.ORDER_FILLING_FOK,
                    mt5.ORDER_FILLING_IOC
                ]

                for fill_mode in filling_modes_to_try:
                    if fill_mode == filling_type:
                        continue  # Already tried this one

                    logger.debug("Trying alternative filling mode", fill_mode=fill_mode)
                    mt5_request["type_filling"] = fill_mode
                    result = mt5.order_send(mt5_request)

                    if result and result.retcode != 10030:
                        break  # Success or different error

            if result is None:
                error = mt5.last_error()
                error_code = error[0] if error else 999
                error_desc = error_description(error_code) if error else "Unknown error"
                logger.error("Order send failed", error_code=error_code, error_desc=error_desc)
                raise OrderExecutionError(
                    f"Order send failed: {error_desc}",
                    error_code=error_code,
                    context=build_order_context(request.symbol, request.action.value, request.volume)
                )

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_desc = trade_server_return_code_description(result.retcode)
                logger.warning("Order not executed", retcode=result.retcode, error_desc=error_desc)
                raise OrderExecutionError(
                    f"Order not executed: {error_desc}",
                    error_code=result.retcode,
                    context=build_order_context(request.symbol, request.action.value, request.volume, ticket=result.order)
                )

            logger.info(
                "Order executed successfully",
                symbol=request.symbol,
                action=request.action.value,
                volume=request.volume,
                price=result.price,
                ticket=result.order
            )

            return TradeResult(
                success=True,
                order_ticket=result.order,
                deal_ticket=result.deal,
                volume=result.volume,
                price=result.price,
                comment=result.comment
            )

    @handle_mt5_errors(retry_count=2)
    def close_position(self, ticket: int) -> TradeResult:
        """
        Close position by ticket

        Args:
            ticket: Position ticket number

        Returns:
            TradeResult object

        Raises:
            OrderExecutionError: If position not found or close fails
        """
        with CorrelationContext():
            logger.info("Closing position", ticket=ticket, instance_id=self.instance_id)

            # Get position info
            positions = mt5.positions_get(ticket=ticket)
            if not positions or len(positions) == 0:
                raise OrderExecutionError(
                    f"Position {ticket} not found",
                    error_code=1,
                    context={'ticket': ticket, 'instance_id': self.instance_id}
                )

            position = positions[0]

            # Determine close order type (opposite of open)
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

            # Get current price
            tick = mt5.symbol_info_tick(position.symbol)
            if tick is None:
                raise DataNotAvailableError(
                    f"Failed to get price for {position.symbol}",
                    context={'symbol': position.symbol, 'ticket': ticket}
                )

            price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

            # Get MT5 symbol info for filling mode detection
            mt5_symbol_info = mt5.symbol_info(position.symbol)
            if mt5_symbol_info is None:
                raise InvalidSymbolError(
                    f"Symbol {position.symbol} info not available",
                    context={'symbol': position.symbol, 'ticket': ticket}
                )

            # Detect supported filling mode for this symbol
            filling_type = self._get_filling_mode(mt5_symbol_info)

            # Build close request
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": position.magic,
                "comment": "Close position",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_type,
            }

            result = mt5.order_send(close_request)

            # If filling mode error, try alternatives
            if result and result.retcode == 10030:  # Unsupported filling mode
                logger.warning("Filling mode rejected for close, trying alternatives")

                filling_modes_to_try = [
                    mt5.ORDER_FILLING_RETURN,
                    mt5.ORDER_FILLING_FOK,
                    mt5.ORDER_FILLING_IOC
                ]

                for fill_mode in filling_modes_to_try:
                    if fill_mode == filling_type:
                        continue

                    close_request["type_filling"] = fill_mode
                    result = mt5.order_send(close_request)

                    if result and result.retcode != 10030:
                        break

            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error = mt5.last_error()
                error_code = result.retcode if result else (error[0] if error else 999)
                error_msg = result.comment if result else ("Unknown error" if not error else str(error))

                raise OrderExecutionError(
                    f"Failed to close position {ticket}: {error_msg}",
                    error_code=error_code,
                    context={'ticket': ticket, 'symbol': position.symbol}
                )

            logger.info("Position closed successfully", ticket=ticket, price=result.price)

            return TradeResult(
                success=True,
                order_ticket=result.order,
                deal_ticket=result.deal,
                volume=result.volume,
                price=result.price,
                comment=f"Closed position {ticket}"
            )

    @handle_mt5_errors(retry_count=2)
    def modify_position(self, ticket: int, sl: Optional[float] = None,
                       tp: Optional[float] = None) -> TradeResult:
        """
        Modify position SL/TP

        Args:
            ticket: Position ticket number
            sl: New stop loss price (optional)
            tp: New take profit price (optional)

        Returns:
            TradeResult object

        Raises:
            OrderExecutionError: If position not found or modification fails
        """
        with CorrelationContext():
            logger.info("Modifying position", ticket=ticket, sl=sl, tp=tp)

            positions = mt5.positions_get(ticket=ticket)
            if not positions or len(positions) == 0:
                raise OrderExecutionError(
                    f"Position {ticket} not found",
                    error_code=1,
                    context={'ticket': ticket}
                )

            position = positions[0]

            # Use current values if not provided
            new_sl = sl if sl is not None else position.sl
            new_tp = tp if tp is not None else position.tp

            modify_request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": new_tp,
            }

            result = mt5.order_send(modify_request)

            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error = mt5.last_error()
                error_code = result.retcode if result else (error[0] if error else 999)
                error_msg = result.comment if result else "Unknown error"

                raise OrderExecutionError(
                    f"Failed to modify position {ticket}: {error_msg}",
                    error_code=error_code,
                    context={'ticket': ticket, 'sl': new_sl, 'tp': new_tp}
                )

            logger.info("Position modified successfully", ticket=ticket, sl=new_sl, tp=new_tp)

            return TradeResult(
                success=True,
                order_ticket=ticket,
                comment=f"Modified position {ticket}"
            )

    @handle_mt5_errors(retry_count=2, fallback_return=[])
    def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """
        Get open positions

        Args:
            symbol: Filter by symbol (optional)

        Returns:
            List of Position objects
        """
        with CorrelationContext():
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()

            if positions is None:
                logger.debug("No positions found", symbol=symbol)
                return []

            result = []
            for pos in positions:
                # Map MT5 type to OrderType
                if pos.type == mt5.ORDER_TYPE_BUY:
                    order_type = OrderType.BUY
                elif pos.type == mt5.ORDER_TYPE_SELL:
                    order_type = OrderType.SELL
                else:
                    continue  # Skip pending orders

                result.append(Position(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    type=order_type,
                    volume=pos.volume,
                    price_open=pos.price_open,
                    price_current=pos.price_current,
                    sl=pos.sl,
                    tp=pos.tp,
                    profit=pos.profit,
                    swap=pos.swap,
                    commission=0.0,  # MT5 doesn't provide commission in position
                    magic=pos.magic,
                    comment=pos.comment,
                    time_open=datetime.fromtimestamp(pos.time)
                ))

            logger.debug("Retrieved positions", count=len(result), symbol=symbol)
            return result

    def get_position_by_ticket(self, ticket: int) -> Optional[Position]:
        """Get position by ticket"""
        positions = self.get_positions()
        for pos in positions:
            if pos.ticket == ticket:
                return pos
        return None

    @handle_mt5_errors(retry_count=2)
    def place_pending_order(self, symbol: str, volume: float, order_type: OrderType,
                           price: float, sl: Optional[float] = None, tp: Optional[float] = None,
                           type_time: int = None, expiration: Optional[datetime] = None,
                           magic: int = 0, deviation: int = 10, comment: str = "") -> TradeResult:
        """
        Place a pending order (limit or stop)

        Args:
            symbol: Trading symbol
            volume: Order volume in lots
            order_type: Order type (BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP)
            price: Activation price for pending order
            sl: Stop loss price (optional)
            tp: Take profit price (optional)
            type_time: Order expiration type (default: ORDER_TIME_GTC)
            expiration: Expiration datetime (required for ORDER_TIME_SPECIFIED)
            magic: Magic number
            deviation: Price deviation in points
            comment: Order comment

        Returns:
            TradeResult with order details

        Raises:
            InvalidSymbolError: If symbol not found
            OrderExecutionError: If order placement fails
        """
        with CorrelationContext():
            logger.info(
                "Placing pending order",
                symbol=symbol,
                order_type=order_type.value,
                price=price,
                volume=volume
            )

            # Validate symbol
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                raise InvalidSymbolError(
                    f"Symbol {symbol} not found",
                    context={'symbol': symbol}
                )

            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    raise InvalidSymbolError(
                        f"Failed to select symbol {symbol}",
                        context={'symbol': symbol}
                    )

            # Get MT5 order type
            mt5_order_type = self.ORDER_TYPE_MAP.get(order_type)
            if mt5_order_type is None:
                raise OrderExecutionError(
                    f"Invalid order type: {order_type}",
                    error_code=1,
                    context={'order_type': order_type.value}
                )

            # Default to GTC if not specified
            if type_time is None:
                type_time = mt5.ORDER_TIME_GTC

            # Validate expiration for time-specific orders
            if type_time in (mt5.ORDER_TIME_SPECIFIED, mt5.ORDER_TIME_SPECIFIED_DAY):
                if expiration is None:
                    raise OrderExecutionError(
                        f"Expiration required for type_time={type_time}",
                        error_code=1,
                        context={'type_time': type_time}
                    )

            # Detect filling mode
            filling_type = self._get_filling_mode(symbol_info)

            # Build request
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_order_type,
                "price": price,
                "deviation": deviation,
                "magic": magic,
                "comment": comment[:31],  # MT5 max comment length
                "type_time": type_time,
                "type_filling": filling_type,
            }

            # Add SL/TP if provided
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp

            # Add expiration if required
            if type_time in (mt5.ORDER_TIME_SPECIFIED, mt5.ORDER_TIME_SPECIFIED_DAY) and expiration is not None:
                expiration_utc = expiration.astimezone(timezone.utc) if expiration.tzinfo else expiration.replace(tzinfo=timezone.utc)
                request["expiration"] = int(expiration_utc.timestamp())

            # Send order
            result = mt5.order_send(request)

            if result is None:
                error = mt5.last_error()
                error_code = error[0] if error else 999
                error_desc = error_description(error_code) if error else "Unknown error"
                raise OrderExecutionError(
                    f"Pending order failed: {error_desc}",
                    error_code=error_code,
                    context={'symbol': symbol, 'order_type': order_type.value}
                )

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_desc = trade_server_return_code_description(result.retcode)
                raise OrderExecutionError(
                    f"Pending order failed: {error_desc}",
                    error_code=result.retcode,
                    context={'symbol': symbol, 'order_type': order_type.value}
                )

            logger.info("Pending order placed successfully", order_ticket=result.order, symbol=symbol, price=price)

            return TradeResult(
                success=True,
                order_ticket=result.order,
                volume=volume,
                price=price,
                comment=f"Pending order placed"
            )

    @handle_mt5_errors(retry_count=2)
    def delete_order(self, ticket: int) -> TradeResult:
        """
        Delete a pending order

        Args:
            ticket: Order ticket number

        Returns:
            TradeResult indicating success or failure

        Raises:
            OrderExecutionError: If order deletion fails
        """
        with CorrelationContext():
            logger.info("Deleting order", ticket=ticket)

            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": ticket,
            }

            result = mt5.order_send(request)

            if result is None:
                error = mt5.last_error()
                error_code = error[0] if error else 999
                error_desc = error_description(error_code) if error else "Unknown error"
                raise OrderExecutionError(
                    f"Delete order failed: {error_desc}",
                    error_code=error_code,
                    context={'ticket': ticket}
                )

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_desc = trade_server_return_code_description(result.retcode)
                raise OrderExecutionError(
                    f"Delete order failed: {error_desc}",
                    error_code=result.retcode,
                    context={'ticket': ticket}
                )

            logger.info("Order deleted successfully", ticket=ticket)

            return TradeResult(
                success=True,
                order_ticket=ticket,
                comment=f"Order deleted"
            )

    @handle_mt5_errors(retry_count=2)
    def modify_order(self, ticket: int, price: float, sl: Optional[float] = None,
                    tp: Optional[float] = None, type_time: int = None,
                    expiration: Optional[datetime] = None) -> TradeResult:
        """
        Modify a pending order

        Args:
            ticket: Order ticket number
            price: New activation price
            sl: New stop loss price
            tp: New take profit price
            type_time: New expiration type
            expiration: New expiration datetime

        Returns:
            TradeResult indicating success or failure

        Raises:
            OrderExecutionError: If order not found or modification fails
        """
        with CorrelationContext():
            logger.info("Modifying order", ticket=ticket, price=price)

            # Get the order
            orders = mt5.orders_get(ticket=ticket)
            if not orders:
                raise OrderExecutionError(
                    f"Order {ticket} not found",
                    error_code=4705,
                    context={'ticket': ticket}
                )

            order = orders[0]

            # Use current values if not provided
            new_sl = sl if sl is not None else order.sl
            new_tp = tp if tp is not None else order.tp
            new_type_time = type_time if type_time is not None else order.type_time

            request = {
                "action": mt5.TRADE_ACTION_MODIFY,
                "order": ticket,
                "price": price,
                "sl": new_sl,
                "tp": new_tp,
                "symbol": order.symbol,
                "type": order.type,
                "type_time": new_type_time,
            }

            # Add expiration if specified
            if new_type_time in (mt5.ORDER_TIME_SPECIFIED, mt5.ORDER_TIME_SPECIFIED_DAY):
                if expiration is None:
                    raise OrderExecutionError(
                        "Expiration required for ORDER_TIME_SPECIFIED",
                        error_code=1,
                        context={'ticket': ticket, 'type_time': new_type_time}
                    )
                expiration_utc = expiration.astimezone(timezone.utc) if expiration.tzinfo else expiration.replace(tzinfo=timezone.utc)
                request["expiration"] = int(expiration_utc.timestamp())

            result = mt5.order_send(request)

            if result is None:
                error = mt5.last_error()
                error_code = error[0] if error else 999
                error_desc = error_description(error_code) if error else "Unknown error"
                raise OrderExecutionError(
                    f"Modify order failed: {error_desc}",
                    error_code=error_code,
                    context={'ticket': ticket}
                )

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_desc = trade_server_return_code_description(result.retcode)
                raise OrderExecutionError(
                    f"Modify order failed: {error_desc}",
                    error_code=result.retcode,
                    context={'ticket': ticket}
                )

            logger.info("Order modified successfully", ticket=ticket)

            return TradeResult(
                success=True,
                order_ticket=ticket,
                comment=f"Order modified"
            )

    @handle_mt5_errors(retry_count=1, fallback_return=None)
    def refresh_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Refresh and return updated symbol information
        Forces a refresh from the server

        Args:
            symbol: Trading symbol

        Returns:
            Updated SymbolInfo or None if failed
        """
        with CorrelationContext():
            # Toggle symbol selection to force refresh
            mt5.symbol_select(symbol, False)
            mt5.symbol_select(symbol, True)

            return self.get_symbol_info(symbol)

    # Convenience methods for pending orders

    def buy_limit(self, symbol: str, volume: float, price: float, **kwargs) -> TradeResult:
        """Place a buy limit order"""
        return self.place_pending_order(symbol, volume, OrderType.BUY_LIMIT, price, **kwargs)

    def sell_limit(self, symbol: str, volume: float, price: float, **kwargs) -> TradeResult:
        """Place a sell limit order"""
        return self.place_pending_order(symbol, volume, OrderType.SELL_LIMIT, price, **kwargs)

    def buy_stop(self, symbol: str, volume: float, price: float, **kwargs) -> TradeResult:
        """Place a buy stop order"""
        return self.place_pending_order(symbol, volume, OrderType.BUY_STOP, price, **kwargs)

    def sell_stop(self, symbol: str, volume: float, price: float, **kwargs) -> TradeResult:
        """Place a sell stop order"""
        return self.place_pending_order(symbol, volume, OrderType.SELL_STOP, price, **kwargs)

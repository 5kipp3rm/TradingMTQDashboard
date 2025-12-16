"""
MT4 Connector - Implementation using MetaTrader4 Python package

This connector uses the third-party MetaTrader4 Python package.
Note: This package has limited broker support and may not work with all brokers.

Installation:
    pip install MetaTrader4

Broker Requirements:
    - Broker must allow API connections
    - May require specific broker configuration
"""

from typing import Optional, List
from datetime import datetime
import logging

try:
    import MetaTrader4
    MT4_AVAILABLE = True
except ImportError:
    MT4_AVAILABLE = False

from .base import (
    BaseMetaTraderConnector, PlatformType, OrderType, ConnectionStatus,
    TickData, OHLCBar, SymbolInfo, Position, AccountInfo,
    TradeRequest, TradeResult
)


logger = logging.getLogger(__name__)


class MT4Connector(BaseMetaTraderConnector):
    """
    MetaTrader 4 connector using MetaTrader4 Python package

    This implementation uses the third-party MetaTrader4 package.
    May not work with all brokers.
    """

    def __init__(self, instance_id: str = "default"):
        """Initialize MT4 connector"""
        super().__init__(instance_id, PlatformType.MT4)

        if not MT4_AVAILABLE:
            logger.error(
                f"[{self.instance_id}] MetaTrader4 package not installed. "
                "Install with: pip install MetaTrader4"
            )
            self.status = ConnectionStatus.ERROR

        self._mt4 = None
        logger.info(f"[{self.instance_id}] MT4ConnectorV1 initialized")

    def connect(self, login: int, password: str, server: str, **kwargs) -> bool:
        """
        Connect to MT4 account

        Args:
            login: MT4 account number
            password: Account password
            server: Broker server name
            **kwargs: Additional connection parameters
                - timeout: Connection timeout in ms (default: 60000)
                - portable: Use portable mode (default: False)

        Returns:
            True if connection successful
        """
        if not MT4_AVAILABLE:
            logger.error(f"[{self.instance_id}] MetaTrader4 package not available")
            self.status = ConnectionStatus.ERROR
            return False

        timeout = kwargs.get('timeout', 60000)
        portable = kwargs.get('portable', False)

        logger.info(
            f"[{self.instance_id}] Connecting to MT4 account",
            extra={
                'login': login,
                'server': server,
                'timeout': timeout
            }
        )

        try:
            # Initialize MT4 connection
            if not MetaTrader4.initialize(
                login=login,
                password=password,
                server=server,
                timeout=timeout,
                portable=portable
            ):
                error_code = MetaTrader4.last_error()
                logger.error(
                    f"[{self.instance_id}] MT4 initialization failed: {error_code}"
                )
                self.status = ConnectionStatus.DISCONNECTED
                return False

            # Verify connection
            account_info = MetaTrader4.account_info()
            if account_info is None:
                logger.error(f"[{self.instance_id}] Failed to retrieve account info")
                self.status = ConnectionStatus.DISCONNECTED
                MetaTrader4.shutdown()
                return False

            self._mt4 = MetaTrader4
            self.status = ConnectionStatus.CONNECTED

            logger.info(
                f"[{self.instance_id}] Successfully connected to MT4",
                extra={
                    'login': login,
                    'server': server,
                    'balance': account_info.balance if account_info else None
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"[{self.instance_id}] MT4 connection error: {str(e)}",
                exc_info=True
            )
            self.status = ConnectionStatus.ERROR
            return False

    def disconnect(self) -> None:
        """Disconnect from MT4"""
        logger.info(f"[{self.instance_id}] Disconnecting from MT4")

        try:
            if self._mt4 and MT4_AVAILABLE:
                MetaTrader4.shutdown()
            self.status = ConnectionStatus.DISCONNECTED
            self._mt4 = None

            logger.info(f"[{self.instance_id}] Successfully disconnected from MT4")
        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Error during disconnect: {str(e)}",
                exc_info=True
            )

    def is_connected(self) -> bool:
        """Check if connected to MT4"""
        if not self._mt4 or not MT4_AVAILABLE:
            return False

        try:
            # Verify connection by checking account info
            account_info = MetaTrader4.account_info()
            return account_info is not None
        except Exception:
            return False

    def reconnect(self) -> bool:
        """Reconnect to MT4 (not implemented)"""
        logger.warning(f"[{self.instance_id}] Reconnect not implemented for MT4ConnectorV1")
        return False

    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        if not self.is_connected():
            return None

        try:
            info = MetaTrader4.account_info()
            if not info:
                return None

            return AccountInfo(
                login=info.login,
                server=info.server,
                name=info.name,
                balance=float(info.balance),
                equity=float(info.equity),
                margin=float(info.margin),
                margin_free=float(info.margin_free),
                margin_level=float(info.margin_level) if info.margin > 0 else 0.0,
                profit=float(info.profit),
                currency=info.currency,
                leverage=int(info.leverage),
                company=info.company
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
            symbols = MetaTrader4.symbols_get(group=group)
            return [s.name for s in symbols] if symbols else []
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
            info = MetaTrader4.symbol_info(symbol)
            if not info:
                return None

            return SymbolInfo(
                name=info.name,
                description=info.description,
                point=float(info.point),
                digits=int(info.digits),
                trade_contract_size=float(info.trade_contract_size),
                trade_tick_value=float(info.trade_tick_value),
                trade_tick_size=float(info.trade_tick_size),
                min_volume=float(info.volume_min),
                max_volume=float(info.volume_max),
                volume_step=float(info.volume_step),
                bid=float(info.bid),
                ask=float(info.ask),
                spread=int(info.spread)
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
            return MetaTrader4.symbol_select(symbol, enable)
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
            tick = MetaTrader4.symbol_info_tick(symbol)
            if not tick:
                return None

            return TickData(
                time=datetime.fromtimestamp(tick.time),
                bid=float(tick.bid),
                ask=float(tick.ask),
                last=float(tick.last) if hasattr(tick, 'last') else float(tick.bid),
                volume=int(tick.volume) if hasattr(tick, 'volume') else 0
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
            # Convert timeframe string to MT4 constant
            tf_map = {
                'M1': MetaTrader4.TIMEFRAME_M1,
                'M5': MetaTrader4.TIMEFRAME_M5,
                'M15': MetaTrader4.TIMEFRAME_M15,
                'M30': MetaTrader4.TIMEFRAME_M30,
                'H1': MetaTrader4.TIMEFRAME_H1,
                'H4': MetaTrader4.TIMEFRAME_H4,
                'D1': MetaTrader4.TIMEFRAME_D1,
                'W1': MetaTrader4.TIMEFRAME_W1,
                'MN1': MetaTrader4.TIMEFRAME_MN1,
            }

            tf = tf_map.get(timeframe.upper(), MetaTrader4.TIMEFRAME_H1)

            rates = MetaTrader4.copy_rates_from_pos(symbol, tf, start_pos, count)
            if rates is None or len(rates) == 0:
                return []

            return [
                OHLCBar(
                    time=datetime.fromtimestamp(rate['time']),
                    open=float(rate['open']),
                    high=float(rate['high']),
                    low=float(rate['low']),
                    close=float(rate['close']),
                    tick_volume=int(rate['tick_volume']),
                    spread=int(rate['spread']) if 'spread' in rate else 0,
                    real_volume=int(rate['real_volume']) if 'real_volume' in rate else 0
                )
                for rate in rates
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
                error_message="Not connected to MT4"
            )

        try:
            # Convert order type
            action_map = {
                OrderType.BUY: MetaTrader4.ORDER_TYPE_BUY,
                OrderType.SELL: MetaTrader4.ORDER_TYPE_SELL,
                OrderType.BUY_LIMIT: MetaTrader4.ORDER_TYPE_BUY_LIMIT,
                OrderType.SELL_LIMIT: MetaTrader4.ORDER_TYPE_SELL_LIMIT,
                OrderType.BUY_STOP: MetaTrader4.ORDER_TYPE_BUY_STOP,
                OrderType.SELL_STOP: MetaTrader4.ORDER_TYPE_SELL_STOP,
            }

            mt4_request = {
                'action': MetaTrader4.TRADE_ACTION_DEAL,
                'symbol': request.symbol,
                'volume': request.volume,
                'type': action_map[request.order_type],
                'price': request.price or 0.0,
                'sl': request.sl or 0.0,
                'tp': request.tp or 0.0,
                'deviation': request.deviation or 10,
                'magic': request.magic or 0,
                'comment': request.comment or "",
            }

            result = MetaTrader4.order_send(mt4_request)

            if result.retcode == MetaTrader4.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=True,
                    order=result.order,
                    deal=result.deal,
                    volume=result.volume,
                    price=result.price,
                    comment=result.comment
                )
            else:
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=result.comment
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
                error_message="Not connected to MT4"
            )

        try:
            # Get position info
            position = self.get_position_by_ticket(ticket)
            if not position:
                return TradeResult(
                    success=False,
                    error_message=f"Position {ticket} not found"
                )

            # Create close request
            close_type = OrderType.SELL if position.type == OrderType.BUY else OrderType.BUY

            request = TradeRequest(
                symbol=position.symbol,
                order_type=close_type,
                volume=position.volume,
                position=ticket
            )

            return self.send_order(request)

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
                error_message="Not connected to MT4"
            )

        try:
            request = {
                'action': MetaTrader4.TRADE_ACTION_SLTP,
                'position': ticket,
                'sl': sl or 0.0,
                'tp': tp or 0.0,
            }

            result = MetaTrader4.order_send(request)

            if result.retcode == MetaTrader4.TRADE_RETCODE_DONE:
                return TradeResult(success=True)
            else:
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=result.comment
                )

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
            positions = MetaTrader4.positions_get(symbol=symbol) if symbol else MetaTrader4.positions_get()

            if not positions:
                return []

            return [
                Position(
                    ticket=int(pos.ticket),
                    symbol=pos.symbol,
                    type=OrderType.BUY if pos.type == 0 else OrderType.SELL,
                    volume=float(pos.volume),
                    price_open=float(pos.price_open),
                    price_current=float(pos.price_current),
                    sl=float(pos.sl),
                    tp=float(pos.tp),
                    profit=float(pos.profit),
                    swap=float(pos.swap),
                    commission=float(pos.commission) if hasattr(pos, 'commission') else 0.0,
                    magic=int(pos.magic),
                    comment=pos.comment,
                    time=datetime.fromtimestamp(pos.time)
                )
                for pos in positions
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

"""
MT5 Connector - MetaTrader 5 implementation
Production-ready with error handling and connection pooling
"""
import MetaTrader5 as mt5
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from .base import (
    BaseMetaTraderConnector, PlatformType, OrderType, ConnectionStatus,
    TickData, OHLCBar, SymbolInfo, Position, AccountInfo,
    TradeRequest, TradeResult
)
from .error_descriptions import trade_server_return_code_description, error_description


logger = logging.getLogger(__name__)


class MT5Connector(BaseMetaTraderConnector):
    """
    MetaTrader 5 connector implementation
    Supports multiple instances with proper resource management
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
        logger.info(f"MT5Connector initialized: {instance_id}")
    
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
        """
        try:
            self.status = ConnectionStatus.CONNECTING
            logger.info(f"[{self.instance_id}] Connecting to MT5 - Server: {server}, Login: {login}")
            
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
                    logger.error(f"[{self.instance_id}] MT5 initialization failed: {error}")
                    self.status = ConnectionStatus.ERROR
                    return False
                
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
                logger.error(f"[{self.instance_id}] Failed to get account info")
                self.status = ConnectionStatus.ERROR
                return False
            
            self.status = ConnectionStatus.CONNECTED
            logger.info(f"[{self.instance_id}] Connected successfully - Account: {account.login}")
            return True
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Connection error: {e}", exc_info=True)
            self.status = ConnectionStatus.ERROR
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MT5"""
        try:
            if self._initialized:
                mt5.shutdown()
                self._initialized = False
                self.status = ConnectionStatus.DISCONNECTED
                logger.info(f"[{self.instance_id}] Disconnected from MT5")
        except Exception as e:
            logger.error(f"[{self.instance_id}] Disconnect error: {e}", exc_info=True)
    
    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        if not self._initialized:
            return False
        
        try:
            account = mt5.account_info()
            return account is not None
        except:
            return False
    
    def reconnect(self) -> bool:
        """Reconnect using stored credentials"""
        if not self._connection_params:
            logger.error(f"[{self.instance_id}] No connection parameters stored")
            return False
        
        logger.info(f"[{self.instance_id}] Attempting to reconnect...")
        self.disconnect()
        return self.connect(**self._connection_params)
    
    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        try:
            account = mt5.account_info()
            if account is None:
                logger.warning(f"[{self.instance_id}] Failed to get account info")
                return None
            
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
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error getting account info: {e}", exc_info=True)
            return None
    
    def get_symbols(self, group: str = "*") -> List[str]:
        """Get list of symbols"""
        try:
            symbols = mt5.symbols_get(group=group)
            if symbols is None:
                logger.warning(f"[{self.instance_id}] No symbols found for group: {group}")
                return []
            
            return [s.name for s in symbols]
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error getting symbols: {e}", exc_info=True)
            return []
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get symbol information"""
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                logger.warning(f"[{self.instance_id}] Symbol not found: {symbol}")
                return None
            
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
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error getting symbol info for {symbol}: {e}", exc_info=True)
            return None
    
    def select_symbol(self, symbol: str, enable: bool = True) -> bool:
        """Enable/disable symbol in Market Watch"""
        try:
            result = mt5.symbol_select(symbol, enable)
            if not result:
                logger.warning(f"[{self.instance_id}] Failed to select symbol: {symbol}")
            return result
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error selecting symbol {symbol}: {e}", exc_info=True)
            return False
    
    def _get_filling_mode(self, mt5_symbol_info) -> int:
        """
        Detect the supported filling mode for a symbol
        
        Args:
            mt5_symbol_info: MT5 symbol info object (from mt5.symbol_info())
            
        Returns:
            MT5 filling mode constant
        """
        # Check what filling modes are supported
        filling_modes = mt5_symbol_info.filling_mode
        
        logger.info(f"[{self.instance_id}] Symbol {mt5_symbol_info.name} filling_mode: {filling_modes}")
        
        # Priority order: RETURN > FOK > IOC
        # RETURN (4) is most commonly supported
        if filling_modes & 4:  # SYMBOL_FILLING_RETURN
            logger.info(f"[{self.instance_id}] Using ORDER_FILLING_RETURN")
            return mt5.ORDER_FILLING_RETURN
        elif filling_modes & 2:  # SYMBOL_FILLING_FOK
            logger.info(f"[{self.instance_id}] Using ORDER_FILLING_FOK")
            return mt5.ORDER_FILLING_FOK
        elif filling_modes & 1:  # SYMBOL_FILLING_IOC
            logger.info(f"[{self.instance_id}] Using ORDER_FILLING_IOC")
            return mt5.ORDER_FILLING_IOC
        else:
            # Default to FOK if nothing else matches
            logger.warning(f"[{self.instance_id}] No filling mode detected, defaulting to FOK")
            return mt5.ORDER_FILLING_FOK
    
    def get_tick(self, symbol: str) -> Optional[TickData]:
        """Get latest tick"""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.warning(f"[{self.instance_id}] No tick data for {symbol}")
                return None
            
            return TickData(
                symbol=symbol,
                time=datetime.fromtimestamp(tick.time),
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                spread=tick.ask - tick.bid
            )
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error getting tick for {symbol}: {e}", exc_info=True)
            return None
    
    def get_bars(self, symbol: str, timeframe: str, count: int, 
                 start_pos: int = 0) -> List[OHLCBar]:
        """Get historical bars"""
        try:
            tf = self.TIMEFRAMES.get(timeframe.upper())
            if tf is None:
                logger.error(f"[{self.instance_id}] Invalid timeframe: {timeframe}")
                return []
            
            rates = mt5.copy_rates_from_pos(symbol, tf, start_pos, count)
            if rates is None or len(rates) == 0:
                # Track consecutive failures
                key = f"{symbol}_{timeframe}"
                self._no_bars_count[key] = self._no_bars_count.get(key, 0) + 1
                
                # Only warn every 10 cycles to reduce noise
                if self._no_bars_count[key] == 1:
                    logger.warning(f"[{self.instance_id}] No bars for {symbol} {timeframe} - Market may be closed or data not available")
                elif self._no_bars_count[key] == 20:
                    logger.warning(f"[{self.instance_id}] {symbol} {timeframe} - Still no data after 20 attempts. Check:")
                    logger.warning(f"  • Forex market hours (Sunday 5PM - Friday 5PM EST)")
                    logger.warning(f"  • MT5 connection and symbol availability")
                    logger.warning(f"  • Timeframe matches broker's available data")
                return []
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
            
            return bars
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error getting bars for {symbol}: {e}", exc_info=True)
            return []
    
    def send_order(self, request: TradeRequest) -> TradeResult:
        """Send trade order"""
        try:
            # Get MT5 symbol info for validation and filling mode
            mt5_symbol_info = mt5.symbol_info(request.symbol)
            if mt5_symbol_info is None:
                return TradeResult(
                    success=False,
                    error_code=1,
                    error_message=f"Symbol {request.symbol} not found"
                )
            
            # Get our SymbolInfo for other validations
            symbol_info = self.get_symbol_info(request.symbol)
            if not symbol_info:
                return TradeResult(
                    success=False,
                    error_code=1,
                    error_message=f"Symbol {request.symbol} not available"
                )
            
            # Validate volume
            if request.volume < symbol_info.volume_min or request.volume > symbol_info.volume_max:
                return TradeResult(
                    success=False,
                    error_code=2,
                    error_message=f"Invalid volume: {request.volume}"
                )
            
            # Prepare order request
            order_type = self.ORDER_TYPE_MAP.get(request.action)
            if order_type is None:
                return TradeResult(
                    success=False,
                    error_code=3,
                    error_message=f"Invalid order type: {request.action}"
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
                logger.warning(f"[{self.instance_id}] Filling mode {filling_type} rejected, trying alternatives...")
                
                # Try all filling modes in order
                filling_modes_to_try = [
                    mt5.ORDER_FILLING_RETURN,
                    mt5.ORDER_FILLING_FOK,
                    mt5.ORDER_FILLING_IOC
                ]
                
                for fill_mode in filling_modes_to_try:
                    if fill_mode == filling_type:
                        continue  # Already tried this one
                    
                    logger.info(f"[{self.instance_id}] Trying filling mode: {fill_mode}")
                    mt5_request["type_filling"] = fill_mode
                    result = mt5.order_send(mt5_request)
                    
                    if result and result.retcode != 10030:
                        break  # Success or different error
            
            if result is None:
                error = mt5.last_error()
                error_desc = error_description(error[0]) if error else "Unknown error"
                logger.error(f"[{self.instance_id}] Order send failed: {error_desc}")
                return TradeResult(
                    success=False,
                    error_code=error[0] if error else 999,
                    error_message=error_desc
                )
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_desc = trade_server_return_code_description(result.retcode)
                logger.warning(f"[{self.instance_id}] Order not executed: {result.retcode} - {error_desc}")
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=error_desc
                )
            
            logger.info(f"[{self.instance_id}] Order executed: {request.symbol} {request.action.value} "
                       f"{request.volume} @ {result.price}, Ticket: {result.order}")
            
            return TradeResult(
                success=True,
                order_ticket=result.order,
                deal_ticket=result.deal,
                volume=result.volume,
                price=result.price,
                comment=result.comment
            )
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error sending order: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=999,
                error_message=str(e)
            )
    
    def close_position(self, ticket: int) -> TradeResult:
        """Close position by ticket"""
        try:
            # Get position info
            positions = mt5.positions_get(ticket=ticket)
            if not positions or len(positions) == 0:
                return TradeResult(
                    success=False,
                    error_code=1,
                    error_message=f"Position {ticket} not found"
                )
            
            position = positions[0]
            
            # Determine close order type (opposite of open)
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            # Get current price
            tick = mt5.symbol_info_tick(position.symbol)
            if tick is None:
                return TradeResult(
                    success=False,
                    error_code=2,
                    error_message=f"Failed to get price for {position.symbol}"
                )
            
            price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
            
            # Get MT5 symbol info for filling mode detection
            mt5_symbol_info = mt5.symbol_info(position.symbol)
            if mt5_symbol_info is None:
                return TradeResult(
                    success=False,
                    error_code=1,
                    error_message=f"Symbol {position.symbol} info not available"
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
                logger.warning(f"[{self.instance_id}] Filling mode {filling_type} rejected for close, trying alternatives...")
                
                filling_modes_to_try = [
                    mt5.ORDER_FILLING_RETURN,
                    mt5.ORDER_FILLING_FOK,
                    mt5.ORDER_FILLING_IOC
                ]
                
                for fill_mode in filling_modes_to_try:
                    if fill_mode == filling_type:
                        continue
                    
                    logger.info(f"[{self.instance_id}] Trying close with filling mode: {fill_mode}")
                    close_request["type_filling"] = fill_mode
                    result = mt5.order_send(close_request)
                    
                    if result and result.retcode != 10030:
                        break
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error = mt5.last_error()
                logger.error(f"[{self.instance_id}] Failed to close position {ticket}: {error}")
                return TradeResult(
                    success=False,
                    error_code=result.retcode if result else 999,
                    error_message=result.comment if result else "Unknown error"
                )
            
            logger.info(f"[{self.instance_id}] Position closed: {ticket} @ {result.price}")
            
            return TradeResult(
                success=True,
                order_ticket=result.order,
                deal_ticket=result.deal,
                volume=result.volume,
                price=result.price,
                comment=f"Closed position {ticket}"
            )
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error closing position {ticket}: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=999,
                error_message=str(e)
            )
    
    def modify_position(self, ticket: int, sl: Optional[float] = None, 
                       tp: Optional[float] = None) -> TradeResult:
        """Modify position SL/TP"""
        try:
            positions = mt5.positions_get(ticket=ticket)
            if not positions or len(positions) == 0:
                return TradeResult(
                    success=False,
                    error_code=1,
                    error_message=f"Position {ticket} not found"
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
                logger.error(f"[{self.instance_id}] Failed to modify position {ticket}: {error}")
                return TradeResult(
                    success=False,
                    error_code=result.retcode if result else 999,
                    error_message=result.comment if result else "Unknown error"
                )
            
            logger.info(f"[{self.instance_id}] Position modified: {ticket} SL={new_sl} TP={new_tp}")
            
            return TradeResult(
                success=True,
                order_ticket=ticket,
                comment=f"Modified position {ticket}"
            )
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error modifying position {ticket}: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=999,
                error_message=str(e)
            )
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """Get open positions"""
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
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
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error getting positions: {e}", exc_info=True)
            return []
    
    def get_position_by_ticket(self, ticket: int) -> Optional[Position]:
        """Get position by ticket"""
        positions = self.get_positions()
        for pos in positions:
            if pos.ticket == ticket:
                return pos
        return None
    
    def place_pending_order(self, symbol: str, volume: float, order_type: OrderType,
                           price: float, sl: Optional[float] = None, tp: Optional[float] = None,
                           type_time: int = None, expiration: Optional[datetime] = None,
                           magic: int = 0, deviation: int = 10, comment: str = "") -> TradeResult:
        """
        Place a pending order (limit or stop).
        
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
        """
        try:
            # Validate symbol
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return TradeResult(
                    success=False,
                    error_code=4301,
                    error_message=f"Symbol {symbol} not found"
                )
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    return TradeResult(
                        success=False,
                        error_code=4302,
                        error_message=f"Failed to select symbol {symbol}"
                    )
            
            # Get MT5 order type
            mt5_order_type = self.ORDER_TYPE_MAP.get(order_type)
            if mt5_order_type is None:
                return TradeResult(
                    success=False,
                    error_code=1,
                    error_message=f"Invalid order type: {order_type}"
                )
            
            # Default to GTC if not specified
            if type_time is None:
                type_time = mt5.ORDER_TIME_GTC
            
            # Validate expiration for time-specific orders
            if type_time in (mt5.ORDER_TIME_SPECIFIED, mt5.ORDER_TIME_SPECIFIED_DAY):
                if expiration is None:
                    return TradeResult(
                        success=False,
                        error_code=1,
                        error_message=f"Expiration required for type_time={type_time}"
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
                # Convert to UTC timestamp
                expiration_utc = expiration.astimezone(timezone.utc) if expiration.tzinfo else expiration.replace(tzinfo=timezone.utc)
                request["expiration"] = int(expiration_utc.timestamp())
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                error_desc = error_description(error[0]) if error else "Unknown error"
                logger.error(f"[{self.instance_id}] Pending order failed: {error_desc}")
                return TradeResult(
                    success=False,
                    error_code=error[0] if error else 999,
                    error_message=error_desc
                )
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_desc = trade_server_return_code_description(result.retcode)
                logger.warning(f"[{self.instance_id}] Pending order failed: {result.retcode} - {error_desc}")
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=error_desc
                )
            
            logger.info(f"[{self.instance_id}] Pending order #{result.order} placed: {symbol} {order_type.value} @ {price}")
            
            return TradeResult(
                success=True,
                order_ticket=result.order,
                volume=volume,
                price=price,
                comment=f"Pending order placed"
            )
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error placing pending order: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=999,
                error_message=str(e)
            )
    
    def delete_order(self, ticket: int) -> TradeResult:
        """
        Delete a pending order.
        
        Args:
            ticket: Order ticket number
            
        Returns:
            TradeResult indicating success or failure
        """
        try:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": ticket,
            }
            
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                error_desc = error_description(error[0]) if error else "Unknown error"
                logger.error(f"[{self.instance_id}] Delete order failed: {error_desc}")
                return TradeResult(
                    success=False,
                    error_code=error[0] if error else 999,
                    error_message=error_desc
                )
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_desc = trade_server_return_code_description(result.retcode)
                logger.warning(f"[{self.instance_id}] Delete order failed: {result.retcode} - {error_desc}")
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=error_desc
                )
            
            logger.info(f"[{self.instance_id}] Order #{ticket} deleted successfully")
            
            return TradeResult(
                success=True,
                order_ticket=ticket,
                comment=f"Order deleted"
            )
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error deleting order {ticket}: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=999,
                error_message=str(e)
            )
    
    def modify_order(self, ticket: int, price: float, sl: Optional[float] = None,
                    tp: Optional[float] = None, type_time: int = None,
                    expiration: Optional[datetime] = None) -> TradeResult:
        """
        Modify a pending order.
        
        Args:
            ticket: Order ticket number
            price: New activation price
            sl: New stop loss price
            tp: New take profit price
            type_time: New expiration type
            expiration: New expiration datetime
            
        Returns:
            TradeResult indicating success or failure
        """
        try:
            # Get the order
            orders = mt5.orders_get(ticket=ticket)
            if not orders:
                return TradeResult(
                    success=False,
                    error_code=4705,
                    error_message=f"Order {ticket} not found"
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
                    return TradeResult(
                        success=False,
                        error_code=1,
                        error_message="Expiration required for ORDER_TIME_SPECIFIED"
                    )
                expiration_utc = expiration.astimezone(timezone.utc) if expiration.tzinfo else expiration.replace(tzinfo=timezone.utc)
                request["expiration"] = int(expiration_utc.timestamp())
            
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                error_desc = error_description(error[0]) if error else "Unknown error"
                logger.error(f"[{self.instance_id}] Modify order failed: {error_desc}")
                return TradeResult(
                    success=False,
                    error_code=error[0] if error else 999,
                    error_message=error_desc
                )
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_desc = trade_server_return_code_description(result.retcode)
                logger.warning(f"[{self.instance_id}] Modify order failed: {result.retcode} - {error_desc}")
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=error_desc
                )
            
            logger.info(f"[{self.instance_id}] Order #{ticket} modified successfully")
            
            return TradeResult(
                success=True,
                order_ticket=ticket,
                comment=f"Order modified"
            )
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error modifying order {ticket}: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=999,
                error_message=str(e)
            )
    
    def refresh_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Refresh and return updated symbol information.
        Forces a refresh from the server.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Updated SymbolInfo or None if failed
        """
        try:
            # Toggle symbol selection to force refresh
            mt5.symbol_select(symbol, False)
            mt5.symbol_select(symbol, True)
            
            return self.get_symbol_info(symbol)
            
        except Exception as e:
            logger.error(f"[{self.instance_id}] Error refreshing symbol {symbol}: {e}", exc_info=True)
            return None
    
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

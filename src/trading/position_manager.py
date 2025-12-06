"""
Position Manager - Automatic SL/TP Adjustment
Implements trailing stops, breakeven, partial profits, and dynamic TP
"""
from datetime import datetime
from typing import Optional, Dict, List
import MetaTrader5 as mt5

from src.connectors.base import BaseMetaTraderConnector, Position
from src.utils.logger import get_logger, log_config

logger = get_logger(__name__)


class PositionManager:
    """
    Manages open positions with automatic SL/TP adjustments
    - Trailing stop loss
    - Breakeven protection
    - Partial profit taking
    - Dynamic take profit extension
    """
    
    def __init__(self, connector: BaseMetaTraderConnector):
        """
        Initialize position manager
        
        Args:
            connector: MT5 connector instance
        """
        self.connector = connector
        self.managed_positions: Dict[int, Dict] = {}  # ticket -> state
        
    def add_position(self, ticket: int, config: Dict):
        """
        Add position to be managed
        
        Args:
            ticket: Position ticket
            config: Management configuration
        """
        self.managed_positions[ticket] = {
            'added_time': datetime.now(),
            'breakeven_set': False,
            'partial_closed': False,
            'trailing_active': False,
            'highest_profit_pips': 0,
            'config': config
        }
        logger.debug(f"Position #{ticket} added to management")
    
    def process_all_positions(self, config: Dict) -> None:
        """
        Process all open positions with automatic management
        
        Args:
            config: Global management configuration from YAML
        """
        positions = self.connector.get_positions()
        if not positions:
            return
        
        for position in positions:
            # Auto-add new positions
            if position.ticket not in self.managed_positions:
                self.add_position(position.ticket, config)
            
            # Process position
            self._process_position(position, config)
    
    def _process_position(self, position: Position, config: Dict) -> None:
        """
        Process single position for automatic adjustments
        
        Args:
            position: Position object
            config: Management configuration
        """
        state = self.managed_positions.get(position.ticket)
        if not state:
            return
        
        # Get symbol info for pip calculation
        symbol_info = self.connector.get_symbol_info(position.symbol)
        if not symbol_info:
            return
        
        pip_value = symbol_info.point * 10
        
        # Calculate profit in pips
        if position.type == 0:  # BUY
            profit_pips = (position.price_current - position.price_open) / pip_value
        else:  # SELL
            profit_pips = (position.price_open - position.price_current) / pip_value
        
        # Update highest profit
        if profit_pips > state['highest_profit_pips']:
            state['highest_profit_pips'] = profit_pips
        
        # 1. Breakeven Protection
        if config.get('enable_breakeven', False):
            self._check_breakeven(position, profit_pips, pip_value, config, state)
        
        # 2. Trailing Stop
        if config.get('enable_trailing_stop', False):
            self._check_trailing_stop(position, profit_pips, pip_value, config, state)
        
        # 3. Partial Profit Taking
        if config.get('enable_partial_close', False):
            self._check_partial_close(position, profit_pips, config, state)
        
        # 4. Dynamic Take Profit Extension
        if config.get('enable_dynamic_tp', False):
            self._check_dynamic_tp(position, profit_pips, pip_value, config, state)
    
    def _check_breakeven(self, position: Position, profit_pips: float, 
                         pip_value: float, config: Dict, state: Dict) -> None:
        """Move SL to breakeven when profit reaches trigger"""
        if state['breakeven_set']:
            return
        
        trigger_pips = config.get('breakeven_trigger_pips', 20)
        offset_pips = config.get('breakeven_offset_pips', 2)
        
        if profit_pips >= trigger_pips:
            # Calculate breakeven SL
            if position.type == 0:  # BUY
                new_sl = position.price_open + (offset_pips * pip_value)
            else:  # SELL
                new_sl = position.price_open - (offset_pips * pip_value)
            
            # Don't move SL backwards
            if position.type == 0 and new_sl <= position.sl:
                return
            if position.type == 1 and new_sl >= position.sl:
                return
            
            # Modify position
            result = self.connector.modify_position(position.ticket, new_sl, position.tp)
            
            if result.success:
                state['breakeven_set'] = True
                logger.info(
                    f"Breakeven set @ {new_sl:.5f} (+{offset_pips} pips)",
                    extra={'symbol': position.symbol, 'custom_icon': '🛡️'}
                )
    
    def _check_trailing_stop(self, position: Position, profit_pips: float,
                            pip_value: float, config: Dict, state: Dict) -> None:
        """Apply trailing stop loss"""
        trailing_distance = config.get('trailing_stop_pips', 15)
        activation_pips = config.get('trailing_activation_pips', 20)
        
        # Check if trailing should activate
        if not state['trailing_active']:
            if profit_pips >= activation_pips:
                state['trailing_active'] = True
                logger.info(
                    f"Trailing stop activated @ {profit_pips:.1f} pips profit",
                    extra={'symbol': position.symbol, 'custom_icon': '📈'}
                )
            else:
                return
        
        # Calculate trailing SL
        if position.type == 0:  # BUY
            new_sl = position.price_current - (trailing_distance * pip_value)
            # Only move SL up, never down
            if position.sl and new_sl <= position.sl:
                return
        else:  # SELL
            new_sl = position.price_current + (trailing_distance * pip_value)
            # Only move SL down, never up
            if position.sl and new_sl >= position.sl:
                return
        
        # Modify position
        result = self.connector.modify_position(position.ticket, new_sl, position.tp)
        
        if result.success:
            logger.debug(
                f"Trailing SL moved to {new_sl:.5f} ({trailing_distance} pips)",
                extra={'symbol': position.symbol}
            )
    
    def _check_partial_close(self, position: Position, profit_pips: float,
                            config: Dict, state: Dict) -> None:
        """Close partial position to lock profits"""
        if state['partial_closed']:
            return
        
        trigger_pips = config.get('partial_close_trigger_pips', 30)
        close_percent = config.get('partial_close_percent', 50)
        
        if profit_pips >= trigger_pips:
            # Calculate volume to close
            close_volume = position.volume * (close_percent / 100)
            
            # Ensure minimum volume
            symbol_info = self.connector.get_symbol_info(position.symbol)
            if symbol_info and close_volume < symbol_info.volume_min:
                logger.warning(
                    f"Partial close volume {close_volume:.2f} < minimum {symbol_info.volume_min:.2f}",
                    extra={'symbol': position.symbol}
                )
                return
            
            # Round to valid lot size
            if symbol_info:
                close_volume = round(close_volume / symbol_info.volume_step) * symbol_info.volume_step
            
            # Partial close using MT5 directly
            tick = mt5.symbol_info_tick(position.symbol)
            if not tick:
                logger.warning(f"Failed to get tick data for {position.symbol}")
                return
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": position.ticket,
                "symbol": position.symbol,
                "volume": close_volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
                "price": tick.bid if position.type == 0 else tick.ask,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Partial close {close_percent}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                state['partial_closed'] = True
                logger.info(
                    f"Partial close: {close_percent}% ({close_volume:.2f} lots) @ {profit_pips:.1f} pips profit",
                    extra={'symbol': position.symbol, 'custom_icon': '💰'}
                )
            else:
                error_msg = f"Failed: {result.comment if result else 'Unknown error'}"
                logger.warning(
                    f"Partial close {error_msg}",
                    extra={'symbol': position.symbol}
                )
    
    def _check_dynamic_tp(self, position: Position, profit_pips: float,
                         pip_value: float, config: Dict, state: Dict) -> None:
        """Extend TP when profit milestones reached"""
        if not position.tp:
            return
        
        extension_pips = config.get('tp_extension_pips', 20)
        trigger_percent = config.get('tp_extension_trigger_percent', 80)
        
        # Calculate how close we are to TP
        if position.type == 0:  # BUY
            tp_distance_pips = (position.tp - position.price_open) / pip_value
        else:  # SELL
            tp_distance_pips = (position.price_open - position.tp) / pip_value
        
        progress_percent = (profit_pips / tp_distance_pips) * 100
        
        # Extend TP if we're close
        if progress_percent >= trigger_percent:
            if position.type == 0:  # BUY
                new_tp = position.tp + (extension_pips * pip_value)
            else:  # SELL
                new_tp = position.tp - (extension_pips * pip_value)
            
            result = self.connector.modify_position(position.ticket, position.sl, new_tp)
            
            if result.success:
                logger.info(
                    f"TP extended by {extension_pips} pips to {new_tp:.5f}",
                    extra={'symbol': position.symbol, 'custom_icon': '🎯'}
                )
    
    def remove_position(self, ticket: int) -> None:
        """Remove position from management"""
        if ticket in self.managed_positions:
            del self.managed_positions[ticket]
            logger.debug(f"Position #{ticket} removed from management")
    
    def cleanup_closed_positions(self) -> None:
        """Remove closed positions from management"""
        open_tickets = {pos.ticket for pos in self.connector.get_positions() or []}
        
        closed_tickets = [
            ticket for ticket in self.managed_positions.keys()
            if ticket not in open_tickets
        ]
        
        for ticket in closed_tickets:
            self.remove_position(ticket)
    
    def get_managed_count(self) -> int:
        """Get number of managed positions"""
        return len(self.managed_positions)
    
    def get_position_state(self, ticket: int) -> Optional[Dict]:
        """Get position management state"""
        return self.managed_positions.get(ticket)

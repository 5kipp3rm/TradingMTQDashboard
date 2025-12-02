"""
Trading Controller - High-level trading orchestration
Manages multiple connector instances and trading logic
"""
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from ..connectors import (
    BaseMetaTraderConnector, OrderType, TradeRequest, TradeResult,
    Position, AccountInfo, TickData, SymbolInfo
)


logger = logging.getLogger(__name__)


class TradingController:
    """
    High-level trading controller
    Orchestrates trading operations across one or more connectors
    """
    
    def __init__(self, connector: BaseMetaTraderConnector):
        """
        Initialize trading controller
        
        Args:
            connector: MetaTrader connector instance
        """
        self.connector = connector
        self.instance_id = connector.get_instance_id()
        logger.info(f"TradingController initialized for {self.instance_id}")
    
    def execute_trade(self, symbol: str, action: OrderType, volume: float,
                     sl: Optional[float] = None, tp: Optional[float] = None,
                     price: Optional[float] = None, comment: str = "") -> TradeResult:
        """
        Execute a trade with validation
        
        Args:
            symbol: Trading symbol
            action: Order type (BUY/SELL)
            volume: Trade volume in lots
            sl: Stop loss price (optional)
            tp: Take profit price (optional)
            price: Entry price (optional, uses market price if None)
            comment: Order comment
            
        Returns:
            TradeResult with execution details
        """
        logger.info(f"[{self.instance_id}] Executing trade: {symbol} {action.value} {volume} lots")
        
        # Validate connection
        if not self.connector.is_connected():
            logger.error(f"[{self.instance_id}] Not connected to MetaTrader")
            return TradeResult(
                success=False,
                error_code=1000,
                error_message="Not connected to MetaTrader"
            )
        
        # Validate symbol
        symbol_info = self.connector.get_symbol_info(symbol)
        if not symbol_info:
            logger.error(f"[{self.instance_id}] Symbol not found: {symbol}")
            return TradeResult(
                success=False,
                error_code=1001,
                error_message=f"Symbol {symbol} not found"
            )
        
        if not symbol_info.trade_allowed:
            logger.error(f"[{self.instance_id}] Trading not allowed for {symbol}")
            return TradeResult(
                success=False,
                error_code=1002,
                error_message=f"Trading not allowed for {symbol}"
            )
        
        # Validate volume
        if volume < symbol_info.volume_min or volume > symbol_info.volume_max:
            logger.error(f"[{self.instance_id}] Invalid volume: {volume}")
            return TradeResult(
                success=False,
                error_code=1003,
                error_message=f"Volume must be between {symbol_info.volume_min} and {symbol_info.volume_max}"
            )
        
        # Validate margin
        account = self.connector.get_account_info()
        if not account:
            logger.error(f"[{self.instance_id}] Failed to get account info")
            return TradeResult(
                success=False,
                error_code=1004,
                error_message="Failed to get account information"
            )
        
        if account.margin_free <= 0:
            logger.error(f"[{self.instance_id}] Insufficient margin")
            return TradeResult(
                success=False,
                error_code=1005,
                error_message="Insufficient margin for trade"
            )
        
        # Create trade request
        request = TradeRequest(
            symbol=symbol,
            action=action,
            volume=volume,
            price=price,
            sl=sl,
            tp=tp,
            comment=comment
        )
        
        # Execute trade
        result = self.connector.send_order(request)
        
        if result.success:
            logger.info(f"[{self.instance_id}] Trade executed successfully: Ticket={result.order_ticket}")
        else:
            logger.error(f"[{self.instance_id}] Trade execution failed: {result.error_message}")
        
        return result
    
    def close_trade(self, ticket: int) -> TradeResult:
        """
        Close an open position
        
        Args:
            ticket: Position ticket number
            
        Returns:
            TradeResult with close details
        """
        logger.info(f"[{self.instance_id}] Closing position: {ticket}")
        
        if not self.connector.is_connected():
            return TradeResult(
                success=False,
                error_message="Not connected to MetaTrader"
            )
        
        # Verify position exists
        position = self.connector.get_position_by_ticket(ticket)
        if not position:
            logger.warning(f"[{self.instance_id}] Position {ticket} not found")
            return TradeResult(
                success=False,
                error_message=f"Position {ticket} not found"
            )
        
        # Close position
        result = self.connector.close_position(ticket)
        
        if result.success:
            logger.info(f"[{self.instance_id}] Position closed successfully: {ticket}")
        else:
            logger.error(f"[{self.instance_id}] Failed to close position {ticket}: {result.error_message}")
        
        return result
    
    def modify_trade(self, ticket: int, sl: Optional[float] = None, 
                    tp: Optional[float] = None) -> TradeResult:
        """
        Modify position SL/TP
        
        Args:
            ticket: Position ticket
            sl: New stop loss (optional)
            tp: New take profit (optional)
            
        Returns:
            TradeResult
        """
        logger.info(f"[{self.instance_id}] Modifying position: {ticket}")
        
        if not self.connector.is_connected():
            return TradeResult(
                success=False,
                error_message="Not connected to MetaTrader"
            )
        
        result = self.connector.modify_position(ticket, sl, tp)
        
        if result.success:
            logger.info(f"[{self.instance_id}] Position modified: {ticket}")
        else:
            logger.error(f"[{self.instance_id}] Failed to modify position: {result.error_message}")
        
        return result
    
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """
        Get all open positions
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of positions
        """
        if not self.connector.is_connected():
            logger.warning(f"[{self.instance_id}] Not connected")
            return []
        
        return self.connector.get_positions(symbol)
    
    def get_position_pnl(self, ticket: int) -> Optional[float]:
        """
        Get position P&L
        
        Args:
            ticket: Position ticket
            
        Returns:
            P&L in account currency or None if position not found
        """
        position = self.connector.get_position_by_ticket(ticket)
        return position.profit if position else None
    
    def get_account_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get account summary
        
        Returns:
            Dictionary with account metrics
        """
        account = self.connector.get_account_info()
        if not account:
            return None
        
        positions = self.get_open_positions()
        
        return {
            'balance': account.balance,
            'equity': account.equity,
            'profit': account.profit,
            'margin': account.margin,
            'margin_free': account.margin_free,
            'margin_level': account.margin_level,
            'open_positions': len(positions),
            'total_volume': sum(p.volume for p in positions)
        }
    
    def close_all_positions(self) -> List[TradeResult]:
        """
        Close all open positions
        
        Returns:
            List of TradeResult for each close operation
        """
        logger.info(f"[{self.instance_id}] Closing all positions")
        
        positions = self.get_open_positions()
        results = []
        
        for position in positions:
            result = self.close_trade(position.ticket)
            results.append(result)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"[{self.instance_id}] Closed {successful}/{len(positions)} positions")
        
        return results
    
    def get_symbol_price(self, symbol: str) -> Optional[TickData]:
        """
        Get current price for symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            TickData or None
        """
        if not self.connector.is_connected():
            return None
        
        return self.connector.get_tick(symbol)

"""
Account Utility Functions
Helper methods for account analysis and position sizing

NOTE: These utilities require the MetaTrader5 Python package which only works on Windows/Linux.
For Mac users, use the bridge-based connectors instead.
"""
from typing import Optional
import logging
from .base import OrderType

logger = logging.getLogger(__name__)

# Try to import MetaTrader5 - only available on Windows/Linux
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning(
        "MetaTrader5 package not available. AccountUtils will not work. "
        "This is expected on macOS. Use MT5ConnectorBridge instead."
    )
    # Create mock module for constants
    from types import ModuleType
    mt5 = ModuleType('MetaTrader5')
    mt5.TRADE_ACTION_DEAL = 1
    mt5.ORDER_TYPE_BUY = 0
    mt5.ORDER_TYPE_SELL = 1
    mt5.ORDER_TYPE_BUY_LIMIT = 2
    mt5.ORDER_TYPE_SELL_LIMIT = 3
    mt5.ORDER_TYPE_BUY_STOP = 4
    mt5.ORDER_TYPE_SELL_STOP = 5
    mt5.ACCOUNT_TRADE_MODE_DEMO = 0
    mt5.ACCOUNT_TRADE_MODE_CONTEST = 1
    mt5.ACCOUNT_TRADE_MODE_REAL = 2
    mt5.ACCOUNT_MARGIN_MODE_RETAIL_NETTING = 0
    mt5.ACCOUNT_MARGIN_MODE_EXCHANGE = 1
    mt5.ACCOUNT_MARGIN_MODE_RETAIL_HEDGING = 2
    mt5.ACCOUNT_STOPOUT_MODE_PERCENT = 0
    mt5.ACCOUNT_STOPOUT_MODE_MONEY = 1


class AccountUtils:
    """
    Account utility functions for margin calculations and position sizing

    NOTE: These methods require the MetaTrader5 Python package (Windows/Linux only).
    On macOS, these methods will return None. Use MT5ConnectorBridge for Mac compatibility.
    """

    @staticmethod
    def margin_check(symbol: str, order_type: int, volume: float, price: float) -> Optional[float]:
        """
        Calculate required margin for an order.

        Args:
            symbol: Trading symbol
            order_type: MT5 order type constant
            volume: Trade volume in lots
            price: Entry price

        Returns:
            Required margin in account currency, or None if calculation fails
        """
        if not MT5_AVAILABLE:
            logger.warning("AccountUtils.margin_check not available - MetaTrader5 package not installed")
            return None

        try:
            result = mt5.order_check({
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price
            })
            
            if result is None:
                logger.warning(f"Margin check failed for {symbol}")
                return None
            
            return result.margin if hasattr(result, 'margin') else None
            
        except Exception as e:
            logger.error(f"Error in margin_check: {e}", exc_info=True)
            return None
    
    @staticmethod
    def order_profit_check(symbol: str, order_type: int, volume: float, 
                          price_open: float, price_close: float) -> Optional[float]:
        """
        Calculate estimated profit for a trade.
        
        Args:
            symbol: Trading symbol
            order_type: MT5 order type (BUY or SELL)
            volume: Trade volume in lots
            price_open: Entry price
            price_close: Exit price
            
        Returns:
            Estimated profit in account currency, or None if calculation fails
        """
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.warning(f"Symbol {symbol} not found")
                return None
            
            point = symbol_info.point
            contract_size = symbol_info.trade_contract_size
            
            # Calculate profit based on order type
            if order_type in (mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP):
                profit_pips = (price_close - price_open) / point
            else:
                profit_pips = (price_open - price_close) / point
            
            # Simple profit calculation (works for forex pairs)
            profit = profit_pips * point * volume * contract_size
            
            return profit
            
        except Exception as e:
            logger.error(f"Error in order_profit_check: {e}", exc_info=True)
            return None
    
    @staticmethod
    def free_margin_check(symbol: str, order_type: int, volume: float, price: float) -> Optional[float]:
        """
        Calculate free margin after opening a position.
        
        Args:
            symbol: Trading symbol
            order_type: MT5 order type
            volume: Trade volume in lots
            price: Entry price
            
        Returns:
            Remaining free margin after trade, or None if calculation fails
        """
        try:
            account = mt5.account_info()
            if account is None:
                logger.warning("Failed to get account info")
                return None
            
            required_margin = AccountUtils.margin_check(symbol, order_type, volume, price)
            if required_margin is None:
                return None
            
            return account.margin_free - required_margin
            
        except Exception as e:
            logger.error(f"Error in free_margin_check: {e}", exc_info=True)
            return None
    
    @staticmethod
    def max_lot_check(symbol: str, order_type: int, price: float, percent: float = 100.0) -> Optional[float]:
        """
        Calculate maximum lot size based on available margin.
        
        Args:
            symbol: Trading symbol
            order_type: MT5 order type
            price: Entry price
            percent: Percentage of available margin to use (default: 100%)
            
        Returns:
            Maximum lot size, or None if calculation fails
            
        Example:
            # Use 50% of available margin
            max_lots = AccountUtils.max_lot_check("EURUSD", mt5.ORDER_TYPE_BUY, 1.0850, percent=50)
        """
        try:
            account = mt5.account_info()
            if account is None:
                logger.warning("Failed to get account info")
                return None
            
            # Get margin required for 1.0 lot
            required_margin_per_lot = AccountUtils.margin_check(symbol, order_type, 1.0, price)
            
            if required_margin_per_lot is None or required_margin_per_lot == 0:
                logger.warning(f"Could not calculate margin for {symbol}")
                return None
            
            # Calculate available margin
            margin_available = account.margin_free * (percent / 100.0)
            
            # Calculate max lots
            max_lots = margin_available / required_margin_per_lot
            
            # Round down to symbol's volume step
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                volume_step = symbol_info.volume_step
                max_lots = (max_lots // volume_step) * volume_step
                
                # Ensure within symbol limits
                max_lots = max(symbol_info.volume_min, min(max_lots, symbol_info.volume_max))
            
            return max_lots
            
        except Exception as e:
            logger.error(f"Error in max_lot_check: {e}", exc_info=True)
            return None
    
    @staticmethod
    def risk_based_lot_size(symbol: str, order_type: int, entry_price: float, 
                           stop_loss: float, risk_percent: float = 1.0) -> Optional[float]:
        """
        Calculate lot size based on risk percentage of account balance.
        
        Args:
            symbol: Trading symbol
            order_type: MT5 order type
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_percent: Percentage of account balance to risk (default: 1%)
            
        Returns:
            Calculated lot size, or None if calculation fails
            
        Example:
            # Risk 2% of account on this trade
            lot_size = AccountUtils.risk_based_lot_size(
                "EURUSD", mt5.ORDER_TYPE_BUY, 1.0850, 1.0830, risk_percent=2.0
            )
        """
        try:
            account = mt5.account_info()
            symbol_info = mt5.symbol_info(symbol)
            
            if account is None or symbol_info is None:
                logger.warning("Failed to get account or symbol info")
                return None
            
            # Calculate risk amount in account currency
            risk_amount = account.balance * (risk_percent / 100.0)
            
            # Calculate stop loss distance in pips
            sl_distance_price = abs(entry_price - stop_loss)
            sl_distance_pips = sl_distance_price / symbol_info.point
            
            # Calculate pip value for 1 lot
            contract_size = symbol_info.trade_contract_size
            pip_value_per_lot = symbol_info.point * contract_size
            
            # Calculate lot size
            if sl_distance_pips > 0 and pip_value_per_lot > 0:
                lot_size = risk_amount / (sl_distance_pips * pip_value_per_lot)
                
                # Round to symbol's volume step
                volume_step = symbol_info.volume_step
                lot_size = (lot_size // volume_step) * volume_step
                
                # Ensure within symbol limits
                lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
                
                return lot_size
            
            return None
            
        except Exception as e:
            logger.error(f"Error in risk_based_lot_size: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_trade_mode_description(trade_mode: int) -> str:
        """Get human-readable trade mode description"""
        mode_map = {
            mt5.ACCOUNT_TRADE_MODE_DEMO: "Demo",
            mt5.ACCOUNT_TRADE_MODE_CONTEST: "Contest",
            mt5.ACCOUNT_TRADE_MODE_REAL: "Real"
        }
        return mode_map.get(trade_mode, "Unknown")
    
    @staticmethod
    def get_margin_mode_description(margin_mode: int) -> str:
        """Get human-readable margin mode description"""
        mode_map = {
            mt5.ACCOUNT_MARGIN_MODE_RETAIL_NETTING: "Retail Netting",
            mt5.ACCOUNT_MARGIN_MODE_EXCHANGE: "Exchange",
            mt5.ACCOUNT_MARGIN_MODE_RETAIL_HEDGING: "Retail Hedging"
        }
        return mode_map.get(margin_mode, "Unknown")
    
    @staticmethod
    def get_stopout_mode_description(stopout_mode: int) -> str:
        """Get human-readable stopout mode description"""
        mode_map = {
            mt5.ACCOUNT_STOPOUT_MODE_PERCENT: "Percent",
            mt5.ACCOUNT_STOPOUT_MODE_MONEY: "Money"
        }
        return mode_map.get(stopout_mode, "Unknown")

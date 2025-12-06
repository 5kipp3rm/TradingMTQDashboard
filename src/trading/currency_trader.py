"""
Currency Trader - Individual currency pair trading logic
Each instance handles one currency pair independently
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import MetaTrader5 as mt5

from src.connectors.base import BaseMetaTraderConnector, OrderType, TradeRequest
from src.strategies.base import BaseStrategy, Signal, SignalType
from src.connectors.account_utils import AccountUtils


@dataclass
class CurrencyTraderConfig:
    """Configuration for a currency trader"""
    symbol: str
    strategy: BaseStrategy
    risk_percent: float = 1.0
    timeframe: str = 'M5'
    cooldown_seconds: int = 60
    max_position_size: float = 1.0
    min_position_size: float = 0.01
    use_position_trading: bool = True  # Position-based vs Crossover
    
    # Per-currency strategy parameters
    fast_period: int = 10
    slow_period: int = 20
    sl_pips: int = 20
    tp_pips: int = 40


class CurrencyTrader:
    """
    Manages trading for a single currency pair
    - Independent state and configuration
    - Own strategy instance
    - Isolated error handling
    """
    
    def __init__(self, 
                 config: CurrencyTraderConfig,
                 connector: BaseMetaTraderConnector):
        """
        Initialize currency trader
        
        Args:
            config: Trading configuration for this currency
            connector: Shared MT5 connector
        """
        self.config = config
        self.connector = connector
        
        # State management
        self.last_signal: Optional[Signal] = None
        self.last_trade_time: Optional[datetime] = None
        self.last_signal_type: Optional[SignalType] = None
        
        # Statistics
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_profit = 0.0
        
        # Validation
        self.is_valid = self._validate_symbol()
    
    def _validate_symbol(self) -> bool:
        """Validate symbol is available"""
        symbol_info = self.connector.get_symbol_info(self.config.symbol)
        if not symbol_info:
            print(f"⚠️  Warning: Symbol {self.config.symbol} not available on this broker")
            return False
        return True
    
    def can_trade(self) -> bool:
        """Check if enough time has passed since last trade"""
        if not self.last_trade_time:
            return True
        
        elapsed = (datetime.now() - self.last_trade_time).total_seconds()
        return elapsed >= self.config.cooldown_seconds
    
    def analyze_market(self) -> Optional[Signal]:
        """
        Analyze market and generate signal
        
        Returns:
            Signal object or None if analysis failed
        """
        try:
            # Get market data
            bars = self.connector.get_bars(
                self.config.symbol, 
                self.config.timeframe, 
                100
            )
            
            if not bars:
                return None
            
            if self.config.use_position_trading:
                # Position-based trading (faster signals)
                import numpy as np
                
                fast_ma = np.mean([bar.close for bar in bars[-self.config.fast_period:]])
                slow_ma = np.mean([bar.close for bar in bars[-self.config.slow_period:]])
                current_price = bars[-1].close
                
                # Determine signal based on MA position
                if fast_ma > slow_ma:
                    signal_type = SignalType.BUY
                elif fast_ma < slow_ma:
                    signal_type = SignalType.SELL
                else:
                    signal_type = SignalType.HOLD
                
                # Calculate SL/TP in price
                symbol_info = self.connector.get_symbol_info(self.config.symbol)
                pip_value = symbol_info.point * 10 if symbol_info else 0.0001
                
                if signal_type == SignalType.BUY:
                    sl = current_price - (self.config.sl_pips * pip_value)
                    tp = current_price + (self.config.tp_pips * pip_value)
                elif signal_type == SignalType.SELL:
                    sl = current_price + (self.config.sl_pips * pip_value)
                    tp = current_price - (self.config.tp_pips * pip_value)
                else:
                    sl = tp = None
                
                # Create signal
                signal = Signal(
                    type=signal_type,
                    symbol=self.config.symbol,
                    timestamp=datetime.now(),
                    price=current_price,
                    stop_loss=sl,
                    take_profit=tp,
                    confidence=0.7 if signal_type != SignalType.HOLD else 0.0,
                    reason=f"Fast MA({self.config.fast_period})={'>' if fast_ma > slow_ma else '<'}Slow MA({self.config.slow_period})"
                )
            else:
                # Crossover-based trading (waits for actual cross)
                signal = self.config.strategy.analyze(
                    self.config.symbol, 
                    self.config.timeframe, 
                    bars
                )
            
            self.last_signal = signal
            return signal
            
        except Exception as e:
            print(f"[{self.config.symbol}] Analysis error: {e}")
            return None
    
    def should_execute_signal(self, signal: Signal) -> bool:
        """
        Determine if signal should be executed
        
        Args:
            signal: Generated trading signal
            
        Returns:
            True if should trade, False otherwise
        """
        # No trade on HOLD
        if signal.type == SignalType.HOLD:
            return False
        
        # Check cooldown
        if not self.can_trade():
            return False
        
        # For position trading, only trade on signal change
        if self.config.use_position_trading:
            if signal.type == self.last_signal_type:
                return False
        
        return True
    
    def calculate_lot_size(self, signal: Signal) -> float:
        """
        Calculate position size based on risk
        
        Args:
            signal: Trading signal with SL/TP
            
        Returns:
            Lot size (volume)
        """
        # Convert signal type to MT5 order type
        mt5_order_type = (mt5.ORDER_TYPE_BUY 
                         if signal.type == SignalType.BUY 
                         else mt5.ORDER_TYPE_SELL)
        
        # Calculate risk-based lot size
        lot_size = AccountUtils.risk_based_lot_size(
            symbol=self.config.symbol,
            order_type=mt5_order_type,
            entry_price=signal.price,
            stop_loss=signal.stop_loss,
            risk_percent=self.config.risk_percent
        )
        
        if not lot_size:
            # Fallback to minimum
            symbol_info = self.connector.get_symbol_info(self.config.symbol)
            lot_size = symbol_info.volume_min if symbol_info else self.config.min_position_size
        
        # Enforce limits
        lot_size = max(self.config.min_position_size, 
                      min(lot_size, self.config.max_position_size))
        
        return lot_size
    
    def execute_trade(self, signal: Signal) -> bool:
        """
        Execute trade based on signal
        
        Args:
            signal: Trading signal
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate lot size
            lot_size = self.calculate_lot_size(signal)
            
            # Convert to OrderType enum
            action = (OrderType.BUY 
                     if signal.type == SignalType.BUY 
                     else OrderType.SELL)
            
            # Create trade request
            request = TradeRequest(
                symbol=self.config.symbol,
                action=action,
                volume=lot_size,
                price=signal.price,
                sl=signal.stop_loss,
                tp=signal.take_profit
            )
            
            # Execute
            result = self.connector.send_order(request)
            
            if result.success:
                self.last_trade_time = datetime.now()
                self.last_signal_type = signal.type
                self.total_trades += 1
                self.successful_trades += 1
                
                print(f"✓ [{self.config.symbol}] {signal.type.name} "
                      f"{lot_size:.2f} lots @ {result.price:.5f} "
                      f"(Order #{result.order_ticket})")
                return True
            else:
                self.failed_trades += 1
                print(f"✗ [{self.config.symbol}] Trade failed: {result.error_message}")
                return False
                
        except Exception as e:
            self.failed_trades += 1
            print(f"✗ [{self.config.symbol}] Execution error: {e}")
            return False
    
    def process_cycle(self) -> Dict[str, Any]:
        """
        Run one complete trading cycle
        
        Returns:
            Dictionary with cycle results
        """
        result = {
            'symbol': self.config.symbol,
            'timestamp': datetime.now(),
            'signal': None,
            'executed': False,
            'error': None
        }
        
        # Skip if symbol is not valid
        if not self.is_valid:
            result['error'] = "Symbol not available"
            return result
        
        try:
            # Analyze market
            signal = self.analyze_market()
            result['signal'] = signal
            
            if not signal:
                result['error'] = "Failed to generate signal"
                return result
            
            # Check if should execute
            if self.should_execute_signal(signal):
                executed = self.execute_trade(signal)
                result['executed'] = executed
            else:
                print(f"[{self.config.symbol}] {signal.type.name} "
                      f"@ {signal.price:.5f} - Skipped (cooldown/duplicate)")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"✗ [{self.config.symbol}] Cycle error: {e}")
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trading statistics for this currency"""
        win_rate = (self.successful_trades / self.total_trades * 100 
                   if self.total_trades > 0 else 0.0)
        
        return {
            'symbol': self.config.symbol,
            'total_trades': self.total_trades,
            'successful': self.successful_trades,
            'failed': self.failed_trades,
            'win_rate': win_rate,
            'last_trade': self.last_trade_time,
            'last_signal_type': self.last_signal_type.name if self.last_signal_type else None
        }
    
    def __repr__(self) -> str:
        return (f"CurrencyTrader(symbol={self.config.symbol}, "
                f"strategy={self.config.strategy.name}, "
                f"trades={self.total_trades})")

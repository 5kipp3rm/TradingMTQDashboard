"""
Backtesting Engine
Test trading strategies on historical data
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import logging
from enum import Enum

from ..connectors.base import OHLCBar, OrderType
from ..strategies.base import BaseStrategy, Signal, SignalType

logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """Position status"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class BacktestPosition:
    """Backtest position record"""
    entry_time: datetime
    entry_price: float
    position_type: OrderType
    volume: float
    symbol: str = "EURUSD"
    sl: Optional[float] = None
    tp: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: str = ""
    profit: float = 0.0
    profit_pips: float = 0.0
    status: PositionStatus = PositionStatus.OPEN


@dataclass
class BacktestMetrics:
    """Backtest performance metrics"""
    # Basic metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    break_even_trades: int = 0
    
    # Profit metrics
    total_profit: float = 0.0
    total_profit_pips: float = 0.0
    avg_profit: float = 0.0
    avg_profit_pips: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    
    # Risk metrics
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    
    # Advanced metrics
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win_streak: int = 0
    largest_loss_streak: int = 0
    avg_trade_duration: float = 0.0  # in hours
    
    # Equity curve
    equity_curve: List[float] = field(default_factory=list)
    dates: List[datetime] = field(default_factory=list)


class BacktestEngine:
    """
    Backtesting engine for strategy evaluation
    
    Features:
    - Historical data replay
    - Position management
    - Performance metrics
    - Transaction costs
    - Slippage simulation
    """
    
    def __init__(self, initial_balance: float = 10000.0, 
                 commission_pips: float = 2.0,
                 slippage_pips: float = 1.0,
                 leverage: int = 100):
        """
        Initialize backtest engine
        
        Args:
            initial_balance: Starting balance
            commission_pips: Commission per trade in pips
            slippage_pips: Slippage per trade in pips
            leverage: Account leverage
        """
        self.initial_balance = initial_balance
        self.commission_pips = commission_pips
        self.slippage_pips = slippage_pips
        self.leverage = leverage
        
        self.balance = initial_balance
        self.equity = initial_balance
        self.positions: List[BacktestPosition] = []
        self.open_positions: List[BacktestPosition] = []
        
        logger.info(f"Backtest engine initialized: Balance=${initial_balance}, Commission={commission_pips}pips")
    
    def run(self, strategy: BaseStrategy, bars: List[OHLCBar],
            symbol: str = "EURUSD", timeframe: str = "H1",
            volume: float = 0.01, max_positions: int = 1) -> BacktestMetrics:
        """
        Run backtest on historical data
        
        Args:
            strategy: Trading strategy to test
            bars: Historical OHLC bars
            symbol: Trading symbol (default: EURUSD)
            timeframe: Timeframe (default: H1)
            volume: Trade volume (lots)
            max_positions: Maximum concurrent positions
            
        Returns:
            BacktestMetrics with performance results
        """
        logger.info(f"Starting backtest: {strategy.name} on {len(bars)} bars")
        
        # Reset state
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.positions = []
        self.open_positions = []
        
        equity_curve = [self.initial_balance]
        dates = [bars[0].time if bars else datetime.now()]
        
        # Minimum bars needed for strategy
        min_bars = 50  # Conservative minimum
        
        # Iterate through bars
        for i in range(min_bars, len(bars)):
            current_bar = bars[i]
            historical_bars = bars[:i+1]
            
            # Update open positions (check SL/TP)
            self._update_positions(current_bar)
            
            # Generate signal if we can open more positions
            if len(self.open_positions) < max_positions:
                signal = strategy.analyze(symbol, timeframe, historical_bars)
                
                if signal:
                    self._open_position(signal, current_bar, volume)
            
            # Update equity
            self._update_equity(current_bar)
            equity_curve.append(self.equity)
            dates.append(current_bar.time)
        
        # Close any remaining positions at end
        if bars:
            last_bar = bars[-1]
            for position in self.open_positions[:]:
                self._close_position(position, last_bar.close, last_bar.time, "End of backtest")
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        metrics.equity_curve = equity_curve
        metrics.dates = dates
        
        logger.info(f"Backtest complete: {metrics.total_trades} trades, "
                   f"Win Rate: {metrics.win_rate:.1f}%, "
                   f"Total Profit: ${metrics.total_profit:.2f}")
        
        return metrics
    
    def _open_position(self, signal: Signal, bar: OHLCBar, volume: float):
        """Open a new position"""
        # Apply slippage
        pip_value = 0.0001 if 'JPY' not in signal.symbol else 0.01
        slippage = self.slippage_pips * pip_value
        
        if signal.type == SignalType.BUY:
            entry_price = signal.price + slippage
            position_type = OrderType.BUY
        else:
            entry_price = signal.price - slippage
            position_type = OrderType.SELL
        
        # Create position
        position = BacktestPosition(
            entry_time=bar.time,
            entry_price=entry_price,
            position_type=position_type,
            volume=volume,
            symbol=signal.symbol,
            sl=signal.stop_loss,
            tp=signal.take_profit
        )
        
        # Apply commission
        commission = self.commission_pips * pip_value * volume * 100000  # Per standard lot
        self.balance -= commission
        
        self.open_positions.append(position)
        self.positions.append(position)
        
        logger.debug(f"Opened {position_type.value} position at {entry_price:.5f}")
    
    def _update_positions(self, bar: OHLCBar):
        """Check and update open positions"""
        for position in self.open_positions[:]:
            # Check if SL or TP hit
            if position.position_type == OrderType.BUY:
                # Check SL
                if position.sl is not None and bar.low <= position.sl:
                    self._close_position(position, position.sl, bar.time, "Stop Loss")
                    continue
                # Check TP
                if position.tp is not None and bar.high >= position.tp:
                    self._close_position(position, position.tp, bar.time, "Take Profit")
                    continue
            else:  # SELL
                # Check SL
                if position.sl is not None and bar.high >= position.sl:
                    self._close_position(position, position.sl, bar.time, "Stop Loss")
                    continue
                # Check TP
                if position.tp is not None and bar.low <= position.tp:
                    self._close_position(position, position.tp, bar.time, "Take Profit")
                    continue
    
    def _close_position(self, position: BacktestPosition, exit_price: float, 
                       exit_time: datetime, reason: str):
        """Close a position"""
        position.exit_price = exit_price
        position.exit_time = exit_time
        position.exit_reason = reason
        position.status = PositionStatus.CLOSED
        
        # Calculate profit
        pip_value = 0.0001 if 'JPY' not in position.symbol else 0.01  # Simplified
        
        if position.position_type == OrderType.BUY:
            profit_pips = (exit_price - position.entry_price) / pip_value
        else:
            profit_pips = (position.entry_price - exit_price) / pip_value
        
        # Simplified P&L calculation (per standard lot)
        profit = profit_pips * pip_value * position.volume * 100000
        
        # Apply commission on exit
        commission = self.commission_pips * pip_value * position.volume * 100000
        profit -= commission
        
        position.profit = profit
        position.profit_pips = profit_pips
        
        self.balance += profit
        
        # Remove from open positions
        if position in self.open_positions:
            self.open_positions.remove(position)
        
        logger.debug(f"Closed {position.position_type.value} position: "
                    f"Profit=${profit:.2f} ({profit_pips:.1f} pips) - {reason}")
    
    def _update_equity(self, bar: OHLCBar):
        """Update equity including unrealized P&L"""
        unrealized_pnl = 0.0
        pip_value = 0.0001  # Default for most pairs
        
        for position in self.open_positions:
            if position.position_type == OrderType.BUY:
                pnl_pips = (bar.close - position.entry_price) / pip_value
            else:
                pnl_pips = (position.entry_price - bar.close) / pip_value
            
            unrealized_pnl += pnl_pips * pip_value * position.volume * 100000
        
        self.equity = self.balance + unrealized_pnl
    
    def _calculate_metrics(self) -> BacktestMetrics:
        """Calculate performance metrics"""
        metrics = BacktestMetrics()
        
        closed_positions = [p for p in self.positions if p.status == PositionStatus.CLOSED]
        
        if not closed_positions:
            return metrics
        
        metrics.total_trades = len(closed_positions)
        
        profits = [p.profit for p in closed_positions]
        profits_pips = [p.profit_pips for p in closed_positions]
        
        # Win/Loss counts
        metrics.winning_trades = sum(1 for p in profits if p > 0)
        metrics.losing_trades = sum(1 for p in profits if p < 0)
        metrics.break_even_trades = sum(1 for p in profits if p == 0)
        
        # Profit metrics
        metrics.total_profit = sum(profits)
        metrics.total_profit_pips = sum(profits_pips)
        metrics.avg_profit = np.mean(profits)
        metrics.avg_profit_pips = np.mean(profits_pips)
        metrics.max_win = max(profits)
        metrics.max_loss = min(profits)
        
        # Win rate
        metrics.win_rate = (metrics.winning_trades / metrics.total_trades * 100) if metrics.total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(p for p in profits if p > 0)
        gross_loss = abs(sum(p for p in profits if p < 0))
        metrics.profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        # Average win/loss
        winning_profits = [p for p in profits if p > 0]
        losing_profits = [p for p in profits if p < 0]
        metrics.avg_win = np.mean(winning_profits) if winning_profits else 0
        metrics.avg_loss = np.mean(losing_profits) if losing_profits else 0
        
        # Drawdown
        if hasattr(self, 'equity_curve') or len(profits) > 0:
            metrics.max_drawdown, metrics.max_drawdown_pct = self._calculate_drawdown(profits)
        
        # Sharpe ratio (simplified)
        if len(profits) > 1:
            returns = np.array(profits) / self.initial_balance
            metrics.sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Win/Loss streaks
        metrics.largest_win_streak = self._calculate_max_streak(profits, True)
        metrics.largest_loss_streak = self._calculate_max_streak(profits, False)
        
        # Average trade duration
        durations = []
        for p in closed_positions:
            if p.exit_time and p.entry_time:
                duration = (p.exit_time - p.entry_time).total_seconds() / 3600  # hours
                durations.append(duration)
        metrics.avg_trade_duration = np.mean(durations) if durations else 0
        
        return metrics
    
    def _calculate_drawdown(self, profits: List[float]) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        
        max_dd = np.max(drawdown) if len(drawdown) > 0 else 0
        max_dd_pct = (max_dd / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
        return max_dd, max_dd_pct
    
    def _calculate_max_streak(self, profits: List[float], winning: bool) -> int:
        """Calculate maximum consecutive win or loss streak"""
        if not profits:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for profit in profits:
            if (winning and profit > 0) or (not winning and profit < 0):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak

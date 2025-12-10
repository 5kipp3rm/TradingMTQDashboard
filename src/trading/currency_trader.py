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
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Optional ML/LLM imports
try:
    from src.ml import FeatureEngineer, RandomForestClassifier, LSTMPricePredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

try:
    from src.llm import SentimentAnalyzer, MarketAnalyst
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


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
    
    # Position stacking (allows multiple positions in same direction)
    allow_position_stacking: bool = False  # Enable to stack positions during strong trends
    max_positions_same_direction: int = 1  # Max positions in same direction (BUY or SELL)
    max_total_positions: int = 5  # Max total positions for this symbol
    stacking_risk_multiplier: float = 1.0  # Risk multiplier for stacked positions (e.g., 1.2 = 20% more)
    
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
                 connector: BaseMetaTraderConnector,
                 intelligent_manager=None):
        """
        Initialize currency trader
        
        Args:
            config: Trading configuration for this currency
            connector: Shared MT5 connector
            intelligent_manager: Optional intelligent position manager for AI decisions
        """
        self.config = config
        self.connector = connector
        self.intelligent_manager = intelligent_manager
        
        # State management
        self.last_signal: Optional[Signal] = None
        self.last_trade_time: Optional[datetime] = None
        self.last_signal_type: Optional[SignalType] = None
        
        # Statistics
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_profit = 0.0
        
        # ML/LLM components (optional)
        self.ml_model = None
        self.sentiment_analyzer = None
        self.market_analyst = None
        self.use_ml_enhancement = False
        self.use_sentiment_filter = False
        
        # Validation
        self.is_valid = self._validate_symbol()
    
    def _validate_symbol(self) -> bool:
        """Validate symbol is available"""
        symbol_info = self.connector.get_symbol_info(self.config.symbol)
        if not symbol_info:
            print(f"⚠️  Warning: Symbol {self.config.symbol} not available on this broker")
            return False
        return True
    
    def enable_ml_enhancement(self, ml_model):
        """Enable ML-enhanced trading"""
        if ML_AVAILABLE:
            self.ml_model = ml_model
            self.use_ml_enhancement = True
            print(f"✅ [{self.config.symbol}] ML enhancement enabled")
        else:
            print(f"⚠️  ML libraries not available")
    
    def enable_sentiment_filter(self, sentiment_analyzer, market_analyst=None):
        """Enable LLM sentiment filtering"""
        if LLM_AVAILABLE:
            self.sentiment_analyzer = sentiment_analyzer
            self.market_analyst = market_analyst
            self.use_sentiment_filter = True
            print(f"✅ [{self.config.symbol}] LLM sentiment filter enabled")
        else:
            print(f"⚠️  LLM libraries not available")
    
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
                logger.debug(f"[{self.config.symbol}] No bars returned from connector")
                return None
            
            logger.debug(f"[{self.config.symbol}] Got {len(bars)} bars for analysis")
            
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
                    reason=f"Fast MA({self.config.fast_period})={'>' if fast_ma > slow_ma else '<' if fast_ma < slow_ma else '='}Slow MA({self.config.slow_period})"
                )
                
                # Log signal generation for monitoring
                logger.info(f"[{self.config.symbol}] 📊 MA Analysis: Fast={fast_ma:.5f}, Slow={slow_ma:.5f} → Signal: {signal_type.name}")
                logger.info(f"[{self.config.symbol}] 🔄 Last signal type: {self.last_signal_type.name if self.last_signal_type else 'None'}")
            else:
                # Crossover-based trading (waits for actual cross)
                signal = self.config.strategy.analyze(
                    self.config.symbol, 
                    self.config.timeframe, 
                    bars
                )
            
            self.last_signal = signal
            
            # ML Enhancement (if enabled)
            if self.use_ml_enhancement and self.ml_model and signal.type != SignalType.HOLD:
                signal = self._enhance_with_ml(signal, bars)
            
            # LLM Sentiment Filter (if enabled)
            if self.use_sentiment_filter and self.sentiment_analyzer and signal.type != SignalType.HOLD:
                signal = self._apply_sentiment_filter(signal)
            
            return signal
            
        except Exception as e:
            print(f"[{self.config.symbol}] Analysis error: {e}")
            return None
    
    def _enhance_with_ml(self, signal: Signal, bars: list) -> Signal:
        """
        Enhance signal with ML prediction
        
        Args:
            signal: Base technical signal
            bars: OHLC bars
            
        Returns:
            Enhanced signal with ML confidence
        """
        try:
            from src.ml import FeatureEngineer
            import pandas as pd
            
            # Convert bars to DataFrame
            df = pd.DataFrame([{
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': getattr(bar, 'tick_volume', 0)  # Handle both tick_volume and volume
            } for bar in bars])
            
            # Generate features
            feature_engineer = FeatureEngineer()
            feature_set = feature_engineer.transform(df)
            
            if len(feature_set.features) == 0:
                return signal
            
            # Get latest features (keep as DataFrame to preserve feature names)
            X = feature_set.features.iloc[-1:]
            
            # Predict
            prediction = self.ml_model.predict(X)
            
            # Convert ML prediction to signal type
            if prediction.prediction > 0:
                ml_signal_type = SignalType.BUY
            elif prediction.prediction < 0:
                ml_signal_type = SignalType.SELL
            else:
                ml_signal_type = SignalType.HOLD
            
            # Combine with technical signal
            if ml_signal_type == signal.type:
                # ML agrees - boost confidence
                new_confidence = min(1.0, (signal.confidence * 0.4) + (prediction.confidence * 0.6))
                signal.confidence = new_confidence
                signal.reason += f" | ML: {ml_signal_type.value} ({prediction.confidence:.2f})"
                signal.metadata['ml_confidence'] = prediction.confidence
                signal.metadata['ml_agrees'] = True
                logger.info(f"  🧠 ML agrees: {ml_signal_type.value} (confidence {new_confidence:.2f})")
            else:
                # ML disagrees - reduce confidence or change signal
                if prediction.confidence > 0.75:
                    # ML is very confident - switch to ML signal
                    signal.type = ml_signal_type
                    signal.confidence = prediction.confidence * 0.8
                    signal.reason = f"ML override: {ml_signal_type.value} ({prediction.confidence:.2f})"
                    signal.metadata['ml_confidence'] = prediction.confidence
                    signal.metadata['ml_override'] = True
                    logger.info(f"  🧠 ML override: {ml_signal_type.value} (confidence {prediction.confidence:.2f})")
                else:
                    # ML is uncertain - reduce technical confidence
                    signal.confidence *= 0.6
                    signal.reason += f" | ML uncertain"
                    signal.metadata['ml_confidence'] = prediction.confidence
                    signal.metadata['ml_agrees'] = False
                    logger.info(f"  🧠 ML disagrees - reduced confidence to {signal.confidence:.2f}")
            
            return signal
            
        except Exception as e:
            logger.warning(f"  ⚠️  ML enhancement failed: {e}")
            return signal
    
    def _apply_sentiment_filter(self, signal: Signal) -> Signal:
        """
        Filter signal using LLM sentiment analysis
        
        Args:
            signal: Signal to filter
            
        Returns:
            Filtered signal (may be changed to HOLD)
        """
        try:
            # For now, we'll use a simplified sentiment check
            # In production, you'd scrape news or use real-time data
            
            # Placeholder: Random sentiment for demo
            # In real implementation, use: self.sentiment_analyzer.analyze_text(news, symbol)
            
            # For now, just log that sentiment filter is available
            signal.metadata['sentiment_enabled'] = True
            signal.reason += " | Sentiment: Enabled"
            
            print(f"  🤖 LLM sentiment filter active")
            
            return signal
            
        except Exception as e:
            print(f"  ⚠️  Sentiment filter failed: {e}")
            return signal
    
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
            logger.info(f"[{self.config.symbol}] ⏸️  HOLD signal - no action needed")
            return False
        
        # Check cooldown
        if not self.can_trade():
            remaining = (self.last_trade_time + timedelta(seconds=self.config.cooldown_seconds) - datetime.now()).total_seconds()
            logger.info(f"[{self.config.symbol}] ⏱️  Cooldown active - {remaining:.0f}s remaining")
            return False
        
        # For position trading, check if we should allow position stacking
        if self.config.use_position_trading:
            # Check current positions to show in logs
            current_positions = self.connector.get_positions(self.config.symbol)
            pos_info = ""
            positions_same_direction = 0
            
            if current_positions:
                tickets = ", ".join([f"#{p.ticket}" for p in current_positions[:3]])
                if len(current_positions) > 3:
                    tickets += f" +{len(current_positions)-3}"
                pos_info = f" (Current: {tickets})"
                
                # Count positions in same direction
                for pos in current_positions:
                    if signal.type == SignalType.BUY and pos.type == 0:  # MT5: 0=BUY
                        positions_same_direction += 1
                    elif signal.type == SignalType.SELL and pos.type == 1:  # MT5: 1=SELL
                        positions_same_direction += 1
            
            # Check if position stacking is enabled (via config or default behavior)
            allow_stacking = getattr(self.config, 'allow_position_stacking', False)
            max_positions_same_dir = getattr(self.config, 'max_positions_same_direction', 1)
            
            if signal.type == self.last_signal_type:
                # Same signal as before
                if allow_stacking and positions_same_direction < max_positions_same_dir:
                    # Allow stacking: add another position in same direction
                    logger.info(f"[{self.config.symbol}] 📊 Position STACKING: Adding position #{positions_same_direction + 1} in {signal.type.name} direction{pos_info}")
                    return True
                else:
                    # No stacking: skip duplicate signal
                    logger.info(f"[{self.config.symbol}] 🔄 Position trading: {signal.type.name} matches last signal ({self.last_signal_type.name}) - SKIP{pos_info}")
                    return False
            else:
                # Signal changed direction
                logger.info(f"[{self.config.symbol}] 🔄 Position trading: Signal changed from {self.last_signal_type.name if self.last_signal_type else 'None'} to {signal.type.name} - EXECUTE{pos_info}")
        
        logger.info(f"[{self.config.symbol}] ✅ Signal approved for execution: {signal.type.name}")
        return True
    
    def calculate_lot_size(self, signal: Signal) -> float:
        """
        Calculate position size based on risk
        Applies risk multiplier for stacked positions
        
        Args:
            signal: Trading signal with SL/TP
            
        Returns:
            Lot size (volume)
        """
        # Convert signal type to MT5 order type
        mt5_order_type = (mt5.ORDER_TYPE_BUY 
                         if signal.type == SignalType.BUY 
                         else mt5.ORDER_TYPE_SELL)
        
        # Check if this is a stacked position (same direction as existing)
        risk_percent = self.config.risk_percent
        current_positions = self.connector.get_positions(self.config.symbol)
        
        if current_positions and self.config.allow_position_stacking:
            # Count positions in same direction
            positions_same_direction = 0
            for pos in current_positions:
                if signal.type == SignalType.BUY and pos.type == 0:  # MT5: 0=BUY
                    positions_same_direction += 1
                elif signal.type == SignalType.SELL and pos.type == 1:  # MT5: 1=SELL
                    positions_same_direction += 1
            
            # Apply risk multiplier for stacked positions
            if positions_same_direction > 0:
                risk_percent *= self.config.stacking_risk_multiplier
                logger.info(f"[{self.config.symbol}] 📈 Stacking position #{positions_same_direction + 1}: Risk adjusted to {risk_percent:.2f}%")
        
        # Calculate risk-based lot size
        lot_size = AccountUtils.risk_based_lot_size(
            symbol=self.config.symbol,
            order_type=mt5_order_type,
            entry_price=signal.price,
            stop_loss=signal.stop_loss,
            risk_percent=risk_percent
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
                # last_signal_type already set in should_execute_signal
                self.total_trades += 1
                self.successful_trades += 1
                
                logger.info(f"✅ [{self.config.symbol}] {signal.type.name} "
                      f"{lot_size:.2f} lots @ {result.price:.5f} "
                      f"→ Ticket #{result.order_ticket}")
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
                logger.info(f"[{self.config.symbol}] ❌ No signal generated - market conditions not met")
                result['error'] = "Failed to generate signal"
                return result
            
            logger.info(f"[{self.config.symbol}] 🔍 Signal: {signal.type.name}, Confidence: {signal.confidence:.3f}, Price: {signal.price:.5f}")
            
            # Check if should execute
            if self.should_execute_signal(signal):
                # Update last signal type IMMEDIATELY after approval
                # (Don't wait for trade execution, as AI might reject it)
                self.last_signal_type = signal.type
                
                # If intelligent manager is available, check with it first
                if self.intelligent_manager and signal.type != SignalType.HOLD:
                    logger.info(f"[{self.config.symbol}] 🤖 Consulting AI for decision...")
                    decision = self.intelligent_manager.make_decision(signal)
                    
                    if not decision.allow_new_trade:
                        logger.info(f"🧠 [{self.config.symbol}] AI REJECTED: {decision.reasoning}")
                        result['executed'] = False
                        result['reason'] = decision.reasoning
                        return result
                    
                    logger.info(f"🧠 [{self.config.symbol}] AI APPROVED: {decision.reasoning}")
                
                # Execute the trade
                executed = self.execute_trade(signal)
                result['executed'] = executed
            else:
                logger.debug(f"[{self.config.symbol}] {signal.type.name} "
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

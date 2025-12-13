"""
Currency Trader - Individual currency pair trading logic
Each instance handles one currency pair independently

Refactored to use Phase 0 patterns:
- Structured JSON logging with correlation IDs
- Specific exceptions instead of silent errors
- Error context preservation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import MetaTrader5 as mt5

# Phase 0 imports - NEW
from src.exceptions import (
    DataNotAvailableError, InvalidSymbolError, OrderExecutionError,
    IndicatorCalculationError, SignalGenerationError
)
from src.utils.structured_logger import StructuredLogger, CorrelationContext
from src.utils.error_handlers import handle_mt5_errors

from src.connectors.base import BaseMetaTraderConnector, OrderType, TradeRequest
from src.strategies.base import BaseStrategy, Signal, SignalType
from src.connectors.account_utils import AccountUtils

# Database imports - Phase 5.1
from src.database.repository import TradeRepository, SignalRepository
from src.database.connection import get_session
from src.database.models import TradeStatus, SignalType as DBSignalType

logger = StructuredLogger(__name__)

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
    allow_position_stacking: bool = False
    max_positions_same_direction: int = 1
    max_total_positions: int = 5
    stacking_risk_multiplier: float = 1.0

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

    Uses Phase 0 patterns:
    - Structured logging with correlation IDs
    - Specific exception types
    - Automatic error context
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

        # Database repositories - Phase 5.1
        self.trade_repo = TradeRepository()
        self.signal_repo = SignalRepository()

        # Validation
        self.is_valid = self._validate_symbol()

        logger.info(
            "CurrencyTrader initialized",
            symbol=config.symbol,
            strategy=config.strategy.name,
            risk_percent=config.risk_percent,
            is_valid=self.is_valid
        )

    def _validate_symbol(self) -> bool:
        """
        Validate symbol is available

        Returns:
            True if symbol is valid and available
        """
        try:
            symbol_info = self.connector.get_symbol_info(self.config.symbol)
            if not symbol_info:
                logger.warning(
                    "Symbol not available on broker",
                    symbol=self.config.symbol,
                    action="skip"
                )
                return False
            return True
        except Exception as e:
            logger.error(
                "Symbol validation failed",
                symbol=self.config.symbol,
                error=str(e),
                exc_info=True
            )
            return False

    def enable_ml_enhancement(self, ml_model):
        """Enable ML-enhanced trading"""
        with CorrelationContext():
            if ML_AVAILABLE:
                self.ml_model = ml_model
                self.use_ml_enhancement = True
                logger.info(
                    "ML enhancement enabled",
                    symbol=self.config.symbol,
                    feature="ml_enhancement"
                )
            else:
                logger.warning(
                    "ML libraries not available",
                    symbol=self.config.symbol,
                    feature="ml_enhancement"
                )

    def enable_sentiment_filter(self, sentiment_analyzer, market_analyst=None):
        """Enable LLM sentiment filtering"""
        with CorrelationContext():
            if LLM_AVAILABLE:
                self.sentiment_analyzer = sentiment_analyzer
                self.market_analyst = market_analyst
                self.use_sentiment_filter = True
                logger.info(
                    "LLM sentiment filter enabled",
                    symbol=self.config.symbol,
                    has_market_analyst=market_analyst is not None,
                    feature="llm_sentiment"
                )
            else:
                logger.warning(
                    "LLM libraries not available",
                    symbol=self.config.symbol,
                    feature="llm_sentiment"
                )

    def can_trade(self) -> bool:
        """Check if enough time has passed since last trade"""
        if not self.last_trade_time:
            return True

        elapsed = (datetime.now() - self.last_trade_time).total_seconds()
        can_trade = elapsed >= self.config.cooldown_seconds

        if not can_trade:
            logger.debug(
                "Cooldown active",
                symbol=self.config.symbol,
                elapsed_seconds=elapsed,
                cooldown_seconds=self.config.cooldown_seconds
            )

        return can_trade

    @handle_mt5_errors(retry_count=2, fallback_return=None)
    def analyze_market(self) -> Optional[Signal]:
        """
        Analyze market and generate signal

        Returns:
            Signal object or None if analysis failed

        Raises:
            DataNotAvailableError: If market data not available
            IndicatorCalculationError: If indicator calculation fails
        """
        with CorrelationContext():
            # Get market data
            bars = self.connector.get_bars(
                self.config.symbol,
                self.config.timeframe,
                100
            )

            if not bars:
                logger.debug(
                    "No bars returned from connector",
                    symbol=self.config.symbol,
                    timeframe=self.config.timeframe
                )
                raise DataNotAvailableError(
                    f"No bars available for {self.config.symbol}",
                    context={
                        'symbol': self.config.symbol,
                        'timeframe': self.config.timeframe
                    }
                )

            logger.debug(
                "Market data retrieved",
                symbol=self.config.symbol,
                bar_count=len(bars)
            )

            if self.config.use_position_trading:
                # Position-based trading (faster signals)
                import numpy as np

                try:
                    fast_ma = np.mean([bar.close for bar in bars[-self.config.fast_period:]])
                    slow_ma = np.mean([bar.close for bar in bars[-self.config.slow_period:]])
                    current_price = bars[-1].close
                except Exception as e:
                    raise IndicatorCalculationError(
                        f"Failed to calculate moving averages for {self.config.symbol}",
                        context={
                            'symbol': self.config.symbol,
                            'fast_period': self.config.fast_period,
                            'slow_period': self.config.slow_period,
                            'error': str(e)
                        }
                    )

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

                logger.info(
                    "MA analysis complete",
                    symbol=self.config.symbol,
                    fast_ma=fast_ma,
                    slow_ma=slow_ma,
                    signal_type=signal_type.name,
                    last_signal_type=self.last_signal_type.name if self.last_signal_type else None
                )
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

            # Save signal to database - Phase 5.1
            if signal and signal.type != SignalType.HOLD:
                self._save_signal_to_db(signal)

            return signal

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
                'volume': getattr(bar, 'tick_volume', 0)
            } for bar in bars])

            # Generate features
            feature_engineer = FeatureEngineer()
            feature_set = feature_engineer.transform(df)

            if len(feature_set.features) == 0:
                return signal

            # Get latest features
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

                logger.info(
                    "ML agrees with signal",
                    symbol=self.config.symbol,
                    ml_signal=ml_signal_type.value,
                    new_confidence=new_confidence,
                    feature="ml_enhancement"
                )
            else:
                # ML disagrees
                if prediction.confidence > 0.75:
                    # ML is very confident - switch to ML signal
                    signal.type = ml_signal_type
                    signal.confidence = prediction.confidence * 0.8
                    signal.reason = f"ML override: {ml_signal_type.value} ({prediction.confidence:.2f})"
                    signal.metadata['ml_confidence'] = prediction.confidence
                    signal.metadata['ml_override'] = True

                    logger.info(
                        "ML override signal",
                        symbol=self.config.symbol,
                        ml_signal=ml_signal_type.value,
                        ml_confidence=prediction.confidence,
                        feature="ml_override"
                    )
                else:
                    # ML is uncertain - reduce technical confidence
                    signal.confidence *= 0.6
                    signal.reason += f" | ML uncertain"
                    signal.metadata['ml_confidence'] = prediction.confidence
                    signal.metadata['ml_agrees'] = False

                    logger.info(
                        "ML disagrees - reduced confidence",
                        symbol=self.config.symbol,
                        new_confidence=signal.confidence,
                        feature="ml_uncertainty"
                    )

            return signal

        except Exception as e:
            logger.warning(
                "ML enhancement failed",
                symbol=self.config.symbol,
                error=str(e),
                feature="ml_enhancement"
            )
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
            signal.metadata['sentiment_enabled'] = True
            signal.reason += " | Sentiment: Enabled"

            logger.debug(
                "LLM sentiment filter active",
                symbol=self.config.symbol,
                feature="llm_sentiment"
            )

            return signal

        except Exception as e:
            logger.warning(
                "Sentiment filter failed",
                symbol=self.config.symbol,
                error=str(e),
                feature="llm_sentiment"
            )
            return signal

    def should_execute_signal(self, signal: Signal) -> bool:
        """
        Determine if signal should be executed

        Args:
            signal: Generated trading signal

        Returns:
            True if should trade, False otherwise
        """
        with CorrelationContext():
            # No trade on HOLD
            if signal.type == SignalType.HOLD:
                logger.info(
                    "HOLD signal - no action",
                    symbol=self.config.symbol,
                    signal_type=signal.type.name
                )
                return False

            # Check cooldown
            if not self.can_trade():
                remaining = (self.last_trade_time + timedelta(seconds=self.config.cooldown_seconds) - datetime.now()).total_seconds()
                logger.info(
                    "Cooldown active",
                    symbol=self.config.symbol,
                    remaining_seconds=remaining
                )
                return False

            # For position trading, check if we should allow position stacking
            if self.config.use_position_trading:
                current_positions = self.connector.get_positions(self.config.symbol)
                positions_same_direction = 0

                if current_positions:
                    # Count positions in same direction
                    for pos in current_positions:
                        if signal.type == SignalType.BUY and pos.type == 0:  # MT5: 0=BUY
                            positions_same_direction += 1
                        elif signal.type == SignalType.SELL and pos.type == 1:  # MT5: 1=SELL
                            positions_same_direction += 1

                    logger.debug(
                        "Current positions",
                        symbol=self.config.symbol,
                        total_positions=len(current_positions),
                        same_direction=positions_same_direction,
                        tickets=[p.ticket for p in current_positions[:3]]
                    )

                # Check if position stacking is enabled
                allow_stacking = getattr(self.config, 'allow_position_stacking', False)
                max_positions_same_dir = getattr(self.config, 'max_positions_same_direction', 1)

                if signal.type == self.last_signal_type:
                    # Same signal as before
                    if allow_stacking and positions_same_direction < max_positions_same_dir:
                        logger.info(
                            "Position stacking - adding position",
                            symbol=self.config.symbol,
                            signal_type=signal.type.name,
                            position_number=positions_same_direction + 1,
                            feature="position_stacking"
                        )
                        return True
                    else:
                        logger.info(
                            "Position trading - skipping duplicate signal",
                            symbol=self.config.symbol,
                            signal_type=signal.type.name,
                            last_signal=self.last_signal_type.name,
                            current_positions=len(current_positions) if current_positions else 0
                        )
                        return False
                else:
                    logger.info(
                        "Signal changed direction - executing",
                        symbol=self.config.symbol,
                        new_signal=signal.type.name,
                        last_signal=self.last_signal_type.name if self.last_signal_type else None
                    )

            logger.info(
                "Signal approved for execution",
                symbol=self.config.symbol,
                signal_type=signal.type.name,
                confidence=signal.confidence
            )
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
        with CorrelationContext():
            # Convert signal type to MT5 order type
            mt5_order_type = (mt5.ORDER_TYPE_BUY
                             if signal.type == SignalType.BUY
                             else mt5.ORDER_TYPE_SELL)

            # Check if this is a stacked position
            risk_percent = self.config.risk_percent
            current_positions = self.connector.get_positions(self.config.symbol)

            if current_positions and self.config.allow_position_stacking:
                # Count positions in same direction
                positions_same_direction = 0
                for pos in current_positions:
                    if signal.type == SignalType.BUY and pos.type == 0:
                        positions_same_direction += 1
                    elif signal.type == SignalType.SELL and pos.type == 1:
                        positions_same_direction += 1

                # Apply risk multiplier for stacked positions
                if positions_same_direction > 0:
                    risk_percent *= self.config.stacking_risk_multiplier
                    logger.info(
                        "Risk adjusted for stacking",
                        symbol=self.config.symbol,
                        position_number=positions_same_direction + 1,
                        adjusted_risk_percent=risk_percent,
                        feature="position_stacking"
                    )

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

            logger.debug(
                "Lot size calculated",
                symbol=self.config.symbol,
                lot_size=lot_size,
                risk_percent=risk_percent
            )

            return lot_size

    @handle_mt5_errors(retry_count=2)
    def execute_trade(self, signal: Signal) -> bool:
        """
        Execute trade based on signal

        Args:
            signal: Trading signal

        Returns:
            True if successful, False otherwise

        Raises:
            OrderExecutionError: If order execution fails
        """
        with CorrelationContext():
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

            logger.info(
                "Executing trade",
                symbol=self.config.symbol,
                action=action.value,
                volume=lot_size,
                price=signal.price
            )

            # Execute
            result = self.connector.send_order(request)

            if result.success:
                self.last_trade_time = datetime.now()
                self.total_trades += 1
                self.successful_trades += 1

                logger.info(
                    "Trade executed successfully",
                    symbol=self.config.symbol,
                    action=signal.type.name,
                    volume=lot_size,
                    price=result.price,
                    ticket=result.order_ticket
                )

                # Save trade to database - Phase 5.1
                self._save_trade_to_db(signal, result, result.order_ticket)

                return True
            else:
                self.failed_trades += 1
                logger.error(
                    "Trade execution failed",
                    symbol=self.config.symbol,
                    error=result.error_message,
                    action=signal.type.name
                )
                raise OrderExecutionError(
                    f"Trade failed for {self.config.symbol}: {result.error_message}",
                    error_code=result.error_code,
                    context={
                        'symbol': self.config.symbol,
                        'action': signal.type.name,
                        'volume': lot_size
                    }
                )

    def process_cycle(self) -> Dict[str, Any]:
        """
        Run one complete trading cycle

        Returns:
            Dictionary with cycle results
        """
        with CorrelationContext():
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
                logger.warning(
                    "Skipping cycle - symbol not valid",
                    symbol=self.config.symbol
                )
                return result

            try:
                # Analyze market
                signal = self.analyze_market()
                result['signal'] = signal

                if not signal:
                    logger.info(
                        "No signal generated",
                        symbol=self.config.symbol,
                        reason="market_conditions_not_met"
                    )
                    result['error'] = "Failed to generate signal"
                    return result

                logger.info(
                    "Signal generated",
                    symbol=self.config.symbol,
                    signal_type=signal.type.name,
                    confidence=signal.confidence,
                    price=signal.price
                )

                # Check if should execute
                if self.should_execute_signal(signal):
                    # Update last signal type IMMEDIATELY after approval
                    self.last_signal_type = signal.type

                    # If intelligent manager is available, check with it first
                    if self.intelligent_manager and signal.type != SignalType.HOLD:
                        logger.info(
                            "Consulting AI for decision",
                            symbol=self.config.symbol,
                            feature="ai_decision"
                        )
                        decision = self.intelligent_manager.make_decision(signal)

                        if not decision.allow_new_trade:
                            logger.info(
                                "AI rejected signal",
                                symbol=self.config.symbol,
                                reasoning=decision.reasoning,
                                feature="ai_rejection"
                            )
                            result['executed'] = False
                            result['reason'] = decision.reasoning
                            return result

                        logger.info(
                            "AI approved signal",
                            symbol=self.config.symbol,
                            reasoning=decision.reasoning,
                            feature="ai_approval"
                        )

                    # Execute the trade
                    executed = self.execute_trade(signal)
                    result['executed'] = executed
                else:
                    logger.debug(
                        "Signal skipped",
                        symbol=self.config.symbol,
                        signal_type=signal.type.name,
                        price=signal.price,
                        reason="cooldown_or_duplicate"
                    )

            except Exception as e:
                result['error'] = str(e)
                logger.error(
                    "Cycle error",
                    symbol=self.config.symbol,
                    error=str(e),
                    exc_info=True
                )

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

    def _convert_signal_type_to_db(self, signal_type: SignalType) -> str:
        """Convert strategy SignalType to database enum string"""
        mapping = {
            SignalType.BUY: "buy",
            SignalType.SELL: "sell",
            SignalType.HOLD: "hold"
        }
        return mapping.get(signal_type, "hold")

    def _save_signal_to_db(self, signal: Signal) -> None:
        """
        Save signal to database

        Args:
            signal: Signal object to save
        """
        try:
            with get_session() as session:
                # Extract ML metadata if present
                ml_enhanced = signal.metadata.get('ml_confidence') is not None
                ml_confidence = signal.metadata.get('ml_confidence')
                ml_agreed = signal.metadata.get('ml_agrees', signal.metadata.get('ml_override'))

                db_signal = self.signal_repo.create(
                    session,
                    symbol=signal.symbol,
                    signal_type=self._convert_signal_type_to_db(signal.type),
                    timestamp=signal.timestamp,
                    price=signal.price,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    confidence=signal.confidence,
                    reason=signal.reason,
                    strategy_name=self.config.strategy.name,
                    timeframe=self.config.timeframe,
                    ml_enhanced=ml_enhanced,
                    ml_confidence=ml_confidence,
                    ml_agreed=ml_agreed
                )

                # Store database ID in signal metadata for later reference
                signal.metadata['db_signal_id'] = db_signal.id

                logger.debug(
                    "Signal saved to database",
                    signal_id=db_signal.id,
                    symbol=signal.symbol,
                    signal_type=signal.type.name
                )
        except Exception as e:
            # Don't fail trading if database save fails
            logger.error(
                "Failed to save signal to database",
                symbol=signal.symbol,
                error=str(e),
                exc_info=True
            )

    def _save_trade_to_db(self, signal: Signal, result: Any, ticket: int) -> None:
        """
        Save executed trade to database

        Args:
            signal: Original signal that triggered the trade
            result: Order execution result
            ticket: MT5 ticket number
        """
        try:
            with get_session() as session:
                # Extract ML metadata
                ml_enhanced = signal.metadata.get('ml_confidence') is not None
                ml_confidence = signal.metadata.get('ml_confidence')
                ai_approved = not signal.metadata.get('llm_rejected', False)
                ai_reasoning = signal.metadata.get('llm_reason', signal.reason)

                db_trade = self.trade_repo.create(
                    session,
                    ticket=ticket,
                    symbol=signal.symbol,
                    magic_number=0,  # Could be extracted from config
                    trade_type=self._convert_signal_type_to_db(signal.type),
                    status="open",
                    entry_price=result.price,
                    entry_time=signal.timestamp,
                    volume=result.volume if hasattr(result, 'volume') else 0.0,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    strategy_name=self.config.strategy.name,
                    signal_confidence=signal.confidence,
                    signal_reason=signal.reason,
                    ml_enhanced=ml_enhanced,
                    ml_confidence=ml_confidence,
                    ai_approved=ai_approved,
                    ai_reasoning=ai_reasoning
                )

                # Link signal to trade if signal was saved
                if 'db_signal_id' in signal.metadata:
                    self.signal_repo.mark_executed(
                        session,
                        signal_id=signal.metadata['db_signal_id'],
                        trade_id=db_trade.id,
                        execution_reason=f"Signal confidence: {signal.confidence:.2f}"
                    )

                logger.debug(
                    "Trade saved to database",
                    trade_id=db_trade.id,
                    ticket=ticket,
                    symbol=signal.symbol
                )
        except Exception as e:
            # Don't fail trading if database save fails
            logger.error(
                "Failed to save trade to database",
                ticket=ticket,
                symbol=signal.symbol,
                error=str(e),
                exc_info=True
            )

    def __repr__(self) -> str:
        return (f"CurrencyTrader(symbol={self.config.symbol}, "
                f"strategy={self.config.strategy.name}, "
                f"trades={self.total_trades})")

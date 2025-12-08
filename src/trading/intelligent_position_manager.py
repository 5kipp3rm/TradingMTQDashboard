"""
Intelligent Position Manager
Uses ML/LLM to make smart decisions about when to open/close positions
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

from src.connectors.base import BaseMetaTraderConnector
from src.strategies.base import Signal, SignalType

logger = logging.getLogger(__name__)


class PositionAction(Enum):
    """Actions the intelligent manager can recommend"""
    OPEN_NEW = "OPEN_NEW"
    CLOSE_LOSING = "CLOSE_LOSING"
    CLOSE_WINNING = "CLOSE_WINNING"
    HOLD = "HOLD"
    REDUCE_EXPOSURE = "REDUCE_EXPOSURE"


@dataclass
class PositionDecision:
    """Decision about position management"""
    action: PositionAction
    confidence: float  # 0.0 to 1.0
    reasoning: str
    positions_to_close: List[int] = None  # Ticket numbers
    allow_new_trade: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.positions_to_close is None:
            self.positions_to_close = []
        if self.metadata is None:
            self.metadata = {}


class IntelligentPositionManager:
    """
    Smart position manager that uses ML/LLM to decide:
    - When to open new positions vs when to wait
    - Which losing positions to close early
    - When to take profits early
    - When to reduce overall exposure
    """
    
    def __init__(self, connector: BaseMetaTraderConnector):
        """
        Initialize intelligent position manager
        
        Args:
            connector: MT5 connector instance
        """
        self.connector = connector
        
        # Optional ML/LLM components
        self.ml_predictor = None
        self.llm_analyst = None
        self.sentiment_analyzer = None
        
        # State tracking
        self.position_history: List[Dict] = []
        self.recent_decisions: List[PositionDecision] = []
        
    def set_ml_predictor(self, predictor):
        """Set ML model for predictions"""
        self.ml_predictor = predictor
        print("✅ ML Predictor enabled for intelligent position management")
    
    def set_llm_analyst(self, analyst):
        """Set LLM analyst for market analysis"""
        self.llm_analyst = analyst
        print("✅ LLM Analyst enabled for intelligent position management")
    
    def set_sentiment_analyzer(self, analyzer):
        """Set sentiment analyzer"""
        self.sentiment_analyzer = analyzer
        print("✅ Sentiment Analyzer enabled for intelligent position management")
    
    def analyze_portfolio(self) -> Dict[str, Any]:
        """
        Analyze current portfolio state
        
        Returns:
            Dictionary with portfolio metrics
        """
        positions = self.connector.get_positions()
        
        if not positions:
            return {
                'total_positions': 0,
                'winning_positions': 0,
                'losing_positions': 0,
                'total_profit': 0.0,
                'largest_loss': 0.0,
                'largest_win': 0.0,
                'avg_profit': 0.0,
                'exposure_symbols': []
            }
        
        winning = [p for p in positions if p.profit > 0]
        losing = [p for p in positions if p.profit < 0]
        
        total_profit = sum(p.profit for p in positions)
        largest_loss = min([p.profit for p in positions]) if positions else 0.0
        largest_win = max([p.profit for p in positions]) if positions else 0.0
        
        # Get unique symbols (exposure)
        symbols = list(set(p.symbol for p in positions))
        
        return {
            'total_positions': len(positions),
            'winning_positions': len(winning),
            'losing_positions': len(losing),
            'total_profit': total_profit,
            'largest_loss': largest_loss,
            'largest_win': largest_win,
            'avg_profit': total_profit / len(positions) if positions else 0.0,
            'exposure_symbols': symbols,
            'positions': positions
        }
    
    def should_close_position(self, position, portfolio_state: Dict) -> PositionDecision:
        """
        Intelligent decision: Should we close this specific position?
        Actively monitors each position for risk management.
        
        Args:
            position: Current open position
            portfolio_state: Current portfolio metrics
            
        Returns:
            PositionDecision with recommendation
        """
        reasons = []
        confidence = 0.5  # Start neutral
        
        logger.info(f"🔍 Analyzing position #{position.ticket} {position.symbol}, P/L: ${position.profit:.2f}")
        
        # Factor 1: Large loss - close immediately
        if position.profit <= -50:
            confidence = 0.95
            reasons.append(f"Large loss ${position.profit:.2f}")
            logger.info(f"   ⚠️  CRITICAL: Large loss detected ${position.profit:.2f}")
        elif position.profit <= -30:
            confidence = 0.80
            reasons.append(f"Significant loss ${position.profit:.2f}")
            logger.info(f"   ⚠️  WARNING: Significant loss ${position.profit:.2f}")
        elif position.profit <= -15:
            confidence = 0.65
            reasons.append(f"Moderate loss ${position.profit:.2f}")
            logger.info(f"   🟡 CAUTION: Moderate loss ${position.profit:.2f}")
        
        # Factor 2: Position in wrong direction vs market
        # If we have signal analyzer, check if position direction is still valid
        total_profit = portfolio_state['total_profit']
        
        # Factor 3: Portfolio drawdown - close worst losers first
        if total_profit < -100:
            if position.profit < -20:
                confidence *= 1.3  # Increase urgency
                reasons.append("Portfolio in drawdown - cutting losses")
                logger.info(f"   🚨 Portfolio drawdown ${total_profit:.2f} - prioritizing close")
        
        # Factor 4: Time in losing position (if available)
        # Positions that have been losing for too long should be closed
        
        # Decision threshold
        logger.info(f"   🎯 Close Confidence: {confidence:.3f} (threshold: ≥0.65 close)")
        
        if confidence >= 0.65:
            logger.info(f"   ❌ DECISION: CLOSE POSITION #{position.ticket}")
            return PositionDecision(
                action=PositionAction.CLOSE_LOSING,
                confidence=confidence,
                reasoning=f"Close losing position: {', '.join(reasons)}",
                allow_new_trade=False,
                metadata={'position_ticket': position.ticket}
            )
        else:
            logger.info(f"   ✅ DECISION: KEEP POSITION #{position.ticket}")
            return PositionDecision(
                action=PositionAction.HOLD,
                confidence=confidence,
                reasoning=f"Hold position: P/L ${position.profit:.2f} acceptable",
                allow_new_trade=True,
                metadata={'position_ticket': position.ticket}
            )
    
    def should_open_new_position(self, signal: Signal, portfolio_state: Dict) -> PositionDecision:
        """
        Intelligent decision: Should we open a new position?
        
        Args:
            signal: Trading signal to evaluate
            portfolio_state: Current portfolio metrics
            
        Returns:
            PositionDecision with recommendation
        """
        reasons = []
        confidence = signal.confidence  # Start with signal confidence
        
        logger.info(f"🤖 AI Evaluation START: {signal.symbol} {signal.type.value}, Base confidence: {confidence:.3f}")
        
        # Factor 1: Current portfolio state
        total_positions = portfolio_state['total_positions']
        total_profit = portfolio_state['total_profit']
        losing_count = portfolio_state['losing_positions']
        
        # Show position tickets for transparency
        positions = portfolio_state.get('positions', [])
        position_summary = ", ".join([f"#{p.ticket}({p.symbol}:${p.profit:.0f})" for p in positions[:5]])
        if len(positions) > 5:
            position_summary += f" +{len(positions)-5} more"
        
        logger.info(f"   📊 Portfolio: {total_positions} pos, P/L: ${total_profit:.2f}, Losing: {losing_count}")
        if positions:
            logger.info(f"   📋 Positions: {position_summary}")
        
        # Factor 2: Portfolio health
        if total_profit < -100:  # Losing more than $100
            old_conf = confidence
            confidence *= 0.5
            logger.info(f"   ⚠️  Drawdown penalty: {old_conf:.3f} → {confidence:.3f} (P/L < -$100)")
            reasons.append(f"Portfolio in drawdown (${total_profit:.2f})")
        elif total_profit > 50:  # Winning
            old_conf = confidence
            confidence *= 1.2
            logger.info(f"   ✅ Profit boost: {old_conf:.3f} → {confidence:.3f} (P/L > $50)")
            reasons.append(f"Portfolio profitable (${total_profit:.2f})")
        
        # Factor 3: Too many losing positions
        if losing_count >= 2:
            old_conf = confidence
            confidence *= 0.6
            logger.info(f"   ⚠️  Losing positions penalty: {old_conf:.3f} → {confidence:.3f} ({losing_count} losing)")
            reasons.append(f"{losing_count} losing positions - reduce exposure")
        
        # Factor 4: Symbol already in portfolio (correlation risk)
        # Allow multiple positions in same symbol, but with awareness
        positions = portfolio_state.get('positions', [])
        positions_in_symbol = sum(1 for p in positions if p.symbol == signal.symbol)
        if positions_in_symbol > 0:
            old_conf = confidence
            if positions_in_symbol >= 5:
                # Too many positions in same symbol
                confidence *= 0.6
                logger.info(f"   ⚠️  High concentration: {old_conf:.3f} → {confidence:.3f} ({positions_in_symbol} in {signal.symbol})")
                reasons.append(f"{positions_in_symbol} positions in {signal.symbol} - high concentration risk")
            else:
                # Allowed, but track it
                confidence *= 0.95
                logger.info(f"   📍 Symbol awareness: {old_conf:.3f} → {confidence:.3f} ({positions_in_symbol} in {signal.symbol})")
                reasons.append(f"{positions_in_symbol} existing position(s) in {signal.symbol}")
        
        # Factor 5: ML prediction (if available)
        if self.ml_predictor:
            try:
                # Get ML confidence boost
                ml_confidence = signal.metadata.get('ml_confidence', 0.5)
                if ml_confidence > 0.75:
                    confidence *= 1.3
                    reasons.append(f"ML high confidence ({ml_confidence:.2f})")
                elif ml_confidence < 0.55:
                    confidence *= 0.7
                    reasons.append(f"ML low confidence ({ml_confidence:.2f})")
            except Exception as e:
                print(f"⚠️  ML evaluation failed: {e}")
        
        # Factor 6: Sentiment analysis (if available)
        if self.sentiment_analyzer:
            try:
                # Check if sentiment aligns with signal
                sentiment_signal = signal.metadata.get('sentiment_signal')
                if sentiment_signal:
                    if sentiment_signal == signal.type.value:
                        confidence *= 1.2
                        reasons.append("Sentiment aligned with signal")
                    else:
                        confidence *= 0.6
                        reasons.append("Sentiment conflicts with signal")
            except Exception as e:
                print(f"⚠️  Sentiment evaluation failed: {e}")
        
        # Factor 7: Position count - NO HARD LIMIT, but reduce confidence for many positions
        if total_positions >= 5:
            confidence *= 0.8
            reasons.append(f"{total_positions} positions - high exposure")
        elif total_positions >= 8:
            confidence *= 0.6
            reasons.append(f"{total_positions} positions - very high exposure")
        elif total_positions >= 10:
            confidence *= 0.4
            reasons.append(f"{total_positions} positions - extreme exposure")
        
        # Decision threshold
        logger.info(f"   ✅ Final Confidence: {confidence:.3f} (threshold: 0.65 strong, 0.45 marginal)")
        
        if confidence >= 0.65:  # Strong signal
            logger.info(f"   ✅ DECISION: OPEN NEW POSITION")
            return PositionDecision(
                action=PositionAction.OPEN_NEW,
                confidence=confidence,
                reasoning=f"Open new position: {', '.join(reasons)}",
                allow_new_trade=True,
                metadata={'evaluated_factors': len(reasons)}
            )
        elif confidence >= 0.45:  # Marginal signal
            logger.info(f"   ⏸️  DECISION: HOLD - Confidence too low")
            return PositionDecision(
                action=PositionAction.HOLD,
                confidence=confidence,
                reasoning=f"Wait for better opportunity: {', '.join(reasons)}",
                allow_new_trade=False,
                metadata={'evaluated_factors': len(reasons)}
            )
        else:  # Weak signal
            return PositionDecision(
                action=PositionAction.HOLD,
                confidence=confidence,
                reasoning=f"Signal too weak: {', '.join(reasons)}",
                allow_new_trade=False,
                metadata={'evaluated_factors': len(reasons)}
            )
    
    def should_close_positions(self, portfolio_state: Dict) -> PositionDecision:
        """
        Intelligent decision: Should we close any existing positions?
        
        Args:
            portfolio_state: Current portfolio metrics
            
        Returns:
            PositionDecision with positions to close
        """
        positions = portfolio_state.get('positions', [])
        
        if not positions:
            return PositionDecision(
                action=PositionAction.HOLD,
                confidence=1.0,
                reasoning="No positions to manage"
            )
        
        to_close = []
        reasons = []
        
        # Strategy 1: Close positions with large losses
        for pos in positions:
            # Calculate loss percentage
            if pos.profit < -50:  # Losing more than $50
                to_close.append(pos.ticket)
                reasons.append(f"#{pos.ticket} {pos.symbol}: Large loss ${pos.profit:.2f}")
        
        # Strategy 2: If portfolio is losing badly, close worst performer
        if portfolio_state['total_profit'] < -150:
            worst = min(positions, key=lambda p: p.profit)
            if worst.ticket not in to_close:
                to_close.append(worst.ticket)
                reasons.append(f"#{worst.ticket} {worst.symbol}: Worst performer (portfolio drawdown)")
        
        # Strategy 3: ML-based decision (if available)
        if self.ml_predictor:
            try:
                for pos in positions:
                    # Get current prediction for this symbol
                    # If prediction says price will move against us, close early
                    # This would require getting fresh bars and predicting
                    # For now, simplified logic
                    pass
            except Exception as e:
                print(f"⚠️  ML close analysis failed: {e}")
        
        # Strategy 4: Close profitable positions if portfolio exposure is high
        if len(positions) >= 8:  # High exposure
            # Take some profits
            profitable = [p for p in positions if p.profit > 20]
            if profitable:
                best = max(profitable, key=lambda p: p.profit)
                if best.ticket not in to_close:
                    to_close.append(best.ticket)
                    reasons.append(f"#{best.ticket} {best.symbol}: Take profit (reduce exposure)")
        
        if to_close:
            return PositionDecision(
                action=PositionAction.CLOSE_LOSING,
                confidence=0.8,
                reasoning=f"Close positions: {', '.join(reasons)}",
                positions_to_close=to_close
            )
        
        return PositionDecision(
            action=PositionAction.HOLD,
            confidence=0.7,
            reasoning="All positions healthy"
        )
    
    def make_decision(self, signal: Signal) -> PositionDecision:
        """
        Make intelligent decision about position management
        
        Args:
            signal: New trading signal to evaluate
            
        Returns:
            PositionDecision with action to take
        """
        # Analyze current portfolio
        portfolio_state = self.analyze_portfolio()
        
        # Log current state
        print(f"\n📊 Portfolio Analysis:")
        print(f"   Positions: {portfolio_state['total_positions']}")
        print(f"   P/L: ${portfolio_state['total_profit']:.2f}")
        print(f"   Winning: {portfolio_state['winning_positions']}, Losing: {portfolio_state['losing_positions']}")
        
        # Step 1: ACTIVELY analyze each position and close losers
        positions = portfolio_state.get('positions', [])
        for position in positions:
            close_decision = self.should_close_position(position, portfolio_state)
            
            if close_decision.action == PositionAction.CLOSE_LOSING:
                print(f"🔍 Close Decision: {close_decision.reasoning}")
                logger.info(f"🚨 AI closing position: {close_decision.reasoning}")
                try:
                    result = self.connector.close_position(position.ticket)
                    if result.success:
                        print(f"✅ Closed position #{position.ticket}")
                        logger.info(f"✅ Closed #{position.ticket}, saved from further loss")
                    else:
                        print(f"❌ Failed to close #{position.ticket}")
                        logger.error(f"❌ Failed to close #{position.ticket}: {result.error_message}")
                except Exception as e:
                    print(f"❌ Failed to close #{position.ticket}: {e}")
                    logger.error(f"❌ Error closing #{position.ticket}: {e}")
                
                # Update portfolio state after closing
                portfolio_state = self.analyze_portfolio()
        
        # Step 2: Decide if we should open new position
        open_decision = self.should_open_new_position(signal, portfolio_state)
        
        print(f"🔍 Open Decision: {open_decision.reasoning}")
        print(f"   Final Confidence: {open_decision.confidence:.2f}")
        
        # Store decision for learning
        self.recent_decisions.append(open_decision)
        if len(self.recent_decisions) > 100:
            self.recent_decisions = self.recent_decisions[-100:]
        
        return open_decision
    
    def get_position_limit_recommendation(self) -> int:
        """
        Dynamic position limit based on market conditions
        
        Returns:
            Recommended maximum positions
        """
        portfolio_state = self.analyze_portfolio()
        
        # Base limit
        base_limit = 15
        
        # Adjust based on portfolio health
        if portfolio_state['total_profit'] < -200:
            return 3  # Severely restrict if losing badly
        elif portfolio_state['total_profit'] < -100:
            return 5  # Restrict if losing
        elif portfolio_state['total_profit'] > 200:
            return 20  # Allow more if winning
        
        return base_limit

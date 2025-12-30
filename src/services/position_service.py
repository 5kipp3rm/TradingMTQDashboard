"""
Position Execution Service

Provides business logic layer for position execution with validation and risk management.
Integrates with session manager for MT5 account access.

Features:
- Position opening with validation
- Position closing (single and bulk)
- Real-time SL/TP modification
- Position preview with risk calculation
- Risk management validation
- Margin requirement checking
"""

from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.services.session_manager import session_manager
from src.connectors.base import (
    TradeRequest, TradeResult, OrderType, Position
)
from src.database.models import TradingAccount
from src.utils.unified_logger import UnifiedLogger
from src.exceptions import (
    ConnectionError, OrderExecutionError, InvalidSymbolError
)


logger = UnifiedLogger.get_logger(__name__)


class PositionValidationError(Exception):
    """Raised when position validation fails"""
    pass


class PositionExecutionService:
    """
    Service for executing and managing trading positions.

    Provides high-level position management with validation, risk checks,
    and integration with multi-account session management.
    """

    def __init__(self):
        """Initialize position execution service"""
        # Risk management limits (can be made configurable)
        self.max_risk_percent_per_trade = 5.0  # Max 5% risk per trade
        self.max_daily_loss_percent = 10.0     # Max 10% daily loss
        self.max_open_positions = 20           # Max 20 simultaneous positions

        logger.info("PositionExecutionService initialized")

    async def open_position(
        self,
        account_id: int,
        db: Session,
        symbol: str,
        order_type: str,
        volume: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: Optional[str] = None,
        magic: int = 234000,
        deviation: int = 20
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Open new position with validation.

        Args:
            account_id: Trading account ID
            db: Database session
            symbol: Trading symbol (e.g., "EURUSD")
            order_type: "BUY" or "SELL"
            volume: Position volume in lots
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            comment: Order comment (optional)
            magic: Magic number for order identification
            deviation: Maximum price deviation in points

        Returns:
            Tuple of (success: bool, ticket: Optional[int], error_message: Optional[str])
        """
        logger.info(
            "Opening position",
            account_id=account_id,
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            sl=stop_loss,
            tp=take_profit
        )

        try:
            # Get account from database
            account = db.get(TradingAccount, account_id)
            if not account:
                error_msg = f"Account {account_id} not found"
                logger.error(error_msg)
                return False, None, error_msg

            if not account.is_active:
                error_msg = f"Account {account_id} is not active"
                logger.error(error_msg)
                return False, None, error_msg

            # Get MT5 connector from session manager
            connector = session_manager.get_session(account_id)
            if not connector:
                error_msg = f"Account {account_id} is not connected"
                logger.error(error_msg)
                return False, None, error_msg

            # Validate order type
            try:
                if order_type.upper() == "BUY":
                    action = OrderType.BUY
                elif order_type.upper() == "SELL":
                    action = OrderType.SELL
                else:
                    error_msg = f"Invalid order type: {order_type}. Must be 'BUY' or 'SELL'"
                    logger.error(error_msg)
                    return False, None, error_msg
            except Exception as e:
                error_msg = f"Error parsing order type: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return False, None, error_msg

            # Get symbol info for validation
            try:
                symbol_info = connector.get_symbol_info(symbol)
                if not symbol_info:
                    error_msg = f"Symbol {symbol} not found or not available"
                    logger.error(error_msg)
                    return False, None, error_msg

                if not symbol_info.trade_allowed:
                    error_msg = f"Trading not allowed for symbol {symbol}"
                    logger.error(error_msg)
                    return False, None, error_msg
            except InvalidSymbolError as e:
                error_msg = str(e)
                logger.error(error_msg)
                return False, None, error_msg
            except Exception as e:
                error_msg = f"Error getting symbol info: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return False, None, error_msg

            # Validate volume
            if volume < symbol_info.volume_min:
                error_msg = f"Volume {volume} below minimum {symbol_info.volume_min}"
                logger.error(error_msg)
                return False, None, error_msg

            if volume > symbol_info.volume_max:
                error_msg = f"Volume {volume} exceeds maximum {symbol_info.volume_max}"
                logger.error(error_msg)
                return False, None, error_msg

            # Validate SL/TP if provided
            current_price = symbol_info.ask if action == OrderType.BUY else symbol_info.bid

            if stop_loss is not None:
                if action == OrderType.BUY and stop_loss >= current_price:
                    error_msg = f"Stop loss {stop_loss} must be below current price {current_price} for BUY"
                    logger.error(error_msg)
                    return False, None, error_msg

                if action == OrderType.SELL and stop_loss <= current_price:
                    error_msg = f"Stop loss {stop_loss} must be above current price {current_price} for SELL"
                    logger.error(error_msg)
                    return False, None, error_msg

            if take_profit is not None:
                if action == OrderType.BUY and take_profit <= current_price:
                    error_msg = f"Take profit {take_profit} must be above current price {current_price} for BUY"
                    logger.error(error_msg)
                    return False, None, error_msg

                if action == OrderType.SELL and take_profit >= current_price:
                    error_msg = f"Take profit {take_profit} must be below current price {current_price} for SELL"
                    logger.error(error_msg)
                    return False, None, error_msg

            # Get account info for margin check
            try:
                account_info = connector.get_account_info()
                if not account_info:
                    error_msg = "Failed to get account info"
                    logger.error(error_msg)
                    return False, None, error_msg

                # Check if account has sufficient margin
                if account_info.margin_free <= 0:
                    error_msg = "Insufficient free margin"
                    logger.error(error_msg)
                    return False, None, error_msg

                # Check max open positions limit
                current_positions = connector.get_positions()
                if len(current_positions) >= self.max_open_positions:
                    error_msg = f"Maximum open positions limit reached ({self.max_open_positions})"
                    logger.error(error_msg)
                    return False, None, error_msg

            except Exception as e:
                error_msg = f"Error checking account status: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return False, None, error_msg

            # Create trade request
            trade_request = TradeRequest(
                symbol=symbol,
                action=action,
                volume=volume,
                sl=stop_loss,
                tp=take_profit,
                deviation=deviation,
                magic=magic,
                comment=comment or f"Opened via TradingMTQ at {datetime.now(timezone.utc).isoformat()}"
            )

            # Execute trade
            try:
                result = connector.send_order(trade_request)

                if result.success:
                    logger.info(
                        "Position opened successfully",
                        account_id=account_id,
                        ticket=result.order_ticket,
                        symbol=symbol,
                        volume=volume,
                        price=result.price
                    )
                    return True, result.order_ticket, None
                else:
                    error_msg = result.error_message or f"Order execution failed (code: {result.error_code})"
                    logger.error(
                        "Position opening failed",
                        account_id=account_id,
                        error=error_msg,
                        error_code=result.error_code
                    )
                    return False, None, error_msg

            except OrderExecutionError as e:
                error_msg = str(e)
                logger.error(f"Order execution error: {error_msg}", exc_info=True)
                return False, None, error_msg
            except Exception as e:
                error_msg = f"Unexpected error during order execution: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return False, None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error opening position: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg

    async def close_position(
        self,
        account_id: int,
        db: Session,
        ticket: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Close existing position.

        Args:
            account_id: Trading account ID
            db: Database session
            ticket: Position ticket number

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        logger.info(f"Closing position - account_id={account_id}, ticket={ticket}")

        try:
            # Get account from database
            account = db.get(TradingAccount, account_id)
            if not account:
                error_msg = f"Account {account_id} not found"
                logger.error(error_msg)
                return False, error_msg

            # Get MT5 connector
            connector = session_manager.get_session(account_id)
            if not connector:
                error_msg = f"Account {account_id} is not connected"
                logger.error(error_msg)
                return False, error_msg

            # Verify position exists
            position = connector.get_position_by_ticket(ticket)
            if not position:
                error_msg = f"Position {ticket} not found"
                logger.error(error_msg)
                return False, error_msg

            # Close position
            try:
                result = connector.close_position(ticket)

                if result.success:
                    logger.info(
                        "Position closed successfully",
                        account_id=account_id,
                        ticket=ticket,
                        symbol=position.symbol,
                        profit=position.profit
                    )
                    return True, None
                else:
                    error_msg = result.error_message or f"Close failed (code: {result.error_code})"
                    logger.error(
                        "Position closing failed",
                        account_id=account_id,
                        ticket=ticket,
                        error=error_msg
                    )
                    return False, error_msg

            except OrderExecutionError as e:
                error_msg = str(e)
                logger.error(f"Order execution error during close: {error_msg}", exc_info=True)
                return False, error_msg
            except Exception as e:
                error_msg = f"Unexpected error closing position: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    async def modify_position(
        self,
        account_id: int,
        db: Session,
        ticket: int,
        new_sl: Optional[float] = None,
        new_tp: Optional[float] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Modify SL/TP on existing position.

        Args:
            account_id: Trading account ID
            db: Database session
            ticket: Position ticket number
            new_sl: New stop loss price (optional)
            new_tp: New take profit price (optional)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        logger.info(
            "Modifying position",
            account_id=account_id,
            ticket=ticket,
            new_sl=new_sl,
            new_tp=new_tp
        )

        try:
            # Validate at least one parameter provided
            if new_sl is None and new_tp is None:
                error_msg = "At least one of new_sl or new_tp must be provided"
                logger.error(error_msg)
                return False, error_msg

            # Get account from database
            account = db.get(TradingAccount, account_id)
            if not account:
                error_msg = f"Account {account_id} not found"
                logger.error(error_msg)
                return False, error_msg

            # Get MT5 connector
            connector = session_manager.get_session(account_id)
            if not connector:
                error_msg = f"Account {account_id} is not connected"
                logger.error(error_msg)
                return False, error_msg

            # Verify position exists and get current state
            position = connector.get_position_by_ticket(ticket)
            if not position:
                error_msg = f"Position {ticket} not found"
                logger.error(error_msg)
                return False, error_msg

            # Get current price for validation
            try:
                symbol_info = connector.get_symbol_info(position.symbol)
                if not symbol_info:
                    error_msg = f"Symbol {position.symbol} not available"
                    logger.error(error_msg)
                    return False, error_msg

                current_price = position.price_current
                is_buy = position.type == OrderType.BUY

                # Validate new SL if provided
                if new_sl is not None:
                    if is_buy and new_sl >= current_price:
                        error_msg = f"Stop loss {new_sl} must be below current price {current_price} for BUY position"
                        logger.error(error_msg)
                        return False, error_msg

                    if not is_buy and new_sl <= current_price:
                        error_msg = f"Stop loss {new_sl} must be above current price {current_price} for SELL position"
                        logger.error(error_msg)
                        return False, error_msg

                # Validate new TP if provided
                if new_tp is not None:
                    if is_buy and new_tp <= current_price:
                        error_msg = f"Take profit {new_tp} must be above current price {current_price} for BUY position"
                        logger.error(error_msg)
                        return False, error_msg

                    if not is_buy and new_tp >= current_price:
                        error_msg = f"Take profit {new_tp} must be below current price {current_price} for SELL position"
                        logger.error(error_msg)
                        return False, error_msg

            except InvalidSymbolError as e:
                error_msg = str(e)
                logger.error(error_msg)
                return False, error_msg
            except Exception as e:
                error_msg = f"Error validating modification: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return False, error_msg

            # Modify position
            try:
                result = connector.modify_position(ticket, sl=new_sl, tp=new_tp)

                if result.success:
                    logger.info(
                        "Position modified successfully",
                        account_id=account_id,
                        ticket=ticket,
                        new_sl=new_sl,
                        new_tp=new_tp
                    )
                    return True, None
                else:
                    error_msg = result.error_message or f"Modification failed (code: {result.error_code})"
                    logger.error(
                        "Position modification failed",
                        account_id=account_id,
                        ticket=ticket,
                        error=error_msg
                    )
                    return False, error_msg

            except OrderExecutionError as e:
                error_msg = str(e)
                logger.error(f"Order execution error during modify: {error_msg}", exc_info=True)
                return False, error_msg
            except Exception as e:
                error_msg = f"Unexpected error modifying position: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    async def bulk_close_positions(
        self,
        account_id: int,
        db: Session,
        symbol: Optional[str] = None
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Close all positions for an account (optionally filtered by symbol).

        Args:
            account_id: Trading account ID
            db: Database session
            symbol: Filter by symbol (optional, closes all if None)

        Returns:
            Tuple of (successful_count: int, failed_count: int, results: List[Dict])
        """
        logger.info(
            "Bulk closing positions",
            account_id=account_id,
            symbol=symbol
        )

        try:
            # Get account from database
            account = db.get(TradingAccount, account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return 0, 0, []

            # Get MT5 connector
            connector = session_manager.get_session(account_id)
            if not connector:
                logger.error(f"Account {account_id} is not connected")
                return 0, 0, []

            # Get positions to close
            positions = connector.get_positions(symbol=symbol)
            if not positions:
                logger.info("No positions to close")
                return 0, 0, []

            logger.info(f"Found {len(positions)} positions to close")

            # Close each position
            successful_count = 0
            failed_count = 0
            results = []

            for position in positions:
                success, error_msg = await self.close_position(account_id, db, position.ticket)

                result_entry = {
                    "ticket": position.ticket,
                    "symbol": position.symbol,
                    "volume": position.volume,
                    "profit": position.profit,
                    "success": success,
                    "error": error_msg
                }
                results.append(result_entry)

                if success:
                    successful_count += 1
                else:
                    failed_count += 1

            logger.info(
                "Bulk close completed",
                account_id=account_id,
                total=len(positions),
                successful=successful_count,
                failed=failed_count
            )

            return successful_count, failed_count, results

        except Exception as e:
            error_msg = f"Unexpected error during bulk close: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return 0, 0, []

    async def preview_position(
        self,
        account_id: int,
        db: Session,
        symbol: str,
        order_type: str,
        volume: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Preview position before execution with risk calculation.

        Args:
            account_id: Trading account ID
            db: Database session
            symbol: Trading symbol
            order_type: "BUY" or "SELL"
            volume: Position volume
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)

        Returns:
            Dictionary with position preview data
        """
        logger.info(
            "Previewing position",
            account_id=account_id,
            symbol=symbol,
            order_type=order_type,
            volume=volume
        )

        try:
            # Get account from database
            account = db.get(TradingAccount, account_id)
            if not account:
                return {"error": f"Account {account_id} not found"}

            # Get MT5 connector
            connector = session_manager.get_session(account_id)
            if not connector:
                return {"error": f"Account {account_id} is not connected"}

            # Validate order type
            try:
                if order_type.upper() == "BUY":
                    action = OrderType.BUY
                elif order_type.upper() == "SELL":
                    action = OrderType.SELL
                else:
                    return {"error": f"Invalid order type: {order_type}"}
            except Exception as e:
                return {"error": f"Error parsing order type: {str(e)}"}

            # Get symbol info
            try:
                symbol_info = connector.get_symbol_info(symbol)
                if not symbol_info:
                    return {"error": f"Symbol {symbol} not found"}

                if not symbol_info.trade_allowed:
                    return {"error": f"Trading not allowed for {symbol}"}
            except Exception as e:
                return {"error": f"Error getting symbol info: {str(e)}"}

            # Get account info
            try:
                account_info = connector.get_account_info()
                if not account_info:
                    return {"error": "Failed to get account info"}
            except Exception as e:
                return {"error": f"Error getting account info: {str(e)}"}

            # Calculate entry price
            entry_price = symbol_info.ask if action == OrderType.BUY else symbol_info.bid

            # Calculate pips and risk/reward
            point = symbol_info.point if hasattr(symbol_info, 'point') else 0.0001
            digits = symbol_info.digits if hasattr(symbol_info, 'digits') else 5
            pip_size = point * (10 if digits == 5 or digits == 3 else 1)

            risk_pips = 0.0
            reward_pips = 0.0
            risk_amount = 0.0
            potential_profit = 0.0
            risk_reward_ratio = 0.0

            if stop_loss is not None:
                risk_pips = abs(entry_price - stop_loss) / pip_size
                # Simplified risk calculation (pip value * volume * risk_pips)
                risk_amount = risk_pips * volume * symbol_info.contract_size * pip_size

            if take_profit is not None:
                reward_pips = abs(take_profit - entry_price) / pip_size
                potential_profit = reward_pips * volume * symbol_info.contract_size * pip_size

            if risk_pips > 0 and reward_pips > 0:
                risk_reward_ratio = reward_pips / risk_pips

            # Calculate margin required (simplified)
            margin_required = volume * symbol_info.contract_size * entry_price
            if hasattr(account_info, 'leverage') and account_info.leverage > 0:
                margin_required = margin_required / account_info.leverage

            # Build preview response
            preview = {
                "symbol": symbol,
                "order_type": order_type.upper(),
                "volume": volume,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_pips": round(risk_pips, 1),
                "reward_pips": round(reward_pips, 1),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "risk_amount": round(risk_amount, 2),
                "potential_profit": round(potential_profit, 2),
                "margin_required": round(margin_required, 2),
                "account_balance": account_info.balance,
                "account_equity": account_info.equity,
                "margin_free": account_info.margin_free,
                "margin_sufficient": margin_required <= account_info.margin_free,
                "spread": symbol_info.spread,
                "contract_size": symbol_info.contract_size
            }

            logger.info(f"Position preview generated - account_id={account_id}")
            return preview

        except Exception as e:
            error_msg = f"Unexpected error during preview: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}

    async def get_open_positions(
        self,
        account_id: Optional[int],
        db: Session,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all open positions for an account or all active accounts.

        Args:
            account_id: Trading account ID (optional - if None, gets positions from all active accounts)
            db: Database session
            symbol: Filter by symbol (optional)

        Returns:
            List of position dictionaries
        """
        logger.info(f"Getting open positions - account_id={account_id}, symbol={symbol}")

        try:
            # If no account_id specified, get positions from all active accounts
            if account_id is None:
                from sqlalchemy import select

                # Get all active accounts
                stmt = select(TradingAccount).where(TradingAccount.is_active == True)
                result = db.execute(stmt)
                active_accounts = result.scalars().all()

                logger.info(f"Getting positions from {len(active_accounts)} active accounts")

                # Collect positions from all active accounts
                all_positions = []
                for account in active_accounts:
                    connector = session_manager.get_session(account.id)
                    if connector:
                        try:
                            positions = connector.get_positions(symbol=symbol)
                            for pos in positions:
                                position_dict = {
                                    "ticket": pos.ticket,
                                    "symbol": pos.symbol,
                                    "type": pos.type.value if isinstance(pos.type, OrderType) else str(pos.type),
                                    "volume": pos.volume,
                                    "price_open": pos.price_open,
                                    "price_current": pos.price_current,
                                    "sl": pos.sl,
                                    "tp": pos.tp,
                                    "profit": pos.profit
                                }
                                all_positions.append(position_dict)
                        except Exception as e:
                            logger.warning(f"Failed to get positions from account {account.id}: {str(e)}")
                            continue

                logger.info(f"Retrieved {len(all_positions)} open positions from all active accounts")
                return all_positions

            # Single account mode
            # Get account from database
            account = db.get(TradingAccount, account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return []

            # Get MT5 connector
            connector = session_manager.get_session(account_id)
            if not connector:
                logger.error(f"Account {account_id} is not connected")
                return []

            # Get positions
            positions = connector.get_positions(symbol=symbol)

            # Convert to dictionaries
            result = []
            for pos in positions:
                position_dict = {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": pos.type.value if isinstance(pos.type, OrderType) else str(pos.type),
                    "volume": pos.volume,
                    "price_open": pos.price_open,
                    "price_current": pos.price_current,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "profit": pos.profit
                }
                result.append(position_dict)

            logger.info(f"Retrieved {len(result)} open positions", extra={"account_id": account_id})
            return result

        except Exception as e:
            error_msg = f"Error getting open positions: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return []


# Global position service instance
position_service = PositionExecutionService()

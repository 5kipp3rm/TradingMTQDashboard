"""
Alert Manager for TradingMTQ

Coordinates alert delivery across multiple channels (email, WebSocket, etc.)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.database.models import (
    AlertConfiguration, AlertHistory, AlertType,
    NotificationChannel, Trade
)
from src.database.connection import get_session
from src.notifications.email_service import EmailNotificationService
from src.api.websocket import connection_manager
from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class AlertManager:
    """
    Manages alert delivery across multiple notification channels

    Features:
    - Multi-channel notifications (email, WebSocket, SMS)
    - Configurable alert types and thresholds
    - Symbol-based filtering
    - Delivery history tracking
    - Error handling and retry logic
    """

    def __init__(self, email_service: Optional[EmailNotificationService] = None):
        self.email_service = email_service
        logger.info("AlertManager initialized", has_email=email_service is not None)

    def get_alert_config(self, alert_type: AlertType) -> Optional[AlertConfiguration]:
        """
        Get alert configuration for specific type

        Args:
            alert_type: Type of alert

        Returns:
            AlertConfiguration or None if not configured
        """
        with get_session() as session:
            config = session.query(AlertConfiguration).filter(
                AlertConfiguration.alert_type == alert_type,
                AlertConfiguration.enabled == True
            ).first()
            return config

    def should_send_alert(
        self,
        alert_type: AlertType,
        trade_data: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[AlertConfiguration]]:
        """
        Check if alert should be sent based on configuration

        Args:
            alert_type: Type of alert
            trade_data: Trade information (for filtering)

        Returns:
            (should_send, config) tuple
        """
        config = self.get_alert_config(alert_type)

        if not config or not config.enabled:
            return False, None

        # Check symbol filter if trade data provided
        if trade_data and config.symbol_filter:
            symbol = trade_data.get('symbol', '').upper()
            filters = config.get_symbol_filters()
            if filters and symbol not in filters:
                logger.debug(
                    "Alert filtered by symbol",
                    alert_type=alert_type.value,
                    symbol=symbol,
                    filters=filters
                )
                return False, None

        # Check profit/loss thresholds
        if alert_type == AlertType.PROFIT_THRESHOLD and trade_data:
            profit = trade_data.get('profit', 0.0)
            if config.profit_threshold and profit < float(config.profit_threshold):
                return False, None

        if alert_type == AlertType.LOSS_THRESHOLD and trade_data:
            profit = trade_data.get('profit', 0.0)
            if config.loss_threshold and profit > float(config.loss_threshold):
                return False, None

        return True, config

    def send_trade_opened_alert(self, trade_data: Dict[str, Any], trade_id: Optional[int] = None) -> bool:
        """
        Send alert when trade is opened

        Args:
            trade_data: Trade information
            trade_id: Database trade ID

        Returns:
            True if at least one notification sent successfully
        """
        alert_type = AlertType.TRADE_OPENED
        should_send, config = self.should_send_alert(alert_type, trade_data)

        if not should_send:
            return False

        success = False

        # Send email notification
        if config.email_enabled and self.email_service:
            recipients = config.get_email_recipients()
            if recipients:
                email_sent = self.email_service.notify_trade_opened(recipients, trade_data)
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.EMAIL,
                    success=email_sent,
                    recipients=recipients,
                    trade_id=trade_id,
                    subject=f"Trade Opened: {trade_data.get('symbol')}"
                )
                success = success or email_sent

        # Send WebSocket notification
        if config.websocket_enabled:
            import asyncio
            try:
                asyncio.create_task(
                    connection_manager.broadcast_trade_event("trade_opened", trade_data)
                )
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.WEBSOCKET,
                    success=True,
                    recipients=["websocket_broadcast"],
                    trade_id=trade_id
                )
                success = True
            except Exception as e:
                logger.error("WebSocket alert failed", error=str(e))
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.WEBSOCKET,
                    success=False,
                    recipients=["websocket_broadcast"],
                    trade_id=trade_id,
                    error_message=str(e)
                )

        logger.info(
            "Trade opened alert sent",
            symbol=trade_data.get('symbol'),
            success=success
        )

        return success

    def send_trade_closed_alert(self, trade_data: Dict[str, Any], trade_id: Optional[int] = None) -> bool:
        """
        Send alert when trade is closed

        Args:
            trade_data: Trade information
            trade_id: Database trade ID

        Returns:
            True if at least one notification sent successfully
        """
        alert_type = AlertType.TRADE_CLOSED
        should_send, config = self.should_send_alert(alert_type, trade_data)

        if not should_send:
            return False

        success = False

        # Send email notification
        if config.email_enabled and self.email_service:
            recipients = config.get_email_recipients()
            if recipients:
                email_sent = self.email_service.notify_trade_closed(recipients, trade_data)
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.EMAIL,
                    success=email_sent,
                    recipients=recipients,
                    trade_id=trade_id,
                    subject=f"Trade Closed: {trade_data.get('symbol')} - ${trade_data.get('profit', 0):.2f}"
                )
                success = success or email_sent

        # Send WebSocket notification
        if config.websocket_enabled:
            import asyncio
            try:
                asyncio.create_task(
                    connection_manager.broadcast_trade_event("trade_closed", trade_data)
                )
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.WEBSOCKET,
                    success=True,
                    recipients=["websocket_broadcast"],
                    trade_id=trade_id
                )
                success = True
            except Exception as e:
                logger.error("WebSocket alert failed", error=str(e))
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.WEBSOCKET,
                    success=False,
                    recipients=["websocket_broadcast"],
                    trade_id=trade_id,
                    error_message=str(e)
                )

        logger.info(
            "Trade closed alert sent",
            symbol=trade_data.get('symbol'),
            profit=trade_data.get('profit'),
            success=success
        )

        return success

    def send_daily_summary(self, performance_data: Dict[str, Any]) -> bool:
        """
        Send daily performance summary

        Args:
            performance_data: Daily performance metrics

        Returns:
            True if sent successfully
        """
        alert_type = AlertType.DAILY_SUMMARY
        should_send, config = self.should_send_alert(alert_type)

        if not should_send:
            return False

        success = False

        # Send email notification
        if config.email_enabled and self.email_service:
            recipients = config.get_email_recipients()
            if recipients:
                email_sent = self.email_service.notify_daily_summary(recipients, performance_data)
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.EMAIL,
                    success=email_sent,
                    recipients=recipients,
                    subject="Daily Performance Summary"
                )
                success = success or email_sent

        # Send WebSocket notification
        if config.websocket_enabled:
            import asyncio
            try:
                asyncio.create_task(
                    connection_manager.broadcast_system_event("daily_summary", performance_data)
                )
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.WEBSOCKET,
                    success=True,
                    recipients=["websocket_broadcast"]
                )
                success = True
            except Exception as e:
                logger.error("WebSocket alert failed", error=str(e))

        logger.info("Daily summary sent", success=success)
        return success

    def send_error_alert(
        self,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send error alert notification

        Args:
            error_message: Error message
            error_details: Additional error context

        Returns:
            True if sent successfully
        """
        alert_type = AlertType.ERROR_ALERT
        should_send, config = self.should_send_alert(alert_type)

        if not should_send:
            return False

        success = False

        # Send email notification
        if config.email_enabled and self.email_service:
            recipients = config.get_email_recipients()
            if recipients:
                email_sent = self.email_service.notify_error(
                    recipients,
                    error_message,
                    error_details
                )
                self._record_alert(
                    alert_type=alert_type,
                    channel=NotificationChannel.EMAIL,
                    success=email_sent,
                    recipients=recipients,
                    subject="Trading Bot Error Alert"
                )
                success = success or email_sent

        logger.info("Error alert sent", success=success)
        return success

    def _record_alert(
        self,
        alert_type: AlertType,
        channel: NotificationChannel,
        success: bool,
        recipients: List[str],
        trade_id: Optional[int] = None,
        subject: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Record alert delivery in history

        Args:
            alert_type: Type of alert
            channel: Notification channel
            success: Whether delivery was successful
            recipients: List of recipients
            trade_id: Related trade ID
            subject: Alert subject
            error_message: Error message if failed
        """
        try:
            with get_session() as session:
                for recipient in recipients:
                    history = AlertHistory(
                        alert_type=alert_type,
                        channel=channel,
                        success=success,
                        recipient=recipient,
                        trade_id=trade_id,
                        subject=subject,
                        error_message=error_message
                    )
                    session.add(history)
                session.commit()
        except Exception as e:
            logger.error("Failed to record alert history", error=str(e))

    def get_alert_history(
        self,
        limit: int = 100,
        alert_type: Optional[AlertType] = None,
        success_only: bool = False
    ) -> List[AlertHistory]:
        """
        Get alert delivery history

        Args:
            limit: Maximum number of records
            alert_type: Filter by alert type
            success_only: Only return successful deliveries

        Returns:
            List of AlertHistory records
        """
        with get_session() as session:
            query = session.query(AlertHistory)

            if alert_type:
                query = query.filter(AlertHistory.alert_type == alert_type)

            if success_only:
                query = query.filter(AlertHistory.success == True)

            query = query.order_by(AlertHistory.sent_at.desc()).limit(limit)

            return query.all()

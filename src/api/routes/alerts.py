"""
Alert Management API Routes

Provides REST endpoints for configuring and managing notifications.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

from src.database.models import AlertConfiguration, AlertHistory, AlertType, NotificationChannel
from src.database.connection import get_session
from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class AlertConfigRequest(BaseModel):
    """Request model for creating/updating alert configuration"""
    alert_type: str = Field(..., description="Alert type (trade_opened, trade_closed, etc.)")
    enabled: bool = Field(True, description="Whether alert is enabled")
    email_enabled: bool = Field(True, description="Enable email notifications")
    sms_enabled: bool = Field(False, description="Enable SMS notifications")
    websocket_enabled: bool = Field(True, description="Enable WebSocket notifications")
    email_recipients: Optional[str] = Field(None, description="Comma-separated email addresses")
    sms_recipients: Optional[str] = Field(None, description="Comma-separated phone numbers")
    profit_threshold: Optional[float] = Field(None, description="Minimum profit for alerts")
    loss_threshold: Optional[float] = Field(None, description="Maximum loss for alerts")
    symbol_filter: Optional[str] = Field(None, description="Comma-separated symbols to filter")


class AlertConfigResponse(BaseModel):
    """Response model for alert configuration"""
    id: int
    alert_type: str
    enabled: bool
    email_enabled: bool
    sms_enabled: bool
    websocket_enabled: bool
    email_recipients: List[str]
    sms_recipients: List[str]
    profit_threshold: Optional[float]
    loss_threshold: Optional[float]
    symbol_filter: List[str]
    created_at: datetime
    updated_at: datetime


class AlertHistoryResponse(BaseModel):
    """Response model for alert history"""
    id: int
    alert_type: str
    channel: str
    sent_at: datetime
    success: bool
    error_message: Optional[str]
    recipient: str
    trade_id: Optional[int]
    subject: Optional[str]


class TestEmailRequest(BaseModel):
    """Request model for testing email configuration"""
    email: EmailStr = Field(..., description="Test recipient email")


# =============================================================================
# Alert Configuration Endpoints
# =============================================================================

@router.get("/config", response_model=List[AlertConfigResponse])
async def get_alert_configurations():
    """
    Get all alert configurations

    Returns:
        List of alert configurations
    """
    try:
        with get_session() as session:
            configs = session.query(AlertConfiguration).all()

            result = []
            for config in configs:
                result.append(AlertConfigResponse(
                    id=config.id,
                    alert_type=config.alert_type.value if hasattr(config.alert_type, 'value') else config.alert_type,
                    enabled=config.enabled,
                    email_enabled=config.email_enabled,
                    sms_enabled=config.sms_enabled,
                    websocket_enabled=config.websocket_enabled,
                    email_recipients=config.get_email_recipients(),
                    sms_recipients=config.get_sms_recipients(),
                    profit_threshold=float(config.profit_threshold) if config.profit_threshold else None,
                    loss_threshold=float(config.loss_threshold) if config.loss_threshold else None,
                    symbol_filter=config.get_symbol_filters(),
                    created_at=config.created_at,
                    updated_at=config.updated_at
                ))

            return result

    except Exception as e:
        logger.error("Failed to fetch alert configurations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{alert_type}", response_model=AlertConfigResponse)
async def get_alert_configuration(alert_type: str):
    """
    Get specific alert configuration

    Args:
        alert_type: Type of alert

    Returns:
        Alert configuration
    """
    try:
        # Validate alert_type
        try:
            alert_type_enum = AlertType(alert_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid alert_type. Valid types: {[t.value for t in AlertType]}"
            )

        with get_session() as session:
            config = session.query(AlertConfiguration).filter(
                AlertConfiguration.alert_type == alert_type_enum
            ).first()

            if not config:
                raise HTTPException(status_code=404, detail="Configuration not found")

            return AlertConfigResponse(
                id=config.id,
                alert_type=config.alert_type.value if hasattr(config.alert_type, 'value') else config.alert_type,
                enabled=config.enabled,
                email_enabled=config.email_enabled,
                sms_enabled=config.sms_enabled,
                websocket_enabled=config.websocket_enabled,
                email_recipients=config.get_email_recipients(),
                sms_recipients=config.get_sms_recipients(),
                profit_threshold=float(config.profit_threshold) if config.profit_threshold else None,
                loss_threshold=float(config.loss_threshold) if config.loss_threshold else None,
                symbol_filter=config.get_symbol_filters(),
                created_at=config.created_at,
                updated_at=config.updated_at
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch alert configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config", response_model=AlertConfigResponse, status_code=201)
async def create_alert_configuration(request: AlertConfigRequest):
    """
    Create new alert configuration

    Args:
        request: Alert configuration data

    Returns:
        Created configuration
    """
    try:
        # Validate alert_type
        try:
            alert_type_enum = AlertType(request.alert_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid alert_type. Valid types: {[t.value for t in AlertType]}"
            )

        with get_session() as session:
            # Check if configuration already exists
            existing = session.query(AlertConfiguration).filter(
                AlertConfiguration.alert_type == alert_type_enum
            ).first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Configuration for {request.alert_type} already exists. Use PUT to update."
                )

            # Create new configuration
            config = AlertConfiguration(
                alert_type=alert_type_enum,
                enabled=request.enabled,
                email_enabled=request.email_enabled,
                sms_enabled=request.sms_enabled,
                websocket_enabled=request.websocket_enabled,
                email_recipients=request.email_recipients,
                sms_recipients=request.sms_recipients,
                profit_threshold=request.profit_threshold,
                loss_threshold=request.loss_threshold,
                symbol_filter=request.symbol_filter
            )

            session.add(config)
            session.commit()
            session.refresh(config)

            logger.info("Alert configuration created", alert_type=request.alert_type)

            return AlertConfigResponse(
                id=config.id,
                alert_type=config.alert_type.value if hasattr(config.alert_type, 'value') else config.alert_type,
                enabled=config.enabled,
                email_enabled=config.email_enabled,
                sms_enabled=config.sms_enabled,
                websocket_enabled=config.websocket_enabled,
                email_recipients=config.get_email_recipients(),
                sms_recipients=config.get_sms_recipients(),
                profit_threshold=float(config.profit_threshold) if config.profit_threshold else None,
                loss_threshold=float(config.loss_threshold) if config.loss_threshold else None,
                symbol_filter=config.get_symbol_filters(),
                created_at=config.created_at,
                updated_at=config.updated_at
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create alert configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/{alert_type}", response_model=AlertConfigResponse)
async def update_alert_configuration(alert_type: str, request: AlertConfigRequest):
    """
    Update alert configuration

    Args:
        alert_type: Type of alert
        request: Updated configuration data

    Returns:
        Updated configuration
    """
    try:
        # Validate alert_type
        try:
            alert_type_enum = AlertType(alert_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid alert_type. Valid types: {[t.value for t in AlertType]}"
            )

        with get_session() as session:
            config = session.query(AlertConfiguration).filter(
                AlertConfiguration.alert_type == alert_type_enum
            ).first()

            if not config:
                raise HTTPException(status_code=404, detail="Configuration not found")

            # Update fields
            config.enabled = request.enabled
            config.email_enabled = request.email_enabled
            config.sms_enabled = request.sms_enabled
            config.websocket_enabled = request.websocket_enabled
            config.email_recipients = request.email_recipients
            config.sms_recipients = request.sms_recipients
            config.profit_threshold = request.profit_threshold
            config.loss_threshold = request.loss_threshold
            config.symbol_filter = request.symbol_filter
            config.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(config)

            logger.info("Alert configuration updated", alert_type=alert_type)

            return AlertConfigResponse(
                id=config.id,
                alert_type=config.alert_type.value if hasattr(config.alert_type, 'value') else config.alert_type,
                enabled=config.enabled,
                email_enabled=config.email_enabled,
                sms_enabled=config.sms_enabled,
                websocket_enabled=config.websocket_enabled,
                email_recipients=config.get_email_recipients(),
                sms_recipients=config.get_sms_recipients(),
                profit_threshold=float(config.profit_threshold) if config.profit_threshold else None,
                loss_threshold=float(config.loss_threshold) if config.loss_threshold else None,
                symbol_filter=config.get_symbol_filters(),
                created_at=config.created_at,
                updated_at=config.updated_at
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update alert configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/config/{alert_type}", status_code=204)
async def delete_alert_configuration(alert_type: str):
    """
    Delete alert configuration

    Args:
        alert_type: Type of alert
    """
    try:
        # Validate alert_type
        try:
            alert_type_enum = AlertType(alert_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid alert_type. Valid types: {[t.value for t in AlertType]}"
            )

        with get_session() as session:
            config = session.query(AlertConfiguration).filter(
                AlertConfiguration.alert_type == alert_type_enum
            ).first()

            if not config:
                raise HTTPException(status_code=404, detail="Configuration not found")

            session.delete(config)
            session.commit()

            logger.info("Alert configuration deleted", alert_type=alert_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete alert configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Alert History Endpoints
# =============================================================================

@router.get("/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    success_only: bool = Query(False, description="Only show successful deliveries")
):
    """
    Get alert delivery history

    Args:
        limit: Maximum number of records
        alert_type: Filter by alert type
        success_only: Only show successful deliveries

    Returns:
        List of alert history records
    """
    try:
        with get_session() as session:
            query = session.query(AlertHistory)

            if alert_type:
                try:
                    alert_type_enum = AlertType(alert_type)
                    query = query.filter(AlertHistory.alert_type == alert_type_enum)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid alert_type. Valid types: {[t.value for t in AlertType]}"
                    )

            if success_only:
                query = query.filter(AlertHistory.success == True)

            query = query.order_by(AlertHistory.sent_at.desc()).limit(limit)
            history = query.all()

            result = []
            for record in history:
                result.append(AlertHistoryResponse(
                    id=record.id,
                    alert_type=record.alert_type.value if hasattr(record.alert_type, 'value') else record.alert_type,
                    channel=record.channel.value if hasattr(record.channel, 'value') else record.channel,
                    sent_at=record.sent_at,
                    success=record.success,
                    error_message=record.error_message,
                    recipient=record.recipient,
                    trade_id=record.trade_id,
                    subject=record.subject
                ))

            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch alert history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get("/types")
async def get_alert_types():
    """
    Get available alert types

    Returns:
        List of valid alert types
    """
    return {
        "alert_types": [t.value for t in AlertType],
        "notification_channels": [c.value for c in NotificationChannel]
    }


@router.post("/test-email")
async def test_email_configuration(request: TestEmailRequest):
    """
    Test email configuration by sending a test email

    Args:
        request: Test email request

    Returns:
        Test result
    """
    try:
        from src.notifications.email_service import EmailNotificationService, EmailConfig
        import os

        # Get email configuration from environment variables
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from_email = os.getenv("SMTP_FROM_EMAIL")

        if not all([smtp_host, smtp_username, smtp_password, smtp_from_email]):
            raise HTTPException(
                status_code=400,
                detail="Email configuration incomplete. Set SMTP environment variables."
            )

        # Create email service
        email_config = EmailConfig(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            from_email=smtp_from_email
        )
        email_service = EmailNotificationService(email_config)

        # Send test email
        success = email_service.test_connection(request.email)

        if success:
            return {"success": True, "message": f"Test email sent to {request.email}"}
        else:
            return {"success": False, "message": "Failed to send test email"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Email test failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

"""
Report Management API Endpoints

Provides REST endpoints for managing report configurations, generating reports,
and viewing report history.
"""

from typing import List, Optional
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator

from src.database import get_session
from src.database.report_models import (
    ReportConfiguration,
    ReportHistory,
    ReportFrequency,
    ReportFormat
)
from src.reports.generator import ReportGenerator
from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter()


# Pydantic Models

class ReportConfigCreate(BaseModel):
    """Request model for creating report configuration"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    frequency: str = Field(..., description="daily, weekly, monthly, or custom")
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    time_of_day: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    report_format: str = Field(default="pdf", description="pdf, csv, or excel")
    include_trades: bool = True
    include_charts: bool = True
    days_lookback: int = Field(default=30, ge=1, le=365)
    account_id: Optional[int] = None
    recipients: List[str] = Field(..., min_items=1)
    cc_recipients: Optional[List[str]] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    is_active: bool = True

    @validator('frequency')
    def validate_frequency(cls, v):
        valid = ['daily', 'weekly', 'monthly', 'custom']
        if v not in valid:
            raise ValueError(f"frequency must be one of {valid}")
        return v

    @validator('report_format')
    def validate_format(cls, v):
        valid = ['pdf', 'csv', 'excel']
        if v not in valid:
            raise ValueError(f"report_format must be one of {valid}")
        return v


class ReportConfigUpdate(BaseModel):
    """Request model for updating report configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    frequency: Optional[str] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    time_of_day: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    report_format: Optional[str] = None
    include_trades: Optional[bool] = None
    include_charts: Optional[bool] = None
    days_lookback: Optional[int] = Field(None, ge=1, le=365)
    account_id: Optional[int] = None
    recipients: Optional[List[str]] = None
    cc_recipients: Optional[List[str]] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    is_active: Optional[bool] = None


class GenerateReportRequest(BaseModel):
    """Request model for generating ad-hoc report"""
    start_date: date
    end_date: date
    account_id: Optional[int] = None
    include_trades: bool = True
    include_charts: bool = False
    email_recipients: Optional[List[str]] = None


# API Endpoints

@router.get("/reports/configurations")
async def list_report_configurations(
    active_only: bool = Query(False, description="Show only active configurations")
):
    """
    List all report configurations.

    Returns list of scheduled report configurations.
    """
    with get_session() as session:
        query = session.query(ReportConfiguration)

        if active_only:
            query = query.filter(ReportConfiguration.is_active == True)

        configs = query.order_by(ReportConfiguration.created_at.desc()).all()

        return {
            "configurations": [config.to_dict() for config in configs],
            "total": len(configs)
        }


@router.get("/reports/configurations/{config_id}")
async def get_report_configuration(config_id: int):
    """
    Get specific report configuration by ID.

    Returns detailed configuration information.
    """
    with get_session() as session:
        config = session.get(ReportConfiguration, config_id)

        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

        return config.to_dict()


@router.post("/reports/configurations", status_code=201)
async def create_report_configuration(config_data: ReportConfigCreate):
    """
    Create new report configuration.

    Creates a new scheduled report configuration.
    """
    with get_session() as session:
        # Convert frequency string to enum
        frequency = ReportFrequency(config_data.frequency)
        report_format = ReportFormat(config_data.report_format)

        # Create configuration
        config = ReportConfiguration(
            name=config_data.name,
            description=config_data.description,
            frequency=frequency,
            day_of_week=config_data.day_of_week,
            day_of_month=config_data.day_of_month,
            time_of_day=config_data.time_of_day,
            report_format=report_format,
            include_trades=config_data.include_trades,
            include_charts=config_data.include_charts,
            days_lookback=config_data.days_lookback,
            account_id=config_data.account_id,
            recipients=','.join(config_data.recipients),
            cc_recipients=','.join(config_data.cc_recipients) if config_data.cc_recipients else None,
            email_subject=config_data.email_subject,
            email_body=config_data.email_body,
            is_active=config_data.is_active
        )

        session.add(config)
        session.commit()
        session.refresh(config)

        logger.info(
            "Report configuration created",
            config_id=config.id,
            name=config.name,
            frequency=config.frequency.value
        )

        return config.to_dict()


@router.put("/reports/configurations/{config_id}")
async def update_report_configuration(config_id: int, config_data: ReportConfigUpdate):
    """
    Update existing report configuration.

    Updates configuration parameters. Only provided fields are updated.
    """
    with get_session() as session:
        config = session.get(ReportConfiguration, config_id)

        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

        # Update provided fields
        update_data = config_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == 'frequency' and value:
                setattr(config, field, ReportFrequency(value))
            elif field == 'report_format' and value:
                setattr(config, field, ReportFormat(value))
            elif field == 'recipients' and value:
                setattr(config, field, ','.join(value))
            elif field == 'cc_recipients' and value:
                setattr(config, field, ','.join(value) if value else None)
            else:
                setattr(config, field, value)

        config.updated_at = datetime.utcnow()

        session.commit()
        session.refresh(config)

        logger.info("Report configuration updated", config_id=config.id)

        return config.to_dict()


@router.delete("/reports/configurations/{config_id}", status_code=204)
async def delete_report_configuration(config_id: int):
    """
    Delete report configuration.

    Deletes scheduled report configuration and associated history.
    """
    with get_session() as session:
        config = session.get(ReportConfiguration, config_id)

        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

        session.delete(config)
        session.commit()

        logger.info("Report configuration deleted", config_id=config_id)

        return None


@router.post("/reports/configurations/{config_id}/activate")
async def activate_report_configuration(config_id: int):
    """
    Activate report configuration.

    Sets configuration as active to enable scheduled generation.
    """
    with get_session() as session:
        config = session.get(ReportConfiguration, config_id)

        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

        config.is_active = True
        config.updated_at = datetime.utcnow()

        session.commit()
        session.refresh(config)

        logger.info("Report configuration activated", config_id=config.id)

        return config.to_dict()


@router.post("/reports/configurations/{config_id}/deactivate")
async def deactivate_report_configuration(config_id: int):
    """
    Deactivate report configuration.

    Sets configuration as inactive to disable scheduled generation.
    """
    with get_session() as session:
        config = session.get(ReportConfiguration, config_id)

        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")

        config.is_active = False
        config.updated_at = datetime.utcnow()

        session.commit()
        session.refresh(config)

        logger.info("Report configuration deactivated", config_id=config.id)

        return config.to_dict()


@router.post("/reports/generate")
async def generate_ad_hoc_report(request: GenerateReportRequest):
    """
    Generate ad-hoc report immediately.

    Generates a performance report for the specified date range without
    scheduling. Optionally sends via email.
    """
    try:
        logger.info(
            "Generating ad-hoc report",
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
            account_id=request.account_id
        )

        # Generate report
        generator = ReportGenerator()
        report_path = generator.generate_performance_report(
            start_date=request.start_date,
            end_date=request.end_date,
            account_id=request.account_id,
            include_trades=request.include_trades,
            include_charts=request.include_charts
        )

        # TODO: Email sending if recipients provided
        # This will be implemented when email service is integrated

        logger.info("Ad-hoc report generated", report_path=str(report_path))

        return {
            "success": True,
            "report_path": str(report_path),
            "file_size": report_path.stat().st_size,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat()
        }

    except Exception as e:
        logger.error("Failed to generate ad-hoc report", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/history")
async def get_report_history(
    config_id: Optional[int] = Query(None, description="Filter by configuration ID"),
    success_only: bool = Query(False, description="Show only successful reports"),
    limit: int = Query(50, ge=1, le=500, description="Maximum records to return")
):
    """
    Get report generation history.

    Returns historical report generation records with status and details.
    """
    with get_session() as session:
        query = session.query(ReportHistory)

        if config_id:
            query = query.filter(ReportHistory.config_id == config_id)

        if success_only:
            query = query.filter(ReportHistory.success == True)

        history = query.order_by(
            ReportHistory.generated_at.desc()
        ).limit(limit).all()

        return {
            "history": [record.to_dict() for record in history],
            "count": len(history)
        }


@router.get("/reports/history/{history_id}")
async def get_report_history_detail(history_id: int):
    """
    Get specific report history record.

    Returns detailed information about a specific report generation.
    """
    with get_session() as session:
        history = session.get(ReportHistory, history_id)

        if not history:
            raise HTTPException(status_code=404, detail=f"History record {history_id} not found")

        return history.to_dict()

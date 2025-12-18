"""
Health Check Endpoints

Simple health check and status endpoints for monitoring API availability.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "TradingMTQ Analytics API",
        "version": "2.0.0"
    }


@router.get("/status")
async def get_status():
    """
    Detailed status endpoint with database and scheduler information.

    Returns:
        Detailed system status
    """
    from src.database.connection import get_async_session
    from src.analytics import get_scheduler
    from sqlalchemy import text

    # Check database connection
    db_status = "connected"
    try:
        async with get_async_session() as session:
            session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check scheduler status
    try:
        scheduler = get_scheduler()
        scheduler_status = scheduler.get_status()
    except Exception as e:
        scheduler_status = {"error": str(e)}

    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_status,
            "scheduler": scheduler_status
        }
    }

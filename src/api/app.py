"""
FastAPI Application

Main FastAPI application for the analytics dashboard API.
Provides REST endpoints for retrieving performance metrics and trade data.
"""

# Python 3.14 compatibility patch - MUST be imported first
from src.utils.python314_compat import *  # noqa

from pathlib import Path
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import (
    analytics, trades, health, websocket as ws_routes, alerts, charts,
    accounts, reports, currencies, account_connections, analytics_aggregated, positions,
    config, trading_bot, trading_control, workers
)
from src.api.websocket import connection_manager
from src.database.connection import init_db
from src.utils.unified_logger import UnifiedLogger, OutputFormat, LogContext
from src.services.trading_bot_service import trading_bot_service

logger = UnifiedLogger.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize unified logging system
    UnifiedLogger.configure(
        log_dir="logs",
        log_level="INFO",
        console_output=True,
        console_format=OutputFormat.COLORED,  # Colored console for development
        file_output=True,
        file_format=OutputFormat.JSON  # JSON files for production/monitoring
    )

    # Startup: Initialize database
    init_db()

    # Startup: Start heartbeat loop
    heartbeat_task = asyncio.create_task(connection_manager.heartbeat_loop())

    # Startup: Start trading bot service
    await trading_bot_service.start()

    logger.info("Trading bot service started - will auto-trade on connected accounts")

    yield

    # Shutdown: Stop trading bot service
    await trading_bot_service.stop()
    logger.info("Trading bot service stopped")

    # Shutdown: Cancel heartbeat and close connections
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="TradingMTQ Analytics API",
        description="REST API for trading performance analytics and monitoring",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )

    # HTTP request logging middleware with correlation ID
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # Create correlation context for this request
        with LogContext() as ctx:
            start_time = time.time()

            # Log request with correlation_id
            logger.info(
                f"→ {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                client=request.client.host if request.client else None,
                correlation_id=ctx.correlation_id
            )

            # Process request
            response = await call_next(request)

            # Log response with correlation_id
            duration = time.time() - start_time
            logger.info(
                f"← {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                correlation_id=ctx.correlation_id
            )

            return response

    # CORS middleware for web dashboard access
    # TEMPORARY: Allow all origins for debugging (REMOVE IN PRODUCTION!)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],         # Allow all origins (DEVELOPMENT ONLY!)
        allow_credentials=False,     # Must be False when allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(analytics_aggregated.router, prefix="/api", tags=["analytics-aggregated"])
    app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
    app.include_router(ws_routes.router, prefix="/api", tags=["websocket"])
    app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
    app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
    app.include_router(accounts.router, prefix="/api", tags=["accounts"])
    app.include_router(account_connections.router, prefix="/api", tags=["account-connections"])
    app.include_router(reports.router, prefix="/api", tags=["reports"])
    app.include_router(currencies.router, prefix="/api", tags=["currencies"])
    app.include_router(positions.router, prefix="/api", tags=["positions"])
    app.include_router(config.router, tags=["configuration"])
    app.include_router(trading_bot.router, prefix="/api", tags=["trading-bot"])
    app.include_router(trading_control.router, prefix="/api", tags=["trading-control"])
    app.include_router(workers.router, prefix="/api", tags=["workers"])

    # Mount static files for dashboard (must be after API routes)
    dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
    if dashboard_path.exists():
        app.mount("/", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": str(exc)
            }
        )

    return app


# Create app instance
app = create_app()

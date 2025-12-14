"""
FastAPI Application

Main FastAPI application for the analytics dashboard API.
Provides REST endpoints for retrieving performance metrics and trade data.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import analytics, trades, health


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
        openapi_url="/api/openapi.json"
    )

    # CORS middleware for web dashboard access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React dev server
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(trades.router, prefix="/api/trades", tags=["trades"])

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

"""
API Module

FastAPI-based REST API for analytics dashboard and real-time monitoring.

Components:
- FastAPI application with analytics endpoints
- CORS middleware for web client access
- Real-time WebSocket support (future)
"""

from src.api.app import create_app

__all__ = ["create_app"]

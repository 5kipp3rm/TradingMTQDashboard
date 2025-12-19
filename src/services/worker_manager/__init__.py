"""
Worker Manager Service - Phase 4 Integration

Bridges Configuration System (Phase 1) with Worker Pool (Phase 2).

This service:
- Loads account configurations
- Validates configs before worker creation
- Spawns workers with proper configurations
- Manages worker lifecycle based on config changes
- Coordinates between ConfigurationService and WorkerPoolManager

Design Pattern: Service Layer + Facade
"""

from src.services.worker_manager.service import WorkerManagerService
from src.services.worker_manager.factory import (
    get_worker_manager_service,
    reset_worker_manager_service,
)

__all__ = [
    "WorkerManagerService",
    "get_worker_manager_service",
    "reset_worker_manager_service",
]

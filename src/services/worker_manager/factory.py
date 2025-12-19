"""
Worker Manager Factory - Dependency Injection

Provides factory methods for creating WorkerManagerService with dependencies.

Design Pattern: Factory Pattern + Dependency Injection
"""

from typing import Optional
import logging

from src.services.worker_manager.service import WorkerManagerService
from src.services.worker_manager.validator import AccountConfigurationValidator
from src.config.v2.factory import ConfigurationFactory
from src.workers.pool import WorkerPoolManager


logger = logging.getLogger(__name__)


# Singleton instance
_worker_manager_service_instance: Optional[WorkerManagerService] = None


def get_worker_manager_service(
    config_service=None,
    worker_pool=None,
    validator=None,
    singleton: bool = True,
) -> WorkerManagerService:
    """
    Get or create WorkerManagerService

    Args:
        config_service: Configuration service (optional, will create if None)
        worker_pool: Worker pool manager (optional, will create if None)
        validator: Configuration validator (optional, will create if None)
        singleton: If True, return singleton instance

    Returns:
        WorkerManagerService instance
    """
    global _worker_manager_service_instance

    # Return singleton if exists and requested
    if singleton and _worker_manager_service_instance is not None:
        return _worker_manager_service_instance

    # Create config service if not provided
    if config_service is None:
        config_service = ConfigurationFactory.create_service(
            repository_type="yaml", merge_strategy_type="default"
        )
        logger.info("Created ConfigurationService for WorkerManagerService")

    # Create worker pool if not provided
    if worker_pool is None:
        worker_pool = WorkerPoolManager(max_workers=10)
        logger.info("Created WorkerPoolManager for WorkerManagerService")

    # Create validator if not provided
    if validator is None:
        validator = AccountConfigurationValidator()
        logger.info("Created AccountConfigurationValidator for WorkerManagerService")

    # Create service
    service = WorkerManagerService(
        config_service=config_service, worker_pool=worker_pool, validator=validator
    )

    # Store as singleton if requested
    if singleton:
        _worker_manager_service_instance = service
        logger.info("Created WorkerManagerService singleton")

    return service


def reset_worker_manager_service() -> None:
    """
    Reset singleton instance (useful for testing)
    """
    global _worker_manager_service_instance
    _worker_manager_service_instance = None
    logger.debug("Reset worker manager service singleton")

"""
Worker Manager Service - Phase 4 Integration Layer

Integrates Configuration System (Phase 1) with Worker Pool (Phase 2).

Design Pattern: Service Layer + Facade
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.config.v2.service import ConfigurationService
from src.workers.pool import WorkerPoolManager
from src.services.worker_manager.models import (
    WorkerCreationRequest,
    WorkerInfo,
    WorkerLifecycleStatus,
    ValidationResult,
)
from src.services.worker_manager.validator import AccountConfigurationValidator
from src.config.v2.models import AccountConfig


logger = logging.getLogger(__name__)


class WorkerManagerService:
    """
    Worker Manager Service

    Coordinates between Configuration System and Worker Pool.

    Responsibilities:
    - Load account configurations
    - Validate configs before worker creation
    - Create workers with proper configurations
    - Track worker lifecycle
    - Handle configuration changes

    Example:
        service = WorkerManagerService(config_service, worker_pool)

        # Start worker from configuration
        worker_info = service.start_worker_from_config("account-001")

        # Start all enabled accounts
        results = service.start_all_enabled_workers()

        # Stop worker
        service.stop_worker("account-001")
    """

    def __init__(
        self,
        config_service: ConfigurationService,
        worker_pool: WorkerPoolManager,
        validator: Optional[AccountConfigValidator] = None,
    ):
        """
        Initialize worker manager service

        Args:
            config_service: Configuration service (injected)
            worker_pool: Worker pool manager (injected)
            validator: Configuration validator (optional, will create if None)
        """
        self.config_service = config_service
        self.worker_pool = worker_pool
        self.validator = validator or AccountConfigValidator()
        self._worker_info: Dict[str, WorkerInfo] = {}  # account_id -> WorkerInfo

        logger.info(
            f"Initialized WorkerManagerService with "
            f"{config_service.__class__.__name__} and "
            f"{worker_pool.__class__.__name__}"
        )

    # =============================================================================
    # Worker Lifecycle Management
    # =============================================================================

    def start_worker_from_config(
        self,
        account_id: str,
        apply_defaults: bool = True,
        validate: bool = True,
    ) -> WorkerInfo:
        """
        Start worker using configuration from ConfigurationService

        Args:
            account_id: Account identifier
            apply_defaults: Apply default configurations
            validate: Validate configuration before starting

        Returns:
            WorkerInfo with worker details

        Raises:
            ValueError: If account not found or configuration invalid
            RuntimeError: If worker creation fails
        """
        logger.info(f"Starting worker from config for account {account_id}")

        # Load configuration
        try:
            config = self.config_service.load_account_config(
                account_id=account_id, apply_defaults=apply_defaults
            )
        except Exception as e:
            logger.error(f"Failed to load config for account {account_id}: {e}")
            raise ValueError(f"Failed to load configuration: {str(e)}")

        # Validate configuration
        if validate:
            validation_result = self.validator.validate(config)
            if not validation_result.valid:
                error_msg = (
                    f"Configuration validation failed for account {account_id}: "
                    f"{', '.join(validation_result.errors)}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            if validation_result.has_warnings:
                logger.warning(
                    f"Configuration has warnings for account {account_id}: "
                    f"{', '.join(validation_result.warnings)}"
                )

        # Create worker creation request
        request = self._config_to_worker_request(config)

        # Start worker
        try:
            worker_id = self.worker_pool.start_worker(
                account_id=request.account_id,
                login=request.login,
                password=request.password,
                server=request.server,
                timeout=request.timeout,
                portable=request.portable,
                auto_connect=request.auto_connect,
            )

            # Track worker info
            worker_info = WorkerInfo(
                worker_id=worker_id,
                account_id=account_id,
                status=WorkerLifecycleStatus.RUNNING,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                metadata={"config_applied": apply_defaults},
            )

            self._worker_info[account_id] = worker_info

            logger.info(f"Started worker {worker_id} for account {account_id}")
            return worker_info

        except Exception as e:
            logger.error(f"Failed to start worker for account {account_id}: {e}")
            raise RuntimeError(f"Worker creation failed: {str(e)}")

    def stop_worker(self, account_id: str, timeout: Optional[float] = None) -> bool:
        """
        Stop worker for account

        Args:
            account_id: Account identifier
            timeout: Stop timeout in seconds

        Returns:
            True if stopped successfully

        Raises:
            ValueError: If no worker found for account
        """
        logger.info(f"Stopping worker for account {account_id}")

        if not self.worker_pool.has_worker_for_account(account_id):
            raise ValueError(f"No worker found for account {account_id}")

        try:
            worker_id = self.worker_pool._account_to_worker.get(account_id)
            if worker_id:
                self.worker_pool.stop_worker(worker_id, timeout=timeout)

                # Update worker info
                if account_id in self._worker_info:
                    old_info = self._worker_info[account_id]
                    self._worker_info[account_id] = WorkerInfo(
                        worker_id=old_info.worker_id,
                        account_id=account_id,
                        status=WorkerLifecycleStatus.STOPPED,
                        created_at=old_info.created_at,
                        started_at=old_info.started_at,
                        stopped_at=datetime.utcnow(),
                    )

                logger.info(f"Stopped worker {worker_id} for account {account_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to stop worker for account {account_id}: {e}")
            raise RuntimeError(f"Worker stop failed: {str(e)}")

        return False

    def restart_worker(self, account_id: str) -> WorkerInfo:
        """
        Restart worker for account

        Stops existing worker (if any) and starts new one with latest config.

        Args:
            account_id: Account identifier

        Returns:
            WorkerInfo for new worker
        """
        logger.info(f"Restarting worker for account {account_id}")

        # Stop existing worker if exists
        if self.worker_pool.has_worker_for_account(account_id):
            try:
                self.stop_worker(account_id)
            except Exception as e:
                logger.warning(f"Error stopping existing worker: {e}")

        # Start new worker
        return self.start_worker_from_config(account_id)

    # =============================================================================
    # Batch Operations
    # =============================================================================

    def start_all_enabled_workers(
        self, apply_defaults: bool = True, validate: bool = True
    ) -> Dict[str, WorkerInfo]:
        """
        Start workers for all enabled accounts

        Args:
            apply_defaults: Apply default configurations
            validate: Validate configurations before starting

        Returns:
            Dictionary of account_id -> WorkerInfo for successfully started workers
        """
        logger.info("Starting all enabled workers")

        started_workers = {}
        failed_workers = {}

        # Get list of all accounts
        try:
            account_ids = self.config_service.list_accounts()
            logger.info(f"Found {len(account_ids)} accounts in configuration")
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            return started_workers

        # Start each account
        for account_id in account_ids:
            try:
                # Load config to check if enabled
                config = self.config_service.load_account_config(
                    account_id=account_id, apply_defaults=apply_defaults
                )

                # Check if account is enabled (if attribute exists)
                if hasattr(config, "enabled") and not config.enabled:
                    logger.debug(f"Skipping disabled account {account_id}")
                    continue

                # Start worker
                worker_info = self.start_worker_from_config(
                    account_id=account_id,
                    apply_defaults=apply_defaults,
                    validate=validate,
                )
                started_workers[account_id] = worker_info
                logger.info(f"Started worker for account {account_id}")

            except Exception as e:
                logger.error(f"Failed to start worker for account {account_id}: {e}")
                failed_workers[account_id] = str(e)

        logger.info(
            f"Started {len(started_workers)} workers, "
            f"failed {len(failed_workers)} workers"
        )

        if failed_workers:
            logger.warning(f"Failed accounts: {', '.join(failed_workers.keys())}")

        return started_workers

    def stop_all_workers(self, timeout: Optional[float] = None) -> int:
        """
        Stop all running workers

        Args:
            timeout: Stop timeout per worker in seconds

        Returns:
            Number of workers stopped
        """
        logger.info("Stopping all workers")

        count = 0
        for account_id in list(self._worker_info.keys()):
            try:
                if self.stop_worker(account_id, timeout=timeout):
                    count += 1
            except Exception as e:
                logger.error(f"Error stopping worker for {account_id}: {e}")

        logger.info(f"Stopped {count} workers")
        return count

    def validate_all_configs(self) -> Dict[str, ValidationResult]:
        """
        Validate all account configurations

        Returns:
            Dictionary of account_id -> ValidationResult
        """
        logger.info("Validating all configurations")

        results = {}

        # Get list of all accounts
        try:
            account_ids = self.config_service.list_accounts()
            logger.info(f"Found {len(account_ids)} accounts to validate")
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            return results

        # Validate each account configuration
        for account_id in account_ids:
            try:
                # Load configuration
                config = self.config_service.load_account_config(
                    account_id=account_id, apply_defaults=True
                )

                # Validate configuration
                validation_result = self.validator.validate(config)
                results[account_id] = validation_result

                if not validation_result.valid:
                    logger.warning(
                        f"Configuration invalid for account {account_id}: "
                        f"{len(validation_result.errors)} errors"
                    )
                elif validation_result.has_warnings:
                    logger.info(
                        f"Configuration valid for account {account_id} "
                        f"with {len(validation_result.warnings)} warnings"
                    )
                else:
                    logger.debug(f"Configuration valid for account {account_id}")

            except Exception as e:
                logger.error(f"Failed to validate account {account_id}: {e}")
                # Create error validation result
                results[account_id] = ValidationResult(
                    valid=False,
                    account_id=account_id,
                    errors=(f"Failed to load configuration: {str(e)}",),
                    warnings=(),
                )

        # Summary statistics
        valid_count = sum(1 for r in results.values() if r.valid)
        invalid_count = len(results) - valid_count

        logger.info(
            f"Validated {len(results)} configurations: "
            f"{valid_count} valid, {invalid_count} invalid"
        )

        return results

    # =============================================================================
    # Worker Information
    # =============================================================================

    def get_worker_info(self, account_id: str) -> Optional[WorkerInfo]:
        """
        Get worker information

        Args:
            account_id: Account identifier

        Returns:
            WorkerInfo if worker exists, None otherwise
        """
        return self._worker_info.get(account_id)

    def list_workers(self) -> List[WorkerInfo]:
        """
        List all tracked workers

        Returns:
            List of WorkerInfo objects
        """
        return list(self._worker_info.values())

    def is_worker_running(self, account_id: str) -> bool:
        """
        Check if worker is running for account

        Args:
            account_id: Account identifier

        Returns:
            True if worker is running
        """
        return self.worker_pool.has_worker_for_account(account_id)

    # =============================================================================
    # Configuration Validation
    # =============================================================================

    def validate_config(self, account_id: str) -> ValidationResult:
        """
        Validate configuration for account

        Args:
            account_id: Account identifier

        Returns:
            ValidationResult
        """
        config = self.config_service.load_account_config(account_id)
        return self.validator.validate(config)

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _config_to_worker_request(
        self, config: AccountConfig
    ) -> WorkerCreationRequest:
        """
        Convert AccountConfig to WorkerCreationRequest

        Args:
            config: Account configuration

        Returns:
            WorkerCreationRequest
        """
        return WorkerCreationRequest(
            account_id=config.account_id,
            login=getattr(config, "login", 0),
            password=getattr(config, "password", ""),
            server=getattr(config, "server", ""),
            timeout=getattr(config, "timeout", 60000),
            portable=getattr(config, "portable", False),
            auto_connect=True,
        )

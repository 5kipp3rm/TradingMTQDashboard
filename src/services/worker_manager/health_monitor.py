"""
Worker Health Monitoring

Provides health checking and monitoring for workers with auto-recovery capabilities.

Design Patterns:
- Observer Pattern: Monitor workers and notify on state changes
- Strategy Pattern: Pluggable health check strategies
- Singleton Pattern: Single monitor instance
"""

import logging
import asyncio
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from src.services.worker_manager.models import WorkerLifecycleStatus


logger = logging.getLogger(__name__)


# =============================================================================
# Health Check Models
# =============================================================================

class HealthStatus(str, Enum):
    """Worker health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    status: HealthStatus
    account_id: str
    worker_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    checks_passed: int = 0
    checks_failed: int = 0
    failure_reasons: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        """Check if worker is healthy"""
        return self.status == HealthStatus.HEALTHY

    @property
    def needs_recovery(self) -> bool:
        """Check if worker needs recovery"""
        return self.status == HealthStatus.UNHEALTHY


@dataclass
class WorkerHealthMetrics:
    """Health metrics for a worker"""
    account_id: str
    worker_id: str
    last_check_time: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    total_checks: int = 0
    total_failures: int = 0
    last_recovery_time: Optional[datetime] = None
    recovery_count: int = 0


# =============================================================================
# Health Monitor
# =============================================================================

class WorkerHealthMonitor:
    """
    Monitors worker health and triggers auto-recovery

    Features:
    - Periodic health checks
    - Configurable failure thresholds
    - Auto-recovery with exponential backoff
    - Health metrics tracking
    - Event notifications
    """

    def __init__(
        self,
        worker_manager_service,
        check_interval: float = 60.0,  # Check every 60 seconds
        failure_threshold: int = 3,  # Restart after 3 consecutive failures
        recovery_enabled: bool = True,
        recovery_backoff_base: float = 60.0,  # Base backoff time in seconds
        recovery_backoff_max: float = 3600.0,  # Max backoff time (1 hour)
    ):
        """
        Initialize health monitor

        Args:
            worker_manager_service: Worker manager service to monitor
            check_interval: Interval between health checks in seconds
            failure_threshold: Number of consecutive failures before recovery
            recovery_enabled: Enable automatic recovery
            recovery_backoff_base: Base backoff time for recovery in seconds
            recovery_backoff_max: Maximum backoff time for recovery in seconds
        """
        self.service = worker_manager_service
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.recovery_enabled = recovery_enabled
        self.recovery_backoff_base = recovery_backoff_base
        self.recovery_backoff_max = recovery_backoff_max

        # Health metrics per worker
        self.metrics: Dict[str, WorkerHealthMetrics] = {}

        # Event callbacks
        self._on_health_change_callbacks: List[Callable] = []
        self._on_recovery_callbacks: List[Callable] = []

        # Monitor state
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

    # =========================================================================
    # Health Check Logic
    # =========================================================================

    def check_worker_health(self, account_id: str) -> HealthCheckResult:
        """
        Check health of a specific worker

        Args:
            account_id: Account ID to check

        Returns:
            Health check result
        """
        result = HealthCheckResult(
            status=HealthStatus.UNKNOWN,
            account_id=account_id,
        )

        try:
            # Check if worker exists
            worker_info = self.service.get_worker_info(account_id)

            if not worker_info:
                result.status = HealthStatus.UNHEALTHY
                result.failure_reasons.append("Worker not found")
                result.checks_failed += 1
                return result

            result.worker_id = worker_info.worker_id

            # Check worker status
            is_running = self.service.is_worker_running(account_id)

            if not is_running:
                result.status = HealthStatus.UNHEALTHY
                result.failure_reasons.append("Worker not running")
                result.checks_failed += 1
            else:
                result.status = HealthStatus.HEALTHY
                result.checks_passed += 1

            # Check for error state
            if worker_info.error:
                result.status = HealthStatus.UNHEALTHY
                result.failure_reasons.append(f"Worker error: {worker_info.error}")
                result.checks_failed += 1

            # Check worker lifecycle status
            if worker_info.status in [WorkerLifecycleStatus.FAILED, WorkerLifecycleStatus.STOPPED]:
                result.status = HealthStatus.UNHEALTHY
                result.failure_reasons.append(f"Worker in {worker_info.status} state")
                result.checks_failed += 1

            # Calculate uptime metric
            if worker_info.started_at:
                uptime = (datetime.utcnow() - worker_info.started_at).total_seconds()
                result.metrics["uptime_seconds"] = uptime

        except Exception as e:
            logger.error(f"Health check failed for account {account_id}: {e}")
            result.status = HealthStatus.UNHEALTHY
            result.failure_reasons.append(f"Health check exception: {str(e)}")
            result.checks_failed += 1

        return result

    def check_all_workers(self) -> Dict[str, HealthCheckResult]:
        """
        Check health of all workers

        Returns:
            Dictionary of account_id -> HealthCheckResult
        """
        results = {}

        try:
            workers = self.service.list_workers()

            for worker_info in workers:
                account_id = worker_info.account_id
                results[account_id] = self.check_worker_health(account_id)

        except Exception as e:
            logger.error(f"Failed to check all workers: {e}")

        return results

    # =========================================================================
    # Recovery Logic
    # =========================================================================

    def recover_worker(self, account_id: str) -> bool:
        """
        Attempt to recover a failed worker

        Args:
            account_id: Account ID to recover

        Returns:
            True if recovery succeeded, False otherwise
        """
        if not self.recovery_enabled:
            logger.info(f"Auto-recovery disabled, skipping recovery for {account_id}")
            return False

        try:
            # Get metrics
            metrics = self.metrics.get(account_id)

            if metrics:
                # Calculate backoff time based on recovery count
                backoff_time = min(
                    self.recovery_backoff_base * (2 ** metrics.recovery_count),
                    self.recovery_backoff_max
                )

                # Check if enough time has passed since last recovery
                if metrics.last_recovery_time:
                    time_since_recovery = (datetime.utcnow() - metrics.last_recovery_time).total_seconds()
                    if time_since_recovery < backoff_time:
                        logger.info(
                            f"Skipping recovery for {account_id}, "
                            f"backoff period not elapsed ({time_since_recovery:.0f}s < {backoff_time:.0f}s)"
                        )
                        return False

            logger.info(f"Attempting to recover worker for account {account_id}")

            # Restart worker
            worker_info = self.service.restart_worker(account_id)

            # Update metrics
            if account_id not in self.metrics:
                self.metrics[account_id] = WorkerHealthMetrics(
                    account_id=account_id,
                    worker_id=worker_info.worker_id,
                )

            self.metrics[account_id].last_recovery_time = datetime.utcnow()
            self.metrics[account_id].recovery_count += 1
            self.metrics[account_id].consecutive_failures = 0  # Reset failure count

            logger.info(f"Successfully recovered worker for account {account_id}")

            # Notify callbacks
            self._notify_recovery(account_id, worker_info.worker_id)

            return True

        except Exception as e:
            logger.error(f"Failed to recover worker for account {account_id}: {e}")
            return False

    # =========================================================================
    # Metrics Tracking
    # =========================================================================

    def update_metrics(self, account_id: str, health_result: HealthCheckResult):
        """
        Update health metrics for a worker

        Args:
            account_id: Account ID
            health_result: Health check result
        """
        if account_id not in self.metrics:
            self.metrics[account_id] = WorkerHealthMetrics(
                account_id=account_id,
                worker_id=health_result.worker_id or "unknown",
            )

        metrics = self.metrics[account_id]
        metrics.last_check_time = health_result.timestamp
        metrics.total_checks += 1

        if not health_result.is_healthy:
            metrics.consecutive_failures += 1
            metrics.total_failures += 1
        else:
            metrics.consecutive_failures = 0

    def get_metrics(self, account_id: str) -> Optional[WorkerHealthMetrics]:
        """Get health metrics for a worker"""
        return self.metrics.get(account_id)

    def get_all_metrics(self) -> Dict[str, WorkerHealthMetrics]:
        """Get health metrics for all workers"""
        return self.metrics.copy()

    # =========================================================================
    # Monitoring Loop
    # =========================================================================

    async def start(self):
        """Start health monitoring loop"""
        if self._running:
            logger.warning("Health monitor already running")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(
            f"Started health monitor (check_interval={self.check_interval}s, "
            f"failure_threshold={self.failure_threshold}, "
            f"recovery_enabled={self.recovery_enabled})"
        )

    async def stop(self):
        """Stop health monitoring loop"""
        if not self._running:
            return

        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped health monitor")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Check all workers
                results = await asyncio.to_thread(self.check_all_workers)

                # Process results
                for account_id, health_result in results.items():
                    # Update metrics
                    self.update_metrics(account_id, health_result)

                    # Get metrics
                    metrics = self.metrics[account_id]

                    # Check if recovery is needed
                    if metrics.consecutive_failures >= self.failure_threshold:
                        logger.warning(
                            f"Worker {account_id} has {metrics.consecutive_failures} "
                            f"consecutive failures (threshold: {self.failure_threshold})"
                        )

                        # Attempt recovery
                        recovery_success = await asyncio.to_thread(
                            self.recover_worker, account_id
                        )

                        if recovery_success:
                            logger.info(f"Recovery successful for worker {account_id}")
                        else:
                            logger.error(f"Recovery failed for worker {account_id}")

                    # Notify health change
                    self._notify_health_change(account_id, health_result)

                # Wait before next check
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(self.check_interval)

    # =========================================================================
    # Event Callbacks
    # =========================================================================

    def on_health_change(self, callback: Callable[[str, HealthCheckResult], None]):
        """Register callback for health status changes"""
        self._on_health_change_callbacks.append(callback)

    def on_recovery(self, callback: Callable[[str, str], None]):
        """Register callback for worker recovery"""
        self._on_recovery_callbacks.append(callback)

    def _notify_health_change(self, account_id: str, health_result: HealthCheckResult):
        """Notify all registered health change callbacks"""
        for callback in self._on_health_change_callbacks:
            try:
                callback(account_id, health_result)
            except Exception as e:
                logger.error(f"Error in health change callback: {e}")

    def _notify_recovery(self, account_id: str, worker_id: str):
        """Notify all registered recovery callbacks"""
        for callback in self._on_recovery_callbacks:
            try:
                callback(account_id, worker_id)
            except Exception as e:
                logger.error(f"Error in recovery callback: {e}")


# =============================================================================
# Singleton Instance
# =============================================================================

_monitor_instance: Optional[WorkerHealthMonitor] = None


def get_health_monitor(
    worker_manager_service=None,
    **kwargs
) -> WorkerHealthMonitor:
    """
    Get or create health monitor instance (singleton)

    Args:
        worker_manager_service: Worker manager service (required for first call)
        **kwargs: Additional configuration parameters

    Returns:
        WorkerHealthMonitor instance
    """
    global _monitor_instance

    if _monitor_instance is None:
        if worker_manager_service is None:
            raise ValueError("worker_manager_service required for first call to get_health_monitor")

        _monitor_instance = WorkerHealthMonitor(worker_manager_service, **kwargs)

    return _monitor_instance

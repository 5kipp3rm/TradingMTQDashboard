"""
Worker Management API Routes

Provides REST API endpoints for managing MT5 workers via WorkerManagerService.

Design Patterns:
- RESTful API design
- Service Layer delegation
- Error handling with proper HTTP status codes
- Request/Response validation with Pydantic

Endpoints:
- POST /workers/{account_id}/start - Start worker for account
- POST /workers/{account_id}/stop - Stop worker
- POST /workers/{account_id}/restart - Restart worker
- GET /workers/{account_id} - Get worker information
- GET /workers - List all workers
- POST /workers/start-all - Start all enabled workers
- POST /workers/stop-all - Stop all workers
- GET /workers/{account_id}/validate - Validate account configuration
- GET /workers/validate-all - Validate all configurations
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.worker_manager import get_worker_manager_service
from src.services.worker_manager.models import WorkerInfo, ValidationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workers", tags=["workers"])


# =============================================================================
# Request/Response Models
# =============================================================================

class StartWorkerRequest(BaseModel):
    """Request model for starting a worker"""
    apply_defaults: bool = Field(True, description="Apply default configurations")
    validate: bool = Field(True, description="Validate configuration before starting")


class StopWorkerRequest(BaseModel):
    """Request model for stopping a worker"""
    timeout: Optional[float] = Field(None, description="Stop timeout in seconds", ge=0)


class WorkerInfoResponse(BaseModel):
    """Response model for worker information"""
    worker_id: str
    account_id: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_worker_info(cls, info: WorkerInfo) -> "WorkerInfoResponse":
        """Create response from WorkerInfo"""
        data = info.to_dict()
        return cls(**data)


class ValidationResultResponse(BaseModel):
    """Response model for validation result"""
    valid: bool
    account_id: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    has_errors: bool
    has_warnings: bool

    @classmethod
    def from_validation_result(cls, result: ValidationResult) -> "ValidationResultResponse":
        """Create response from ValidationResult"""
        data = result.to_dict()
        data["has_errors"] = result.has_errors
        data["has_warnings"] = result.has_warnings
        return cls(**data)


class BatchStartResponse(BaseModel):
    """Response model for batch start operation"""
    started_count: int
    started_workers: Dict[str, WorkerInfoResponse]


class BatchStopResponse(BaseModel):
    """Response model for batch stop operation"""
    stopped_count: int


class BatchValidationResponse(BaseModel):
    """Response model for batch validation"""
    total_count: int
    valid_count: int
    invalid_count: int
    results: Dict[str, ValidationResultResponse]


# =============================================================================
# Single Worker Operations
# =============================================================================

@router.post("/{account_id}/start", response_model=WorkerInfoResponse, status_code=201)
async def start_worker(
    account_id: str,
    request: StartWorkerRequest = StartWorkerRequest(),
):
    """
    Start a worker for the specified account

    Args:
        account_id: Account ID to start worker for
        request: Start worker request parameters

    Returns:
        Worker information

    Raises:
        HTTPException: 400 if validation fails, 500 if start fails
    """
    try:
        service = get_worker_manager_service()

        worker_info = service.start_worker_from_config(
            account_id=account_id,
            apply_defaults=request.apply_defaults,
            validate=request.validate,
        )

        logger.info(f"Started worker {worker_info.worker_id} for account {account_id}")
        return WorkerInfoResponse.from_worker_info(worker_info)

    except ValueError as e:
        logger.warning(f"Validation failed for account {account_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start worker for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start worker: {str(e)}")


@router.post("/{account_id}/stop", response_model=dict, status_code=200)
async def stop_worker(
    account_id: str,
    request: StopWorkerRequest = StopWorkerRequest(),
):
    """
    Stop the worker for the specified account

    Args:
        account_id: Account ID to stop worker for
        request: Stop worker request parameters

    Returns:
        Success message

    Raises:
        HTTPException: 404 if worker not found, 500 if stop fails
    """
    try:
        service = get_worker_manager_service()

        success = service.stop_worker(
            account_id=account_id,
            timeout=request.timeout,
        )

        logger.info(f"Stopped worker for account {account_id}")
        return {"success": success, "message": f"Worker stopped for account {account_id}"}

    except ValueError as e:
        logger.warning(f"Worker not found for account {account_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to stop worker for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop worker: {str(e)}")


@router.post("/{account_id}/restart", response_model=WorkerInfoResponse, status_code=200)
async def restart_worker(account_id: str):
    """
    Restart the worker for the specified account

    Args:
        account_id: Account ID to restart worker for

    Returns:
        Worker information

    Raises:
        HTTPException: 404 if worker not found, 500 if restart fails
    """
    try:
        service = get_worker_manager_service()

        worker_info = service.restart_worker(account_id)

        logger.info(f"Restarted worker {worker_info.worker_id} for account {account_id}")
        return WorkerInfoResponse.from_worker_info(worker_info)

    except ValueError as e:
        logger.warning(f"Worker not found for account {account_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restart worker for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart worker: {str(e)}")


@router.get("/{account_id}", response_model=WorkerInfoResponse, status_code=200)
async def get_worker_info(account_id: str):
    """
    Get information about a worker

    Args:
        account_id: Account ID to get worker info for

    Returns:
        Worker information

    Raises:
        HTTPException: 404 if worker not found
    """
    try:
        service = get_worker_manager_service()

        worker_info = service.get_worker_info(account_id)

        if not worker_info:
            raise HTTPException(
                status_code=404,
                detail=f"No worker found for account {account_id}"
            )

        return WorkerInfoResponse.from_worker_info(worker_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get worker info for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get worker info: {str(e)}")


@router.get("", response_model=List[WorkerInfoResponse], status_code=200)
async def list_workers():
    """
    List all workers

    Returns:
        List of worker information

    Raises:
        HTTPException: 500 if listing fails
    """
    try:
        service = get_worker_manager_service()

        workers = service.list_workers()

        return [WorkerInfoResponse.from_worker_info(w) for w in workers]

    except Exception as e:
        logger.error(f"Failed to list workers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list workers: {str(e)}")


# =============================================================================
# Batch Operations
# =============================================================================

@router.post("/start-all", response_model=BatchStartResponse, status_code=201)
async def start_all_workers(
    apply_defaults: bool = Query(True, description="Apply default configurations"),
    validate: bool = Query(True, description="Validate configurations before starting"),
):
    """
    Start workers for all enabled accounts

    Args:
        apply_defaults: Apply default configurations
        validate: Validate configurations before starting

    Returns:
        Batch start result

    Raises:
        HTTPException: 500 if operation fails
    """
    try:
        service = get_worker_manager_service()

        started_workers = service.start_all_enabled_workers(
            apply_defaults=apply_defaults,
            validate=validate,
        )

        logger.info(f"Started {len(started_workers)} workers")

        return BatchStartResponse(
            started_count=len(started_workers),
            started_workers={
                account_id: WorkerInfoResponse.from_worker_info(info)
                for account_id, info in started_workers.items()
            }
        )

    except Exception as e:
        logger.error(f"Failed to start all workers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start all workers: {str(e)}")


@router.post("/stop-all", response_model=BatchStopResponse, status_code=200)
async def stop_all_workers(
    timeout: Optional[float] = Query(None, description="Stop timeout in seconds", ge=0),
):
    """
    Stop all running workers

    Args:
        timeout: Stop timeout per worker in seconds

    Returns:
        Batch stop result

    Raises:
        HTTPException: 500 if operation fails
    """
    try:
        service = get_worker_manager_service()

        stopped_count = service.stop_all_workers(timeout=timeout)

        logger.info(f"Stopped {stopped_count} workers")

        return BatchStopResponse(stopped_count=stopped_count)

    except Exception as e:
        logger.error(f"Failed to stop all workers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop all workers: {str(e)}")


# =============================================================================
# Validation Operations
# =============================================================================

@router.get("/{account_id}/validate", response_model=ValidationResultResponse, status_code=200)
async def validate_configuration(account_id: str):
    """
    Validate account configuration

    Args:
        account_id: Account ID to validate configuration for

    Returns:
        Validation result

    Raises:
        HTTPException: 500 if validation fails
    """
    try:
        service = get_worker_manager_service()

        result = service.validate_config(account_id)

        return ValidationResultResponse.from_validation_result(result)

    except Exception as e:
        logger.error(f"Failed to validate config for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate configuration: {str(e)}")


@router.get("/validate-all", response_model=BatchValidationResponse, status_code=200)
async def validate_all_configurations():
    """
    Validate all account configurations

    Returns:
        Batch validation result

    Raises:
        HTTPException: 500 if validation fails
    """
    try:
        service = get_worker_manager_service()

        results = service.validate_all_configs()

        valid_count = sum(1 for r in results.values() if r.valid)
        invalid_count = len(results) - valid_count

        return BatchValidationResponse(
            total_count=len(results),
            valid_count=valid_count,
            invalid_count=invalid_count,
            results={
                account_id: ValidationResultResponse.from_validation_result(result)
                for account_id, result in results.items()
            }
        )

    except Exception as e:
        logger.error(f"Failed to validate all configs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate all configurations: {str(e)}")

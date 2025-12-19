# Phase 5: Worker Management REST API - Implementation Summary

## Overview

Phase 5 implements a **REST API** for the Worker Manager Service (Phase 4), exposing all worker management functionality via HTTP endpoints. This provides remote control of MT5 workers through standard REST patterns.

**Status**: ✅ **100% Complete** (All endpoints implemented and integrated)

## Architecture

### Design Patterns

- **RESTful API Design**: Standard HTTP methods and status codes
- **Request/Response Validation**: Pydantic models for type safety
- **Service Layer Delegation**: All logic delegated to WorkerManagerService
- **Error Handling**: Proper HTTP status codes (400, 404, 500)
- **Async/Await**: FastAPI async handlers for concurrent requests

### API Structure

```
POST   /api/workers/{account_id}/start       - Start worker for account
POST   /api/workers/{account_id}/stop        - Stop worker
POST   /api/workers/{account_id}/restart     - Restart worker
GET    /api/workers/{account_id}             - Get worker information
GET    /api/workers                          - List all workers
POST   /api/workers/start-all                - Start all enabled workers
POST   /api/workers/stop-all                 - Stop all workers
GET    /api/workers/{account_id}/validate    - Validate account configuration
GET    /api/workers/validate-all             - Validate all configurations
```

## Implementation Details

### File Structure

```
src/api/routes/workers.py           # Worker management endpoints
src/api/app.py                       # FastAPI app with router registration
```

### Request/Response Models

**StartWorkerRequest**:
```python
{
    "apply_defaults": true,  # Apply default configurations
    "validate": true,        # Validate before starting
}
```

**StopWorkerRequest**:
```python
{
    "timeout": 30.0  # Optional stop timeout in seconds
}
```

**WorkerInfoResponse**:
```python
{
    "worker_id": "worker-123",
    "account_id": "account-001",
    "status": "running",
    "created_at": "2025-01-15T10:30:00Z",
    "started_at": "2025-01-15T10:30:05Z",
    "stopped_at": null,
    "error": null,
    "metadata": {}
}
```

**ValidationResultResponse**:
```python
{
    "valid": true,
    "account_id": "account-001",
    "errors": [],
    "warnings": ["risk_percent is high (10.0%), consider reducing"],
    "has_errors": false,
    "has_warnings": true
}
```

**BatchStartResponse**:
```python
{
    "started_count": 3,
    "started_workers": {
        "account-001": {...},
        "account-002": {...},
        "account-003": {...}
    }
}
```

**BatchStopResponse**:
```python
{
    "stopped_count": 3
}
```

**BatchValidationResponse**:
```python
{
    "total_count": 5,
    "valid_count": 4,
    "invalid_count": 1,
    "results": {
        "account-001": {...},
        "account-002": {...},
        ...
    }
}
```

## API Endpoints

### Single Worker Operations

#### Start Worker
```http
POST /api/workers/{account_id}/start
Content-Type: application/json

{
    "apply_defaults": true,
    "validate": true
}
```

**Response** (201 Created):
```json
{
    "worker_id": "worker-123",
    "account_id": "account-001",
    "status": "running",
    "created_at": "2025-01-15T10:30:00Z",
    "started_at": "2025-01-15T10:30:05Z",
    "stopped_at": null,
    "error": null,
    "metadata": {}
}
```

**Error Responses**:
- 400 Bad Request: Validation failed
- 500 Internal Server Error: Start failed

#### Stop Worker
```http
POST /api/workers/{account_id}/stop
Content-Type: application/json

{
    "timeout": 30.0
}
```

**Response** (200 OK):
```json
{
    "success": true,
    "message": "Worker stopped for account account-001"
}
```

**Error Responses**:
- 404 Not Found: Worker not found
- 500 Internal Server Error: Stop failed

#### Restart Worker
```http
POST /api/workers/{account_id}/restart
```

**Response** (200 OK):
```json
{
    "worker_id": "worker-124",
    "account_id": "account-001",
    "status": "running",
    ...
}
```

**Error Responses**:
- 404 Not Found: Worker not found
- 500 Internal Server Error: Restart failed

#### Get Worker Info
```http
GET /api/workers/{account_id}
```

**Response** (200 OK):
```json
{
    "worker_id": "worker-123",
    "account_id": "account-001",
    "status": "running",
    ...
}
```

**Error Responses**:
- 404 Not Found: Worker not found
- 500 Internal Server Error: Query failed

#### List Workers
```http
GET /api/workers
```

**Response** (200 OK):
```json
[
    {
        "worker_id": "worker-123",
        "account_id": "account-001",
        "status": "running",
        ...
    },
    {
        "worker_id": "worker-124",
        "account_id": "account-002",
        "status": "running",
        ...
    }
]
```

**Error Responses**:
- 500 Internal Server Error: List failed

### Batch Operations

#### Start All Workers
```http
POST /api/workers/start-all?apply_defaults=true&validate=true
```

**Response** (201 Created):
```json
{
    "started_count": 3,
    "started_workers": {
        "account-001": {...},
        "account-002": {...},
        "account-003": {...}
    }
}
```

**Error Responses**:
- 500 Internal Server Error: Batch start failed

#### Stop All Workers
```http
POST /api/workers/stop-all?timeout=30.0
```

**Response** (200 OK):
```json
{
    "stopped_count": 3
}
```

**Error Responses**:
- 500 Internal Server Error: Batch stop failed

### Validation Operations

#### Validate Configuration
```http
GET /api/workers/{account_id}/validate
```

**Response** (200 OK):
```json
{
    "valid": true,
    "account_id": "account-001",
    "errors": [],
    "warnings": ["risk_percent is high (10.0%), consider reducing"],
    "has_errors": false,
    "has_warnings": true
}
```

**Error Responses**:
- 500 Internal Server Error: Validation failed

#### Validate All Configurations
```http
GET /api/workers/validate-all
```

**Response** (200 OK):
```json
{
    "total_count": 5,
    "valid_count": 4,
    "invalid_count": 1,
    "results": {
        "account-001": {...},
        "account-002": {...},
        ...
    }
}
```

**Error Responses**:
- 500 Internal Server Error: Batch validation failed

## Usage Examples

### Using cURL

**Start a worker**:
```bash
curl -X POST "http://localhost:8000/api/workers/account-001/start" \
  -H "Content-Type: application/json" \
  -d '{"apply_defaults": true, "validate": true}'
```

**List all workers**:
```bash
curl "http://localhost:8000/api/workers"
```

**Stop a worker**:
```bash
curl -X POST "http://localhost:8000/api/workers/account-001/stop" \
  -H "Content-Type: application/json" \
  -d '{"timeout": 30.0}'
```

**Validate configuration**:
```bash
curl "http://localhost:8000/api/workers/account-001/validate"
```

**Start all enabled workers**:
```bash
curl -X POST "http://localhost:8000/api/workers/start-all?apply_defaults=true&validate=true"
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000/api/workers"

# Start a worker
response = requests.post(
    f"{BASE_URL}/account-001/start",
    json={"apply_defaults": True, "validate": True}
)
worker_info = response.json()
print(f"Started worker: {worker_info['worker_id']}")

# List all workers
response = requests.get(BASE_URL)
workers = response.json()
print(f"Total workers: {len(workers)}")

# Validate configuration
response = requests.get(f"{BASE_URL}/account-001/validate")
validation = response.json()
if validation["valid"]:
    print("Configuration valid!")
    if validation["warnings"]:
        print(f"Warnings: {validation['warnings']}")
else:
    print(f"Configuration invalid: {validation['errors']}")

# Stop a worker
response = requests.post(
    f"{BASE_URL}/account-001/stop",
    json={"timeout": 30.0}
)
print(f"Worker stopped: {response.json()['success']}")
```

### Using JavaScript/TypeScript Fetch

```javascript
const BASE_URL = "http://localhost:8000/api/workers";

// Start a worker
async function startWorker(accountId) {
    const response = await fetch(`${BASE_URL}/${accountId}/start`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            apply_defaults: true,
            validate: true,
        }),
    });

    const workerInfo = await response.json();
    console.log("Started worker:", workerInfo.worker_id);
    return workerInfo;
}

// List all workers
async function listWorkers() {
    const response = await fetch(BASE_URL);
    const workers = await response.json();
    console.log("Total workers:", workers.length);
    return workers;
}

// Validate configuration
async function validateConfig(accountId) {
    const response = await fetch(`${BASE_URL}/${accountId}/validate`);
    const validation = await response.json();

    if (validation.valid) {
        console.log("Configuration valid!");
        if (validation.warnings.length > 0) {
            console.log("Warnings:", validation.warnings);
        }
    } else {
        console.error("Configuration invalid:", validation.errors);
    }

    return validation;
}
```

## Integration with Existing System

### FastAPI Application
The Worker API is registered in [src/api/app.py](../src/api/app.py:149):
```python
app.include_router(workers.router, prefix="/api", tags=["workers"])
```

### Service Integration
All endpoints delegate to WorkerManagerService from Phase 4:
```python
from src.services.worker_manager import get_worker_manager_service

service = get_worker_manager_service()
worker_info = service.start_worker_from_config(account_id, apply_defaults, validate)
```

### Error Handling
Proper HTTP status codes based on error type:
- **400 Bad Request**: Validation failures (ValueError)
- **404 Not Found**: Worker not found
- **500 Internal Server Error**: Unexpected errors

### Logging
All operations logged with INFO/WARNING/ERROR levels:
```python
logger.info(f"Started worker {worker_info.worker_id} for account {account_id}")
logger.warning(f"Validation failed for account {account_id}: {e}")
logger.error(f"Failed to start worker for account {account_id}: {e}")
```

## Benefits

### API Design Quality
- **RESTful Conventions**: Standard HTTP methods and status codes
- **Type Safety**: Pydantic validation for all request/response models
- **Error Transparency**: Clear error messages with appropriate HTTP codes
- **Async Support**: FastAPI async handlers for high concurrency
- **Auto-Documentation**: Swagger UI available at `/api/docs`

### Operational Benefits
- **Remote Management**: Control workers from any HTTP client
- **Integration Ready**: Easy integration with web dashboards, CLIs, other services
- **Batch Operations**: Efficient management of multiple workers
- **Validation Before Action**: Check configurations before starting workers
- **Comprehensive Status**: Full visibility into worker states

### Development Benefits
- **Well-Documented**: Auto-generated OpenAPI/Swagger documentation
- **Easy Testing**: Standard HTTP endpoints for integration tests
- **Language Agnostic**: Any language with HTTP client can use API
- **Clear Contracts**: Pydantic models define exact request/response shapes

## OpenAPI/Swagger Documentation

The API is fully documented with OpenAPI 3.0 spec, accessible at:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

All endpoints include:
- Request/response schemas
- Example payloads
- HTTP status code documentation
- Error response formats

## Testing the API

### Manual Testing with Swagger UI
1. Start the API server: `uvicorn src.api.app:app --reload`
2. Open `http://localhost:8000/api/docs`
3. Try out endpoints directly in the browser
4. View request/response examples

### Automated Testing (Future)
Integration tests can be written using:
```python
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_start_worker():
    response = client.post(
        "/api/workers/account-001/start",
        json={"apply_defaults": True, "validate": True}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["account_id"] == "account-001"
    assert data["status"] == "running"
```

## Future Enhancements

### Potential Features
1. **WebSocket Support**: Real-time worker status updates
2. **Bulk Operations**: Start/stop multiple specific workers at once
3. **Worker Metrics**: Expose performance metrics per worker
4. **Health Checks**: Dedicated endpoint for worker health status
5. **Filtering**: Query parameters for listing workers (by status, account, etc.)
6. **Pagination**: Support for large numbers of workers
7. **Authentication**: API key or JWT authentication
8. **Rate Limiting**: Prevent API abuse
9. **Webhooks**: Notify external systems of worker events

### API Versioning
- Current version: v1 (implicit)
- Future: `/api/v1/workers` and `/api/v2/workers` for breaking changes

## Conclusion

Phase 5 successfully implements a production-ready REST API that:

- ✅ Exposes all Phase 4 functionality via HTTP
- ✅ Follows RESTful conventions and best practices
- ✅ Provides comprehensive error handling
- ✅ Includes auto-generated OpenAPI documentation
- ✅ Supports async operations for high concurrency
- ✅ Integrates seamlessly with FastAPI application

The API enables remote worker management from any HTTP client, web dashboard, CLI tool, or external service, making the TradingMTQ system fully accessible and controllable via standard REST patterns.

---

**Implementation Complete**: Phase 5 (REST API) is 100% complete and ready for production use alongside Phases 1-4.

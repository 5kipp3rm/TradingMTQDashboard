"""
Logs API Routes - Retrieve and filter application logs
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import re
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LogEntry(BaseModel):
    """Single log entry"""
    timestamp: datetime
    level: str
    logger: str
    message: str
    correlation_id: Optional[str] = None
    account_id: Optional[int] = None
    event_type: Optional[str] = None
    symbol: Optional[str] = None
    # Additional fields that may exist
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    duration: Optional[float] = None
    client: Optional[str] = None
    # Raw fields for any additional data
    extra: Optional[Dict[str, Any]] = None


class LogsResponse(BaseModel):
    """Response containing logs"""
    logs: List[LogEntry]
    total: int
    filtered: int
    page: int
    page_size: int
    log_type: Optional[str] = None
    account_id: Optional[int] = None


class LogTypeInfo(BaseModel):
    """Information about a log type"""
    name: str
    display_name: str
    file_pattern: str
    description: str


class LogTypesResponse(BaseModel):
    """Available log types"""
    log_types: List[LogTypeInfo]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clean_ansi_codes(text: str) -> str:
    """Remove ANSI color codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON log line"""
    try:
        log_data = json.loads(line.strip())
        # Clean ANSI codes from level
        if 'level' in log_data:
            log_data['level'] = clean_ansi_codes(log_data['level'])
            # Extract just the level name (INFO, WARNING, ERROR, etc.)
            level_match = re.search(r'\[(I|W|E|D)\]\s+(\w+)', log_data['level'])
            if level_match:
                log_data['level'] = level_match.group(2)
        return log_data
    except json.JSONDecodeError:
        return None


def get_log_files(log_type: str, days: int = 7) -> List[Path]:
    """Get log files for a specific type and date range"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return []

    # Determine file pattern based on log type
    patterns = {
        "backend": "trading_*.log",
        "trades": "trades_*.log",
        "errors": "errors_*.log",
        "all": "*.log"
    }

    pattern = patterns.get(log_type, "*.log")

    # Get files from the last N days
    cutoff_date = datetime.now() - timedelta(days=days)
    log_files = []

    for file_path in sorted(log_dir.glob(pattern), reverse=True):
        # Extract date from filename (e.g., trading_20251230.log)
        match = re.search(r'_(\d{8})\.log$', file_path.name)
        if match:
            file_date_str = match.group(1)
            file_date = datetime.strptime(file_date_str, '%Y%m%d')
            if file_date >= cutoff_date:
                log_files.append(file_path)

    return log_files


def read_logs_from_files(
    log_files: List[Path],
    account_id: Optional[int] = None,
    search: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> tuple[List[Dict[str, Any]], int]:
    """
    Read and filter logs from multiple files

    Returns:
        Tuple of (filtered_logs, total_count)
    """
    all_logs = []

    # Read logs from files (newest first)
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    log_data = parse_log_line(line)
                    if log_data:
                        all_logs.append(log_data)
        except Exception as e:
            logger.error(f"Error reading log file {log_file}: {e}")
            continue

    # Sort by timestamp (newest first)
    all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    total_count = len(all_logs)

    # Apply filters
    filtered_logs = all_logs

    if account_id is not None:
        filtered_logs = [
            log for log in filtered_logs
            if log.get('account_id') == account_id
        ]

    if search:
        search_lower = search.lower()
        filtered_logs = [
            log for log in filtered_logs
            if search_lower in log.get('message', '').lower()
            or search_lower in log.get('logger', '').lower()
        ]

    if level:
        level_upper = level.upper()
        filtered_logs = [
            log for log in filtered_logs
            if level_upper in log.get('level', '').upper()
        ]

    filtered_count = len(filtered_logs)

    # Apply pagination
    paginated_logs = filtered_logs[offset:offset + limit]

    return paginated_logs, filtered_count


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/types", response_model=LogTypesResponse)
async def get_log_types():
    """
    Get available log types

    Returns information about different log categories that can be filtered.
    """
    log_types = [
        LogTypeInfo(
            name="all",
            display_name="All Logs",
            file_pattern="*.log",
            description="All application logs including backend, trades, and errors"
        ),
        LogTypeInfo(
            name="backend",
            display_name="Backend Logs",
            file_pattern="trading_*.log",
            description="General application and backend processing logs"
        ),
        LogTypeInfo(
            name="trades",
            display_name="Trades & Positions",
            file_pattern="trades_*.log",
            description="Trading activity, positions, and execution logs"
        ),
        LogTypeInfo(
            name="errors",
            display_name="Errors",
            file_pattern="errors_*.log",
            description="Error and warning logs"
        )
    ]

    return LogTypesResponse(log_types=log_types)


@router.get("", response_model=LogsResponse)
async def get_logs(
    log_type: str = Query(
        "all",
        description="Type of logs to retrieve (all, backend, trades, errors)"
    ),
    account_id: Optional[int] = Query(
        None,
        description="Filter by account ID (null for all accounts)"
    ),
    search: Optional[str] = Query(
        None,
        description="Search text in log messages"
    ),
    level: Optional[str] = Query(
        None,
        description="Filter by log level (INFO, WARNING, ERROR, DEBUG)"
    ),
    days: int = Query(
        7,
        ge=1,
        le=30,
        description="Number of days to look back (1-30)"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of logs to return (1-1000)"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)"
    )
):
    """
    Retrieve logs with filtering options

    Parameters:
    - **log_type**: Type of logs (all, backend, trades, errors)
    - **account_id**: Filter by specific account (omit for all accounts)
    - **search**: Search term to filter messages
    - **level**: Filter by log level (INFO, WARNING, ERROR, DEBUG)
    - **days**: Number of days to look back (1-30)
    - **limit**: Number of logs per page (1-1000)
    - **page**: Page number for pagination

    Returns logs sorted by timestamp (newest first).
    """
    # Validate log_type
    valid_types = ["all", "backend", "trades", "errors"]
    if log_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid log_type '{log_type}'. Must be one of: {', '.join(valid_types)}"
        )

    # Calculate offset for pagination
    offset = (page - 1) * limit

    # Get log files
    log_files = get_log_files(log_type, days)

    if not log_files:
        return LogsResponse(
            logs=[],
            total=0,
            filtered=0,
            page=page,
            page_size=limit,
            log_type=log_type,
            account_id=account_id
        )

    # Read and filter logs
    logs_data, filtered_count = read_logs_from_files(
        log_files,
        account_id=account_id,
        search=search,
        level=level,
        limit=limit,
        offset=offset
    )

    # Convert to LogEntry models
    log_entries = []
    for log_data in logs_data:
        try:
            # Extract known fields
            entry_dict = {
                'timestamp': log_data.get('timestamp'),
                'level': log_data.get('level', 'INFO'),
                'logger': log_data.get('logger', 'unknown'),
                'message': log_data.get('message', ''),
                'correlation_id': log_data.get('correlation_id'),
                'account_id': log_data.get('account_id'),
                'event_type': log_data.get('event_type'),
                'symbol': log_data.get('symbol'),
                'method': log_data.get('method'),
                'path': log_data.get('path'),
                'status_code': log_data.get('status_code'),
                'duration': log_data.get('duration'),
                'client': log_data.get('client')
            }

            # Add any extra fields
            extra_fields = {
                k: v for k, v in log_data.items()
                if k not in entry_dict
            }
            if extra_fields:
                entry_dict['extra'] = extra_fields

            log_entries.append(LogEntry(**entry_dict))
        except Exception as e:
            logger.warning(f"Failed to parse log entry: {e}")
            continue

    return LogsResponse(
        logs=log_entries,
        total=filtered_count,
        filtered=filtered_count,
        page=page,
        page_size=limit,
        log_type=log_type,
        account_id=account_id
    )


@router.get("/stats")
async def get_log_stats(days: int = Query(7, ge=1, le=30)):
    """
    Get statistics about logs

    Returns counts by log type, level, and date.
    """
    stats = {
        "days": days,
        "by_type": {},
        "by_level": {},
        "total_size_bytes": 0
    }

    log_dir = Path("logs")
    if not log_dir.exists():
        return stats

    # Count files and sizes by type
    cutoff_date = datetime.now() - timedelta(days=days)

    for log_type in ["backend", "trades", "errors"]:
        log_files = get_log_files(log_type, days)
        total_lines = 0
        total_size = 0

        for log_file in log_files:
            try:
                total_size += log_file.stat().st_size
                with open(log_file, 'r') as f:
                    total_lines += sum(1 for _ in f)
            except Exception:
                continue

        stats["by_type"][log_type] = {
            "files": len(log_files),
            "total_lines": total_lines,
            "total_size_bytes": total_size
        }
        stats["total_size_bytes"] += total_size

    return stats

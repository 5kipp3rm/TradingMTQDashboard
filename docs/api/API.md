# TradingMTQ REST API Documentation

**Version:** 2.0.0  
**Base URL:** `http://localhost:8000/api`  
**Documentation:** http://localhost:8000/api/docs (Swagger UI)  
**Alternative Docs:** http://localhost:8000/api/redoc (ReDoc)

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Response Format](#response-format)
- [Analytics](#analytics)
- [Trades](#trades)
- [Positions](#positions)
- [Accounts](#accounts)
- [Currencies](#currencies)
- [Configuration](#configuration)
- [Alerts](#alerts)
- [Charts](#charts)
- [Reports](#reports)
- [Health](#health)
- [WebSocket](#websocket)
- [Trading Bot](#trading-bot)
- [Trading Control](#trading-control)
- [Account Connections](#account-connections)
- [Workers](#workers)
- [Error Codes](#error-codes)

---

## Overview

The TradingMTQ API provides comprehensive trading management, analytics, and configuration for MetaTrader 5 (MT5) trading accounts. It supports:

- Real-time trading operations
- Performance analytics and reporting
- Multi-account management
- Automated trading control
- Configuration management
- WebSocket notifications

---

## Authentication

Currently, the API does not require authentication. This should be implemented for production use.

---

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { }
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes
| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `204` | No Content (successful deletion) |
| `400` | Bad Request (validation error) |
| `404` | Not Found |
| `409` | Conflict (duplicate resource) |
| `500` | Internal Server Error |

---

## Analytics

Performance analytics and metrics endpoints.

### GET `/analytics/overview`
Get summary analytics for specified period.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 30 | Number of days (1-365) |
| `account_id` | integer | No | - | Filter by account ID |

**Response:**
```json
{
  "total_trades": 150,
  "net_profit": 2500.50,
  "win_rate": 65.5,
  "avg_daily_profit": 125.25,
  "total_lots": 15.5,
  "profit_factor": 1.85,
  "max_drawdown": 150.00,
  "sharpe_ratio": 1.35
}
```

### GET `/analytics/daily`
Get daily performance records.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | No | - | Start date (YYYY-MM-DD) |
| `end_date` | date | No | - | End date (YYYY-MM-DD) |
| `days` | integer | No | 30 | Max records (1-365) |
| `account_id` | integer | No | - | Filter by account |

**Response:**
```json
[
  {
    "date": "2024-01-15",
    "trades": 5,
    "winners": 3,
    "losers": 2,
    "net_profit": 125.50,
    "win_rate": 60.0,
    "profit_factor": 1.75
  }
]
```

### GET `/analytics/date/{date}`
Get performance metrics for specific date.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | date | Yes | Date (YYYY-MM-DD) |

### POST `/analytics/aggregate`
Manually trigger aggregation for specific date.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `date` | date | No | yesterday | Date to aggregate |

### GET `/analytics/metrics`
Get time series data for charting.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 30 | Number of days (1-365) |
| `account_id` | integer | No | - | Filter by account |

**Response:**
```json
{
  "dates": ["2024-01-01", "2024-01-02"],
  "cumulative_profit": [100.0, 225.5],
  "win_rates": [65.0, 67.5],
  "trade_counts": [3, 5]
}
```

---

## Trades

Trade history and statistics.

### GET `/trades`
Get trades with optional filtering.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `symbol` | string | No | - | Filter by symbol (e.g., EURUSD) |
| `status` | string | No | - | Filter by status (OPEN, CLOSED) |
| `start_date` | date | No | - | Start date |
| `end_date` | date | No | - | End date |
| `limit` | integer | No | 100 | Max trades (1-1000) |

**Response:**
```json
{
  "trades": [
    {
      "ticket": 123456,
      "symbol": "EURUSD",
      "type": "BUY",
      "open_time": "2024-01-15T10:30:00",
      "close_time": "2024-01-15T15:45:00",
      "open_price": 1.0850,
      "close_price": 1.0890,
      "volume": 0.1,
      "profit": 40.00,
      "pips": 40.0,
      "status": "CLOSED"
    }
  ]
}
```

### GET `/trades/{ticket}`
Get specific trade by ticket number.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticket` | integer | Yes | MT5 ticket number |

### GET `/trades/statistics`
Get trade statistics grouped by symbol.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 30 | Number of days (1-365) |

**Response:**
```json
{
  "EURUSD": {
    "total_trades": 50,
    "win_rate": 65.0,
    "total_profit": 500.50,
    "avg_profit": 10.01
  }
}
```

---

## Positions

Position management and trading operations.

### POST `/positions/open`
Open a new trading position.

**Request Body:**
```json
{
  "account_id": 1,
  "symbol": "EURUSD",
  "order_type": "BUY",
  "volume": 0.1,
  "stop_loss": 1.0930,
  "take_profit": 1.0990,
  "comment": "Scalping trade",
  "magic": 234000,
  "deviation": 20
}
```

**Response:**
```json
{
  "success": true,
  "ticket": 123456,
  "message": "Position opened successfully"
}
```

### POST `/positions/{ticket}/close`
Close an open position.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticket` | integer | Yes | Position ticket number |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Trading account ID |

### PUT `/positions/{ticket}/modify`
Modify SL/TP on open position.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticket` | integer | Yes | Position ticket |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Account ID |

**Request Body:**
```json
{
  "stop_loss": 1.0920,
  "take_profit": 1.1000
}
```

### POST `/positions/close-all`
Close all positions for account.

**Request Body:**
```json
{
  "account_id": 1,
  "symbol": "EURUSD"  // Optional: filter by symbol
}
```

**Response:**
```json
{
  "success": true,
  "closed_count": 3,
  "results": [
    {
      "ticket": 123456,
      "success": true,
      "message": "Closed successfully"
    }
  ]
}
```

### POST `/positions/preview`
Preview position with risk calculation before execution.

**Request Body:**
```json
{
  "account_id": 1,
  "symbol": "EURUSD",
  "order_type": "BUY",
  "volume": 0.1,
  "stop_loss": 1.0930,
  "take_profit": 1.0990
}
```

**Response:**
```json
{
  "risk_amount": 50.00,
  "risk_percent": 0.5,
  "potential_profit": 100.00,
  "risk_reward_ratio": 2.0,
  "margin_required": 108.50,
  "pip_value": 1.00
}
```

### GET `/positions/open`
Get all open positions.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Account ID |
| `symbol` | string | No | Filter by symbol |

**Response:**
```json
{
  "positions": [
    {
      "ticket": 123456,
      "symbol": "EURUSD",
      "type": "BUY",
      "volume": 0.1,
      "open_price": 1.0850,
      "current_price": 1.0870,
      "sl": 1.0800,
      "tp": 1.0950,
      "profit": 20.00,
      "open_time": "2024-01-15T10:30:00"
    }
  ]
}
```

---

## Accounts

Trading account management.

### GET `/accounts`
List all trading accounts.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `active_only` | boolean | No | false | Show only active accounts |

**Response:**
```json
{
  "accounts": [
    {
      "id": 1,
      "account_number": 5012345,
      "account_name": "Main Trading",
      "broker": "Broker Name",
      "server": "Server-Live",
      "platform_type": "MT5",
      "is_demo": true,
      "is_active": true,
      "balance": 10000.00,
      "currency": "USD",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### GET `/accounts/{id}`
Get specific account by ID.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Account ID |

### POST `/accounts`
Create new trading account.

**Request Body:**
```json
{
  "account_number": 5012345,
  "account_name": "Main Trading",
  "broker": "Broker Name",
  "server": "Server-Live",
  "platform_type": "MT5",
  "login": 5012345,
  "password": "password",
  "is_demo": true,
  "is_active": true,
  "initial_balance": 10000,
  "currency": "USD"
}
```

### PUT `/accounts/{id}`
Update existing account.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Account ID |

**Request Body:** Partial account data (only fields to update)

### DELETE `/accounts/{id}`
Delete trading account.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Account ID |

### POST `/accounts/{id}/set-default`
Set account as default.

### POST `/accounts/{id}/activate`
Activate account.

### POST `/accounts/{id}/deactivate`
Deactivate account.

### GET `/accounts/{id}/config`
Get account configuration including trading settings.

**Response:**
```json
{
  "config_source": "hybrid",
  "trading_config": {
    "risk": {
      "risk_per_trade": 1.0,
      "max_daily_loss": 5.0
    },
    "strategy": {
      "strategy_type": "crossover",
      "timeframe": "M5"
    },
    "position_management": {
      "max_positions": 3,
      "use_trailing_stop": true
    }
  }
}
```

### PUT `/accounts/{id}/config`
Update account configuration.

**Request Body:**
```json
{
  "config_source": "hybrid",
  "trading_config": {
    "risk": {...},
    "strategy": {...},
    "position_management": {...}
  }
}
```

---

## Currencies

Currency pair configuration management.

### GET `/currencies`
List all currency configurations.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled_only` | boolean | No | false | Show only enabled currencies |

**Response:**
```json
{
  "currencies": [
    {
      "id": 1,
      "symbol": "EURUSD",
      "enabled": true,
      "risk_percent": 1.0,
      "max_position_size": 1.0,
      "min_position_size": 0.01,
      "strategy_type": "crossover",
      "timeframe": "M5",
      "fast_period": 10,
      "slow_period": 20,
      "sl_pips": 50,
      "tp_pips": 100,
      "cooldown_seconds": 300,
      "trade_on_signal_change": true
    }
  ]
}
```

### GET `/currencies/{symbol}`
Get specific currency configuration.

### POST `/currencies`
Create new currency configuration.

**Request Body:**
```json
{
  "symbol": "EURUSD",
  "enabled": true,
  "risk_percent": 1.0,
  "max_position_size": 1.0,
  "min_position_size": 0.01,
  "strategy_type": "crossover",
  "timeframe": "M5",
  "fast_period": 10,
  "slow_period": 20,
  "sl_pips": 50,
  "tp_pips": 100,
  "cooldown_seconds": 300,
  "trade_on_signal_change": true
}
```

### PUT `/currencies/{symbol}`
Update currency configuration.

### DELETE `/currencies/{symbol}`
Delete currency configuration.

### POST `/currencies/{symbol}/enable`
Enable currency for trading.

### POST `/currencies/{symbol}/disable`
Disable currency for trading.

### POST `/currencies/validate`
Validate configuration without saving.

**Request Body:** Currency configuration

**Response:**
```json
{
  "valid": true,
  "errors": []
}
```

### POST `/currencies/reload`
Hot-reload configurations from YAML.

**Response:**
```json
{
  "success": true,
  "added": 2,
  "updated": 5,
  "errors": []
}
```

### POST `/currencies/export`
Export database configs to YAML.

---

## Configuration

System-wide configuration management.

### GET `/config/currencies`
Get all currencies.

### POST `/config/currencies`
Create or update currency.

### POST `/config/currencies/{symbol}/enable`
Enable currency.

### POST `/config/currencies/{symbol}/disable`
Disable currency.

### GET `/config/preferences`
Get trading preferences.

### PUT `/config/preferences`
Update trading preferences.

### GET `/config/favorites`
Get favorite currencies.

### POST `/config/favorites/{symbol}`
Add symbol to favorites.

### DELETE `/config/favorites/{symbol}`
Remove from favorites.

---

## Alerts

Alert configuration and delivery history.

### GET `/alerts`
Get all alert configurations.

### GET `/alerts/{id}`
Get specific alert configuration.

### POST `/alerts`
Create new alert configuration.

**Request Body:**
```json
{
  "alert_type": "trade_opened",
  "enabled": true,
  "email_enabled": true,
  "sms_enabled": false,
  "email_recipients": "user@example.com",
  "profit_threshold": 50.0
}
```

### PUT `/alerts/{id}`
Update alert configuration.

### DELETE `/alerts/{id}`
Delete alert configuration.

### GET `/alerts/history`
Get alert delivery history.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 100 | Max records (1-1000) |
| `alert_type` | string | No | - | Filter by type |
| `delivered_only` | boolean | No | false | Show only delivered |

### GET `/alerts/types`
Get available alert types.

**Response:**
```json
{
  "alert_types": [
    "trade_opened",
    "trade_closed",
    "daily_profit_target",
    "daily_loss_limit",
    "position_sl_hit",
    "position_tp_hit"
  ],
  "channels": ["email", "sms", "webhook"]
}
```

### POST `/alerts/test-email`
Send test email.

**Request Body:**
```json
{
  "email": "test@example.com"
}
```

---

## Charts

Chart data for visualization.

### GET `/charts/equity`
Get equity curve data.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | No | - | Start date |
| `end_date` | date | No | - | End date |
| `interval` | string | No | daily | Interval: daily, trade, hourly |
| `account_id` | integer | No | - | Filter by account |

**Response:**
```json
{
  "data": [
    {
      "timestamp": "2024-01-15T10:00:00",
      "balance": 10000.00,
      "equity": 10025.50
    }
  ]
}
```

### GET `/charts/heatmap`
Get trade distribution heatmap (by hour/day).

**Response:**
```json
{
  "heatmap": [
    {
      "hour": 10,
      "day": 1,
      "trade_count": 5,
      "total_profit": 125.50
    }
  ]
}
```

### GET `/charts/symbol-performance`
Get performance comparison across symbols.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `top_n` | integer | No | 10 | Max symbols (1-50) |

### GET `/charts/win-loss-analysis`
Get detailed win/loss analysis.

**Response:**
```json
{
  "profit_distribution": [
    {"range": "0-50", "count": 10},
    {"range": "50-100", "count": 5}
  ],
  "win_streak": 5,
  "loss_streak": 2,
  "avg_win_duration": "2:30:00",
  "avg_loss_duration": "1:15:00"
}
```

### GET `/charts/monthly-comparison`
Get month-over-month comparison.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `months` | integer | No | 12 | Number of months (1-24) |

### GET `/charts/risk-reward`
Get risk/reward scatter plot data.

---

## Reports

Report generation and scheduling.

### GET `/reports`
List report configurations.

### POST `/reports`
Create report configuration.

**Request Body:**
```json
{
  "name": "Weekly Report",
  "frequency": "weekly",
  "report_format": "pdf",
  "recipients": ["user@example.com"],
  "include_charts": true
}
```

### POST `/reports/generate`
Generate ad-hoc report.

**Request Body:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "include_trades": true,
  "include_charts": false
}
```

**Response:**
```json
{
  "report_path": "/reports/report_20240115.pdf",
  "generated_at": "2024-01-15T10:30:00"
}
```

### GET `/reports/history`
Get report generation history.

---

## Health

System health and status.

### GET `/health`
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "service": "TradingMTQ Analytics API",
  "version": "2.0.0"
}
```

### GET `/health/status`
Detailed system status.

**Response:**
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "pool_size": 5
  },
  "scheduler": {
    "running": true,
    "jobs": 3
  },
  "uptime": "5d 12h 30m"
}
```

---

## WebSocket

Real-time updates via WebSocket connection.

### WebSocket `/ws`
Connect to WebSocket for real-time updates.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | No | Client identifier |

**Connection URL:** `ws://localhost:8000/api/ws?client_id=dashboard`

#### Messages

**Ping/Pong:**
```json
// Client sends
{"type": "ping"}

// Server responds
{"type": "pong", "timestamp": "2024-01-15T10:30:00"}
```

**Subscribe to channels:**
```json
// Client sends
{
  "type": "subscribe",
  "channels": ["trades", "positions", "performance"]
}

// Server responds
{
  "type": "subscribed",
  "channels": ["trades", "positions", "performance"]
}
```

#### Events Received

**Position Opened:**
```json
{
  "type": "position_opened",
  "data": {
    "ticket": 123456,
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.1
  }
}
```

**Position Closed:**
```json
{
  "type": "position_closed",
  "data": {
    "ticket": 123456,
    "profit": 40.00
  }
}
```

**Performance Update:**
```json
{
  "type": "performance_update",
  "data": {
    "daily_profit": 125.50,
    "open_positions": 3
  }
}
```

### GET `/ws/stats`
Get WebSocket connection statistics.

**Response:**
```json
{
  "active_connections": 5,
  "total_messages_sent": 1234,
  "uptime": "2:30:00"
}
```

---

## Trading Bot

Trading bot service control.

### GET `/trading-bot/status`
Get trading bot status.

**Response:**
```json
{
  "running": true,
  "connected_accounts": 3,
  "active_traders": 5,
  "uptime": "1d 5h 30m"
}
```

### POST `/trading-bot/start`
Start trading bot service.

### POST `/trading-bot/stop`
Stop trading bot service.

### POST `/trading-bot/restart`
Restart trading bot service.

---

## Trading Control

Automated trading control for specific accounts.

### POST `/trading-control/start`
Start automated trading for account.

**Request Body:**
```json
{
  "account_id": 1,
  "currency_symbols": ["EURUSD", "GBPUSD"],
  "check_autotrading": true
}
```

**Response:**
```json
{
  "success": true,
  "account_id": 1,
  "trading_enabled": true,
  "active_currencies": ["EURUSD", "GBPUSD"]
}
```

### POST `/trading-control/stop`
Stop automated trading.

**Request Body:**
```json
{
  "account_id": 1
}
```

### GET `/trading-control/status`
Get current trading status.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Account ID |

**Response:**
```json
{
  "account_id": 1,
  "trading_enabled": true,
  "active_currencies": ["EURUSD", "GBPUSD"],
  "last_check": "2024-01-15T10:30:00"
}
```

### GET `/trading-control/autotrading-status`
Check AutoTrading status in MT5.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Account ID |

**Response:**
```json
{
  "enabled": true,
  "message": "AutoTrading is enabled in MT5 terminal",
  "instructions": null
}
```

---

## Account Connections

MT5 account connection management.

### POST `/account-connections/{account_id}/connect`
Connect to MT5 account.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Account ID |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force` | boolean | No | false | Force reconnect if already connected |

**Response:**
```json
{
  "success": true,
  "account_id": 1,
  "connected": true,
  "account_info": {
    "balance": 10000.00,
    "equity": 10025.50,
    "margin": 100.00
  }
}
```

### POST `/account-connections/{account_id}/disconnect`
Disconnect from MT5 account.

### GET `/account-connections/{account_id}/status`
Get real-time connection status.

**Response:**
```json
{
  "account_id": 1,
  "connected": true,
  "last_connected": "2024-01-15T10:00:00",
  "last_error": null,
  "account_info": {
    "balance": 10000.00,
    "equity": 10025.50
  }
}
```

### POST `/account-connections/connect-all`
Connect all active accounts.

**Response:**
```json
{
  "success": true,
  "connected_count": 3,
  "results": [
    {
      "account_id": 1,
      "success": true,
      "message": "Connected successfully"
    }
  ]
}
```

### POST `/account-connections/disconnect-all`
Disconnect all connected accounts.

---

## Workers

Worker process management for automated trading.

### POST `/workers/{account_id}/start`
Start worker for account.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Account ID |

**Request Body:**
```json
{
  "apply_defaults": true,
  "validate": true
}
```

**Response:**
```json
{
  "account_id": 1,
  "running": true,
  "started_at": "2024-01-15T10:30:00",
  "currencies": ["EURUSD", "GBPUSD"]
}
```

### POST `/workers/{account_id}/stop`
Stop worker.

### POST `/workers/{account_id}/restart`
Restart worker.

### GET `/workers/{account_id}`
Get worker information.

### GET `/workers`
List all workers.

**Response:**
```json
{
  "workers": [
    {
      "account_id": 1,
      "running": true,
      "started_at": "2024-01-15T10:00:00",
      "currencies": ["EURUSD", "GBPUSD"],
      "total_trades": 25
    }
  ]
}
```

### POST `/workers/start-all`
Start all enabled workers.

### POST `/workers/stop-all`
Stop all workers.

### GET `/workers/{account_id}/validate`
Validate account configuration.

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

### GET `/workers/validate-all`
Validate all configurations.

---

## Aggregated Analytics

Cross-account aggregated analytics.

### GET `/aggregate`
Get aggregated performance across accounts.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `account_ids` | string | No | all | Comma-separated IDs (e.g., "1,2,3") |
| `days` | integer | No | 30 | Number of days (1-365) |

**Response:**
```json
{
  "total_accounts": 3,
  "total_trades": 150,
  "net_profit": 2500.50,
  "aggregate_win_rate": 65.5,
  "total_volume": 15.5
}
```

### GET `/comparison`
Side-by-side account comparison.

**Response:**
```json
{
  "accounts": [
    {
      "account_id": 1,
      "account_name": "Main Trading",
      "trades": 50,
      "net_profit": 1000.00,
      "win_rate": 70.0
    }
  ]
}
```

### GET `/overview`
High-level system summary.

### GET `/trades`
Get trades from multiple accounts with pagination.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `account_ids` | string | No | all | Comma-separated IDs |
| `limit` | integer | No | 100 | Max trades (1-1000) |
| `skip` | integer | No | 0 | Skip count for pagination |

---

## Error Codes

Common error responses and their meanings.

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Validation Error | Invalid request parameters or body |
| 401 | Unauthorized | Authentication required (not implemented) |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists or conflict with current state |
| 422 | Unprocessable Entity | Request syntax is correct but semantically invalid |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Service temporarily unavailable (e.g., MT5 connection down) |

**Example Error Response:**
```json
{
  "detail": "Account with ID 999 not found",
  "error_code": "ACCOUNT_NOT_FOUND",
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. This should be added for production use.

---

## Webhooks

Webhook support for external integrations (planned feature).

---

## SDK Examples

### Python
```python
import requests

API_BASE = "http://localhost:8000/api"

# Get analytics overview
response = requests.get(f"{API_BASE}/analytics/overview?days=30")
data = response.json()
print(f"Net Profit: ${data['net_profit']}")

# Open a position
position_data = {
    "account_id": 1,
    "symbol": "EURUSD",
    "order_type": "BUY",
    "volume": 0.1,
    "stop_loss": 1.0930,
    "take_profit": 1.0990
}
response = requests.post(f"{API_BASE}/positions/open", json=position_data)
print(f"Position opened: {response.json()}")
```

### JavaScript
```javascript
const API_BASE = 'http://localhost:8000/api';

// Get analytics overview
fetch(`${API_BASE}/analytics/overview?days=30`)
  .then(res => res.json())
  .then(data => console.log(`Net Profit: $${data.net_profit}`));

// Open a position
fetch(`${API_BASE}/positions/open`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    account_id: 1,
    symbol: 'EURUSD',
    order_type: 'BUY',
    volume: 0.1,
    stop_loss: 1.0930,
    take_profit: 1.0990
  })
})
  .then(res => res.json())
  .then(data => console.log('Position opened:', data));
```

---

## Changelog

### Version 2.0.0 (Current)
- Multi-account support
- Worker-based automated trading
- Enhanced analytics and reporting
- WebSocket real-time updates
- Improved configuration management

### Version 1.0.0
- Initial release
- Basic trading operations
- Performance analytics
- Single account support

---

## Support

For issues, questions, or contributions, please refer to the project repository.

**API Documentation:** http://localhost:8000/api/docs  
**Project Docs:** [docs/](../docs/)

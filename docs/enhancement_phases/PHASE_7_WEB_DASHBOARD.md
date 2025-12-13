# Phase 7: Web Dashboard & REST API

**Duration:** 3-4 weeks
**Difficulty:** Advanced
**Focus:** Real-time monitoring and remote control

---

## Overview

Build a complete web interface for monitoring and controlling your trading system:
- FastAPI REST API backend
- React TypeScript frontend
- WebSocket real-time updates
- JWT authentication
- Live charts and controls

---

## 7.1 REST API with FastAPI

### Tasks Checklist:

- [ ] **Core API Endpoints**
  - [ ] GET /api/status - System health
  - [ ] GET /api/positions - Open positions
  - [ ] GET /api/performance - Metrics
  - [ ] POST /api/trade - Manual trade
  - [ ] POST /api/close/{ticket} - Close position
  - [ ] GET /api/signals - Current signals
  - [ ] POST /api/strategy/enable - Control strategies

- [ ] **Authentication**
  - [ ] JWT token generation
  - [ ] Login endpoint
  - [ ] Protected routes
  - [ ] API key management

- [ ] **WebSocket**
  - [ ] Real-time position updates
  - [ ] Trade notifications
  - [ ] System metrics stream

### Files to Create:

```
src/api/
├── __init__.py
├── main.py                   # FastAPI app
├── routes/
│   ├── __init__.py
│   ├── trading.py            # Trading endpoints
│   ├── monitoring.py         # Monitoring endpoints
│   └── admin.py              # Admin endpoints
├── auth/
│   ├── __init__.py
│   ├── jwt_handler.py        # JWT authentication
│   └── middleware.py         # Auth middleware
├── websocket/
│   ├── __init__.py
│   └── connection_manager.py # WebSocket manager
└── schemas/
    ├── __init__.py
    ├── position.py           # Pydantic models
    ├── trade.py
    └── user.py
```

### Implementation Example:

```python
# src/api/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI(title="TradingMTQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "mt5_connected": orchestrator.connector.is_connected(),
        "active_strategies": len(orchestrator.traders),
        "open_positions": len(orchestrator.connector.get_positions())
    }

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            positions = orchestrator.connector.get_positions()
            await websocket.send_json({
                "type": "positions",
                "data": [
                    {
                        "ticket": p.ticket,
                        "symbol": p.symbol,
                        "profit": p.profit
                    } for p in positions
                ]
            })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
```

**For complete API implementation, see:** [../ENHANCEMENT_ROADMAP.md](../ENHANCEMENT_ROADMAP.md#71-rest-api-with-fastapi)

---

## 7.2 React Dashboard

### Tasks Checklist:

- [ ] **Dashboard Components**
  - [ ] PositionsTable - Live positions
  - [ ] EquityCurve - Real-time chart
  - [ ] PerformanceCards - Metrics display
  - [ ] SignalFeed - Live signals
  - [ ] TradeForm - Manual trading

- [ ] **Real-time Updates**
  - [ ] WebSocket integration
  - [ ] Auto-refresh data
  - [ ] Live notifications

### Project Structure:

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── PositionsTable.tsx
│   │   ├── EquityCurve.tsx
│   │   └── TradeForm.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   └── useApi.ts
│   ├── services/
│   │   └── api.ts
│   └── App.tsx
└── package.json
```

### Setup Instructions:

```bash
# Create React app
npx create-react-app frontend --template typescript
cd frontend

# Install dependencies
npm install recharts axios

# Start development server
npm start
```

### Example Component:

```typescript
// frontend/src/components/PositionsTable.tsx
import React from 'react';

interface Position {
  ticket: number;
  symbol: string;
  profit: number;
}

export const PositionsTable: React.FC<{positions: Position[]}> = ({positions}) => {
  return (
    <table>
      <thead>
        <tr>
          <th>Ticket</th>
          <th>Symbol</th>
          <th>P&L</th>
        </tr>
      </thead>
      <tbody>
        {positions.map(pos => (
          <tr key={pos.ticket}>
            <td>#{pos.ticket}</td>
            <td>{pos.symbol}</td>
            <td className={pos.profit >= 0 ? 'profit' : 'loss'}>
              ${pos.profit.toFixed(2)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

**For complete React implementation, see:** [../ENHANCEMENT_ROADMAP.md](../ENHANCEMENT_ROADMAP.md#72-react-dashboard)

---

## Installation Guide

### Backend:

```bash
# Install FastAPI dependencies
pip install fastapi uvicorn python-jose passlib python-multipart websockets

# Run API server
cd src/api
uvicorn main:app --reload --port 8000
```

### Frontend:

```bash
# Install Node.js dependencies
cd frontend
npm install

# Start development server
npm start
```

### Access:

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## Testing Checklist

- [ ] API endpoints return correct data
- [ ] WebSocket streams positions
- [ ] Authentication works
- [ ] Frontend connects to backend
- [ ] Real-time updates working
- [ ] Manual trades execute
- [ ] Charts display correctly

---

## Expected Outcomes

After Phase 7:

1. **Professional Web Interface**
   - Modern React dashboard
   - Real-time data updates
   - Mobile-responsive design

2. **Remote Control**
   - Execute trades from browser
   - Close positions remotely
   - Enable/disable strategies

3. **Better Monitoring**
   - Visual position tracking
   - Live performance charts
   - Instant notifications

---

**For full implementation details, refer to the main:** [Enhancement Roadmap](../ENHANCEMENT_ROADMAP.md)

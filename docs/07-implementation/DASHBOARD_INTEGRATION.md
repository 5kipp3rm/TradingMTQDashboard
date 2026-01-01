# TradingMTQ Dashboard Integration

## 🎯 Overview
The TradingMTQ dashboard is now integrated as a **React + TypeScript + Vite** application using the `lovely-dashboard-refactor` branch from the TradingMTQDashboard repository.

## 🏗️ Architecture

```
TradingMTQ/
├── src/api/                    # FastAPI Backend (Port 8000)
│   └── app.py                  # API server with CORS for dashboard
└── dashboard/                  # React Frontend (Port 8080)
    ├── src/
    │   ├── lib/api.ts         # API client for backend
    │   └── hooks/
    │       └── useDashboardData.ts  # Data fetching hook
    └── vite.config.ts         # Vite config with proxy
```

## 🔌 Connection Flow

1. **Development Mode:**
   - Frontend runs on `http://localhost:8080` (Vite dev server)
   - Backend runs on `http://localhost:8000` (FastAPI)
   - Vite proxies `/api/*` requests to backend
   - CORS configured for `localhost:8080`

2. **Production Mode:**
   - Frontend builds to `dashboard/dist`
   - FastAPI serves static files from `dashboard/dist`
   - All requests go to `http://localhost:8000`

## 🚀 Quick Start

### Option 1: One Command (Recommended)
```bash
./start-dev.sh
```

### Option 2: Manual Start
```bash
# Terminal 1: Start Backend
source .venv/bin/activate
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Dashboard
cd dashboard
npm run dev
```

## 📡 API Endpoints

The dashboard connects to these backend endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /api/analytics/overview` | Dashboard summary stats |
| `GET /api/analytics/daily?days=30` | Daily performance data |
| `GET /api/trades?limit=100` | Recent trades |
| `GET /api/positions` | Current open positions |
| `GET /api/accounts` | Account information |
| `GET /api/currencies` | Currency pairs config |
| `GET /api/config` | System configuration |
| `GET /api/alerts?limit=50` | Recent alerts |

## 🔧 Configuration

### Dashboard Environment Variables (`.env`)
```bash
VITE_API_URL=http://localhost:8000/api
```

### Backend CORS Settings
The backend is configured to allow requests from:
- `http://localhost:8080` - Vite dev server
- `http://localhost:8000` - Production mode
- `http://localhost:3000` - Alternative React dev server

## 📦 Build for Production

```bash
# Build dashboard
cd dashboard
npm run build

# The built files will be in dashboard/dist
# FastAPI will serve them automatically from http://localhost:8000/
```

## 🔄 Updating the Dashboard

The dashboard is a **git submodule** tracking the `lovely-dashboard-refactor` branch:

```bash
# Pull latest dashboard changes
cd dashboard
git pull origin lovely-dashboard-refactor
cd ..
git add dashboard
git commit -m "Update dashboard submodule"
git push

# Push dashboard changes
cd dashboard
# Make your changes
git add .
git commit -m "Update dashboard"
git push origin lovely-dashboard-refactor
cd ..
git add dashboard
git commit -m "Update dashboard submodule reference"
git push
```

## 🛠️ Development Features

### API Client
- Automatic error handling
- Type-safe API calls
- Fallback to mock data if backend unavailable
- Located in: `dashboard/src/lib/api.ts`

### Data Hook
- Fetches real data from backend
- Falls back to mock data on error
- Auto-refresh capability
- Located in: `dashboard/src/hooks/useDashboardData.ts`

### Proxy Configuration
- Vite proxies `/api/*` to backend
- Configured in: `dashboard/vite.config.ts`

## 🐛 Troubleshooting

### Dashboard not connecting to API
1. Check backend is running: `http://localhost:8000/api/docs`
2. Check CORS configuration in `src/api/app.py`
3. Verify proxy settings in `dashboard/vite.config.ts`
4. Check browser console for errors

### Build errors
```bash
cd dashboard
rm -rf node_modules package-lock.json
npm install
```

### Port conflicts
Change ports in:
- Backend: `start-dev.sh` or uvicorn command
- Frontend: `dashboard/vite.config.ts`

## 📝 Notes

- The dashboard uses **Shadcn UI** components
- Styled with **Tailwind CSS**
- Built with **React 18** and **TypeScript**
- Data fetching with **@tanstack/react-query**
- Charts with **Recharts**

# TradingMTQ Analytics Dashboard

Modern web-based analytics dashboard for TradingMTQ trading bot performance monitoring.

## Features

- **Real-time Performance Metrics**
  - Total trades executed
  - Net profit/loss tracking
  - Win rate percentage
  - Average daily profit

- **Interactive Charts**
  - Cumulative profit over time
  - Win rate trends
  - Powered by Chart.js

- **Trade Management**
  - Recent trades table with filtering
  - Daily performance breakdown
  - CSV export functionality

- **Responsive Design**
  - Dark theme optimized for trading
  - Mobile-friendly layout
  - Auto-refresh every 60 seconds

## Quick Start

### 1. Start the API Server

```bash
# From project root
tradingmtq serve
```

The API server will start on `http://localhost:8000`

### 2. Access the Dashboard

Open your browser to:
- **Dashboard**: http://localhost:8000/
- **API Docs**: http://localhost:8000/api/docs

## Dashboard Components

### Summary Cards
- **Total Trades**: Number of trades executed in the selected period
- **Net Profit**: Total profit/loss in USD
- **Win Rate**: Percentage of winning trades
- **Avg Daily Profit**: Average profit per trading day

### Charts
- **Cumulative Profit**: Line chart showing profit growth over time
- **Win Rate Trend**: Bar chart showing daily win rate percentages

### Tables
- **Recent Trades**: Last 50 trades with details (ticket, symbol, entry/exit, profit, pips)
- **Daily Performance**: Daily aggregated statistics (trades, winners, losers, profit, win rate)

## Period Selection

Use the period dropdown to view data for:
- Last 7 Days
- Last 30 Days (default)
- Last 90 Days
- Last Year

## Export Data

Click the **Export CSV** button on the Recent Trades table to download trades as a CSV file for analysis in Excel or other tools.

## Configuration

### API Endpoint

The dashboard connects to the API at `http://localhost:8000/api` by default.

To change the API endpoint, edit `dashboard/js/api.js`:

```javascript
const API_BASE_URL = 'http://your-server:8000/api';
```

### Auto-Refresh Interval

The dashboard auto-refreshes every 60 seconds. To change this, edit `dashboard/js/dashboard.js`:

```javascript
// Change 60000 (60 seconds) to your preferred interval in milliseconds
setInterval(() => this.loadDashboard(), 60000);
```

## Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Technical Stack

- **Frontend**: Vanilla JavaScript (ES6+)
- **Charts**: Chart.js 4.4.0
- **Styling**: Custom CSS with dark theme
- **API**: FastAPI REST endpoints

## Troubleshooting

### Dashboard shows "Disconnected"
- Ensure the API server is running (`tradingmtq serve`)
- Check that port 8000 is not blocked by firewall
- Verify the API_BASE_URL in `js/api.js` is correct

### No data displayed
- Ensure the trading bot has run and generated trade data
- Run `tradingmtq aggregate --backfill` to populate daily performance data
- Check browser console for errors (F12 → Console tab)

### Charts not displaying
- Verify Chart.js is loading (check browser console)
- Ensure there is data in the selected period
- Try refreshing the page

## Development

### File Structure
```
dashboard/
├── index.html          # Main dashboard page
├── css/
│   └── styles.css     # Dashboard styling
├── js/
│   ├── api.js         # API client
│   └── dashboard.js   # Dashboard controller
└── README.md          # This file
```

### Making Changes

1. Edit files in the `dashboard/` directory
2. Refresh browser to see changes (no build step required)
3. For API changes, restart the server

## API Endpoints Used

- `GET /api/health` - Health check
- `GET /api/status` - System status
- `GET /api/analytics/summary` - Summary metrics
- `GET /api/analytics/metrics` - Time series data
- `GET /api/analytics/daily` - Daily performance records
- `GET /api/trades/` - Recent trades list

See full API documentation at http://localhost:8000/api/docs

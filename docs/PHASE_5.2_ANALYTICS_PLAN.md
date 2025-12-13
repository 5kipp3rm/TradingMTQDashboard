# Phase 5.2: Advanced Analytics & Dashboard - Implementation Plan

**Start Date:** TBD (After Production Deployment Stable)
**Duration:** 1-2 weeks
**Effort:** 40-60 hours
**Prerequisites:** Phase 5.1 Complete ✅

---

## 📊 Overview

Phase 5.2 builds on the database layer from Phase 5.1 to provide comprehensive analytics, visualization, and reporting capabilities for data-driven trading decisions.

### Goals

1. **Daily Performance Aggregation** - Automated calculation of daily statistics
2. **Web Dashboard** - Real-time visualization and monitoring
3. **Reporting System** - Automated reports and notifications
4. **Data Export** - CSV/Excel export functionality

### Business Value

- **Data-Driven Decisions**: Make informed trading adjustments
- **Performance Tracking**: Monitor progress toward goals
- **Pattern Recognition**: Identify successful strategies
- **Accountability**: Track and audit all trading activity

---

## 🎯 Phase 5.2 Deliverables

| Component | Status | LOC Est. | Priority |
|-----------|--------|----------|----------|
| Daily Performance Aggregation | 📋 Planned | 300 | HIGH |
| Background Job System | 📋 Planned | 200 | HIGH |
| REST API Backend | 📋 Planned | 500 | HIGH |
| Web Dashboard Frontend | 📋 Planned | 800 | HIGH |
| Reporting Engine | 📋 Planned | 400 | MEDIUM |
| Export Functionality | 📋 Planned | 200 | MEDIUM |
| Email Notifications | 📋 Planned | 150 | LOW |
| **Total Estimated** | 📋 | **~2,550** | |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│  Dashboard │ Charts │ Reports │ Settings                │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/WebSocket
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  REST API (FastAPI)                     │
│  • /api/trades     • /api/performance                   │
│  • /api/signals    • /api/charts                        │
│  • /api/accounts   • /api/reports                       │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│              Repository Layer (Phase 5.1) ✅            │
│  TradeRepository │ SignalRepository │ ...               │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│                Database (PostgreSQL)                    │
│  trades │ signals │ account_snapshots │ daily_perf      │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Task Breakdown

### Task 1: Daily Performance Aggregation (HIGH Priority)

**Duration:** 2-3 days
**File:** `src/analytics/daily_aggregator.py`

#### Features

1. **Automated Calculation**
   - Total trades per day
   - Win/loss counts
   - Gross profit/loss
   - Net profit
   - Win rate
   - Profit factor
   - Average trade duration
   - Best/worst trades

2. **Data Population**
   - Read from trades table
   - Calculate daily metrics
   - Populate `daily_performance` table
   - Handle timezone conversions

3. **Scheduling**
   - Run at end of trading day
   - Backfill historical data
   - Handle missing days

#### Implementation

```python
# src/analytics/daily_aggregator.py
from datetime import date, timedelta
from decimal import Decimal
from src.database.repository import TradeRepository, DailyPerformanceRepository
from src.database.connection import get_session
from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

class DailyAggregator:
    """Calculate and store daily performance metrics"""

    def __init__(self):
        self.trade_repo = TradeRepository()
        self.perf_repo = DailyPerformanceRepository()

    def aggregate_day(self, target_date: date):
        """Calculate metrics for specific day"""
        with get_session() as session:
            # Get all closed trades for the day
            trades = self.trade_repo.get_trades_by_date(
                session,
                target_date=target_date,
                status="CLOSED"
            )

            if not trades:
                logger.info("No trades for date", date=target_date)
                return None

            # Calculate metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.profit > 0)
            losing_trades = sum(1 for t in trades if t.profit < 0)

            gross_profit = sum(t.profit for t in trades if t.profit > 0)
            gross_loss = abs(sum(t.profit for t in trades if t.profit < 0))
            net_profit = sum(t.profit for t in trades)

            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

            # Save to database
            performance = self.perf_repo.create_or_update(
                session,
                target_date=target_date,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                gross_profit=gross_profit,
                gross_loss=gross_loss,
                net_profit=net_profit,
                win_rate=win_rate,
                profit_factor=profit_factor
            )

            logger.info(
                "Daily aggregation complete",
                date=target_date,
                trades=total_trades,
                profit=float(net_profit)
            )

            return performance

    def aggregate_range(self, start_date: date, end_date: date):
        """Aggregate multiple days"""
        current = start_date
        while current <= end_date:
            self.aggregate_day(current)
            current += timedelta(days=1)

    def backfill_all(self):
        """Backfill all historical data"""
        with get_session() as session:
            # Get date of first trade
            first_trade = self.trade_repo.get_first_trade(session)
            if not first_trade:
                logger.warning("No trades found for backfill")
                return

            start_date = first_trade.entry_time.date()
            end_date = date.today()

            logger.info(
                "Starting backfill",
                start=start_date,
                end=end_date
            )

            self.aggregate_range(start_date, end_date)
```

#### CLI Command

```python
# Add to src/cli/app.py
@cli.command()
@click.option('--backfill', is_flag=True, help='Backfill all historical data')
@click.option('--date', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Aggregate specific date')
def aggregate(backfill, date):
    """Run daily performance aggregation"""
    from src.analytics.daily_aggregator import DailyAggregator

    aggregator = DailyAggregator()

    if backfill:
        click.echo("Backfilling all historical data...")
        aggregator.backfill_all()
        click.echo("Backfill complete!")

    elif date:
        click.echo(f"Aggregating date: {date.date()}")
        aggregator.aggregate_day(date.date())
        click.echo("Aggregation complete!")

    else:
        # Aggregate yesterday (after trading day ends)
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)
        click.echo(f"Aggregating yesterday: {yesterday}")
        aggregator.aggregate_day(yesterday)
        click.echo("Aggregation complete!")
```

**Usage:**
```bash
# Aggregate yesterday
tradingmtq aggregate

# Aggregate specific date
tradingmtq aggregate --date 2025-12-13

# Backfill all historical data
tradingmtq aggregate --backfill
```

---

### Task 2: Background Job System (HIGH Priority)

**Duration:** 1-2 days
**Technology:** APScheduler or Celery

#### Option A: APScheduler (Simpler)

```python
# src/analytics/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.analytics.daily_aggregator import DailyAggregator
from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

class AnalyticsScheduler:
    """Schedule automated analytics tasks"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.aggregator = DailyAggregator()

    def start(self):
        """Start scheduler with configured jobs"""

        # Daily aggregation at 11:59 PM
        self.scheduler.add_job(
            self.run_daily_aggregation,
            trigger=CronTrigger(hour=23, minute=59),
            id='daily_aggregation',
            name='Daily Performance Aggregation',
            replace_existing=True
        )

        # Weekly report on Sundays at 6 PM
        self.scheduler.add_job(
            self.run_weekly_report,
            trigger=CronTrigger(day_of_week='sun', hour=18),
            id='weekly_report',
            name='Weekly Performance Report',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Analytics scheduler started")

    def run_daily_aggregation(self):
        """Run daily aggregation job"""
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)

        logger.info("Running scheduled daily aggregation", date=yesterday)
        try:
            self.aggregator.aggregate_day(yesterday)
            logger.info("Daily aggregation completed successfully")
        except Exception as e:
            logger.error("Daily aggregation failed", error=str(e))

    def run_weekly_report(self):
        """Generate weekly report"""
        logger.info("Running scheduled weekly report")
        # TODO: Implement weekly report generation

    def stop(self):
        """Stop scheduler"""
        self.scheduler.shutdown()
        logger.info("Analytics scheduler stopped")
```

#### Integration with Trading System

```python
# In src/trading/orchestrator.py or main.py
from src.analytics.scheduler import AnalyticsScheduler

# Start scheduler when trading starts
scheduler = AnalyticsScheduler()
scheduler.start()

# Stop when trading stops
scheduler.stop()
```

---

### Task 3: REST API Backend (HIGH Priority)

**Duration:** 3-4 days
**Framework:** FastAPI
**File:** `src/api/main.py`

#### API Endpoints

```python
# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from src.database.connection import get_session
from src.database.repository import (
    TradeRepository, SignalRepository,
    AccountSnapshotRepository, DailyPerformanceRepository
)
from src.api.schemas import (
    TradeResponse, SignalResponse, AccountSnapshotResponse,
    DailyPerformanceResponse, PerformanceStatsResponse
)

app = FastAPI(
    title="TradingMTQ Analytics API",
    description="REST API for trading analytics and monitoring",
    version="2.0.0"
)

# CORS middleware for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Repositories
trade_repo = TradeRepository()
signal_repo = SignalRepository()
snap_repo = AccountSnapshotRepository()
perf_repo = DailyPerformanceRepository()


@app.get("/api/trades", response_model=List[TradeResponse])
def get_trades(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, le=1000),
    session: Session = Depends(get_session)
):
    """Get trades with optional filtering"""
    trades = trade_repo.get_trades(
        session,
        symbol=symbol,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return trades


@app.get("/api/trades/{ticket}", response_model=TradeResponse)
def get_trade(ticket: int, session: Session = Depends(get_session)):
    """Get specific trade by ticket"""
    trade = trade_repo.get_by_ticket(session, ticket)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@app.get("/api/trades/statistics", response_model=PerformanceStatsResponse)
def get_trade_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    symbol: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get aggregated trade statistics"""
    stats = trade_repo.get_trade_statistics(
        session,
        start_date=start_date,
        end_date=end_date,
        symbol=symbol
    )
    return stats


@app.get("/api/signals", response_model=List[SignalResponse])
def get_signals(
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    executed: Optional[bool] = None,
    limit: int = Query(100, le=1000),
    session: Session = Depends(get_session)
):
    """Get signals with optional filtering"""
    signals = signal_repo.get_signals(
        session,
        symbol=symbol,
        signal_type=signal_type,
        executed=executed,
        limit=limit
    )
    return signals


@app.get("/api/account/latest", response_model=AccountSnapshotResponse)
def get_latest_snapshot(
    account_number: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Get latest account snapshot"""
    snapshot = snap_repo.get_latest_snapshot(session, account_number)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshots found")
    return snapshot


@app.get("/api/account/history", response_model=List[AccountSnapshotResponse])
def get_account_history(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    account_number: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Get account snapshot history"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=7)
    if not end_date:
        end_date = datetime.now()

    snapshots = snap_repo.get_snapshots_by_date_range(
        session,
        account_number=account_number,
        start_date=start_date,
        end_date=end_date
    )
    return snapshots


@app.get("/api/performance/daily", response_model=List[DailyPerformanceResponse])
def get_daily_performance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """Get daily performance data"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    performance = perf_repo.get_performance_range(
        session,
        start_date=start_date,
        end_date=end_date
    )
    return performance


@app.get("/api/performance/summary")
def get_performance_summary(session: Session = Depends(get_session)):
    """Get overall performance summary"""
    summary = perf_repo.get_performance_summary(session)
    return summary


@app.get("/api/health")
def health_check():
    """API health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

#### Pydantic Schemas

```python
# src/api/schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional

class TradeResponse(BaseModel):
    id: int
    ticket: Optional[int]
    symbol: str
    trade_type: str
    status: str
    entry_price: Decimal
    entry_time: datetime
    exit_price: Optional[Decimal]
    exit_time: Optional[datetime]
    profit: Optional[Decimal]
    volume: Decimal

    class Config:
        from_attributes = True

class SignalResponse(BaseModel):
    id: int
    symbol: str
    signal_type: str
    timestamp: datetime
    price: Decimal
    confidence: float
    strategy_name: str
    executed: bool

    class Config:
        from_attributes = True

class AccountSnapshotResponse(BaseModel):
    id: int
    account_number: int
    balance: Decimal
    equity: Decimal
    profit: Decimal
    margin: Decimal
    margin_free: Decimal
    open_positions: int
    snapshot_time: datetime

    class Config:
        from_attributes = True

class DailyPerformanceResponse(BaseModel):
    id: int
    date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    gross_profit: Decimal
    gross_loss: Decimal
    net_profit: Decimal
    win_rate: Optional[Decimal]
    profit_factor: Optional[Decimal]

    class Config:
        from_attributes = True

class PerformanceStatsResponse(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
```

#### Running the API

```bash
# Install FastAPI
pip install fastapi uvicorn[standard]

# Run development server
uvicorn src.api.main:app --reload --port 8000

# Access API docs
# http://localhost:8000/docs
```

---

### Task 4: Web Dashboard Frontend (HIGH Priority)

**Duration:** 4-5 days
**Framework:** React + TypeScript (or Vue.js)
**File:** `frontend/` directory

#### Dashboard Features

1. **Overview Page**
   - Current balance/equity
   - Today's P&L
   - Open positions count
   - Win rate chart
   - Recent trades table

2. **Performance Page**
   - Daily performance chart (30/60/90 days)
   - Monthly comparison
   - Strategy performance breakdown
   - Best/worst performing pairs

3. **Trades Page**
   - Filterable trade history
   - Trade details modal
   - Export to CSV
   - Search by ticket/symbol

4. **Signals Page**
   - Recent signals
   - Signal vs execution comparison
   - Signal quality metrics
   - Strategy breakdown

5. **Analytics Page**
   - Advanced charts
   - Custom date ranges
   - Correlation analysis
   - Drawdown analysis

#### Technology Stack

```json
{
  "frontend": {
    "framework": "React 18 + TypeScript",
    "ui": "Material-UI or Tailwind CSS",
    "charts": "Chart.js or Recharts",
    "http": "Axios",
    "state": "React Query + Context API"
  },
  "backend": {
    "api": "FastAPI (already defined)",
    "websocket": "FastAPI WebSocket (for real-time updates)"
  }
}
```

#### Quick Start Template

```bash
# Create React app with TypeScript
npx create-react-app frontend --template typescript

# Install dependencies
cd frontend
npm install @mui/material @emotion/react @emotion/styled
npm install chart.js react-chartjs-2
npm install axios react-query
npm install react-router-dom
```

**Note:** Full frontend implementation is a significant task. I can provide detailed React components if needed, or we can use a simpler approach first (e.g., Streamlit dashboard).

---

### Task 5: Reporting Engine (MEDIUM Priority)

**Duration:** 2-3 days
**File:** `src/analytics/reports.py`

#### Features

1. **Daily Report**
   - Summary of day's trading
   - Win/loss breakdown
   - Top performers
   - Issues/anomalies

2. **Weekly Report**
   - Week overview
   - Performance trends
   - Strategy analysis
   - Recommendations

3. **Monthly Report**
   - Comprehensive analysis
   - Month-over-month comparison
   - Detailed statistics
   - Charts and visualizations

#### Implementation (PDF Generation)

```python
# src/analytics/reports.py
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from datetime import date, timedelta
from src.database.repository import TradeRepository, DailyPerformanceRepository
from src.database.connection import get_session

class ReportGenerator:
    """Generate PDF reports"""

    def __init__(self):
        self.trade_repo = TradeRepository()
        self.perf_repo = DailyPerformanceRepository()

    def generate_daily_report(self, target_date: date, output_path: str):
        """Generate daily performance report"""
        with get_session() as session:
            # Get data
            stats = self.trade_repo.get_trade_statistics(
                session,
                start_date=target_date,
                end_date=target_date
            )

            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title = Paragraph(
                f"Trading Performance Report - {target_date}",
                styles['Title']
            )
            story.append(title)
            story.append(Spacer(1, 12))

            # Statistics table
            data = [
                ['Metric', 'Value'],
                ['Total Trades', str(stats['total_trades'])],
                ['Winning Trades', str(stats['winning_trades'])],
                ['Losing Trades', str(stats['losing_trades'])],
                ['Win Rate', f"{stats['win_rate']:.2f}%"],
                ['Net Profit', f"${stats['total_profit']:.2f}"],
                ['Profit Factor', f"{stats['profit_factor']:.2f}"],
            ]

            table = Table(data)
            story.append(table)

            # Build PDF
            doc.build(story)
```

---

### Task 6: Export Functionality (MEDIUM Priority)

**Duration:** 1 day
**File:** `src/analytics/export.py`

#### CSV Export

```python
# src/analytics/export.py
import csv
from datetime import date
from src.database.repository import TradeRepository
from src.database.connection import get_session

class DataExporter:
    """Export data to various formats"""

    def __init__(self):
        self.trade_repo = TradeRepository()

    def export_trades_csv(
        self,
        output_path: str,
        start_date: date = None,
        end_date: date = None
    ):
        """Export trades to CSV"""
        with get_session() as session:
            trades = self.trade_repo.get_trades(
                session,
                start_date=start_date,
                end_date=end_date
            )

            with open(output_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'ticket', 'symbol', 'type', 'status',
                    'entry_price', 'entry_time', 'exit_price',
                    'exit_time', 'profit', 'volume'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for trade in trades:
                    writer.writerow({
                        'ticket': trade.ticket,
                        'symbol': trade.symbol,
                        'type': trade.trade_type,
                        'status': trade.status,
                        'entry_price': float(trade.entry_price),
                        'entry_time': trade.entry_time.isoformat(),
                        'exit_price': float(trade.exit_price) if trade.exit_price else '',
                        'exit_time': trade.exit_time.isoformat() if trade.exit_time else '',
                        'profit': float(trade.profit) if trade.profit else '',
                        'volume': float(trade.volume),
                    })
```

---

### Task 7: Email Notifications (LOW Priority)

**Duration:** 1 day
**File:** `src/notifications/email.py`

#### Implementation

```python
# src/notifications/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

class EmailNotifier:
    """Send email notifications"""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_daily_report(self, to_email: str, report_path: str, date: str):
        """Send daily report via email"""
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = f'Trading Performance Report - {date}'

        body = f"""
        Daily trading performance report attached.

        Date: {date}

        Best regards,
        TradingMTQ
        """

        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        with open(report_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='pdf')
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=f'report_{date}.pdf'
            )
            msg.attach(attachment)

        # Send email
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
```

---

## 📦 Dependencies

Add to `requirements.txt`:

```
# API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0

# Scheduling
apscheduler>=3.10.4

# Reports
reportlab>=4.0.7
matplotlib>=3.8.2

# Export
openpyxl>=3.1.2

# Notifications
python-dotenv>=1.0.0
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_analytics.py
def test_daily_aggregation():
    """Test daily aggregation logic"""
    pass

def test_api_endpoints():
    """Test REST API endpoints"""
    pass

def test_report_generation():
    """Test PDF report generation"""
    pass
```

### Integration Tests

- API with database
- Frontend with API
- End-to-end workflows

---

## 🚀 Deployment

### Development

```bash
# Terminal 1: Run API
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Run Frontend
cd frontend && npm start

# Terminal 3: Run Trading System
tradingmtq trade
```

### Production

```bash
# API (with Gunicorn)
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend (build and serve)
cd frontend && npm run build
# Serve with nginx or similar

# Trading System (as service)
# Use Windows Service or Task Scheduler
```

---

## 📊 Success Metrics

- [ ] Daily aggregation runs automatically
- [ ] API responds in <100ms
- [ ] Dashboard loads in <2s
- [ ] Reports generated successfully
- [ ] Data exports work correctly
- [ ] Real-time updates working

---

## 🎯 Next Steps After 5.2

1. **Phase 6: Advanced ML** - Model training from historical data
2. **Phase 7: Mobile App** - iOS/Android monitoring
3. **Phase 8: Multi-Account** - Manage multiple trading accounts
4. **Phase 9: Backtesting Integration** - Use historical data for optimization

---

**Status:** 📋 Planned (Awaits Production Stable)
**Prerequisites:** Phase 5.1 Complete ✅
**Estimated Start:** After 24-48 hours production stability

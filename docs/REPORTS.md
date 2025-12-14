# Performance Reports System

## Overview

The TradingMTQ Performance Reports System provides automated PDF report generation, email delivery, and scheduled reporting capabilities for trading performance analytics.

## Features

- 📄 **PDF Report Generation** - Professional PDF reports with ReportLab
- 📧 **Email Delivery** - Automated email sending with attachments
- ⏰ **Scheduled Reports** - Daily, weekly, monthly, and custom schedules
- 🔄 **Ad-Hoc Generation** - Generate reports on-demand via API
- 📊 **Performance Tracking** - Track report generation history and success rates
- 🎯 **Multi-Account Support** - Generate reports for specific accounts or all accounts
- 🌐 **Web UI** - User-friendly dashboard for report management

## Architecture

### Components

```
src/reports/
├── generator.py        # PDF report generation with ReportLab
├── email_service.py    # Email delivery with SMTP
├── scheduler.py        # Background scheduling with APScheduler
└── __init__.py         # Package exports

src/database/report_models.py  # Database models

src/api/routes/reports.py      # REST API endpoints

dashboard/
├── reports.html        # Web UI for report management
├── css/reports.css     # Report page styles
└── js/reports.js       # Report management JavaScript
```

### Database Models

#### ReportConfiguration
Stores scheduled report configurations:
- Basic info: name, description
- Schedule: frequency (daily/weekly/monthly), day of week/month, time of day
- Content: report format, days lookback, include trades/charts
- Email: recipients, CC, subject, body
- Status: is_active, last_run, next_run, run_count, last_error

#### ReportHistory
Tracks report generation attempts:
- Metadata: config_id, generated_at, report dates
- Status: success, error_message
- Delivery: file_path, file_size, email_sent, email_recipients
- Performance: execution_time_ms

## Installation

### Prerequisites

```bash
pip install reportlab>=4.0.7 pillow>=10.1.0 apscheduler>=3.10.0
```

### Database Migration

The report models will be created automatically when you run:

```bash
tradingmtq aggregate --initialize
```

Or manually create tables:

```python
from src.database import init_db
init_db()
```

## Usage

### 1. Quick Ad-Hoc Reports (API)

Generate a report immediately via REST API:

```bash
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "account_id": 1,
    "include_trades": true,
    "include_charts": false
  }'
```

Response:
```json
{
  "success": true,
  "report_path": "/path/to/report.pdf",
  "file_size": 245678,
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

### 2. Scheduled Reports (API)

#### Create a Daily Report

```bash
curl -X POST http://localhost:8000/api/reports/configurations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Performance Summary",
    "description": "Automated daily report sent at 9 AM",
    "frequency": "daily",
    "time_of_day": "09:00",
    "report_format": "pdf",
    "include_trades": true,
    "include_charts": true,
    "days_lookback": 30,
    "recipients": ["manager@company.com", "trader@company.com"],
    "email_subject": "Daily Trading Performance Report",
    "is_active": true
  }'
```

#### Create a Weekly Report

```bash
curl -X POST http://localhost:8000/api/reports/configurations \
  -H "Content-Type": application/json" \
  -d '{
    "name": "Weekly Performance Review",
    "frequency": "weekly",
    "day_of_week": 1,
    "time_of_day": "10:00",
    "report_format": "pdf",
    "include_trades": true,
    "include_charts": true,
    "days_lookback": 7,
    "account_id": 1,
    "recipients": ["team@company.com"],
    "cc_recipients": ["management@company.com"],
    "is_active": true
  }'
```

Day of week: 0=Monday, 1=Tuesday, ..., 6=Sunday

#### Create a Monthly Report

```bash
curl -X POST http://localhost:8000/api/reports/configurations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Performance Report",
    "frequency": "monthly",
    "day_of_month": 1,
    "time_of_day": "08:00",
    "report_format": "pdf",
    "include_trades": true,
    "include_charts": true,
    "days_lookback": 30,
    "recipients": ["cfo@company.com"],
    "is_active": true
  }'
```

Day of month: 1-31

### 3. Using the Web UI

Navigate to `http://localhost:8000/reports.html` to access the report management dashboard.

#### Quick Generate
1. Select date range
2. Choose account (or "All Accounts")
3. Select options (include trades/charts)
4. Click "Generate Report Now"

#### Create Scheduled Report
1. Click "New Report" button
2. Fill in:
   - **Basic Info**: Name, description
   - **Schedule**: Frequency, day, time
   - **Content**: Account, days lookback, format, options
   - **Email**: Recipients, CC, subject, body
3. Toggle "Active" to enable automatic generation
4. Click "Save Report"

#### Manage Reports
- **Edit**: Modify existing report configurations
- **Run Now**: Manually trigger report generation
- **Pause/Activate**: Toggle automatic generation
- **Delete**: Remove report configuration

#### View History
- See all report generation attempts
- Filter by success/failure
- View error messages
- Check email delivery status

### 4. Programmatic Usage (Python)

#### Generate Report Programmatically

```python
from src.reports.generator import ReportGenerator
from datetime import date, timedelta

# Create generator
generator = ReportGenerator(output_dir="./reports")

# Generate report
end_date = date.today()
start_date = end_date - timedelta(days=30)

report_path = generator.generate_performance_report(
    start_date=start_date,
    end_date=end_date,
    account_id=1,  # Or None for all accounts
    include_trades=True,
    include_charts=True
)

print(f"Report generated: {report_path}")
```

#### Send Report via Email

```python
from src.reports.email_service import EmailService, EmailConfiguration

# Configure email
email_config = EmailConfiguration(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your_email@gmail.com",
    smtp_password="your_app_password",
    from_email="your_email@gmail.com",
    from_name="TradingMTQ Reports",
    use_tls=True
)

# Create service
email_service = EmailService(email_config)

# Send report
success = email_service.send_report(
    to_emails=["recipient@example.com"],
    subject="Trading Performance Report",
    report_path=report_path,
    body_html="<p>Please find attached your performance report.</p>",
    cc_emails=["manager@example.com"]
)

print(f"Email sent: {success}")
```

#### Use Scheduler Programmatically

```python
from src.reports.scheduler import ReportScheduler
from src.reports.generator import ReportGenerator
from src.reports.email_service import EmailService, EmailConfiguration

# Setup components
generator = ReportGenerator()
email_config = EmailConfiguration(...)
email_service = EmailService(email_config)

# Create scheduler
scheduler = ReportScheduler(
    report_generator=generator,
    email_service=email_service
)

# Start scheduler (loads active configurations)
scheduler.start()

# Schedule specific report
scheduler.schedule_report(config_id=1)

# Manually trigger report
scheduler.trigger_report_now(config_id=1)

# Get job status
status = scheduler.get_job_status(config_id=1)
print(f"Next run: {status['next_run_time']}")

# Stop scheduler
scheduler.stop()
```

## API Reference

### Endpoints

#### List Report Configurations
```
GET /api/reports/configurations?active_only={bool}
```

#### Get Report Configuration
```
GET /api/reports/configurations/{config_id}
```

#### Create Report Configuration
```
POST /api/reports/configurations
Content-Type: application/json

{
  "name": "string",
  "description": "string (optional)",
  "frequency": "daily|weekly|monthly|custom",
  "day_of_week": "int (0-6, for weekly)",
  "day_of_month": "int (1-31, for monthly)",
  "time_of_day": "string (HH:MM)",
  "report_format": "pdf|csv|excel",
  "include_trades": "bool",
  "include_charts": "bool",
  "days_lookback": "int (1-365)",
  "account_id": "int (optional)",
  "recipients": ["email1@example.com"],
  "cc_recipients": ["email2@example.com"] (optional),
  "email_subject": "string (optional)",
  "email_body": "string (optional)",
  "is_active": "bool"
}
```

#### Update Report Configuration
```
PUT /api/reports/configurations/{config_id}
Content-Type: application/json

{
  // Partial update - include only fields to change
}
```

#### Delete Report Configuration
```
DELETE /api/reports/configurations/{config_id}
```

#### Activate Report
```
POST /api/reports/configurations/{config_id}/activate
```

#### Deactivate Report
```
POST /api/reports/configurations/{config_id}/deactivate
```

#### Generate Ad-Hoc Report
```
POST /api/reports/generate
Content-Type: application/json

{
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "account_id": "int (optional)",
  "include_trades": "bool",
  "include_charts": "bool",
  "email_recipients": ["email@example.com"] (optional)
}
```

#### Get Report History
```
GET /api/reports/history?config_id={int}&success_only={bool}&limit={int}
```

#### Get Report History Detail
```
GET /api/reports/history/{history_id}
```

## Email Configuration

### Gmail Setup

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account → Security
   - Select "2-Step Verification"
   - At bottom, select "App passwords"
   - Generate password for "Mail"
3. Use the generated password in email configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=TradingMTQ Reports
SMTP_USE_TLS=true
```

Load in your application:

```python
from dotenv import load_dotenv
import os

load_dotenv()

email_config = EmailConfiguration(
    smtp_host=os.getenv('SMTP_HOST'),
    smtp_port=int(os.getenv('SMTP_PORT')),
    smtp_user=os.getenv('SMTP_USER'),
    smtp_password=os.getenv('SMTP_PASSWORD'),
    from_email=os.getenv('SMTP_FROM_EMAIL'),
    from_name=os.getenv('SMTP_FROM_NAME'),
    use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
)
```

## Report Contents

### Report Sections

1. **Title Page**
   - Report title and date range
   - Account information
   - Generation timestamp

2. **Executive Summary**
   - Key performance metrics table
   - Net profit/loss
   - Win rate
   - Total trades
   - Average profit per trade

3. **Detailed Performance Metrics**
   - Winning trades analysis
   - Losing trades analysis
   - Profit factor
   - Average win/loss
   - Largest win/loss
   - Consecutive wins/losses

4. **Trade List** (optional)
   - Recent trades table
   - Symbol, entry/exit, profit/loss
   - Limited to most recent 50 trades

5. **Charts** (optional)
   - Equity curve
   - Drawdown chart
   - Win/loss distribution

## Troubleshooting

### Reports Not Generating

**Check scheduler status:**
```python
from src.reports.scheduler import ReportScheduler

scheduler = ReportScheduler()
scheduler.start()

jobs = scheduler.get_scheduled_jobs()
print(f"Scheduled jobs: {len(jobs)}")
for job in jobs:
    print(f"  {job['name']}: next run at {job['next_run_time']}")
```

**Check configuration:**
```bash
curl http://localhost:8000/api/reports/configurations
```

**Check history for errors:**
```bash
curl http://localhost:8000/api/reports/history?success_only=false
```

### Email Not Sending

**Test connection:**
```python
from src.reports.email_service import EmailService, EmailConfiguration

config = EmailConfiguration(...)
service = EmailService(config)

success = service.test_connection()
print(f"Connection test: {'success' if success else 'failed'}")
```

**Common issues:**
- Invalid SMTP credentials
- Firewall blocking port 587/465
- Gmail app password not generated
- TLS/SSL misconfiguration

### PDF Generation Errors

**Check dependencies:**
```bash
pip install reportlab pillow
```

**Verify data exists:**
```python
from src.database import get_session
from src.database import DailyPerformance
from datetime import date, timedelta

with get_session() as session:
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    count = session.query(DailyPerformance).filter(
        DailyPerformance.date >= start_date,
        DailyPerformance.date <= end_date
    ).count()

    print(f"Performance records: {count}")
```

## Testing

### Run Unit Tests

```bash
# Test report generator
pytest tests/test_report_generator.py -v

# Test email service
pytest tests/test_email_service.py -v

# Test scheduler
pytest tests/test_report_scheduler.py -v

# Test API endpoints
pytest tests/test_reports_api.py -v

# Test integration
pytest tests/test_reports_integration.py -v

# Run all report tests
pytest tests/test_report*.py -v
```

### Manual Testing

```python
# Quick test: Generate a report
from src.reports.generator import ReportGenerator
from datetime import date, timedelta

generator = ReportGenerator()
report_path = generator.generate_performance_report(
    start_date=date.today() - timedelta(days=7),
    end_date=date.today(),
    include_trades=True,
    include_charts=False
)

print(f"Test report: {report_path}")
```

## Performance Considerations

### Report Generation Time
- Small reports (7 days, no trades): ~0.5-1 second
- Medium reports (30 days, with trades): ~1-2 seconds
- Large reports (365 days, with trades and charts): ~3-5 seconds

### Email Delivery Time
- Single recipient: ~1-2 seconds
- Multiple recipients: ~1-3 seconds
- With large attachments (>5MB): ~3-10 seconds

### Scheduler Performance
- Minimal overhead when idle
- Each scheduled job check: <10ms
- Can handle 100+ scheduled reports efficiently

### Database Considerations
- Report history grows over time
- Consider archiving old history records (>90 days)
- Index on `config_id` and `generated_at` for faster queries

## Security Considerations

1. **Email Credentials**: Store SMTP credentials securely (environment variables, secrets manager)
2. **File Permissions**: Ensure report directory has appropriate permissions
3. **Input Validation**: All API inputs are validated via Pydantic
4. **SQL Injection**: Protected by SQLAlchemy parameterized queries
5. **Path Traversal**: Report paths are sanitized and validated

## Future Enhancements

Potential improvements:
- [ ] Support for Excel and CSV report formats
- [ ] Custom report templates
- [ ] Report compression for email (ZIP)
- [ ] Cloud storage integration (S3, GCS)
- [ ] Webhook notifications on report generation
- [ ] Report retention policies (auto-delete old reports)
- [ ] Report comparison (compare two periods)
- [ ] Multi-language support
- [ ] Advanced charting with Plotly
- [ ] Report scheduling calendar view

## Support

For issues or questions:
1. Check logs: `logs/tradingmtq.log`
2. Review history: `GET /api/reports/history`
3. Test components individually (generator, email, scheduler)
4. Check database models are migrated correctly

## License

This component is part of TradingMTQ and follows the same license terms.

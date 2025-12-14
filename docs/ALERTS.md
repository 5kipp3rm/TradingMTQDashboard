# Alert & Notification System

TradingMTQ includes a comprehensive alert and notification system that sends real-time updates about trading activity via multiple channels.

## Features

✅ **Multi-Channel Notifications**
- Email notifications (SMTP)
- Real-time WebSocket updates
- SMS support (coming soon)

✅ **Configurable Alert Types**
- Trade opened notifications
- Trade closed notifications
- Daily performance summaries
- Error/system alerts
- Profit/loss threshold alerts

✅ **Advanced Filtering**
- Symbol-based filtering (e.g., only EURUSD trades)
- Profit/loss thresholds
- Customizable recipients per alert type

✅ **Delivery Tracking**
- Complete history of sent notifications
- Success/failure tracking
- Error logging for troubleshooting

## Quick Start

### 1. Configure Email Settings

Create `config/email.yaml` from the example:

```bash
cp config/email.example.yaml config/email.yaml
```

Edit `config/email.yaml` with your SMTP settings:

```yaml
email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  username: "your-email@gmail.com"
  password: "your-app-password"
  from_email: "your-email@gmail.com"
  from_name: "TradingMTQ Bot"
  use_tls: true
  use_ssl: false
```

**Gmail Users**: Enable 2FA and generate an App Password at https://myaccount.google.com/apppasswords

### 2. Configure Alerts

Access the Alert Settings page in the dashboard:

```
http://localhost:8000/alerts.html
```

Or click the "🔔 Alerts" button in the dashboard header.

### 3. Enable Alert Types

For each alert type, configure:

1. **Enable/Disable** - Toggle the alert on/off
2. **Channels** - Choose Email, WebSocket, or both
3. **Recipients** - Add comma-separated email addresses
4. **Filters** (optional):
   - **Symbol Filter**: Only alert for specific pairs (e.g., "EURUSD, GBPUSD")
   - **Profit Threshold**: Minimum profit to trigger alert
   - **Loss Threshold**: Maximum loss to trigger alert

### 4. Test Email Configuration

Use the "Test Email Configuration" section at the bottom of the alerts page to verify your SMTP settings are working.

## Alert Types

### Trade Opened
Notifies when a new trade is opened.

**Includes:**
- Symbol
- Direction (BUY/SELL)
- Entry price
- Volume
- Stop loss
- Take profit

**Example Email:**
```
🟢 Trade Opened: EURUSD BUY
Entry Price: 1.12345
Volume: 0.10 lots
Stop Loss: 1.12000
Take Profit: 1.13000
```

### Trade Closed
Notifies when a trade is closed.

**Includes:**
- Symbol
- Direction
- Entry/exit prices
- Profit/loss
- Pips gained/lost

**Example Email:**
```
🟢 Trade Closed: EURUSD - $50.00
Profit/Loss: $50.00 (+50.0 pips)
Entry Price: 1.12345
Exit Price: 1.12845
```

### Daily Summary
Sends a daily performance summary at end of trading day.

**Includes:**
- Total trades
- Winning/losing trade counts
- Net profit/loss
- Win rate %

**Example Email:**
```
📊 Daily Performance Summary - 2025-12-14

Net Profit/Loss: $150.00
Total Trades: 10
Winning Trades: 6
Losing Trades: 4
Win Rate: 60.0%
```

### Error Alerts
Notifies of system errors and critical issues.

**Includes:**
- Error message
- Error details/context
- Timestamp

### Profit/Loss Threshold Alerts
Triggers when a trade's profit or loss exceeds configured thresholds.

**Configuration:**
- Set minimum profit threshold (e.g., $100)
- Set maximum loss threshold (e.g., -$50)

## API Endpoints

### Get Alert Types
```http
GET /api/alerts/types
```

Returns available alert types and notification channels.

### List Configurations
```http
GET /api/alerts/config
```

Returns all alert configurations.

### Get Specific Configuration
```http
GET /api/alerts/config/{alert_type}
```

Returns configuration for specific alert type.

### Create Configuration
```http
POST /api/alerts/config
Content-Type: application/json

{
  "alert_type": "trade_opened",
  "enabled": true,
  "email_enabled": true,
  "websocket_enabled": true,
  "email_recipients": "user@example.com",
  "symbol_filter": "EURUSD, GBPUSD"
}
```

### Update Configuration
```http
PUT /api/alerts/config/{alert_type}
Content-Type: application/json

{
  "alert_type": "trade_opened",
  "enabled": false,
  "email_enabled": true,
  "email_recipients": "newuser@example.com"
}
```

### Delete Configuration
```http
DELETE /api/alerts/config/{alert_type}
```

### Get Alert History
```http
GET /api/alerts/history?limit=100&alert_type=trade_opened&success_only=true
```

Query parameters:
- `limit` - Maximum records (default: 100, max: 1000)
- `alert_type` - Filter by alert type
- `success_only` - Only show successful deliveries

### Test Email
```http
POST /api/alerts/test-email
Content-Type: application/json

{
  "email": "test@example.com"
}
```

## Environment Variables

Set these environment variables for email configuration (alternative to YAML file):

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM_EMAIL="your-email@gmail.com"
```

## Database Schema

### alert_configurations
Stores alert preferences:
- `id` - Primary key
- `alert_type` - Type of alert (enum)
- `enabled` - Whether alert is active
- `email_enabled` - Email channel enabled
- `sms_enabled` - SMS channel enabled (future)
- `websocket_enabled` - WebSocket channel enabled
- `email_recipients` - Comma-separated emails
- `sms_recipients` - Comma-separated phone numbers
- `profit_threshold` - Minimum profit trigger
- `loss_threshold` - Maximum loss trigger
- `symbol_filter` - Comma-separated symbols

### alert_history
Tracks all sent notifications:
- `id` - Primary key
- `alert_type` - Type of alert
- `channel` - Delivery channel (email, websocket, sms)
- `sent_at` - Timestamp
- `success` - Delivery success status
- `error_message` - Error if failed
- `recipient` - Email/phone/identifier
- `trade_id` - Related trade (if applicable)
- `subject` - Alert subject/title

## Troubleshooting

### Email Not Sending

1. **Check SMTP Configuration**
   - Verify `smtp_host`, `smtp_port`, `username`, `password`
   - Ensure `use_tls` matches port (587 = TLS, 465 = SSL)

2. **Gmail App Password**
   - Regular password won't work with 2FA enabled
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Use App Password in `password` field

3. **Test Email Configuration**
   - Use the "Test Email" feature in alerts settings
   - Check server logs for detailed error messages

4. **Check Firewall/Network**
   - Ensure outbound SMTP connections are allowed
   - Some networks block port 587/465

### Alerts Not Triggering

1. **Check Alert Configuration**
   - Ensure alert type is `enabled: true`
   - Verify channel is enabled (email_enabled/websocket_enabled)
   - Check recipients are configured

2. **Check Symbol Filter**
   - If symbol_filter is set, ensure trade symbol matches
   - Symbol filter is case-sensitive (use uppercase: "EURUSD")

3. **Check Thresholds**
   - For profit/loss threshold alerts, verify thresholds are set correctly
   - Profit threshold: Alert only if profit >= threshold
   - Loss threshold: Alert only if loss <= threshold (negative)

4. **Check Alert History**
   - Use API endpoint `/api/alerts/history` to see delivery attempts
   - Check for error messages in failed deliveries

### WebSocket Notifications Not Working

1. **Check Browser Console**
   - Open browser dev tools (F12)
   - Look for WebSocket connection errors

2. **Verify API Server Running**
   - Dashboard must be served by the API server
   - Access via `http://localhost:8000` not `file://`

3. **Check WebSocket Route**
   - Ensure WebSocket endpoint is registered
   - Test with: `ws://localhost:8000/api/ws`

## Integration with Trading Bot

The alert manager is automatically integrated with the trading bot. When trades are opened or closed, the bot will:

1. Query alert configurations from database
2. Check if alert should be sent (enabled, filters, thresholds)
3. Send notifications via enabled channels
4. Record delivery history in database
5. Broadcast WebSocket event for real-time dashboard updates

### Example Integration Code

```python
from src.notifications.alert_manager import AlertManager
from src.notifications.email_service import EmailConfig, EmailNotificationService

# Initialize email service
email_config = EmailConfig.gmail("your-email@gmail.com", "app-password")
email_service = EmailNotificationService(email_config)

# Initialize alert manager
alert_manager = AlertManager(email_service)

# Send trade opened alert
trade_data = {
    "symbol": "EURUSD",
    "trade_type": "BUY",
    "entry_price": 1.12345,
    "volume": 0.1,
    "stop_loss": 1.12000,
    "take_profit": 1.13000
}
alert_manager.send_trade_opened_alert(trade_data, trade_id=123)

# Send trade closed alert
trade_data = {
    "symbol": "EURUSD",
    "trade_type": "BUY",
    "entry_price": 1.12345,
    "exit_price": 1.12845,
    "profit": 50.00,
    "pips": 50.0
}
alert_manager.send_trade_closed_alert(trade_data, trade_id=123)
```

## Security Best Practices

1. **Never Commit Passwords**
   - Keep `config/email.yaml` out of version control
   - Use `.gitignore` to exclude sensitive files

2. **Use App Passwords**
   - Don't use your main email password
   - Generate app-specific passwords with limited permissions

3. **Restrict SMTP Access**
   - Use firewall rules to restrict outbound SMTP
   - Monitor for unusual email sending patterns

4. **Secure API Endpoints**
   - Add authentication to alert configuration endpoints (future enhancement)
   - Use HTTPS in production
   - Implement rate limiting

## Future Enhancements

🔜 **SMS Notifications**
- Integration with Twilio/AWS SNS
- Phone number verification
- SMS delivery tracking

🔜 **Push Notifications**
- Mobile app push notifications
- Browser push notifications
- Notification preferences per device

🔜 **Advanced Filtering**
- Time-based filters (only during trading hours)
- Strategy-based filters (only ML-enhanced trades)
- Combination filters (AND/OR logic)

🔜 **Notification Templates**
- Customizable email templates
- Multi-language support
- Branding customization

🔜 **Delivery Optimization**
- Batching (multiple trades in one email)
- Throttling (max N emails per hour)
- Digest mode (hourly/daily summaries)

## Support

For issues or questions:
- Check API logs: Look for email/alert errors
- Check database: Query `alert_history` for delivery status
- Review configuration: Verify YAML/env vars are correct

## Version History

### v2.2.0 - Alert System (2025-12-14)
- ✅ Email notifications via SMTP
- ✅ Real-time WebSocket notifications
- ✅ Configurable alert types
- ✅ Symbol filtering and thresholds
- ✅ Web UI for alert management
- ✅ Delivery tracking and history
- ✅ Test email functionality
- ✅ API endpoints for configuration

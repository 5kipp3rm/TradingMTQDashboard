"""
Email Notification Service for TradingMTQ

Provides email notifications for trade events using SMTP.
Supports multiple providers (Gmail, Outlook, custom SMTP).
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class EmailConfig:
    """Email service configuration"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str = "TradingMTQ Bot",
        use_tls: bool = True,
        use_ssl: bool = False
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls
        self.use_ssl = use_ssl

    @classmethod
    def gmail(cls, email: str, app_password: str) -> 'EmailConfig':
        """Create Gmail configuration (requires app password)"""
        return cls(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            username=email,
            password=app_password,
            from_email=email,
            from_name="TradingMTQ Bot",
            use_tls=True,
            use_ssl=False
        )

    @classmethod
    def outlook(cls, email: str, password: str) -> 'EmailConfig':
        """Create Outlook configuration"""
        return cls(
            smtp_host="smtp-mail.outlook.com",
            smtp_port=587,
            username=email,
            password=password,
            from_email=email,
            from_name="TradingMTQ Bot",
            use_tls=True,
            use_ssl=False
        )


class EmailNotificationService:
    """
    Email notification service for trading alerts

    Features:
    - Trade opened/closed notifications
    - Daily performance summaries
    - Error alerts
    - Custom HTML templates
    """

    def __init__(self, config: EmailConfig):
        self.config = config
        self.enabled = True
        logger.info(
            "EmailNotificationService initialized",
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            from_email=config.from_email
        )

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Send an email notification

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text fallback (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email notifications are disabled")
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            message["To"] = ", ".join(to_emails)

            # Add plain text version
            if body_text:
                part_text = MIMEText(body_text, "plain")
                message.attach(part_text)

            # Add HTML version
            part_html = MIMEText(body_html, "html")
            message.attach(part_html)

            # Send email
            if self.config.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    self.config.smtp_host,
                    self.config.smtp_port,
                    context=context
                ) as server:
                    server.login(self.config.username, self.config.password)
                    server.sendmail(
                        self.config.from_email,
                        to_emails,
                        message.as_string()
                    )
            else:
                with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                    if self.config.use_tls:
                        server.starttls()
                    server.login(self.config.username, self.config.password)
                    server.sendmail(
                        self.config.from_email,
                        to_emails,
                        message.as_string()
                    )

            logger.info(
                "Email sent successfully",
                to=to_emails,
                subject=subject
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to send email",
                error=str(e),
                to=to_emails,
                subject=subject
            )
            return False

    def notify_trade_opened(
        self,
        to_emails: List[str],
        trade_data: Dict[str, Any]
    ) -> bool:
        """
        Send notification when a trade is opened

        Args:
            to_emails: Recipient email addresses
            trade_data: Trade information

        Returns:
            True if sent successfully
        """
        symbol = trade_data.get('symbol', 'UNKNOWN')
        trade_type = trade_data.get('trade_type', 'UNKNOWN')
        entry_price = trade_data.get('entry_price', 0.0)
        volume = trade_data.get('volume', 0.0)
        stop_loss = trade_data.get('stop_loss')
        take_profit = trade_data.get('take_profit')

        subject = f"🟢 Trade Opened: {symbol} {trade_type}"

        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              .header {{ background-color: #4CAF50; color: white; padding: 15px; border-radius: 5px; }}
              .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
              .trade-detail {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 4px solid #4CAF50; }}
              .label {{ font-weight: bold; color: #333; }}
              .value {{ color: #666; }}
              .footer {{ margin-top: 20px; text-align: center; color: #999; font-size: 12px; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h2>🟢 New Trade Opened</h2>
              </div>
              <div class="content">
                <div class="trade-detail">
                  <span class="label">Symbol:</span>
                  <span class="value">{symbol}</span>
                </div>
                <div class="trade-detail">
                  <span class="label">Direction:</span>
                  <span class="value">{trade_type}</span>
                </div>
                <div class="trade-detail">
                  <span class="label">Entry Price:</span>
                  <span class="value">{entry_price:.5f}</span>
                </div>
                <div class="trade-detail">
                  <span class="label">Volume:</span>
                  <span class="value">{volume:.2f} lots</span>
                </div>
                {"" if stop_loss is None else f'''
                <div class="trade-detail">
                  <span class="label">Stop Loss:</span>
                  <span class="value">{stop_loss:.5f}</span>
                </div>
                '''}
                {"" if take_profit is None else f'''
                <div class="trade-detail">
                  <span class="label">Take Profit:</span>
                  <span class="value">{take_profit:.5f}</span>
                </div>
                '''}
                <div class="trade-detail">
                  <span class="label">Time:</span>
                  <span class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
              </div>
              <div class="footer">
                <p>TradingMTQ Automated Trading Bot</p>
              </div>
            </div>
          </body>
        </html>
        """

        text_body = f"""
        Trade Opened: {symbol} {trade_type}

        Entry Price: {entry_price:.5f}
        Volume: {volume:.2f} lots
        Stop Loss: {stop_loss:.5f if stop_loss else 'Not set'}
        Take Profit: {take_profit:.5f if take_profit else 'Not set'}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        return self.send_email(to_emails, subject, html_body, text_body)

    def notify_trade_closed(
        self,
        to_emails: List[str],
        trade_data: Dict[str, Any]
    ) -> bool:
        """
        Send notification when a trade is closed

        Args:
            to_emails: Recipient email addresses
            trade_data: Trade information

        Returns:
            True if sent successfully
        """
        symbol = trade_data.get('symbol', 'UNKNOWN')
        trade_type = trade_data.get('trade_type', 'UNKNOWN')
        entry_price = trade_data.get('entry_price', 0.0)
        exit_price = trade_data.get('exit_price', 0.0)
        profit = trade_data.get('profit', 0.0)
        pips = trade_data.get('pips', 0.0)

        is_profit = profit >= 0
        emoji = "🟢" if is_profit else "🔴"
        color = "#4CAF50" if is_profit else "#f44336"

        subject = f"{emoji} Trade Closed: {symbol} - ${profit:.2f}"

        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
              .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
              .trade-detail {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 4px solid {color}; }}
              .profit {{ font-size: 24px; font-weight: bold; color: {color}; text-align: center; padding: 20px; }}
              .label {{ font-weight: bold; color: #333; }}
              .value {{ color: #666; }}
              .footer {{ margin-top: 20px; text-align: center; color: #999; font-size: 12px; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h2>{emoji} Trade Closed</h2>
              </div>
              <div class="content">
                <div class="profit">
                  ${profit:.2f} ({pips:+.1f} pips)
                </div>
                <div class="trade-detail">
                  <span class="label">Symbol:</span>
                  <span class="value">{symbol}</span>
                </div>
                <div class="trade-detail">
                  <span class="label">Direction:</span>
                  <span class="value">{trade_type}</span>
                </div>
                <div class="trade-detail">
                  <span class="label">Entry Price:</span>
                  <span class="value">{entry_price:.5f}</span>
                </div>
                <div class="trade-detail">
                  <span class="label">Exit Price:</span>
                  <span class="value">{exit_price:.5f}</span>
                </div>
                <div class="trade-detail">
                  <span class="label">Time:</span>
                  <span class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
              </div>
              <div class="footer">
                <p>TradingMTQ Automated Trading Bot</p>
              </div>
            </div>
          </body>
        </html>
        """

        text_body = f"""
        Trade Closed: {symbol}

        Profit/Loss: ${profit:.2f} ({pips:+.1f} pips)
        Direction: {trade_type}
        Entry Price: {entry_price:.5f}
        Exit Price: {exit_price:.5f}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        return self.send_email(to_emails, subject, html_body, text_body)

    def notify_daily_summary(
        self,
        to_emails: List[str],
        performance_data: Dict[str, Any]
    ) -> bool:
        """
        Send daily performance summary

        Args:
            to_emails: Recipient email addresses
            performance_data: Daily performance metrics

        Returns:
            True if sent successfully
        """
        total_trades = performance_data.get('total_trades', 0)
        winning_trades = performance_data.get('winning_trades', 0)
        losing_trades = performance_data.get('losing_trades', 0)
        net_profit = performance_data.get('net_profit', 0.0)
        win_rate = performance_data.get('win_rate', 0.0)

        is_profit = net_profit >= 0
        emoji = "📊" if is_profit else "📉"
        color = "#4CAF50" if is_profit else "#f44336"

        subject = f"{emoji} Daily Summary - ${net_profit:.2f}"

        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              .header {{ background-color: #2196F3; color: white; padding: 15px; border-radius: 5px; }}
              .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
              .metric {{ margin: 15px 0; padding: 15px; background-color: white; border-radius: 5px; }}
              .metric-value {{ font-size: 28px; font-weight: bold; color: {color}; }}
              .metric-label {{ color: #666; font-size: 14px; }}
              .stats {{ display: flex; justify-content: space-around; flex-wrap: wrap; }}
              .stat {{ text-align: center; padding: 15px; flex: 1; min-width: 120px; }}
              .stat-value {{ font-size: 24px; font-weight: bold; color: #333; }}
              .stat-label {{ color: #666; font-size: 12px; }}
              .footer {{ margin-top: 20px; text-align: center; color: #999; font-size: 12px; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h2>📊 Daily Performance Summary</h2>
                <p>{datetime.now().strftime('%Y-%m-%d')}</p>
              </div>
              <div class="content">
                <div class="metric">
                  <div class="metric-label">Net Profit/Loss</div>
                  <div class="metric-value">${net_profit:.2f}</div>
                </div>
                <div class="stats">
                  <div class="stat">
                    <div class="stat-value">{total_trades}</div>
                    <div class="stat-label">Total Trades</div>
                  </div>
                  <div class="stat">
                    <div class="stat-value" style="color: #4CAF50;">{winning_trades}</div>
                    <div class="stat-label">Winning</div>
                  </div>
                  <div class="stat">
                    <div class="stat-value" style="color: #f44336;">{losing_trades}</div>
                    <div class="stat-label">Losing</div>
                  </div>
                  <div class="stat">
                    <div class="stat-value">{win_rate:.1f}%</div>
                    <div class="stat-label">Win Rate</div>
                  </div>
                </div>
              </div>
              <div class="footer">
                <p>TradingMTQ Automated Trading Bot</p>
              </div>
            </div>
          </body>
        </html>
        """

        text_body = f"""
        Daily Performance Summary - {datetime.now().strftime('%Y-%m-%d')}

        Net Profit/Loss: ${net_profit:.2f}
        Total Trades: {total_trades}
        Winning Trades: {winning_trades}
        Losing Trades: {losing_trades}
        Win Rate: {win_rate:.1f}%
        """

        return self.send_email(to_emails, subject, html_body, text_body)

    def notify_error(
        self,
        to_emails: List[str],
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send error alert notification

        Args:
            to_emails: Recipient email addresses
            error_message: Error message
            error_details: Additional error context

        Returns:
            True if sent successfully
        """
        subject = "⚠️ Trading Bot Error Alert"

        details_html = ""
        if error_details:
            details_html = "<h3>Error Details:</h3><ul>"
            for key, value in error_details.items():
                details_html += f"<li><strong>{key}:</strong> {value}</li>"
            details_html += "</ul>"

        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              .header {{ background-color: #ff9800; color: white; padding: 15px; border-radius: 5px; }}
              .content {{ background-color: #fff3e0; padding: 20px; margin-top: 20px; border-radius: 5px; border-left: 4px solid #ff9800; }}
              .error-message {{ font-family: monospace; background-color: white; padding: 15px; border-radius: 5px; color: #d32f2f; }}
              .footer {{ margin-top: 20px; text-align: center; color: #999; font-size: 12px; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h2>⚠️ Trading Bot Error Alert</h2>
              </div>
              <div class="content">
                <h3>Error Message:</h3>
                <div class="error-message">{error_message}</div>
                {details_html}
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
              </div>
              <div class="footer">
                <p>TradingMTQ Automated Trading Bot</p>
              </div>
            </div>
          </body>
        </html>
        """

        text_body = f"""
        Trading Bot Error Alert

        Error: {error_message}

        {f"Details: {error_details}" if error_details else ""}

        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        return self.send_email(to_emails, subject, html_body, text_body)

    def test_connection(self, to_email: str) -> bool:
        """
        Test email connection by sending a test email

        Args:
            to_email: Test recipient email

        Returns:
            True if test successful
        """
        subject = "✅ TradingMTQ Email Test"
        html_body = """
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4CAF50;">✅ Email Configuration Test</h2>
            <p>If you're reading this, your email notifications are configured correctly!</p>
            <p><strong>TradingMTQ</strong> is ready to send you trading alerts.</p>
          </body>
        </html>
        """
        text_body = "Email Configuration Test\n\nIf you're reading this, your email notifications are configured correctly!"

        return self.send_email([to_email], subject, html_body, text_body)

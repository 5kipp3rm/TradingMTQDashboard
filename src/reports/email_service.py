"""
Email Service for Report Delivery

Handles email composition and delivery of PDF performance reports.
Supports SMTP with TLS/SSL, HTML emails, and file attachments.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib
import ssl
from datetime import datetime

from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class EmailConfiguration:
    """Email server configuration"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        from_name: Optional[str] = None,
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name or "TradingMTQ Reports"
        self.use_tls = use_tls


class EmailService:
    """
    Service for sending emails with report attachments.
    """

    def __init__(self, config: EmailConfiguration):
        """
        Initialize email service.

        Args:
            config: Email server configuration
        """
        self.config = config

    def send_report(
        self,
        to_emails: List[str],
        subject: str,
        report_path: Path,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> bool:
        """
        Send performance report via email.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            report_path: Path to PDF report file
            body_html: Optional HTML email body
            body_text: Optional plain text email body
            cc_emails: Optional CC recipients
            bcc_emails: Optional BCC recipients

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            logger.info(
                "Sending report email",
                recipients=len(to_emails),
                subject=subject,
                attachment=report_path.name
            )

            # Create message
            msg = self._create_message(
                to_emails=to_emails,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails
            )

            # Attach report
            self._attach_file(msg, report_path)

            # Send email
            self._send_message(msg, to_emails, cc_emails, bcc_emails)

            logger.info(
                "Report email sent successfully",
                recipients=len(to_emails)
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to send report email",
                error=str(e),
                exc_info=True
            )
            return False

    def send_daily_digest(
        self,
        to_emails: List[str],
        report_paths: List[Path],
        summary_data: Dict[str, Any]
    ) -> bool:
        """
        Send daily digest email with multiple reports.

        Args:
            to_emails: List of recipient email addresses
            report_paths: List of paths to PDF reports
            summary_data: Summary data for email body

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            logger.info(
                "Sending daily digest",
                recipients=len(to_emails),
                reports=len(report_paths)
            )

            # Create digest subject
            date_str = datetime.now().strftime("%B %d, %Y")
            subject = f"TradingMTQ Daily Performance Digest - {date_str}"

            # Create digest body
            body_html = self._create_digest_body(summary_data)
            body_text = self._create_digest_body_text(summary_data)

            # Create message
            msg = self._create_message(
                to_emails=to_emails,
                subject=subject,
                body_html=body_html,
                body_text=body_text
            )

            # Attach all reports
            for report_path in report_paths:
                self._attach_file(msg, report_path)

            # Send email
            self._send_message(msg, to_emails)

            logger.info("Daily digest sent successfully")
            return True

        except Exception as e:
            logger.error(
                "Failed to send daily digest",
                error=str(e),
                exc_info=True
            )
            return False

    def _create_message(
        self,
        to_emails: List[str],
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> MIMEMultipart:
        """Create email message"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
        msg['To'] = ', '.join(to_emails)

        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)

        # Add text body
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))

        # Add HTML body
        if body_html:
            msg.attach(MIMEText(body_html, 'html'))
        elif not body_text:
            # Provide default body if none specified
            default_body = self._create_default_body()
            msg.attach(MIMEText(default_body, 'html'))

        return msg

    def _attach_file(self, msg: MIMEMultipart, file_path: Path):
        """Attach file to email message"""
        with open(file_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='pdf')
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=file_path.name
            )
            msg.attach(attachment)

    def _send_message(
        self,
        msg: MIMEMultipart,
        to_emails: List[str],
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ):
        """Send email message via SMTP"""
        # Combine all recipients
        all_recipients = to_emails.copy()
        if cc_emails:
            all_recipients.extend(cc_emails)
        if bcc_emails:
            all_recipients.extend(bcc_emails)

        # Create SSL context
        context = ssl.create_default_context()

        # Connect and send
        if self.config.use_tls:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg, to_addrs=all_recipients)
        else:
            with smtplib.SMTP_SSL(
                self.config.smtp_host,
                self.config.smtp_port,
                context=context
            ) as server:
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg, to_addrs=all_recipients)

    def _create_default_body(self) -> str:
        """Create default email body"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2563eb;">TradingMTQ Performance Report</h2>
            <p>Please find your trading performance report attached.</p>
            <p>This report contains detailed analytics and insights about your trading performance.</p>
            <hr style="border: 1px solid #e0e0e0;">
            <p style="font-size: 12px; color: #666;">
                This is an automated email from TradingMTQ Analytics Platform.<br>
                Generated on {timestamp}
            </p>
        </body>
        </html>
        """.format(timestamp=datetime.now().strftime("%B %d, %Y at %I:%M %p"))

    def _create_digest_body(self, summary_data: Dict[str, Any]) -> str:
        """Create HTML body for daily digest"""
        total_trades = summary_data.get('total_trades', 0)
        net_profit = summary_data.get('net_profit', 0)
        win_rate = summary_data.get('win_rate', 0)

        profit_color = "#10b981" if net_profit >= 0 else "#ef4444"

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #2563eb;">Daily Performance Digest</h1>
            <p style="font-size: 14px; color: #666;">
                {datetime.now().strftime("%B %d, %Y")}
            </p>

            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h2 style="color: #1e293b; margin-top: 0;">Summary</h2>

                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">
                            <strong>Total Trades:</strong>
                        </td>
                        <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: right;">
                            {total_trades}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">
                            <strong>Net Profit:</strong>
                        </td>
                        <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: right; color: {profit_color}; font-weight: bold;">
                            ${net_profit:.2f}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;">
                            <strong>Win Rate:</strong>
                        </td>
                        <td style="padding: 10px; text-align: right;">
                            {win_rate:.1f}%
                        </td>
                    </tr>
                </table>
            </div>

            <p style="font-size: 14px;">
                Detailed performance reports are attached to this email.
            </p>

            <hr style="border: 1px solid #e0e0e0; margin: 30px 0;">

            <p style="font-size: 12px; color: #666;">
                This is an automated daily digest from TradingMTQ Analytics Platform.<br>
                To manage your email preferences, please log in to your dashboard.
            </p>
        </body>
        </html>
        """

    def _create_digest_body_text(self, summary_data: Dict[str, Any]) -> str:
        """Create plain text body for daily digest"""
        total_trades = summary_data.get('total_trades', 0)
        net_profit = summary_data.get('net_profit', 0)
        win_rate = summary_data.get('win_rate', 0)

        return f"""
TradingMTQ Daily Performance Digest
{datetime.now().strftime("%B %d, %Y")}

SUMMARY
-------
Total Trades: {total_trades}
Net Profit: ${net_profit:.2f}
Win Rate: {win_rate:.1f}%

Detailed performance reports are attached to this email.

---
This is an automated daily digest from TradingMTQ Analytics Platform.
To manage your email preferences, please log in to your dashboard.
        """

    def test_connection(self) -> bool:
        """
        Test SMTP connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Testing SMTP connection", host=self.config.smtp_host)

            context = ssl.create_default_context()

            if self.config.use_tls:
                with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=10) as server:
                    server.starttls(context=context)
                    server.login(self.config.smtp_user, self.config.smtp_password)
            else:
                with smtplib.SMTP_SSL(
                    self.config.smtp_host,
                    self.config.smtp_port,
                    context=context,
                    timeout=10
                ) as server:
                    server.login(self.config.smtp_user, self.config.smtp_password)

            logger.info("SMTP connection successful")
            return True

        except Exception as e:
            logger.error(
                "SMTP connection failed",
                error=str(e),
                exc_info=True
            )
            return False

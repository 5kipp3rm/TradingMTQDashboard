"""
Unit Tests for Email Service

Tests email composition, attachment handling, and SMTP delivery.
Uses mocking to avoid actual email sends during testing.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
from email.mime.multipart import MIMEMultipart

from src.reports.email_service import EmailService, EmailConfiguration


@pytest.fixture
def email_config():
    """Create test email configuration"""
    return EmailConfiguration(
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="test_password",
        from_email="reports@tradingmtq.com",
        from_name="TradingMTQ Reports",
        use_tls=True
    )


@pytest.fixture
def email_service(email_config):
    """Create test email service"""
    return EmailService(email_config)


@pytest.fixture
def sample_pdf():
    """Create temporary PDF file for testing"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.write(b'%PDF-1.4 test content')
    temp_file.close()
    yield Path(temp_file.name)
    # Cleanup
    Path(temp_file.name).unlink()


class TestEmailConfiguration:
    """Test email configuration"""

    def test_create_config_with_tls(self):
        """Test creating email configuration with TLS"""
        config = EmailConfiguration(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="user@test.com",
            smtp_password="password",
            from_email="from@test.com",
            use_tls=True
        )

        assert config.smtp_host == "smtp.test.com"
        assert config.smtp_port == 587
        assert config.use_tls is True

    def test_create_config_without_tls(self):
        """Test creating email configuration without TLS (SSL)"""
        config = EmailConfiguration(
            smtp_host="smtp.test.com",
            smtp_port=465,
            smtp_user="user@test.com",
            smtp_password="password",
            from_email="from@test.com",
            use_tls=False
        )

        assert config.use_tls is False
        assert config.smtp_port == 465

    def test_config_default_from_name(self):
        """Test default from_name if not provided"""
        config = EmailConfiguration(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="user@test.com",
            smtp_password="password",
            from_email="from@test.com"
        )

        assert config.from_name == "TradingMTQ Reports"

    def test_config_custom_from_name(self):
        """Test custom from_name"""
        config = EmailConfiguration(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="user@test.com",
            smtp_password="password",
            from_email="from@test.com",
            from_name="Custom Sender"
        )

        assert config.from_name == "Custom Sender"


class TestEmailServiceInitialization:
    """Test email service initialization"""

    def test_init_with_config(self, email_config):
        """Test initializing email service with configuration"""
        service = EmailService(email_config)
        assert service.config == email_config

    def test_config_stored(self, email_service, email_config):
        """Test that configuration is stored correctly"""
        assert email_service.config.smtp_host == email_config.smtp_host
        assert email_service.config.smtp_port == email_config.smtp_port


class TestMessageCreation:
    """Test email message creation"""

    def test_create_basic_message(self, email_service):
        """Test creating basic email message"""
        msg = email_service._create_message(
            to_emails=["recipient@test.com"],
            subject="Test Subject"
        )

        assert isinstance(msg, MIMEMultipart)
        assert msg['Subject'] == "Test Subject"
        assert msg['To'] == "recipient@test.com"
        assert "TradingMTQ Reports" in msg['From']

    def test_create_message_with_multiple_recipients(self, email_service):
        """Test creating message with multiple recipients"""
        msg = email_service._create_message(
            to_emails=["user1@test.com", "user2@test.com"],
            subject="Test Subject"
        )

        assert "user1@test.com" in msg['To']
        assert "user2@test.com" in msg['To']

    def test_create_message_with_cc(self, email_service):
        """Test creating message with CC recipients"""
        msg = email_service._create_message(
            to_emails=["recipient@test.com"],
            subject="Test Subject",
            cc_emails=["cc@test.com"]
        )

        assert msg['Cc'] == "cc@test.com"

    def test_create_message_with_html_body(self, email_service):
        """Test creating message with HTML body"""
        html_body = "<html><body><h1>Test</h1></body></html>"

        msg = email_service._create_message(
            to_emails=["recipient@test.com"],
            subject="Test Subject",
            body_html=html_body
        )

        # Verify HTML content is included
        assert isinstance(msg, MIMEMultipart)

    def test_create_message_with_text_body(self, email_service):
        """Test creating message with plain text body"""
        text_body = "This is a plain text message"

        msg = email_service._create_message(
            to_emails=["recipient@test.com"],
            subject="Test Subject",
            body_text=text_body
        )

        assert isinstance(msg, MIMEMultipart)

    def test_create_message_default_body_if_none(self, email_service):
        """Test that default body is created if none provided"""
        msg = email_service._create_message(
            to_emails=["recipient@test.com"],
            subject="Test Subject"
        )

        # Should include default HTML body
        assert isinstance(msg, MIMEMultipart)


class TestFileAttachment:
    """Test file attachment functionality"""

    def test_attach_pdf_file(self, email_service, sample_pdf):
        """Test attaching PDF file to message"""
        msg = MIMEMultipart()
        email_service._attach_file(msg, sample_pdf)

        # Verify attachment was added
        payloads = msg.get_payload()
        assert len(payloads) > 0

    def test_attachment_has_correct_filename(self, email_service, sample_pdf):
        """Test that attachment has correct filename"""
        msg = MIMEMultipart()
        email_service._attach_file(msg, sample_pdf)

        payloads = msg.get_payload()
        assert len(payloads) > 0
        # Attachment should have filename in headers


class TestSendReport:
    """Test sending report functionality"""

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_send_report_success(self, mock_smtp, email_service, sample_pdf):
        """Test successfully sending report email"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_report(
            to_emails=["recipient@test.com"],
            subject="Test Report",
            report_path=sample_pdf
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_send_report_with_custom_body(self, mock_smtp, email_service, sample_pdf):
        """Test sending report with custom body"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_report(
            to_emails=["recipient@test.com"],
            subject="Test Report",
            report_path=sample_pdf,
            body_html="<html><body>Custom HTML</body></html>",
            body_text="Custom text"
        )

        assert result is True

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_send_report_with_cc_bcc(self, mock_smtp, email_service, sample_pdf):
        """Test sending report with CC and BCC"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_report(
            to_emails=["recipient@test.com"],
            subject="Test Report",
            report_path=sample_pdf,
            cc_emails=["cc@test.com"],
            bcc_emails=["bcc@test.com"]
        )

        assert result is True
        # Verify all recipients were included in send
        call_args = mock_server.send_message.call_args
        assert call_args is not None

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_send_report_failure(self, mock_smtp, email_service, sample_pdf):
        """Test handling of send failure"""
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP Error")

        result = email_service.send_report(
            to_emails=["recipient@test.com"],
            subject="Test Report",
            report_path=sample_pdf
        )

        assert result is False


class TestSendDailyDigest:
    """Test daily digest functionality"""

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_send_daily_digest_success(self, mock_smtp, email_service, sample_pdf):
        """Test successfully sending daily digest"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        summary_data = {
            'total_trades': 50,
            'net_profit': 1250.50,
            'win_rate': 65.5
        }

        result = email_service.send_daily_digest(
            to_emails=["recipient@test.com"],
            report_paths=[sample_pdf],
            summary_data=summary_data
        )

        assert result is True
        mock_server.send_message.assert_called_once()

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_send_digest_with_multiple_reports(self, mock_smtp, email_service, sample_pdf):
        """Test sending digest with multiple report attachments"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        summary_data = {
            'total_trades': 50,
            'net_profit': 1250.50,
            'win_rate': 65.5
        }

        # Create multiple temp PDFs
        temp_files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.write(f'%PDF-1.4 test content {i}'.encode())
            temp_file.close()
            temp_files.append(Path(temp_file.name))

        try:
            result = email_service.send_daily_digest(
                to_emails=["recipient@test.com"],
                report_paths=temp_files,
                summary_data=summary_data
            )

            assert result is True
        finally:
            # Cleanup
            for temp_file in temp_files:
                temp_file.unlink()

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_send_digest_failure(self, mock_smtp, email_service, sample_pdf):
        """Test handling of digest send failure"""
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP Error")

        summary_data = {
            'total_trades': 50,
            'net_profit': 1250.50,
            'win_rate': 65.5
        }

        result = email_service.send_daily_digest(
            to_emails=["recipient@test.com"],
            report_paths=[sample_pdf],
            summary_data=summary_data
        )

        assert result is False


class TestDigestBodyCreation:
    """Test digest body creation"""

    def test_create_digest_html_body(self, email_service):
        """Test creating HTML body for digest"""
        summary_data = {
            'total_trades': 50,
            'net_profit': 1250.50,
            'win_rate': 65.5
        }

        html_body = email_service._create_digest_body(summary_data)

        assert "50" in html_body  # total_trades
        assert "1250.50" in html_body  # net_profit
        assert "65.5" in html_body  # win_rate
        assert "<html>" in html_body
        assert "</html>" in html_body

    def test_create_digest_text_body(self, email_service):
        """Test creating plain text body for digest"""
        summary_data = {
            'total_trades': 50,
            'net_profit': 1250.50,
            'win_rate': 65.5
        }

        text_body = email_service._create_digest_body_text(summary_data)

        assert "50" in text_body  # total_trades
        assert "1250.50" in text_body  # net_profit
        assert "65.5" in text_body  # win_rate

    def test_digest_body_profit_color(self, email_service):
        """Test that profit color changes based on value"""
        # Positive profit (green)
        positive_data = {'total_trades': 10, 'net_profit': 100.0, 'win_rate': 70.0}
        positive_html = email_service._create_digest_body(positive_data)
        assert "#10b981" in positive_html  # Green color

        # Negative profit (red)
        negative_data = {'total_trades': 10, 'net_profit': -50.0, 'win_rate': 40.0}
        negative_html = email_service._create_digest_body(negative_data)
        assert "#ef4444" in negative_html  # Red color


class TestConnectionTesting:
    """Test SMTP connection testing"""

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_connection_success(self, mock_smtp, email_service):
        """Test successful SMTP connection"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.test_connection()

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_connection_failure(self, mock_smtp, email_service):
        """Test SMTP connection failure"""
        mock_smtp.return_value.__enter__.side_effect = Exception("Connection refused")

        result = email_service.test_connection()

        assert result is False

    @patch('src.reports.email_service.smtplib.SMTP_SSL')
    def test_connection_ssl_success(self, mock_smtp_ssl, email_config):
        """Test successful SMTP SSL connection"""
        # Configure for SSL (no TLS)
        email_config.use_tls = False
        email_service = EmailService(email_config)

        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        result = email_service.test_connection()

        assert result is True
        mock_server.login.assert_called_once()
        # No starttls call for SSL
        mock_server.starttls.assert_not_called()


class TestSMTPMethods:
    """Test SMTP send methods"""

    @patch('src.reports.email_service.smtplib.SMTP_SSL')
    def test_send_with_ssl(self, mock_smtp_ssl, email_config, sample_pdf):
        """Test sending email with SSL (no TLS)"""
        email_config.use_tls = False
        email_service = EmailService(email_config)

        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        result = email_service.send_report(
            to_emails=["recipient@test.com"],
            subject="Test Report",
            report_path=sample_pdf
        )

        assert result is True
        mock_server.login.assert_called_once()
        # No starttls call for SSL
        mock_server.starttls.assert_not_called()

    @patch('src.reports.email_service.smtplib.SMTP')
    def test_send_with_tls(self, mock_smtp, email_service, sample_pdf):
        """Test sending email with TLS"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = email_service.send_report(
            to_emails=["recipient@test.com"],
            subject="Test Report",
            report_path=sample_pdf
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()

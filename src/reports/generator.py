"""
PDF Report Generator

Generates professional PDF performance reports with charts, tables, and analytics.
Uses ReportLab for PDF generation and matplotlib for embedded charts.
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from src.database import get_session, TradingAccount
from src.database.repository import DailyPerformanceRepository, TradeRepository
from src.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class ReportGenerator:
    """
    Generates PDF performance reports with analytics, charts, and tables.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator.

        Args:
            output_dir: Directory for generated reports (default: ./reports)
        """
        self.output_dir = output_dir or Path("./reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for reports"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=20,
            spaceAfter=12,
            borderPadding=5
        ))

        # Metric style for large numbers
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#10b981'),
            alignment=TA_CENTER,
            spaceAfter=5
        ))

        # Metric label style
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER
        ))

    def generate_performance_report(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[int] = None,
        include_trades: bool = True,
        include_charts: bool = True
    ) -> Path:
        """
        Generate comprehensive performance report.

        Args:
            start_date: Report start date
            end_date: Report end date
            account_id: Optional account ID to filter by
            include_trades: Whether to include trade list
            include_charts: Whether to include performance charts

        Returns:
            Path to generated PDF file
        """
        logger.info(
            "Generating performance report",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            account_id=account_id
        )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        account_suffix = f"_account_{account_id}" if account_id else "_all_accounts"
        filename = f"performance_report_{start_date}_{end_date}{account_suffix}_{timestamp}.pdf"
        output_path = self.output_dir / filename

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Build report content
        story = []

        # Title page
        story.extend(self._create_title_page(start_date, end_date, account_id))

        # Executive summary
        story.extend(self._create_executive_summary(start_date, end_date, account_id))
        story.append(PageBreak())

        # Detailed metrics
        story.extend(self._create_detailed_metrics(start_date, end_date, account_id))

        # Trade list (if requested)
        if include_trades:
            story.append(PageBreak())
            story.extend(self._create_trade_list(start_date, end_date, account_id))

        # Build PDF
        doc.build(story)

        logger.info(
            "Performance report generated",
            output_path=str(output_path),
            size_bytes=output_path.stat().st_size
        )

        return output_path

    def _create_title_page(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[int]
    ) -> List:
        """Create report title page"""
        elements = []

        # Title
        title = Paragraph(
            "Trading Performance Report",
            self.styles['ReportTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))

        # Report period
        period_text = f"<b>Report Period:</b> {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        elements.append(Paragraph(period_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))

        # Account info
        if account_id:
            with get_session() as session:
                account = session.get(TradingAccount, account_id)
                if account:
                    account_text = f"<b>Account:</b> {account.account_name} ({account.account_number})"
                    elements.append(Paragraph(account_text, self.styles['Normal']))
        else:
            elements.append(Paragraph("<b>Account:</b> All Accounts", self.styles['Normal']))

        elements.append(Spacer(1, 0.1*inch))

        # Generation timestamp
        gen_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        gen_text = f"<i>Generated on {gen_time}</i>"
        elements.append(Paragraph(gen_text, self.styles['Normal']))

        elements.append(Spacer(1, 0.5*inch))

        return elements

    def _create_executive_summary(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[int]
    ) -> List:
        """Create executive summary with key metrics"""
        elements = []

        # Section header
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))

        # Fetch summary data
        with get_session() as session:
            repo = DailyPerformanceRepository()
            summary = repo.get_performance_summary(session, start_date, end_date, account_id=account_id)

        if not summary:
            elements.append(Paragraph("No trading data available for this period.", self.styles['Normal']))
            return elements

        # Create metrics table
        metrics_data = [
            ['Metric', 'Value'],
            ['Total Days', str(summary.get('total_days', 0))],
            ['Total Trades', str(summary.get('total_trades', 0))],
            ['Winning Days', str(summary.get('winning_days', 0))],
            ['Losing Days', str(summary.get('losing_days', 0))],
            ['Total Profit', f"${summary.get('total_profit', 0):.2f}"],
            ['Average Daily Profit', f"${summary.get('average_daily_profit', 0):.2f}"],
        ]

        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        elements.append(metrics_table)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_detailed_metrics(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[int]
    ) -> List:
        """Create detailed metrics section"""
        elements = []

        elements.append(Paragraph("Detailed Performance Metrics", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))

        # Fetch trade statistics
        with get_session() as session:
            trade_repo = TradeRepository()

            # Get all trades for detailed analysis
            from src.database.models import Trade, TradeStatus
            from sqlalchemy import and_

            query_filters = [
                Trade.status == TradeStatus.CLOSED,
                Trade.exit_time >= datetime.combine(start_date, datetime.min.time()),
                Trade.exit_time <= datetime.combine(end_date, datetime.max.time())
            ]

            if account_id:
                query_filters.append(Trade.account_id == account_id)

            trades = session.query(Trade).filter(and_(*query_filters)).all()

        if not trades:
            elements.append(Paragraph("No trades found for this period.", self.styles['Normal']))
            return elements

        # Calculate detailed metrics
        winning_trades = [t for t in trades if t.profit and t.profit > 0]
        losing_trades = [t for t in trades if t.profit and t.profit < 0]

        total_trades = len(trades)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

        avg_win = sum(float(t.profit) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(float(t.profit) for t in losing_trades) / len(losing_trades) if losing_trades else 0

        largest_win = max((float(t.profit) for t in winning_trades), default=0)
        largest_loss = min((float(t.profit) for t in losing_trades), default=0)

        # Create detailed metrics table
        detailed_data = [
            ['Metric', 'Value'],
            ['Win Rate', f"{win_rate:.2f}%"],
            ['Total Winning Trades', str(len(winning_trades))],
            ['Total Losing Trades', str(len(losing_trades))],
            ['Average Win', f"${avg_win:.2f}"],
            ['Average Loss', f"${avg_loss:.2f}"],
            ['Largest Win', f"${largest_win:.2f}"],
            ['Largest Loss', f"${largest_loss:.2f}"],
            ['Profit Factor', f"{abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "N/A"],
        ]

        detailed_table = Table(detailed_data, colWidths=[3*inch, 2*inch])
        detailed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        elements.append(detailed_table)

        return elements

    def _create_trade_list(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[int],
        limit: int = 50
    ) -> List:
        """Create recent trades list"""
        elements = []

        elements.append(Paragraph("Recent Trades", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))

        # Fetch recent trades
        with get_session() as session:
            from src.database.models import Trade, TradeStatus
            from sqlalchemy import and_

            query_filters = [
                Trade.status == TradeStatus.CLOSED,
                Trade.exit_time >= datetime.combine(start_date, datetime.min.time()),
                Trade.exit_time <= datetime.combine(end_date, datetime.max.time())
            ]

            if account_id:
                query_filters.append(Trade.account_id == account_id)

            trades = session.query(Trade).filter(and_(*query_filters)).order_by(
                Trade.exit_time.desc()
            ).limit(limit).all()

        if not trades:
            elements.append(Paragraph("No trades found.", self.styles['Normal']))
            return elements

        # Create trades table
        trade_data = [['Symbol', 'Type', 'Entry', 'Exit', 'Profit', 'Date']]

        for trade in trades:
            trade_data.append([
                trade.symbol,
                trade.trade_type.value.upper(),
                f"${float(trade.entry_price):.4f}",
                f"${float(trade.exit_price):.4f}" if trade.exit_price else "N/A",
                f"${float(trade.profit):.2f}" if trade.profit else "N/A",
                trade.exit_time.strftime("%Y-%m-%d") if trade.exit_time else "N/A"
            ])

        trades_table = Table(trade_data, colWidths=[1*inch, 0.7*inch, 1*inch, 1*inch, 1*inch, 1.3*inch])
        trades_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64748b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        elements.append(trades_table)
        elements.append(Spacer(1, 0.1*inch))

        if len(trades) == limit:
            note = Paragraph(
                f"<i>Note: Showing most recent {limit} trades only.</i>",
                self.styles['Normal']
            )
            elements.append(note)

        return elements

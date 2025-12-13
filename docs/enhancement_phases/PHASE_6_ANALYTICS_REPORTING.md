# Phase 6: Advanced Analytics & Reporting

**Duration:** 2-3 weeks
**Difficulty:** Intermediate to Advanced
**Focus:** Deep insights into trading performance

---

## Overview

This phase adds sophisticated analytics and automated reporting:
- Advanced performance metrics (Sortino, Calmar, MAE/MFE)
- Strategy comparison and A/B testing
- Daily/weekly/monthly automated reports
- Email and Telegram notifications

---

## 6.1 Trade Analytics Engine

### Skills to Learn:
- Statistical analysis
- Data visualization (Matplotlib, Plotly)
- Performance metrics calculation
- Comparative analysis

### Tasks Checklist:

- [ ] **Advanced Performance Metrics**
  - [ ] Sortino ratio (downside deviation focus)
  - [ ] Calmar ratio (return/max drawdown)
  - [ ] Omega ratio (probability-weighted)
  - [ ] Tail ratio (95th/5th percentile)
  - [ ] Maximum Adverse Excursion (MAE)
  - [ ] Maximum Favorable Excursion (MFE)

- [ ] **Strategy Comparison**
  - [ ] Side-by-side performance comparison
  - [ ] Statistical significance testing
  - [ ] Rolling performance windows
  - [ ] Risk-adjusted returns comparison

- [ ] **Trade Quality Analysis**
  - [ ] MAE/MFE scatter plots
  - [ ] Optimal SL/TP identification
  - [ ] Entry quality scoring
  - [ ] Exit quality scoring

### Files to Create:

```
src/analysis/
├── __init__.py
├── advanced_metrics.py       # Advanced trading metrics
├── strategy_comparison.py    # Compare strategy performance
├── correlation_analysis.py   # Currency pair correlations
└── trade_quality.py          # MAE/MFE analysis
```

### Implementation:

#### 1. Advanced Metrics Calculator

```python
# src/analysis/advanced_metrics.py
import numpy as np
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class AdvancedMetricsResult:
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    tail_ratio: float
    common_sense_ratio: float
    avg_mae: float
    avg_mfe: float
    mae_mfe_ratio: float
    max_consecutive_losses: int
    max_consecutive_wins: int
    profit_factor: float

class AdvancedMetrics:
    """Calculate advanced trading performance metrics"""

    @staticmethod
    def calculate_sortino_ratio(returns: List[float],
                                 target_return: float = 0.0,
                                 periods_per_year: int = 252) -> float:
        """
        Sortino Ratio - Like Sharpe but only penalizes downside volatility

        Formula: (Mean Return - Target) / Downside Deviation
        Higher is better, focuses on harmful volatility
        """
        excess_returns = np.array(returns) - target_return
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return float('inf')

        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0.0

        return (np.mean(excess_returns) / downside_std) * np.sqrt(periods_per_year)

    @staticmethod
    def calculate_calmar_ratio(returns: List[float],
                                max_drawdown: float,
                                periods_per_year: int = 252) -> float:
        """
        Calmar Ratio - Annual return divided by maximum drawdown

        Measures reward per unit of drawdown risk
        Higher is better
        """
        if max_drawdown == 0:
            return 0.0

        annual_return = np.mean(returns) * periods_per_year
        return annual_return / abs(max_drawdown)

    @staticmethod
    def calculate_omega_ratio(returns: List[float],
                               threshold: float = 0.0) -> float:
        """
        Omega Ratio - Probability weighted ratio of gains vs losses

        Formula: Sum(returns > threshold) / Sum(|returns < threshold|)
        Higher is better, >1 means more gains than losses
        """
        gains = sum(r - threshold for r in returns if r > threshold)
        losses = abs(sum(r - threshold for r in returns if r < threshold))

        if losses == 0:
            return float('inf') if gains > 0 else 0.0

        return gains / losses

    @staticmethod
    def calculate_tail_ratio(returns: List[float],
                              percentile: float = 5.0) -> float:
        """
        Tail Ratio - 95th percentile / 5th percentile

        Measures the ratio of right tail (gains) to left tail (losses)
        Higher is better
        """
        right_tail = np.percentile(returns, 100 - percentile)
        left_tail = abs(np.percentile(returns, percentile))

        if left_tail == 0:
            return float('inf')

        return right_tail / left_tail

    @staticmethod
    def calculate_profit_factor(trades: List[Dict]) -> float:
        """
        Profit Factor - Gross profit / Gross loss

        >1 means profitable, >2 is good, >3 is excellent
        """
        gross_profit = sum(t['profit'] for t in trades if t['profit'] > 0)
        gross_loss = abs(sum(t['profit'] for t in trades if t['profit'] < 0))

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    @staticmethod
    def calculate_mae_mfe(trades: List[Dict]) -> Dict[str, float]:
        """
        Maximum Adverse/Favorable Excursion

        Shows worst drawdown and best run-up during trades
        Helps identify optimal SL/TP levels
        """
        mae_values = []
        mfe_values = []

        for trade in trades:
            # Calculate worst point during trade (MAE)
            mae = trade.get('worst_drawdown_pct', 0)
            # Calculate best point during trade (MFE)
            mfe = trade.get('best_runup_pct', 0)

            mae_values.append(abs(mae))
            mfe_values.append(mfe)

        if not mae_values or not mfe_values:
            return {
                'avg_mae': 0,
                'avg_mfe': 0,
                'mae_mfe_ratio': 0,
                'percentile_95_mfe': 0,
                'percentile_5_mae': 0
            }

        avg_mae = np.mean(mae_values)
        avg_mfe = np.mean(mfe_values)

        return {
            'avg_mae': avg_mae,
            'avg_mfe': avg_mfe,
            'mae_mfe_ratio': avg_mfe / avg_mae if avg_mae > 0 else 0,
            'percentile_95_mfe': np.percentile(mfe_values, 95),
            'percentile_5_mae': np.percentile(mae_values, 5)
        }

    @staticmethod
    def calculate_consecutive_streaks(trades: List[Dict]) -> tuple:
        """Calculate max consecutive wins and losses"""
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in sorted(trades, key=lambda t: t['entry_time']):
            if trade['profit'] > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    @classmethod
    def calculate_all(cls, returns: List[float],
                     trades: List[Dict],
                     max_drawdown: float) -> AdvancedMetricsResult:
        """Calculate all advanced metrics at once"""
        mae_mfe = cls.calculate_mae_mfe(trades)
        max_wins, max_losses = cls.calculate_consecutive_streaks(trades)

        return AdvancedMetricsResult(
            sortino_ratio=cls.calculate_sortino_ratio(returns),
            calmar_ratio=cls.calculate_calmar_ratio(returns, max_drawdown),
            omega_ratio=cls.calculate_omega_ratio(returns),
            tail_ratio=cls.calculate_tail_ratio(returns),
            common_sense_ratio=cls.calculate_tail_ratio(returns, percentile=10),
            avg_mae=mae_mfe['avg_mae'],
            avg_mfe=mae_mfe['avg_mfe'],
            mae_mfe_ratio=mae_mfe['mae_mfe_ratio'],
            max_consecutive_losses=max_losses,
            max_consecutive_wins=max_wins,
            profit_factor=cls.calculate_profit_factor(trades)
        )
```

#### 2. Strategy Comparison Tool

```python
# src/analysis/strategy_comparison.py
import pandas as pd
import numpy as np
from typing import List, Dict
from scipy import stats

class StrategyComparison:
    """Compare performance of multiple strategies"""

    def __init__(self, strategies_data: Dict[str, List[Dict]]):
        """
        Initialize with strategy data

        Args:
            strategies_data: Dict mapping strategy name to list of trades
        """
        self.strategies = strategies_data
        self.results = {}

    def compare_all(self) -> pd.DataFrame:
        """Compare all strategies side-by-side"""
        comparison = []

        for name, trades in self.strategies.items():
            if not trades:
                continue

            returns = [t['profit'] for t in trades]
            winners = sum(1 for r in returns if r > 0)

            comparison.append({
                'Strategy': name,
                'Total Trades': len(trades),
                'Win Rate %': (winners / len(trades) * 100) if trades else 0,
                'Total Profit': sum(returns),
                'Avg Profit': np.mean(returns),
                'Std Dev': np.std(returns),
                'Sharpe Ratio': self._calculate_sharpe(returns),
                'Max Drawdown': self._calculate_max_dd(returns),
                'Profit Factor': self._calculate_pf(trades)
            })

        df = pd.DataFrame(comparison)
        df = df.sort_values('Sharpe Ratio', ascending=False)
        return df

    def test_significance(self, strategy_a: str, strategy_b: str) -> Dict:
        """
        Test if difference between two strategies is statistically significant

        Uses t-test to compare means
        """
        trades_a = self.strategies.get(strategy_a, [])
        trades_b = self.strategies.get(strategy_b, [])

        if not trades_a or not trades_b:
            return {'error': 'Insufficient data'}

        returns_a = [t['profit'] for t in trades_a]
        returns_b = [t['profit'] for t in trades_b]

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(returns_a, returns_b)

        return {
            'strategy_a': strategy_a,
            'strategy_b': strategy_b,
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'mean_diff': np.mean(returns_a) - np.mean(returns_b),
            'interpretation': 'Significant difference' if p_value < 0.05 else 'No significant difference'
        }

    def _calculate_sharpe(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not returns or np.std(returns) == 0:
            return 0.0
        return (np.mean(returns) / np.std(returns)) * np.sqrt(252)

    def _calculate_max_dd(self, returns: List[float]) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        return np.max(drawdown) if len(drawdown) > 0 else 0

    def _calculate_pf(self, trades: List[Dict]) -> float:
        """Calculate profit factor"""
        profits = sum(t['profit'] for t in trades if t['profit'] > 0)
        losses = abs(sum(t['profit'] for t in trades if t['profit'] < 0))
        return profits / losses if losses > 0 else float('inf')
```

---

## 6.2 Automated Reporting

### Skills to Learn:
- Report generation (HTML, PDF)
- Email automation (SMTP)
- Telegram bot integration
- Template engines (Jinja2)
- Chart generation (Matplotlib)

### Tasks Checklist:

- [ ] **Daily Performance Reports**
  - [ ] Generate HTML reports
  - [ ] Create equity curve charts
  - [ ] Send via email
  - [ ] Send via Telegram

- [ ] **Weekly/Monthly Analysis**
  - [ ] Comprehensive performance review
  - [ ] Strategy effectiveness analysis
  - [ ] Risk exposure breakdown
  - [ ] Recommendations section

- [ ] **Real-time Notifications**
  - [ ] Trade execution alerts
  - [ ] Large loss warnings
  - [ ] Milestone achievements
  - [ ] System errors

### Files to Create:

```
src/reporting/
├── __init__.py
├── report_generator.py       # Generate reports
├── email_notifier.py         # Email reports
├── telegram_notifier.py      # Telegram notifications
└── templates/
    ├── daily_report.html     # HTML email template
    └── monthly_report.html   # Monthly summary
```

### Implementation:

#### 1. Report Generator

```python
# src/reporting/report_generator.py
from jinja2 import Template
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import os

class DailyReport:
    """Generate comprehensive daily trading reports"""

    def __init__(self, trades: List[Dict], metrics: Dict):
        self.trades = trades
        self.metrics = metrics
        self.date = datetime.now()

    def generate_html(self) -> str:
        """Generate HTML report"""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }
                h2 {
                    color: #34495e;
                    margin-top: 30px;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 15px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background-color: #3498db;
                    color: white;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                tr:hover {
                    background-color: #f1f1f1;
                }
                .profit { color: #27ae60; font-weight: bold; }
                .loss { color: #e74c3c; font-weight: bold; }
                .summary-box {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .metric {
                    display: inline-block;
                    margin: 15px 30px;
                    text-align: center;
                }
                .metric-label {
                    font-size: 13px;
                    opacity: 0.9;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                .metric-value {
                    font-size: 32px;
                    font-weight: bold;
                    margin-top: 5px;
                }
                .chart-container {
                    margin: 20px 0;
                    text-align: center;
                }
                img {
                    max-width: 100%;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 TradingMTQ Daily Report</h1>
                <p style="color: #7f8c8d; font-size: 14px;">{{ date }}</p>

                <div class="summary-box">
                    <h2 style="margin-top: 0; border: none; color: white;">Daily Summary</h2>
                    <div class="metric">
                        <div class="metric-label">Trades Executed</div>
                        <div class="metric-value">{{ trades_count }}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Win Rate</div>
                        <div class="metric-value">{{ win_rate }}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Total Profit</div>
                        <div class="metric-value" style="color: {{ '#2ecc71' if profit >= 0 else '#e74c3c' }}">
                            ${{ profit }}
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Profit Factor</div>
                        <div class="metric-value">{{ profit_factor }}</div>
                    </div>
                </div>

                <h2>📈 Equity Curve</h2>
                <div class="chart-container">
                    <img src="cid:equity_curve" alt="Equity Curve">
                </div>

                <h2>🏆 Top Performing Trades</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Direction</th>
                            <th>Entry</th>
                            <th>Exit</th>
                            <th>Profit</th>
                            <th>Pips</th>
                            <th>Strategy</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for trade in top_trades %}
                        <tr>
                            <td>{{ trade.entry_time.strftime('%H:%M') }}</td>
                            <td><strong>{{ trade.symbol }}</strong></td>
                            <td>{{ trade.direction }}</td>
                            <td>{{ trade.entry_price }}</td>
                            <td>{{ trade.exit_price }}</td>
                            <td class="{{ 'profit' if trade.profit >= 0 else 'loss' }}">
                                ${{ "%.2f"|format(trade.profit) }}
                            </td>
                            <td>{{ "%.1f"|format(trade.profit_pips) }}</td>
                            <td>{{ trade.strategy }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <h2>💱 Performance by Currency Pair</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Trades</th>
                            <th>Win Rate</th>
                            <th>Total P&L</th>
                            <th>Avg Profit</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for symbol, stats in symbol_stats.items() %}
                        <tr>
                            <td><strong>{{ symbol }}</strong></td>
                            <td>{{ stats.trades }}</td>
                            <td>{{ "%.1f"|format(stats.win_rate) }}%</td>
                            <td class="{{ 'profit' if stats.profit >= 0 else 'loss' }}">
                                ${{ "%.2f"|format(stats.profit) }}
                            </td>
                            <td>${{ "%.2f"|format(stats.avg_profit) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #ecf0f1; color: #95a5a6; font-size: 12px; text-align: center;">
                    <p>Generated by TradingMTQ Automated Trading System</p>
                    <p>{{ date }}</p>
                </div>
            </div>
        </body>
        </html>
        """)

        symbol_stats = self._calculate_symbol_stats()

        return template.render(
            date=self.date.strftime('%A, %B %d, %Y'),
            trades_count=len(self.trades),
            win_rate=self._calculate_win_rate(),
            profit=sum(t['profit'] for t in self.trades),
            profit_factor=self._calculate_profit_factor(),
            top_trades=sorted(self.trades, key=lambda t: t['profit'], reverse=True)[:10],
            symbol_stats=symbol_stats
        )

    def _calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if not self.trades:
            return 0.0
        winning = sum(1 for t in self.trades if t['profit'] > 0)
        return round(winning / len(self.trades) * 100, 1)

    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        profits = sum(t['profit'] for t in self.trades if t['profit'] > 0)
        losses = abs(sum(t['profit'] for t in self.trades if t['profit'] < 0))

        if losses == 0:
            return float('inf') if profits > 0 else 0.0

        return round(profits / losses, 2)

    def _calculate_symbol_stats(self) -> Dict:
        """Calculate statistics per currency pair"""
        df = pd.DataFrame(self.trades)
        if df.empty:
            return {}

        stats = {}
        for symbol in df['symbol'].unique():
            symbol_trades = df[df['symbol'] == symbol]
            winning = (symbol_trades['profit'] > 0).sum()

            stats[symbol] = {
                'trades': len(symbol_trades),
                'win_rate': round(winning / len(symbol_trades) * 100, 1) if len(symbol_trades) > 0 else 0,
                'profit': round(symbol_trades['profit'].sum(), 2),
                'avg_profit': round(symbol_trades['profit'].mean(), 2)
            }

        return stats

    def generate_equity_curve_chart(self, filepath: str = 'equity_curve.png'):
        """Generate equity curve chart"""
        if not self.trades:
            return

        df = pd.DataFrame(self.trades)
        df = df.sort_values('entry_time')
        df['cumulative_profit'] = df['profit'].cumsum()

        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot equity curve
        ax.plot(df['entry_time'], df['cumulative_profit'],
                linewidth=2.5, color='#3498db', label='Cumulative Profit')

        # Fill area under curve
        ax.fill_between(df['entry_time'], 0, df['cumulative_profit'],
                        alpha=0.2, color='#3498db')

        # Zero line
        ax.axhline(y=0, color='#e74c3c', linestyle='--', alpha=0.5, linewidth=1.5)

        # Formatting
        ax.set_title('Daily Equity Curve', fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax.set_ylabel('Cumulative Profit ($)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
        ax.legend(loc='upper left', fontsize=11)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

    def save_to_file(self, filepath: str):
        """Save HTML report to file"""
        html = self.generate_html()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ Report saved to {filepath}")
```

#### 2. Email Notifier

```python
# src/reporting/email_notifier.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import List
import os
from datetime import datetime

class EmailNotifier:
    """Send email notifications with trading reports"""

    def __init__(self, smtp_host: str, smtp_port: int,
                 username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_daily_report(self, recipients: List[str],
                         html_content: str,
                         chart_path: str = None):
        """Send daily report email with embedded chart"""
        msg = MIMEMultipart('related')
        msg['Subject'] = f'📊 TradingMTQ Daily Report - {datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = self.username
        msg['To'] = ', '.join(recipients)

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Attach chart image if exists
        if chart_path and os.path.exists(chart_path):
            with open(chart_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<equity_curve>')
                img.add_header('Content-Disposition', 'inline', filename='equity_curve.png')
                msg.attach(img)

        # Send email
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                print(f"✅ Email sent to {', '.join(recipients)}")
                return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    def send_alert(self, recipients: List[str], subject: str, message: str):
        """Send simple text alert"""
        msg = MIMEText(message)
        msg['Subject'] = f'⚠️ TradingMTQ Alert - {subject}'
        msg['From'] = self.username
        msg['To'] = ', '.join(recipients)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                return True
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")
            return False
```

#### 3. Telegram Notifier

```python
# src/reporting/telegram_notifier.py
import requests
from typing import Optional
from datetime import datetime

class TelegramNotifier:
    """Send Telegram notifications for trading events"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = 'HTML'):
        """Send text message"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    def send_trade_notification(self, trade: dict):
        """Send notification when trade is executed"""
        profit_emoji = "🟢" if trade['profit'] >= 0 else "🔴"
        direction_emoji = "🔼" if trade['direction'] == 'BUY' else "🔽"

        message = f"""
{profit_emoji} <b>Trade Closed</b>

{direction_emoji} <b>Symbol:</b> {trade['symbol']}
<b>Direction:</b> {trade['direction']}
<b>Entry:</b> {trade['entry_price']:.5f}
<b>Exit:</b> {trade['exit_price']:.5f}
<b>Profit:</b> ${trade['profit']:.2f} ({trade.get('profit_pips', 0):.1f} pips)
<b>Strategy:</b> {trade['strategy']}

<i>Time: {trade['entry_time'].strftime('%H:%M:%S')}</i>
        """

        self.send_message(message.strip())

    def send_daily_summary(self, stats: dict):
        """Send end-of-day summary"""
        profit_emoji = "💚" if stats['profit'] >= 0 else "❤️"

        message = f"""
📊 <b>Daily Summary - {stats['date']}</b>

{profit_emoji} <b>Profit:</b> ${stats['profit']:.2f}
📈 <b>Trades:</b> {stats['trades']}
✅ <b>Win Rate:</b> {stats['win_rate']:.1f}%
💪 <b>Profit Factor:</b> {stats['profit_factor']:.2f}

<b>Best Trade:</b> ${stats['best_trade']:.2f}
<b>Worst Trade:</b> ${stats['worst_trade']:.2f}
<b>Max Drawdown:</b> {stats['max_dd']:.2f}%

<i>Great job today! 🚀</i>
        """

        self.send_message(message.strip())

    def send_alert(self, alert_type: str, message: str):
        """Send alert notification"""
        emoji_map = {
            'error': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅'
        }

        emoji = emoji_map.get(alert_type, '📢')

        alert_message = f"""
{emoji} <b>Alert: {alert_type.upper()}</b>

{message}

<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
        """

        self.send_message(alert_message.strip())
```

---

## Integration Example

### Complete Daily Report System:

```python
# scripts/send_daily_report.py
from src.reporting.report_generator import DailyReport
from src.reporting.email_notifier import EmailNotifier
from src.reporting.telegram_notifier import TelegramNotifier
from src.database.repository import TradeRepository
from datetime import datetime, timedelta
import os

def generate_and_send_daily_report():
    """Generate and send daily report via email and Telegram"""

    # Get today's trades from database
    db = TradeRepository()
    today = datetime.now().date()
    start_time = datetime.combine(today, datetime.min.time())
    end_time = datetime.combine(today, datetime.max.time())

    trades = db.get_trades_by_date_range(start_time, end_time)

    if not trades:
        print("No trades today, skipping report")
        return

    # Convert to dict format
    trades_dict = [{
        'symbol': t.symbol,
        'direction': t.direction,
        'entry_price': t.entry_price,
        'exit_price': t.exit_price,
        'profit': t.profit,
        'profit_pips': t.profit_pips,
        'entry_time': t.entry_time,
        'strategy': t.strategy_name
    } for t in trades]

    # Generate report
    report = DailyReport(trades_dict, {})

    # Generate HTML
    html = report.generate_html()

    # Generate chart
    chart_path = 'temp/equity_curve.png'
    os.makedirs('temp', exist_ok=True)
    report.generate_equity_curve_chart(chart_path)

    # Save HTML report
    report.save_to_file(f'reports/daily_report_{today}.html')

    # Send via email
    email = EmailNotifier(
        smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('SMTP_PORT', 587)),
        username=os.getenv('EMAIL_USERNAME'),
        password=os.getenv('EMAIL_PASSWORD')
    )

    recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
    email.send_daily_report(recipients, html, chart_path)

    # Send summary via Telegram
    telegram = TelegramNotifier(
        bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_id=os.getenv('TELEGRAM_CHAT_ID')
    )

    total_profit = sum(t['profit'] for t in trades_dict)
    winners = sum(1 for t in trades_dict if t['profit'] > 0)

    telegram.send_daily_summary({
        'date': today.strftime('%Y-%m-%d'),
        'trades': len(trades_dict),
        'profit': total_profit,
        'win_rate': (winners / len(trades_dict) * 100) if trades_dict else 0,
        'profit_factor': report._calculate_profit_factor(),
        'best_trade': max(t['profit'] for t in trades_dict),
        'worst_trade': min(t['profit'] for t in trades_dict),
        'max_dd': 0  # Calculate from equity curve
    })

    print("✅ Daily report sent successfully!")

if __name__ == '__main__':
    generate_and_send_daily_report()
```

---

## Configuration (.env additions):

```env
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENTS=recipient1@email.com,recipient2@email.com

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

---

## Testing Checklist

- [ ] Generate sample report with test data
- [ ] Verify HTML renders correctly in email clients
- [ ] Test email delivery to multiple recipients
- [ ] Test Telegram bot sends messages
- [ ] Verify charts are properly embedded
- [ ] Test with zero trades (edge case)
- [ ] Verify performance metrics are accurate
- [ ] Schedule daily report (cron job)

---

## Expected Outcomes

After Phase 6, you will have:

1. **Comprehensive Analytics**
   - Advanced metrics (Sortino, Calmar, MAE/MFE)
   - Strategy comparison tools
   - Trade quality analysis

2. **Automated Reporting**
   - Daily HTML email reports
   - Telegram notifications
   - Real-time trade alerts

3. **Better Decision Making**
   - Data-driven strategy selection
   - Identify optimal SL/TP levels
   - Track performance trends

---

## Next Steps

Continue to **Phase 7: Web Dashboard & REST API** for visual monitoring!

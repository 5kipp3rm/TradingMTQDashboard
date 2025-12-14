/**
 * Advanced Charts for TradingMTQ Dashboard
 */

const API_URL = 'http://localhost:8000/api';
const charts = {};

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Load data for the tab if not already loaded
    switch(tabName) {
        case 'equity':
            if (!charts.equity) loadEquityCurve();
            break;
        case 'distribution':
            if (!charts.heatmap) loadTradeDistribution();
            break;
        case 'performance':
            if (!charts.symbolWinRate) loadSymbolPerformance();
            break;
        case 'analysis':
            if (!charts.profitDist) loadWinLossAnalysis();
            if (!charts.monthly) loadMonthlyComparison();
            break;
        case 'risk':
            if (!charts.riskReward) loadRiskReward();
            break;
    }
}

/**
 * Load Equity Curve
 */
async function loadEquityCurve() {
    const granularity = document.getElementById('equityGranularity').value;
    const days = document.getElementById('equityPeriod').value;
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    try {
        const response = await fetch(
            `${API_URL}/charts/equity-curve?start_date=${startDate}&end_date=${endDate}&granularity=${granularity}`
        );
        const data = await response.json();

        const ctx = document.getElementById('equityChart').getContext('2d');

        if (charts.equity) {
            charts.equity.destroy();
        }

        const labels = data.data.map(d => d.date);
        const balances = data.data.map(d => d.balance || d.cumulative_profit);
        const cumProfits = data.data.map(d => d.cumulative_profit);

        charts.equity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Balance',
                    data: balances,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    fill: true,
                    tension: 0.1
                }, {
                    label: 'Cumulative Profit',
                    data: cumProfits,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: granularity === 'daily' ? 'Date' : 'Trade #'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Value ($)'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    } catch (error) {
        console.error('Failed to load equity curve:', error);
    }
}

/**
 * Load Trade Distribution Heatmap
 */
async function loadTradeDistribution() {
    const days = document.getElementById('heatmapPeriod').value;
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    try {
        const response = await fetch(
            `${API_URL}/charts/trade-distribution?start_date=${startDate}&end_date=${endDate}`
        );
        const data = await response.json();

        const ctx = document.getElementById('heatmapChart').getContext('2d');

        if (charts.heatmap) {
            charts.heatmap.destroy();
        }

        // Create matrix data for heatmap
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const hours = Array.from({length: 24}, (_, i) => `${i}:00`);

        // Build data matrix
        const matrix = {};
        dayNames.forEach(day => {
            matrix[day] = Array(24).fill(0);
        });

        data.data.forEach(item => {
            matrix[item.day][item.hour] = item.avg_profit;
        });

        // Flatten for chart
        const chartData = [];
        dayNames.forEach((day, dayIndex) => {
            hours.forEach((hour, hourIndex) => {
                chartData.push({
                    x: hourIndex,
                    y: dayIndex,
                    v: matrix[day][hourIndex]
                });
            });
        });

        charts.heatmap = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Average Profit',
                    data: chartData,
                    backgroundColor: function(context) {
                        const value = context.raw.v;
                        if (value > 0) {
                            const intensity = Math.min(Math.abs(value) / 50, 1);
                            return `rgba(75, 192, 192, ${intensity})`;
                        } else {
                            const intensity = Math.min(Math.abs(value) / 50, 1);
                            return `rgba(255, 99, 132, ${intensity})`;
                        }
                    },
                    borderColor: 'rgba(0, 0, 0, 0.1)',
                    pointRadius: 15,
                    pointHoverRadius: 20
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const hour = hours[context.raw.x];
                                const day = dayNames[context.raw.y];
                                const profit = context.raw.v.toFixed(2);
                                return `${day} ${hour}: $${profit}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        min: 0,
                        max: 23,
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return `${value}:00`;
                            }
                        },
                        title: {
                            display: true,
                            text: 'Hour of Day'
                        }
                    },
                    y: {
                        type: 'linear',
                        min: 0,
                        max: 6,
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return dayNames[value];
                            }
                        },
                        title: {
                            display: true,
                            text: 'Day of Week'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load trade distribution:', error);
    }
}

/**
 * Load Symbol Performance
 */
async function loadSymbolPerformance() {
    const days = document.getElementById('symbolPeriod').value;
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    try {
        const response = await fetch(
            `${API_URL}/charts/symbol-performance?start_date=${startDate}&end_date=${endDate}&limit=10`
        );
        const data = await response.json();

        const symbols = data.symbols.map(s => s.symbol);
        const winRates = data.symbols.map(s => s.win_rate);
        const profits = data.symbols.map(s => s.net_profit);
        const trades = data.symbols.map(s => s.total_trades);

        // Win Rate Chart
        const winRateCtx = document.getElementById('symbolWinRateChart').getContext('2d');
        if (charts.symbolWinRate) charts.symbolWinRate.destroy();

        charts.symbolWinRate = new Chart(winRateCtx, {
            type: 'bar',
            data: {
                labels: symbols,
                datasets: [{
                    label: 'Win Rate (%)',
                    data: winRates,
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Win Rate (%)'
                        }
                    }
                }
            }
        });

        // Profit Chart
        const profitCtx = document.getElementById('symbolProfitChart').getContext('2d');
        if (charts.symbolProfit) charts.symbolProfit.destroy();

        charts.symbolProfit = new Chart(profitCtx, {
            type: 'bar',
            data: {
                labels: symbols,
                datasets: [{
                    label: 'Net Profit ($)',
                    data: profits,
                    backgroundColor: profits.map(p => p >= 0 ? 'rgba(75, 192, 192, 0.5)' : 'rgba(255, 99, 132, 0.5)'),
                    borderColor: profits.map(p => p >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Net Profit ($)'
                        }
                    }
                }
            }
        });

        // Comparison Chart
        const comparisonCtx = document.getElementById('symbolComparisonChart').getContext('2d');
        if (charts.symbolComparison) charts.symbolComparison.destroy();

        charts.symbolComparison = new Chart(comparisonCtx, {
            type: 'bar',
            data: {
                labels: symbols,
                datasets: [{
                    label: 'Total Trades',
                    data: trades,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                }, {
                    label: 'Net Profit ($)',
                    data: profits,
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Number of Trades'
                        }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Net Profit ($)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load symbol performance:', error);
    }
}

/**
 * Load Win/Loss Analysis
 */
async function loadWinLossAnalysis() {
    const days = 90;
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    try {
        const response = await fetch(
            `${API_URL}/charts/win-loss-analysis?start_date=${startDate}&end_date=${endDate}`
        );
        const data = await response.json();

        // Profit Distribution
        const profitDistCtx = document.getElementById('profitDistChart').getContext('2d');
        if (charts.profitDist) charts.profitDist.destroy();

        const labels = Object.keys(data.profit_distribution);
        const values = Object.values(data.profit_distribution);

        charts.profitDist = new Chart(profitDistCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Number of Trades',
                    data: values,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Profit Range ($)'
                        }
                    }
                }
            }
        });

        // Duration Chart
        const durationCtx = document.getElementById('durationChart').getContext('2d');
        if (charts.duration) charts.duration.destroy();

        const durationLabels = Object.keys(data.duration_analysis);
        const durationValues = Object.values(data.duration_analysis);

        charts.duration = new Chart(durationCtx, {
            type: 'doughnut',
            data: {
                labels: durationLabels,
                datasets: [{
                    data: durationValues,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(153, 102, 255, 0.5)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load win/loss analysis:', error);
    }
}

/**
 * Load Monthly Comparison
 */
async function loadMonthlyComparison() {
    const months = document.getElementById('monthlyPeriod').value;

    try {
        const response = await fetch(
            `${API_URL}/charts/monthly-comparison?months=${months}`
        );
        const data = await response.json();

        const ctx = document.getElementById('monthlyChart').getContext('2d');
        if (charts.monthly) charts.monthly.destroy();

        const labels = data.data.map(d => d.month_name);
        const profits = data.data.map(d => d.net_profit);
        const winRates = data.data.map(d => d.avg_win_rate);

        charts.monthly = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Net Profit ($)',
                    data: profits,
                    backgroundColor: profits.map(p => p >= 0 ? 'rgba(75, 192, 192, 0.5)' : 'rgba(255, 99, 132, 0.5)'),
                    borderColor: profits.map(p => p >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)'),
                    borderWidth: 1,
                    yAxisID: 'y'
                }, {
                    label: 'Win Rate (%)',
                    data: winRates,
                    type: 'line',
                    borderColor: 'rgba(255, 206, 86, 1)',
                    backgroundColor: 'rgba(255, 206, 86, 0.1)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Net Profit ($)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        min: 0,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Win Rate (%)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load monthly comparison:', error);
    }
}

/**
 * Load Risk/Reward Scatter
 */
async function loadRiskReward() {
    const days = document.getElementById('riskPeriod').value;
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    try {
        const response = await fetch(
            `${API_URL}/charts/risk-reward-scatter?start_date=${startDate}&end_date=${endDate}&limit=200`
        );
        const data = await response.json();

        const ctx = document.getElementById('riskRewardChart').getContext('2d');
        if (charts.riskReward) charts.riskReward.destroy();

        const wins = data.data.filter(d => d.outcome === 'win');
        const losses = data.data.filter(d => d.outcome === 'loss');

        charts.riskReward = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Winning Trades',
                    data: wins.map(d => ({x: d.risk, y: d.reward})),
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)'
                }, {
                    label: 'Losing Trades',
                    data: losses.map(d => ({x: d.risk, y: d.reward})),
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const trade = data.data[context.dataIndex];
                                return [
                                    `Symbol: ${trade.symbol}`,
                                    `Risk: ${trade.risk.toFixed(5)}`,
                                    `Reward: ${trade.reward.toFixed(5)}`,
                                    `R:R Ratio: ${trade.risk_reward_ratio}`,
                                    `Profit: $${trade.profit.toFixed(2)}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Risk (pips)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Reward (pips)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load risk/reward scatter:', error);
    }
}

// Initialize first tab on page load
document.addEventListener('DOMContentLoaded', function() {
    loadEquityCurve();
});

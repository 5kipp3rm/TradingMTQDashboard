/**
 * Dashboard Controller
 */

class Dashboard {
    constructor() {
        this.charts = {};
        this.currentPeriod = 30;
        this.isConnected = false;
        this.wsConnected = false;

        this.initializeElements();
        this.attachEventListeners();
        this.initializeAccountManager();
        this.initializeWebSocket();
        this.checkAPIHealth();
        this.loadDashboard();

        // Auto-refresh every 60 seconds (backup to WebSocket updates)
        setInterval(() => this.loadDashboard(), 60000);
    }

    /**
     * Initialize account manager integration
     */
    async initializeAccountManager() {
        // Wait for account manager to be ready
        if (typeof accountManager !== 'undefined') {
            await accountManager.init();
            accountManager.renderAccountSelector('accountSelectorContainer');

            // Listen for account changes
            window.addEventListener('accountChanged', () => {
                this.loadDashboard();
            });
        }
    }

    /**
     * Initialize DOM element references
     */
    initializeElements() {
        this.elements = {
            // Status
            statusDot: document.getElementById('statusDot'),
            statusText: document.getElementById('statusText'),
            lastUpdate: document.getElementById('lastUpdate'),

            // Summary Cards
            totalTrades: document.getElementById('totalTrades'),
            netProfit: document.getElementById('netProfit'),
            winRate: document.getElementById('winRate'),
            avgDailyProfit: document.getElementById('avgDailyProfit'),

            // Controls
            periodSelect: document.getElementById('periodSelect'),
            refreshBtn: document.getElementById('refreshBtn'),
            exportBtn: document.getElementById('exportBtn'),

            // Tables
            tradesTableBody: document.getElementById('tradesTableBody'),
            dailyTableBody: document.getElementById('dailyTableBody'),

            // Charts
            profitChart: document.getElementById('profitChart'),
            winRateChart: document.getElementById('winRateChart'),
        };
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        this.elements.periodSelect.addEventListener('change', (e) => {
            this.currentPeriod = parseInt(e.target.value);
            this.loadDashboard();
        });

        this.elements.refreshBtn.addEventListener('click', () => {
            this.loadDashboard();
        });

        this.elements.exportBtn.addEventListener('click', () => {
            this.exportToCSV();
        });
    }

    /**
     * Initialize WebSocket connection for real-time updates
     */
    initializeWebSocket() {
        // Register connection state listener
        wsClient.onConnection((state, data) => {
            this.handleWebSocketStateChange(state, data);
        });

        // Register message handlers
        wsClient.on('connection', (message) => {
            console.log('[Dashboard] WebSocket connected:', message);
            this.wsConnected = true;
            this.updateStatus(true, 'Connected (Live)');
        });

        wsClient.on('trade_event', (message) => {
            console.log('[Dashboard] Trade event:', message);
            this.handleTradeEvent(message);
        });

        wsClient.on('performance_update', (message) => {
            console.log('[Dashboard] Performance update:', message);
            this.handlePerformanceUpdate(message);
        });

        wsClient.on('system_event', (message) => {
            console.log('[Dashboard] System event:', message);
            this.handleSystemEvent(message);
        });

        wsClient.on('heartbeat', (message) => {
            // Silent heartbeat handling
            this.updateLastUpdate();
        });

        wsClient.on('pong', (message) => {
            console.log('[Dashboard] Pong received');
        });

        // Connect to WebSocket
        wsClient.connect();
    }

    /**
     * Handle WebSocket state changes
     */
    handleWebSocketStateChange(state, data) {
        switch (state) {
            case 'connected':
                this.wsConnected = true;
                this.updateStatus(true, 'Connected (Live)');
                break;

            case 'disconnected':
                this.wsConnected = false;
                this.updateStatus(true, 'Connected (Polling)');
                break;

            case 'reconnecting':
                this.updateStatus(true, `Reconnecting (${data.attempt})`);
                break;

            case 'error':
                console.error('[Dashboard] WebSocket error:', data);
                break;

            case 'max_reconnect_attempts':
                this.updateStatus(false, 'Connection Failed');
                break;
        }
    }

    /**
     * Handle trade event from WebSocket
     */
    handleTradeEvent(message) {
        const event = message.event;
        const trade = message.data;

        // Show notification
        this.showNotification(`Trade ${event}: ${trade.symbol}`, trade.profit >= 0 ? 'success' : 'danger');

        // Reload dashboard data
        this.loadDashboard();
    }

    /**
     * Handle performance update from WebSocket
     */
    handlePerformanceUpdate(message) {
        const data = message.data;

        // Update summary cards without full reload
        if (data.total_trades !== undefined) {
            this.elements.totalTrades.textContent = this.formatNumber(data.total_trades);
        }
        if (data.net_profit !== undefined) {
            this.elements.netProfit.textContent = this.formatCurrency(data.net_profit);
            this.elements.netProfit.className = 'metric-value ' + (data.net_profit >= 0 ? 'positive' : 'negative');
        }
        if (data.win_rate !== undefined) {
            this.elements.winRate.textContent = this.formatPercentage(data.win_rate);
            this.elements.winRate.className = 'metric-value ' + (data.win_rate >= 50 ? 'positive' : 'negative');
        }

        this.updateLastUpdate();
    }

    /**
     * Handle system event from WebSocket
     */
    handleSystemEvent(message) {
        const event = message.event;
        const data = message.data;

        console.log(`[Dashboard] System event: ${event}`, data);

        // Show notification for important events
        if (event === 'aggregation_complete') {
            this.showNotification('Daily aggregation completed', 'success');
            this.loadDashboard();
        }
    }

    /**
     * Check API Health
     */
    async checkAPIHealth() {
        try {
            const health = await api.getHealth();
            this.updateStatus(true, 'Connected');
            this.isConnected = true;
        } catch (error) {
            this.updateStatus(false, 'Disconnected');
            this.isConnected = false;
            console.error('API Health Check Failed:', error);
        }
    }

    /**
     * Update status indicator
     */
    updateStatus(isConnected, text) {
        this.elements.statusDot.className = 'status-dot ' + (isConnected ? 'connected' : 'error');
        this.elements.statusText.textContent = text;
    }

    /**
     * Update last update timestamp
     */
    updateLastUpdate() {
        const now = new Date();
        this.elements.lastUpdate.textContent = `Last updated: ${now.toLocaleTimeString()}`;
    }

    /**
     * Load all dashboard data
     */
    async loadDashboard() {
        if (!this.isConnected) {
            await this.checkAPIHealth();
            if (!this.isConnected) return;
        }

        try {
            this.updateStatus(true, 'Loading...');

            // Load data in parallel
            await Promise.all([
                this.loadSummary(),
                this.loadMetrics(),
                this.loadTrades(),
                this.loadDailyPerformance(),
            ]);

            this.updateStatus(true, 'Connected');
            this.updateLastUpdate();
        } catch (error) {
            this.updateStatus(false, 'Error loading data');
            console.error('Dashboard Load Error:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    /**
     * Load summary statistics
     */
    async loadSummary() {
        try {
            const accountId = typeof accountManager !== 'undefined' ? accountManager.currentAccountId : null;

            // Use aggregated analytics if "All Accounts" is selected (accountId is null)
            let data;
            if (accountId === null) {
                // Load aggregated performance across all accounts
                data = await api.getAggregatePerformance(this.currentPeriod);
            } else {
                // Load single account summary
                data = await api.getSummary(this.currentPeriod, accountId);
            }

            // Update summary cards
            this.elements.totalTrades.textContent = this.formatNumber(data.total_trades || 0);

            const netProfit = data.total_profit || data.net_profit || 0;
            this.elements.netProfit.textContent = this.formatCurrency(netProfit);
            this.elements.netProfit.className = 'metric-value ' + (netProfit >= 0 ? 'positive' : 'negative');

            // Calculate win rate from summary data
            let winRate = 0;
            if (data.total_trades && data.total_trades > 0) {
                const winningTrades = data.winning_trades || (data.winning_days || 0);
                winRate = (winningTrades / data.total_trades * 100);
            }
            // For aggregated performance, win_rate is already calculated
            if (data.win_rate !== undefined) {
                winRate = data.win_rate;
            }
            this.elements.winRate.textContent = this.formatPercentage(winRate);
            this.elements.winRate.className = 'metric-value ' + (winRate >= 50 ? 'positive' : 'negative');

            const avgProfit = data.average_daily_profit || 0;
            this.elements.avgDailyProfit.textContent = this.formatCurrency(avgProfit);
            this.elements.avgDailyProfit.className = 'metric-value ' + (avgProfit >= 0 ? 'positive' : 'negative');

        } catch (error) {
            console.error('Summary Load Error:', error);
            this.showError('Failed to load summary data');
        }
    }

    /**
     * Load metrics for charts
     */
    async loadMetrics() {
        try {
            const accountId = typeof accountManager !== 'undefined' ? accountManager.currentAccountId : null;
            const data = await api.getMetrics(this.currentPeriod, accountId);

            // Update Profit Chart
            this.updateProfitChart(data);

            // Update Win Rate Chart
            this.updateWinRateChart(data);

        } catch (error) {
            console.error('Metrics Load Error:', error);
        }
    }

    /**
     * Update cumulative profit chart
     */
    updateProfitChart(data) {
        const ctx = this.elements.profitChart.getContext('2d');

        if (this.charts.profit) {
            this.charts.profit.destroy();
        }

        this.charts.profit = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates || [],
                datasets: [{
                    label: 'Cumulative Profit ($)',
                    data: data.cumulative_profit || [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        labels: { color: '#f1f5f9' }
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            color: '#94a3b8',
                            callback: (value) => '$' + value.toLocaleString()
                        },
                        grid: { color: '#334155' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: '#334155' }
                    }
                }
            }
        });
    }

    /**
     * Update win rate trend chart
     */
    updateWinRateChart(data) {
        const ctx = this.elements.winRateChart.getContext('2d');

        if (this.charts.winRate) {
            this.charts.winRate.destroy();
        }

        this.charts.winRate = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.dates || [],
                datasets: [{
                    label: 'Win Rate (%)',
                    data: data.win_rates || [],
                    backgroundColor: 'rgba(37, 99, 235, 0.6)',
                    borderColor: '#2563eb',
                    borderWidth: 1,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        labels: { color: '#f1f5f9' }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            color: '#94a3b8',
                            callback: (value) => value + '%'
                        },
                        grid: { color: '#334155' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: '#334155' }
                    }
                }
            }
        });
    }

    /**
     * Load recent trades
     */
    async loadTrades() {
        try {
            const data = await api.getTrades({ limit: 50 });
            this.renderTradesTable(data.trades || []);
        } catch (error) {
            console.error('Trades Load Error:', error);
            this.elements.tradesTableBody.innerHTML = '<tr><td colspan="8" class="loading-cell">Failed to load trades</td></tr>';
        }
    }

    /**
     * Render trades table
     */
    renderTradesTable(trades) {
        if (!trades || trades.length === 0) {
            this.elements.tradesTableBody.innerHTML = '<tr><td colspan="8" class="loading-cell">No trades found</td></tr>';
            return;
        }

        this.elements.tradesTableBody.innerHTML = trades.map(trade => `
            <tr>
                <td>${trade.ticket || '-'}</td>
                <td><strong>${trade.symbol}</strong></td>
                <td>${trade.trade_type}</td>
                <td>${this.formatDateTime(trade.entry_time)}</td>
                <td>${trade.exit_time ? this.formatDateTime(trade.exit_time) : '-'}</td>
                <td class="${trade.profit >= 0 ? 'profit' : 'loss'}">
                    ${this.formatCurrency(trade.profit)}
                </td>
                <td>${this.formatNumber(trade.pips, 1)}</td>
                <td><span class="status-badge ${trade.status.toLowerCase()}">${trade.status}</span></td>
            </tr>
        `).join('');
    }

    /**
     * Load daily performance data
     */
    async loadDailyPerformance() {
        try {
            const accountId = typeof accountManager !== 'undefined' ? accountManager.currentAccountId : null;
            const params = { limit: 30 };
            if (accountId) params.accountId = accountId;
            const data = await api.getDailyPerformance(params);
            this.renderDailyTable(data.records || []);
        } catch (error) {
            console.error('Daily Performance Load Error:', error);
            this.elements.dailyTableBody.innerHTML = '<tr><td colspan="7" class="loading-cell">Failed to load daily data</td></tr>';
        }
    }

    /**
     * Render daily performance table
     */
    renderDailyTable(records) {
        if (!records || records.length === 0) {
            this.elements.dailyTableBody.innerHTML = '<tr><td colspan="7" class="loading-cell">No daily data found</td></tr>';
            return;
        }

        this.elements.dailyTableBody.innerHTML = records.map(record => `
            <tr>
                <td><strong>${record.date}</strong></td>
                <td>${record.total_trades}</td>
                <td class="profit">${record.winning_trades}</td>
                <td class="loss">${record.losing_trades}</td>
                <td class="${record.net_profit >= 0 ? 'profit' : 'loss'}">
                    ${this.formatCurrency(record.net_profit)}
                </td>
                <td>${this.formatPercentage(record.win_rate || 0)}</td>
                <td>${this.formatNumber(record.profit_factor || 0, 2)}</td>
            </tr>
        `).join('');
    }

    /**
     * Export trades to CSV
     */
    async exportToCSV() {
        try {
            const data = await api.getTrades({ limit: 1000 });
            const trades = data.trades || [];

            if (trades.length === 0) {
                alert('No trades to export');
                return;
            }

            const csv = this.convertToCSV(trades);
            this.downloadCSV(csv, `trades_${new Date().toISOString().split('T')[0]}.csv`);
        } catch (error) {
            console.error('Export Error:', error);
            alert('Failed to export trades');
        }
    }

    /**
     * Convert data to CSV format
     */
    convertToCSV(data) {
        const headers = ['Ticket', 'Symbol', 'Type', 'Volume', 'Entry Price', 'Exit Price',
                        'Entry Time', 'Exit Time', 'Profit', 'Pips', 'Status'];

        const rows = data.map(trade => [
            trade.ticket,
            trade.symbol,
            trade.trade_type,
            trade.volume,
            trade.entry_price,
            trade.exit_price || '',
            trade.entry_time,
            trade.exit_time || '',
            trade.profit,
            trade.pips,
            trade.status
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        return csvContent;
    }

    /**
     * Download CSV file
     */
    downloadCSV(csv, filename) {
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    /**
     * Format number
     */
    formatNumber(value, decimals = 0) {
        return Number(value).toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    /**
     * Format currency
     */
    formatCurrency(value) {
        return '$' + this.formatNumber(value, 2);
    }

    /**
     * Format percentage
     */
    formatPercentage(value) {
        return this.formatNumber(value, 2) + '%';
    }

    /**
     * Format datetime
     */
    formatDateTime(isoString) {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('Dashboard Error:', message);
        this.showNotification(message, 'danger');
    }

    /**
     * Show notification toast
     */
    showNotification(message, type = 'info') {
        // Simple console notification for now
        // In production, you'd want a proper toast library
        console.log(`[Notification ${type.toUpperCase()}]`, message);

        // You could implement browser notifications here:
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('TradingMTQ', {
                body: message,
                icon: '/favicon.ico'
            });
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

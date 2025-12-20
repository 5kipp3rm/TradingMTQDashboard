/**
 * API Client for TradingMTQ Analytics
 */

// Only declare if not already defined
if (typeof API_BASE_URL === 'undefined') {
    var API_BASE_URL = 'http://localhost:8000/api';
}

class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    /**
     * Make HTTP request to API
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * Health Check
     */
    async getHealth() {
        return this.request('/health');
    }

    /**
     * System Status
     */
    async getStatus() {
        return this.request('/status');
    }

    /**
     * Get Analytics Summary
     */
    async getSummary(days = 30, accountId = null) {
        let url = `/analytics/summary?days=${days}`;
        if (accountId) url += `&account_id=${accountId}`;
        return this.request(url);
    }

    /**
     * Get Daily Performance Records
     */
    async getDailyPerformance(params = {}) {
        const queryParams = new URLSearchParams();

        if (params.startDate) queryParams.append('start_date', params.startDate);
        if (params.endDate) queryParams.append('end_date', params.endDate);
        if (params.limit) queryParams.append('limit', params.limit);
        if (params.accountId) queryParams.append('account_id', params.accountId);

        const query = queryParams.toString();
        return this.request(`/analytics/daily${query ? '?' + query : ''}`);
    }

    /**
     * Get Performance Metrics for Charting
     */
    async getMetrics(days = 30, accountId = null) {
        let url = `/analytics/metrics?days=${days}`;
        if (accountId) url += `&account_id=${accountId}`;
        return this.request(url);
    }

    /**
     * Get Trades List
     */
    async getTrades(params = {}) {
        const queryParams = new URLSearchParams();

        if (params.symbol) queryParams.append('symbol', params.symbol);
        if (params.status) queryParams.append('status', params.status);
        if (params.startDate) queryParams.append('start_date', params.startDate);
        if (params.endDate) queryParams.append('end_date', params.endDate);
        if (params.limit) queryParams.append('limit', params.limit || 50);

        const query = queryParams.toString();
        return this.request(`/trades/${query ? '?' + query : ''}`);
    }

    /**
     * Get Trade by Ticket
     */
    async getTrade(ticket) {
        return this.request(`/trades/${ticket}`);
    }

    /**
     * Get Statistics by Symbol
     */
    async getStatsBySymbol(days = 30) {
        return this.request(`/trades/stats/by-symbol?days=${days}`);
    }

    /**
     * Trigger Manual Aggregation
     */
    async triggerAggregation(date = null) {
        const query = date ? `?target_date=${date}` : '';
        return this.request(`/analytics/aggregate${query}`, {
            method: 'POST',
        });
    }

    /**
     * Get Aggregated Performance across multiple accounts
     */
    async getAggregatePerformance(days = 30, accountIds = null) {
        let url = `/analytics/aggregate?days=${days}`;
        if (accountIds && Array.isArray(accountIds) && accountIds.length > 0) {
            url += `&account_ids=${accountIds.join(',')}`;
        }
        return this.request(url);
    }

    /**
     * Get Account Comparison
     */
    async getAccountComparison(days = 30, accountIds = null) {
        let url = `/analytics/comparison?days=${days}`;
        if (accountIds && Array.isArray(accountIds) && accountIds.length > 0) {
            url += `&account_ids=${accountIds.join(',')}`;
        }
        return this.request(url);
    }

    /**
     * Get Aggregate Summary
     */
    async getAggregateSummary() {
        return this.request('/analytics/summary');
    }

    /**
     * Get Aggregate Trades from multiple accounts
     */
    async getAggregateTrades(params = {}) {
        const queryParams = new URLSearchParams();

        if (params.accountIds && Array.isArray(params.accountIds) && params.accountIds.length > 0) {
            queryParams.append('account_ids', params.accountIds.join(','));
        }
        if (params.limit) queryParams.append('limit', params.limit || 100);
        if (params.offset) queryParams.append('offset', params.offset || 0);

        const query = queryParams.toString();
        return this.request(`/analytics/trades${query ? '?' + query : ''}`);
    }

    /**
     * Position Execution Methods
     */

    /**
     * Open a new position
     */
    async openPosition(accountId, symbol, orderType, volume, stopLoss = null, takeProfit = null, comment = null) {
        const payload = {
            account_id: accountId,
            symbol: symbol,
            order_type: orderType,
            volume: volume
        };

        if (stopLoss !== null) payload.stop_loss = stopLoss;
        if (takeProfit !== null) payload.take_profit = takeProfit;
        if (comment) payload.comment = comment;

        return this.request('/positions/open', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Close an open position
     */
    async closePosition(accountId, ticket) {
        return this.request(`/positions/${ticket}/close?account_id=${accountId}`, {
            method: 'POST'
        });
    }

    /**
     * Modify SL/TP on an open position
     */
    async modifyPosition(accountId, ticket, newSl = null, newTp = null) {
        const payload = {};
        if (newSl !== null) payload.stop_loss = newSl;
        if (newTp !== null) payload.take_profit = newTp;

        return this.request(`/positions/${ticket}/modify?account_id=${accountId}`, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Preview position before execution
     */
    async previewPosition(accountId, symbol, orderType, volume, stopLoss = null, takeProfit = null) {
        const payload = {
            account_id: accountId,
            symbol: symbol,
            order_type: orderType,
            volume: volume
        };

        if (stopLoss !== null) payload.stop_loss = stopLoss;
        if (takeProfit !== null) payload.take_profit = takeProfit;

        return this.request('/positions/preview', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Get all open positions for an account
     */
    async getOpenPositions(accountId, symbol = null) {
        let url = `/positions/open?account_id=${accountId}`;
        if (symbol) url += `&symbol=${symbol}`;
        return this.request(url);
    }

    /**
     * Close all positions for an account
     */
    async bulkClosePositions(accountId, symbol = null) {
        const payload = {
            account_id: accountId
        };
        if (symbol) payload.symbol = symbol;

        return this.request('/positions/close-all', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }
}

// Export singleton instance
const api = new APIClient();

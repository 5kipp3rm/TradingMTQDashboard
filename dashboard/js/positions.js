/**
 * Position Execution UI Controller
 * Handles position opening, closing, modification, and real-time updates
 */

class PositionManager {
    constructor() {
        this.positions = [];
        this.currentAccountId = null;
        this.previewData = null;
        this.previewOrderType = null;
        this.ws = null;
        this.init();
    }

    /**
     * Initialize the position manager
     */
    async init() {
        // Wait for account manager to be ready
        if (typeof accountManager !== 'undefined') {
            await accountManager.init();
            this.currentAccountId = accountManager.currentAccountId;

            // Render account selector
            accountManager.renderAccountSelector('accountSelectorContainer');

            // Listen for account changes
            window.addEventListener('accountChanged', (e) => {
                this.currentAccountId = e.detail.accountId;
                this.loadPositions();
            });
        }

        this.setupEventListeners();
        this.setupWebSocket();
        await this.loadPositions();
    }

    /**
     * Setup event listeners for UI interactions
     */
    setupEventListeners() {
        // Execution form buttons
        document.getElementById('previewBtn').addEventListener('click', () => this.handlePreview());
        document.getElementById('buyBtn').addEventListener('click', () => this.handleExecute('BUY'));
        document.getElementById('sellBtn').addEventListener('click', () => this.handleExecute('SELL'));

        // Refresh and close all buttons
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadPositions());
        document.getElementById('closeAllBtn').addEventListener('click', () => this.handleCloseAll());

        // Preview modal
        document.getElementById('previewModalClose').addEventListener('click', () => this.closePreviewModal());
        document.getElementById('previewCancelBtn').addEventListener('click', () => this.closePreviewModal());
        document.getElementById('previewConfirmBtn').addEventListener('click', () => this.executeFromPreview());

        // Modify modal
        document.getElementById('modifyModalClose').addEventListener('click', () => this.closeModifyModal());
        document.getElementById('modifyCancelBtn').addEventListener('click', () => this.closeModifyModal());
        document.getElementById('modifyConfirmBtn').addEventListener('click', () => this.saveModification());

        // Close modals on backdrop click
        document.getElementById('previewModal').addEventListener('click', (e) => {
            if (e.target.id === 'previewModal') this.closePreviewModal();
        });
        document.getElementById('modifyModal').addEventListener('click', (e) => {
            if (e.target.id === 'modifyModal') this.closeModifyModal();
        });
    }

    /**
     * Setup WebSocket connection for real-time updates
     */
    setupWebSocket() {
        const wsUrl = `ws://${window.location.hostname}:8000/api/ws`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected for position updates');
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);

            if (message.type === 'position_event') {
                this.handlePositionEvent(message.event, message.data);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected, reconnecting in 5s...');
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }

    /**
     * Handle WebSocket position events
     */
    handlePositionEvent(eventType, data) {
        // Only handle events for current account
        if (data.account_id !== this.currentAccountId) return;

        switch (eventType) {
            case 'position_opened':
                this.showToast('Position opened successfully', 'success');
                this.loadPositions();
                break;
            case 'position_closed':
                this.showToast('Position closed successfully', 'success');
                this.loadPositions();
                break;
            case 'position_modified':
                this.showToast('Position modified successfully', 'success');
                this.loadPositions();
                break;
        }
    }

    /**
     * Load open positions from API
     */
    async loadPositions() {
        if (!this.currentAccountId) {
            this.renderPositions([]);
            return;
        }

        try {
            const container = document.getElementById('positionsContainer');
            container.innerHTML = '<div class="loading">Loading positions...</div>';

            this.positions = await api.getOpenPositions(this.currentAccountId);
            this.renderPositions(this.positions);
        } catch (error) {
            console.error('Error loading positions:', error);
            this.showToast('Failed to load positions', 'error');
            this.renderPositions([]);
        }
    }

    /**
     * Render positions list
     */
    renderPositions(positions) {
        const container = document.getElementById('positionsContainer');

        if (positions.length === 0) {
            container.innerHTML = '<div class="no-positions">No open positions</div>';
            return;
        }

        container.innerHTML = positions.map(pos => this.renderPositionCard(pos)).join('');

        // Add event listeners to action buttons
        positions.forEach(pos => {
            document.getElementById(`modify-${pos.ticket}`).addEventListener('click', () =>
                this.showModifyModal(pos)
            );
            document.getElementById(`close-${pos.ticket}`).addEventListener('click', () =>
                this.closePosition(pos.ticket)
            );
        });
    }

    /**
     * Render individual position card
     */
    renderPositionCard(position) {
        const profitClass = position.profit >= 0 ? 'profit-positive' : 'profit-negative';
        const typeClass = position.type.toLowerCase() === 'buy' ? 'buy' : 'sell';
        const profitColor = position.profit >= 0 ? 'positive' : 'negative';

        return `
            <div class="position-card ${profitClass}">
                <div class="position-header">
                    <span class="position-symbol">${position.symbol}</span>
                    <span class="position-type ${typeClass}">${position.type}</span>
                </div>

                <div class="position-details">
                    <div class="position-detail">
                        <span class="detail-label">Ticket</span>
                        <span class="detail-value">${position.ticket}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">Volume</span>
                        <span class="detail-value">${position.volume.toFixed(2)}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">Open Price</span>
                        <span class="detail-value">${position.price_open.toFixed(5)}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">Current Price</span>
                        <span class="detail-value">${position.price_current.toFixed(5)}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">Stop Loss</span>
                        <span class="detail-value">${position.sl ? position.sl.toFixed(5) : 'None'}</span>
                    </div>
                    <div class="position-detail">
                        <span class="detail-label">Take Profit</span>
                        <span class="detail-value">${position.tp ? position.tp.toFixed(5) : 'None'}</span>
                    </div>
                </div>

                <div class="position-profit ${profitColor}">
                    ${position.profit >= 0 ? '+' : ''}${position.profit.toFixed(2)} USD
                </div>

                <div class="position-actions">
                    <button class="btn btn-small btn-secondary" id="modify-${position.ticket}">Modify</button>
                    <button class="btn btn-small btn-danger" id="close-${position.ticket}">Close</button>
                </div>
            </div>
        `;
    }

    /**
     * Get form data for position execution
     */
    getFormData() {
        const symbol = document.getElementById('symbol').value.trim().toUpperCase();
        const volume = parseFloat(document.getElementById('volume').value);
        const stopLoss = document.getElementById('stopLoss').value ? parseFloat(document.getElementById('stopLoss').value) : null;
        const takeProfit = document.getElementById('takeProfit').value ? parseFloat(document.getElementById('takeProfit').value) : null;
        const comment = document.getElementById('comment').value.trim() || null;

        return { symbol, volume, stopLoss, takeProfit, comment };
    }

    /**
     * Validate form data
     */
    validateForm() {
        if (!this.currentAccountId) {
            this.showToast('Please select an account', 'error');
            return false;
        }

        const { symbol, volume } = this.getFormData();

        if (!symbol) {
            this.showToast('Please enter a symbol', 'error');
            return false;
        }

        if (!volume || volume <= 0) {
            this.showToast('Please enter a valid volume', 'error');
            return false;
        }

        return true;
    }

    /**
     * Handle preview button click
     */
    async handlePreview() {
        if (!this.validateForm()) return;

        const { symbol, volume, stopLoss, takeProfit } = this.getFormData();

        try {
            // Get preview for BUY (default)
            const preview = await api.previewPosition(
                this.currentAccountId,
                symbol,
                'BUY',
                volume,
                stopLoss,
                takeProfit
            );

            this.showPreviewModal(preview, 'BUY');
        } catch (error) {
            console.error('Error getting preview:', error);
            this.showToast(error.message || 'Failed to preview position', 'error');
        }
    }

    /**
     * Handle execute button click (Buy/Sell)
     */
    async handleExecute(orderType) {
        if (!this.validateForm()) return;

        const { symbol, volume, stopLoss, takeProfit, comment } = this.getFormData();

        try {
            const result = await api.openPosition(
                this.currentAccountId,
                symbol,
                orderType,
                volume,
                stopLoss,
                takeProfit,
                comment
            );

            this.showToast(`${orderType} position opened (Ticket: ${result.ticket})`, 'success');
            this.clearForm();
        } catch (error) {
            console.error('Error opening position:', error);
            this.showToast(error.message || 'Failed to open position', 'error');
        }
    }

    /**
     * Show preview modal
     */
    showPreviewModal(preview, orderType) {
        this.previewData = preview;
        this.previewOrderType = orderType;

        const modalBody = document.getElementById('previewModalBody');
        const riskRewardRatio = preview.risk_reward_ratio || 0;
        const riskRewardColor = riskRewardRatio >= 2 ? 'success' : riskRewardRatio >= 1 ? '' : 'danger';
        const marginColor = preview.margin_sufficient ? 'success' : 'danger';

        modalBody.innerHTML = `
            <div class="preview-grid">
                <div class="preview-item">
                    <span class="preview-label">Symbol</span>
                    <span class="preview-value highlight">${preview.symbol}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Order Type</span>
                    <span class="preview-value highlight">${preview.order_type}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Volume</span>
                    <span class="preview-value">${preview.volume.toFixed(2)} lots</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Entry Price</span>
                    <span class="preview-value">${preview.entry_price.toFixed(5)}</span>
                </div>

                <div class="preview-divider"></div>

                <div class="preview-item">
                    <span class="preview-label">Stop Loss</span>
                    <span class="preview-value">${preview.stop_loss ? preview.stop_loss.toFixed(5) : 'None'}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Take Profit</span>
                    <span class="preview-value">${preview.take_profit ? preview.take_profit.toFixed(5) : 'None'}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Risk (Pips)</span>
                    <span class="preview-value danger">${preview.risk_pips.toFixed(1)}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Reward (Pips)</span>
                    <span class="preview-value success">${preview.reward_pips.toFixed(1)}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Risk Amount</span>
                    <span class="preview-value danger">${preview.risk_amount.toFixed(2)} USD</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Potential Profit</span>
                    <span class="preview-value success">${preview.potential_profit.toFixed(2)} USD</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Risk/Reward Ratio</span>
                    <span class="preview-value ${riskRewardColor}">1:${riskRewardRatio.toFixed(2)}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Spread</span>
                    <span class="preview-value">${preview.spread.toFixed(1)} pips</span>
                </div>

                <div class="preview-divider"></div>

                <div class="preview-item">
                    <span class="preview-label">Margin Required</span>
                    <span class="preview-value">${preview.margin_required.toFixed(2)} USD</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Margin Available</span>
                    <span class="preview-value ${marginColor}">${preview.margin_free.toFixed(2)} USD</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Account Balance</span>
                    <span class="preview-value">${preview.account_balance.toFixed(2)} USD</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Account Equity</span>
                    <span class="preview-value">${preview.account_equity.toFixed(2)} USD</span>
                </div>
            </div>
            ${!preview.margin_sufficient ? '<div class="preview-warning"><p>⚠️ Warning: Insufficient margin for this trade!</p></div>' : ''}
        `;

        document.getElementById('previewModal').classList.add('active');
        document.getElementById('previewConfirmBtn').disabled = !preview.margin_sufficient;
    }

    /**
     * Execute from preview modal
     */
    async executeFromPreview() {
        if (!this.previewData || !this.previewOrderType) return;

        this.closePreviewModal();

        const { symbol, volume, stop_loss, take_profit } = this.previewData;
        const { comment } = this.getFormData();

        try {
            const result = await api.openPosition(
                this.currentAccountId,
                symbol,
                this.previewOrderType,
                volume,
                stop_loss,
                take_profit,
                comment
            );

            this.showToast(`${this.previewOrderType} position opened (Ticket: ${result.ticket})`, 'success');
            this.clearForm();
        } catch (error) {
            console.error('Error opening position:', error);
            this.showToast(error.message || 'Failed to open position', 'error');
        }
    }

    /**
     * Close preview modal
     */
    closePreviewModal() {
        document.getElementById('previewModal').classList.remove('active');
        this.previewData = null;
        this.previewOrderType = null;
    }

    /**
     * Show modify position modal
     */
    showModifyModal(position) {
        document.getElementById('modifyTicket').value = position.ticket;
        document.getElementById('modifyStopLoss').value = position.sl || '';
        document.getElementById('modifyTakeProfit').value = position.tp || '';
        document.getElementById('modifyModal').classList.add('active');
    }

    /**
     * Save position modification
     */
    async saveModification() {
        const ticket = parseInt(document.getElementById('modifyTicket').value);
        const newSl = document.getElementById('modifyStopLoss').value ?
            parseFloat(document.getElementById('modifyStopLoss').value) : null;
        const newTp = document.getElementById('modifyTakeProfit').value ?
            parseFloat(document.getElementById('modifyTakeProfit').value) : null;

        if (!newSl && !newTp) {
            this.showToast('Please enter at least one value (SL or TP)', 'error');
            return;
        }

        try {
            await api.modifyPosition(this.currentAccountId, ticket, newSl, newTp);
            this.closeModifyModal();
            this.showToast('Position modified successfully', 'success');
        } catch (error) {
            console.error('Error modifying position:', error);
            this.showToast(error.message || 'Failed to modify position', 'error');
        }
    }

    /**
     * Close modify modal
     */
    closeModifyModal() {
        document.getElementById('modifyModal').classList.remove('active');
        document.getElementById('modifyForm').reset();
    }

    /**
     * Close individual position
     */
    async closePosition(ticket) {
        if (!confirm(`Are you sure you want to close position #${ticket}?`)) return;

        try {
            await api.closePosition(this.currentAccountId, ticket);
            this.showToast('Position closed successfully', 'success');
        } catch (error) {
            console.error('Error closing position:', error);
            this.showToast(error.message || 'Failed to close position', 'error');
        }
    }

    /**
     * Close all positions
     */
    async handleCloseAll() {
        if (this.positions.length === 0) {
            this.showToast('No positions to close', 'info');
            return;
        }

        if (!confirm(`Are you sure you want to close ALL ${this.positions.length} positions?`)) return;

        try {
            const result = await api.bulkClosePositions(this.currentAccountId);
            this.showToast(
                `Closed ${result.successful_count} positions, ${result.failed_count} failed`,
                result.failed_count === 0 ? 'success' : 'error'
            );
        } catch (error) {
            console.error('Error closing all positions:', error);
            this.showToast(error.message || 'Failed to close positions', 'error');
        }
    }

    /**
     * Clear execution form
     */
    clearForm() {
        document.getElementById('executionForm').reset();
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<p class="toast-message">${message}</p>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'toastSlideOut 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize position manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.positionManager = new PositionManager();
});

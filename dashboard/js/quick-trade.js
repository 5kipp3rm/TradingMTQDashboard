/**
 * Quick Trade Modal Controller
 */

class QuickTradeModal {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.currentSymbol = null;
        this.symbolInfo = null;
        this.priceUpdateInterval = null;
        this.currencies = [];

        this.initializeElements();
        this.attachEventListeners();

        // Ensure modal is hidden on initialization
        if (this.elements.quickTradeModal) {
            this.elements.quickTradeModal.classList.remove('active');
        }
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        this.elements = {
            // Modal
            quickTradeBtn: document.getElementById('quickTradeBtn'),
            quickTradeModal: document.getElementById('quickTradeModal'),
            closeQuickTradeModal: document.getElementById('closeQuickTradeModal'),

            // Form fields
            qtSymbol: document.getElementById('qtSymbol'),
            qtVolume: document.getElementById('qtVolume'),
            qtStopLoss: document.getElementById('qtStopLoss'),
            qtTakeProfit: document.getElementById('qtTakeProfit'),
            qtComment: document.getElementById('qtComment'),

            // Price display
            qtBidPrice: document.getElementById('qtBidPrice'),
            qtAskPrice: document.getElementById('qtAskPrice'),

            // Calculator
            qtPositionValue: document.getElementById('qtPositionValue'),
            qtRiskAmount: document.getElementById('qtRiskAmount'),
            qtRewardAmount: document.getElementById('qtRewardAmount'),
            qtRiskReward: document.getElementById('qtRiskReward'),

            // Buttons
            qtBuyBtn: document.getElementById('qtBuyBtn'),
            qtSellBtn: document.getElementById('qtSellBtn'),
            qtCancelBtn: document.getElementById('qtCancelBtn'),
        };

        // Check if critical elements exist
        if (!this.elements.quickTradeBtn) {
            console.error('Quick Trade button not found');
        }
        if (!this.elements.quickTradeModal) {
            console.error('Quick Trade modal not found');
        }
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Check if elements exist before attaching listeners
        if (!this.elements.quickTradeBtn) {
            console.error('Cannot attach event listeners - Quick Trade button not found');
            return;
        }

        // Open modal
        this.elements.quickTradeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Quick Trade button clicked');
            this.openModal();
        });

        // Close modal
        if (this.elements.closeQuickTradeModal) {
            this.elements.closeQuickTradeModal.addEventListener('click', () => this.closeModal());
        }

        if (this.elements.qtCancelBtn) {
            this.elements.qtCancelBtn.addEventListener('click', () => this.closeModal());
        }

        // Close on backdrop click
        if (this.elements.quickTradeModal) {
            this.elements.quickTradeModal.addEventListener('click', (e) => {
                if (e.target === this.elements.quickTradeModal) {
                    this.closeModal();
                }
            });
        }

        // Symbol change
        if (this.elements.qtSymbol) {
            this.elements.qtSymbol.addEventListener('change', () => this.onSymbolChange());
        }

        // Input changes for calculator
        if (this.elements.qtVolume) {
            this.elements.qtVolume.addEventListener('input', () => this.updateCalculator());
        }
        if (this.elements.qtStopLoss) {
            this.elements.qtStopLoss.addEventListener('input', () => this.updateCalculator());
        }
        if (this.elements.qtTakeProfit) {
            this.elements.qtTakeProfit.addEventListener('input', () => this.updateCalculator());
        }

        // Trade buttons
        if (this.elements.qtBuyBtn) {
            this.elements.qtBuyBtn.addEventListener('click', () => this.executeTrade('BUY'));
        }
        if (this.elements.qtSellBtn) {
            this.elements.qtSellBtn.addEventListener('click', () => this.executeTrade('SELL'));
        }

        console.log('Quick Trade Modal event listeners attached successfully');
    }

    /**
     * Open the Quick Trade modal
     */
    async openModal() {
        try {
            console.log('Opening Quick Trade modal...');

            // Load currencies if not loaded
            if (this.currencies.length === 0) {
                await this.loadCurrencies();
            }

            // Show modal with both style and class
            this.elements.quickTradeModal.style.display = 'flex';
            this.elements.quickTradeModal.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent scrolling

            // Reset form
            this.resetForm();

            // If a symbol is selected, load its info
            if (this.elements.qtSymbol.value) {
                await this.onSymbolChange();
            }

            console.log('Modal opened successfully');
        } catch (error) {
            console.error('Error opening Quick Trade modal:', error);
            alert('Failed to open Quick Trade modal');
        }
    }

    /**
     * Close the Quick Trade modal
     */
    closeModal() {
        console.log('Closing Quick Trade modal...');
        this.elements.quickTradeModal.style.display = 'none';
        this.elements.quickTradeModal.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
        this.stopPriceUpdates();
    }

    /**
     * Load available currencies from API
     */
    async loadCurrencies() {
        try {
            // Use the currencies API endpoint
            const response = await api.request('/currencies?enabled=true');
            this.currencies = response.currencies || [];

            // If API returns no currencies, use defaults
            if (this.currencies.length === 0 && typeof getEnabledDefaultCurrencies === 'function') {
                console.log('No currencies from API, using default currencies');
                this.currencies = getEnabledDefaultCurrencies();
            }

            // Populate dropdown with categories
            this.populateCurrencyDropdown();
        } catch (error) {
            console.error('Error loading currencies:', error);

            // Fallback to default currencies if available
            if (typeof getEnabledDefaultCurrencies === 'function') {
                console.log('Using default currencies as fallback');
                this.currencies = getEnabledDefaultCurrencies();
                this.populateCurrencyDropdown();
            } else {
                // Last resort: hardcoded common pairs
                console.warn('Default currencies not loaded, using hardcoded pairs');
                const fallbackPairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'XAUUSD'];
                this.elements.qtSymbol.innerHTML = '<option value="">Select Currency...</option>';
                fallbackPairs.forEach(symbol => {
                    const option = document.createElement('option');
                    option.value = symbol;
                    option.textContent = symbol;
                    this.elements.qtSymbol.appendChild(option);
                });
            }
        }
    }

    /**
     * Populate currency dropdown with categories
     */
    populateCurrencyDropdown() {
        this.elements.qtSymbol.innerHTML = '<option value="">Select Currency...</option>';

        // Group by category
        const categories = {};
        this.currencies.forEach(curr => {
            const category = curr.category || 'Other';
            if (!categories[category]) {
                categories[category] = [];
            }
            categories[category].push(curr);
        });

        // Add currencies by category with optgroups
        Object.keys(categories).sort().forEach(category => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = category;

            categories[category].forEach(curr => {
                const option = document.createElement('option');
                option.value = curr.symbol;
                option.textContent = `${curr.symbol} - ${curr.description || ''}`;
                optgroup.appendChild(option);
            });

            this.elements.qtSymbol.appendChild(optgroup);
        });
    }

    /**
     * Handle symbol change
     */
    async onSymbolChange() {
        const symbol = this.elements.qtSymbol.value;
        if (!symbol) {
            this.stopPriceUpdates();
            return;
        }

        this.currentSymbol = symbol;

        // Load symbol info and start price updates
        await this.loadSymbolInfo();
        this.startPriceUpdates();
        this.updateCalculator();
    }

    /**
     * Load symbol information
     */
    async loadSymbolInfo() {
        try {
            // Get symbol info from currencies API or use defaults
            const currency = this.currencies.find(c => c.symbol === this.currentSymbol);
            this.symbolInfo = {
                symbol: this.currentSymbol,
                digits: currency?.digits || 5,
                point: currency?.point || 0.00001,
                contract_size: currency?.contract_size || 100000,
                bid: 0,
                ask: 0
            };

            // Update prices (in real system, this would come from MT5)
            await this.updatePrices();
        } catch (error) {
            console.error('Error loading symbol info:', error);
        }
    }

    /**
     * Update current prices
     */
    async updatePrices() {
        try {
            // In a real system, fetch from MT5 connector
            // For now, use mock prices
            if (!this.symbolInfo) return;

            // Mock price update (replace with actual MT5 tick data)
            this.symbolInfo.bid = this.getMockPrice();
            this.symbolInfo.ask = this.symbolInfo.bid + (this.symbolInfo.point * 10);

            this.elements.qtBidPrice.textContent = this.symbolInfo.bid.toFixed(this.symbolInfo.digits);
            this.elements.qtAskPrice.textContent = this.symbolInfo.ask.toFixed(this.symbolInfo.digits);

            this.updateCalculator();
        } catch (error) {
            console.error('Error updating prices:', error);
        }
    }

    /**
     * Get mock price (replace with real MT5 data)
     */
    getMockPrice() {
        const basePrices = {
            'EURUSD': 1.08500,
            'GBPUSD': 1.27500,
            'USDJPY': 149.500,
            'AUDUSD': 0.65500,
            'USDCAD': 1.35500,
            'XAUUSD': 2050.00
        };

        const basePrice = basePrices[this.currentSymbol] || 1.0000;
        // Add small random variation
        const variation = (Math.random() - 0.5) * 0.001;
        return basePrice + variation;
    }

    /**
     * Start price updates
     */
    startPriceUpdates() {
        this.stopPriceUpdates();
        this.priceUpdateInterval = setInterval(() => {
            this.updatePrices();
        }, 2000); // Update every 2 seconds
    }

    /**
     * Stop price updates
     */
    stopPriceUpdates() {
        if (this.priceUpdateInterval) {
            clearInterval(this.priceUpdateInterval);
            this.priceUpdateInterval = null;
        }
    }

    /**
     * Update profit/loss calculator
     */
    updateCalculator() {
        if (!this.symbolInfo || !this.symbolInfo.bid) {
            this.elements.qtPositionValue.textContent = '$0.00';
            this.elements.qtRiskAmount.textContent = '$0.00';
            this.elements.qtRewardAmount.textContent = '$0.00';
            this.elements.qtRiskReward.textContent = '-';
            return;
        }

        const volume = parseFloat(this.elements.qtVolume.value) || 0;
        const stopLoss = parseFloat(this.elements.qtStopLoss.value) || 0;
        const takeProfit = parseFloat(this.elements.qtTakeProfit.value) || 0;

        // Calculate position value
        const positionValue = volume * this.symbolInfo.contract_size;
        this.elements.qtPositionValue.textContent = this.formatCurrency(positionValue);

        // Calculate risk (SL distance)
        let riskAmount = 0;
        if (stopLoss > 0) {
            const slDistance = Math.abs(this.symbolInfo.bid - stopLoss);
            const pipValue = (this.symbolInfo.contract_size * this.symbolInfo.point);
            riskAmount = (slDistance / this.symbolInfo.point) * pipValue * volume;
        }
        this.elements.qtRiskAmount.textContent = this.formatCurrency(riskAmount);

        // Calculate reward (TP distance)
        let rewardAmount = 0;
        if (takeProfit > 0) {
            const tpDistance = Math.abs(takeProfit - this.symbolInfo.bid);
            const pipValue = (this.symbolInfo.contract_size * this.symbolInfo.point);
            rewardAmount = (tpDistance / this.symbolInfo.point) * pipValue * volume;
        }
        this.elements.qtRewardAmount.textContent = this.formatCurrency(rewardAmount);

        // Calculate risk/reward ratio
        if (riskAmount > 0 && rewardAmount > 0) {
            const ratio = (rewardAmount / riskAmount).toFixed(2);
            this.elements.qtRiskReward.textContent = `1:${ratio}`;
        } else {
            this.elements.qtRiskReward.textContent = '-';
        }
    }

    /**
     * Execute trade
     */
    async executeTrade(orderType) {
        try {
            // Validate
            const symbol = this.elements.qtSymbol.value;
            const volume = parseFloat(this.elements.qtVolume.value);

            if (!symbol) {
                alert('Please select a currency pair');
                return;
            }

            if (!volume || volume <= 0) {
                alert('Please enter a valid volume');
                return;
            }

            // Get account ID
            const accountId = typeof accountManager !== 'undefined' ? accountManager.currentAccountId : null;
            if (!accountId) {
                alert('Please select an account first');
                return;
            }

            // Disable buttons
            this.elements.qtBuyBtn.disabled = true;
            this.elements.qtSellBtn.disabled = true;

            // Prepare order data
            const stopLoss = parseFloat(this.elements.qtStopLoss.value) || null;
            const takeProfit = parseFloat(this.elements.qtTakeProfit.value) || null;
            const comment = this.elements.qtComment.value || null;

            // Execute trade
            console.log('Executing trade:', { accountId, symbol, orderType, volume, stopLoss, takeProfit, comment });
            const result = await api.openPosition(accountId, symbol, orderType, volume, stopLoss, takeProfit, comment);

            // Success
            alert(`✅ ${orderType} order placed successfully!\nTicket: ${result.ticket || result.order_ticket}`);
            this.closeModal();

            // Reload positions and dashboard
            if (this.dashboard) {
                this.dashboard.loadOpenPositions();
                this.dashboard.loadDashboard();
            }

        } catch (error) {
            console.error('Trade execution error:', error);
            alert(`❌ Trade failed: ${error.message}`);
        } finally {
            // Re-enable buttons
            this.elements.qtBuyBtn.disabled = false;
            this.elements.qtSellBtn.disabled = false;
        }
    }

    /**
     * Reset form
     */
    resetForm() {
        this.elements.qtVolume.value = '0.10';
        this.elements.qtStopLoss.value = '';
        this.elements.qtTakeProfit.value = '';
        this.elements.qtComment.value = '';
        this.elements.qtBidPrice.textContent = '-';
        this.elements.qtAskPrice.textContent = '-';
        this.updateCalculator();
    }

    /**
     * Format currency
     */
    formatCurrency(value) {
        return '$' + value.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
}

/**
 * Account Manager
 *
 * Manages trading account selection and switching in the dashboard.
 * Provides UI components for account selection and handles API communication.
 */

const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api'
    : '/api';

class AccountManager {
    constructor() {
        this.accounts = [];
        this.currentAccountId = null;
        this.initialized = false;
    }

    /**
     * Initialize account manager
     */
    async init() {
        if (this.initialized) return;

        try {
            await this.loadAccounts();
            this.setupEventListeners();
            this.initialized = true;
        } catch (error) {
            console.error('Failed to initialize account manager:', error);
        }
    }

    /**
     * Load accounts from API
     */
    async loadAccounts() {
        try {
            const response = await fetch(`${API_URL}/accounts`);
            if (!response.ok) throw new Error('Failed to load accounts');

            const data = await response.json();
            this.accounts = data.accounts;
            this.currentAccountId = this.getSelectedAccountId() || data.default_account_id;

            return this.accounts;
        } catch (error) {
            console.error('Error loading accounts:', error);
            throw error;
        }
    }

    /**
     * Get currently selected account ID from localStorage
     */
    getSelectedAccountId() {
        const stored = localStorage.getItem('selected_account_id');
        return stored ? parseInt(stored) : null;
    }

    /**
     * Set currently selected account ID
     */
    setSelectedAccountId(accountId) {
        this.currentAccountId = accountId;
        if (accountId) {
            localStorage.setItem('selected_account_id', accountId.toString());
        } else {
            localStorage.removeItem('selected_account_id');
        }

        // Dispatch event for other components to react
        window.dispatchEvent(new CustomEvent('accountChanged', {
            detail: { accountId: accountId }
        }));
    }

    /**
     * Get current account details
     */
    getCurrentAccount() {
        if (!this.currentAccountId) return null;
        return this.accounts.find(acc => acc.id === this.currentAccountId);
    }

    /**
     * Render account selector dropdown
     */
    renderAccountSelector(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const html = `
            <div class="account-selector">
                <label for="accountSelect">Trading Account:</label>
                <select id="accountSelect" class="account-select">
                    <option value="">All Accounts</option>
                    ${this.accounts
                        .filter(acc => acc.is_active)
                        .map(account => `
                            <option value="${account.id}" ${account.id === this.currentAccountId ? 'selected' : ''}>
                                ${account.account_name} (${account.account_number})
                                ${account.is_demo ? '📝' : '💰'}
                                ${account.is_default ? '⭐' : ''}
                            </option>
                        `).join('')}
                </select>
            </div>
        `;

        container.innerHTML = html;

        // Add change listener
        const select = document.getElementById('accountSelect');
        if (select) {
            select.addEventListener('change', (e) => {
                const accountId = e.target.value ? parseInt(e.target.value) : null;
                this.setSelectedAccountId(accountId);
            });
        }
    }

    /**
     * Render account info card
     */
    renderAccountInfo(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const account = this.getCurrentAccount();

        if (!account) {
            container.innerHTML = '<div class="account-info">All Accounts</div>';
            return;
        }

        const html = `
            <div class="account-info-card">
                <h3>${account.account_name}</h3>
                <div class="account-details">
                    <div class="detail-row">
                        <span class="label">Account Number:</span>
                        <span class="value">${account.account_number}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Broker:</span>
                        <span class="value">${account.broker}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Type:</span>
                        <span class="value">${account.is_demo ? 'Demo' : 'Live'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Currency:</span>
                        <span class="value">${account.currency}</span>
                    </div>
                    ${account.is_default ? '<div class="default-badge">Default Account</div>' : ''}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    /**
     * Get account filter parameter for API calls
     */
    getAccountFilterParam() {
        return this.currentAccountId ? `account_id=${this.currentAccountId}` : '';
    }

    /**
     * Setup global event listeners
     */
    setupEventListeners() {
        // Listen for account changes to update UI
        window.addEventListener('accountChanged', () => {
            // Update any account info displays
            const infoContainers = document.querySelectorAll('[data-account-info]');
            infoContainers.forEach(container => {
                this.renderAccountInfo(container.id);
            });
        });
    }

    /**
     * Create new account (admin function)
     */
    async createAccount(accountData) {
        try {
            const response = await fetch(`${API_URL}/accounts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(accountData)
            });

            if (!response.ok) throw new Error('Failed to create account');

            const newAccount = await response.json();
            await this.loadAccounts(); // Reload accounts list
            return newAccount;
        } catch (error) {
            console.error('Error creating account:', error);
            throw error;
        }
    }

    /**
     * Set account as default
     */
    async setDefaultAccount(accountId) {
        try {
            const response = await fetch(`${API_URL}/accounts/${accountId}/set-default`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to set default account');

            await this.loadAccounts(); // Reload to get updated default status
            return true;
        } catch (error) {
            console.error('Error setting default account:', error);
            throw error;
        }
    }
}

// Global instance
const accountManager = new AccountManager();

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => accountManager.init());
} else {
    accountManager.init();
}

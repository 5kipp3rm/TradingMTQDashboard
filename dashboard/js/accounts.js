/**
 * Account Management JavaScript
 * Handles account CRUD operations, connection management, and real-time updates
 */

// API Configuration
// Only declare if not already defined
if (typeof API_BASE_URL === 'undefined') {
    var API_BASE_URL = 'http://localhost:8000/api';
}
if (typeof WS_URL === 'undefined') {
    var WS_URL = 'ws://localhost:8000/api/ws';
}

// Global State
let accounts = [];
let connectionStates = new Map();
let websocket = null;

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadAccounts();
    connectWebSocket();
});

function initializeEventListeners() {
    // Header buttons
    document.getElementById('addAccountBtn').addEventListener('click', openAddAccountModal);
    document.getElementById('connectAllBtn').addEventListener('click', connectAllAccounts);
    document.getElementById('disconnectAllBtn').addEventListener('click', disconnectAllAccounts);
    document.getElementById('refreshAccountsBtn').addEventListener('click', loadAccounts);

    // Filters
    document.getElementById('filterStatus').addEventListener('change', applyFilters);
    document.getElementById('filterType').addEventListener('change', applyFilters);
    document.getElementById('filterConnection').addEventListener('change', applyFilters);

    // Form submission
    document.getElementById('accountForm').addEventListener('submit', handleAccountFormSubmit);
}

// ============================================================================
// API Functions
// ============================================================================

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        // Handle 204 No Content responses (like DELETE)
        if (response.status === 204) {
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showToast(`Error: ${error.message}`, 'error');
        throw error;
    }
}

async function loadAccounts() {
    try {
        const data = await apiRequest('/accounts');
        accounts = data.accounts;

        // Update summary cards
        updateSummaryCards(data);

        // Load connection states
        await loadConnectionStates();

        // Render table
        renderAccountsTable();
    } catch (error) {
        console.error('Failed to load accounts:', error);
    }
}

async function loadConnectionStates() {
    connectionStates.clear();

    for (const account of accounts) {
        try {
            const state = await apiRequest(`/accounts/${account.id}/status`);
            connectionStates.set(account.id, state);
        } catch (error) {
            console.error(`Failed to load connection state for account ${account.id}:`, error);
        }
    }
}

async function createAccount(accountData) {
    try {
        const newAccount = await apiRequest('/accounts', {
            method: 'POST',
            body: JSON.stringify(accountData)
        });
        showToast('Account created successfully', 'success');
        await loadAccounts();
        return newAccount;
    } catch (error) {
        throw error;
    }
}

async function updateAccount(accountId, accountData) {
    try {
        const updatedAccount = await apiRequest(`/accounts/${accountId}`, {
            method: 'PUT',
            body: JSON.stringify(accountData)
        });
        showToast('Account updated successfully', 'success');
        await loadAccounts();
        return updatedAccount;
    } catch (error) {
        throw error;
    }
}

async function deleteAccount(accountId) {
    if (!confirm('Are you sure you want to delete this account? This action cannot be undone.')) {
        return;
    }

    try {
        await apiRequest(`/accounts/${accountId}`, {
            method: 'DELETE'
        });
        showToast('Account deleted successfully', 'success');
        await loadAccounts();
    } catch (error) {
        console.error('Failed to delete account:', error);
    }
}

async function connectAccount(accountId) {
    try {
        showToast('Connecting account...', 'info');

        // Get account details
        const account = accounts.find(a => a.id === accountId);
        if (!account) {
            throw new Error('Account not found');
        }

        // Use Phase 4 worker system
        if (typeof workerConnector !== 'undefined') {
            await workerConnector.connectAccount(account);
            showToast('✅ Phase 4 worker started successfully!', 'success');
        } else {
            // Fallback to old system if worker connector not available
            await apiRequest(`/accounts/${accountId}/connect`, {
                method: 'POST'
            });
            showToast('Account connected successfully', 'success');
        }

        await loadConnectionStates();
        renderAccountsTable();
    } catch (error) {
        console.error('Failed to connect account:', error);
        showToast(`Failed to connect: ${error.message}`, 'error');
    }
}

async function disconnectAccount(accountId) {
    try {
        showToast('Disconnecting account...', 'info');

        // Get account details
        const account = accounts.find(a => a.id === accountId);
        if (!account) {
            throw new Error('Account not found');
        }

        // Use Phase 4 worker system
        if (typeof workerConnector !== 'undefined') {
            await workerConnector.disconnectAccount(account);
            showToast('✅ Phase 4 worker stopped successfully!', 'success');
        } else {
            // Fallback to old system if worker connector not available
            await apiRequest(`/accounts/${accountId}/disconnect`, {
                method: 'POST'
            });
            showToast('Account disconnected successfully', 'success');
        }

        await loadConnectionStates();
        renderAccountsTable();
    } catch (error) {
        console.error('Failed to disconnect account:', error);
        showToast(`Failed to disconnect: ${error.message}`, 'error');
    }
}

async function connectAllAccounts() {
    if (!confirm('Connect to all active accounts using Phase 4 workers?')) {
        return;
    }

    try {
        showToast('Connecting all accounts...', 'info');

        // Use Phase 4 worker system
        if (typeof workerConnector !== 'undefined') {
            const result = await workerConnector.connectAllAccounts(accounts);
            showToast(`✅ Phase 4: Connected ${result.successful} of ${result.total} accounts`, 'success');

            // Show details if there were failures
            if (result.failed > 0) {
                console.warn('Some accounts failed to connect:', result.results.filter(r => !r.success));
            }
        } else {
            // Fallback to old system
            const result = await apiRequest('/accounts/connect-all', {
                method: 'POST'
            });
            showToast(`Connected ${result.successful} of ${result.total} accounts`, 'success');
        }

        await loadConnectionStates();
        renderAccountsTable();
    } catch (error) {
        console.error('Failed to connect all accounts:', error);
        showToast(`Failed to connect accounts: ${error.message}`, 'error');
    }
}

async function disconnectAllAccounts() {
    if (!confirm('Disconnect from all connected Phase 4 workers?')) {
        return;
    }

    try {
        showToast('Disconnecting all accounts...', 'info');

        // Use Phase 4 worker system
        if (typeof workerConnector !== 'undefined') {
            const result = await workerConnector.disconnectAllWorkers();
            showToast(`✅ Phase 4: Disconnected ${result.successful} workers`, 'success');
        } else {
            // Fallback to old system
            const result = await apiRequest('/accounts/disconnect-all', {
                method: 'POST'
            });
            showToast(`Disconnected ${result.successful} of ${result.total} accounts`, 'success');
        }

        await loadConnectionStates();
        renderAccountsTable();
    } catch (error) {
        console.error('Failed to disconnect all accounts:', error);
        showToast(`Failed to disconnect accounts: ${error.message}`, 'error');
    }
}

async function setDefaultAccount(accountId) {
    try {
        await apiRequest(`/accounts/${accountId}/set-default`, {
            method: 'POST'
        });
        showToast('Default account updated', 'success');
        await loadAccounts();
    } catch (error) {
        console.error('Failed to set default account:', error);
    }
}

async function toggleAccountActive(accountId, currentStatus) {
    const endpoint = currentStatus ? 'deactivate' : 'activate';

    try {
        await apiRequest(`/accounts/${accountId}/${endpoint}`, {
            method: 'POST'
        });
        showToast(`Account ${currentStatus ? 'deactivated' : 'activated'} successfully`, 'success');
        await loadAccounts();
    } catch (error) {
        console.error('Failed to toggle account status:', error);
    }
}

// ============================================================================
// UI Rendering
// ============================================================================

function updateSummaryCards(data) {
    document.getElementById('totalAccounts').textContent = data.total;
    document.getElementById('activeAccounts').textContent = data.active_count;
    document.getElementById('demoAccounts').textContent = data.accounts.filter(a => a.is_demo).length;

    // Count connected accounts
    const connectedCount = Array.from(connectionStates.values()).filter(s => s.is_connected).length;
    document.getElementById('connectedAccounts').textContent = connectedCount;
}

function renderAccountsTable() {
    const tbody = document.getElementById('accountsTableBody');
    const filteredAccounts = getFilteredAccounts();

    if (filteredAccounts.length === 0) {
        tbody.innerHTML = `
            <tr class="loading-row">
                <td colspan="9">
                    <div class="loading-spinner">
                        <i class="fas fa-inbox"></i> No accounts found
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filteredAccounts.map(account => {
        const connectionState = connectionStates.get(account.id);
        const isConnected = connectionState?.is_connected || false;
        const connectionError = connectionState?.connection_error;

        return `
            <tr>
                <td>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        <span class="status-badge ${account.is_active ? 'active' : 'inactive'}">
                            <i class="fas fa-${account.is_active ? 'check-circle' : 'times-circle'}"></i>
                            ${account.is_active ? 'Active' : 'Inactive'}
                        </span>
                        ${account.is_default ? '<span class="status-badge default"><i class="fas fa-star"></i> Default</span>' : ''}
                    </div>
                </td>
                <td>
                    <div>
                        <strong>${account.account_name}</strong>
                        <div style="color: #6b7280; font-size: 0.85rem;">#${account.account_number}</div>
                    </div>
                </td>
                <td>
                    <span class="platform-badge ${account.platform_type === 'MT4' ? 'mt4' : 'mt5'}">
                        ${account.platform_type || 'MT5'}
                    </span>
                </td>
                <td>${account.broker}</td>
                <td>${account.server}</td>
                <td>
                    <span class="type-badge ${account.is_demo ? 'demo' : 'live'}">
                        ${account.is_demo ? 'Demo' : 'Live'}
                    </span>
                </td>
                <td>
                    <div class="connection-status ${isConnected ? 'connected' : (connectionError ? 'error' : 'disconnected')}">
                        <i class="fas fa-circle"></i>
                        ${isConnected ? 'Connected' : (connectionError ? 'Error' : 'Disconnected')}
                    </div>
                    ${connectionError ? `<div style="font-size: 0.75rem; color: #ef4444; margin-top: 0.25rem;">${connectionError}</div>` : ''}
                </td>
                <td>
                    ${account.last_connected ? new Date(account.last_connected).toLocaleString() : 'Never'}
                </td>
                <td>
                    <div class="action-buttons">
                        ${isConnected
                            ? `<button class="btn-icon disconnect" onclick="disconnectAccount(${account.id})" title="Disconnect">
                                <i class="fas fa-power-off"></i>
                               </button>`
                            : `<button class="btn-icon connect" onclick="connectAccount(${account.id})" title="Connect" ${!account.is_active ? 'disabled' : ''}>
                                <i class="fas fa-plug"></i>
                               </button>`
                        }
                        <button class="btn-icon config" onclick="openAccountConfig(${account.id})" title="Configure Trading Settings">
                            <i class="fas fa-cog"></i>
                        </button>
                        <button class="btn-icon edit" onclick="openEditAccountModal(${account.id})" title="Edit Account">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="viewAccountDetails(${account.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-icon delete" onclick="deleteAccount(${account.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function getFilteredAccounts() {
    const statusFilter = document.getElementById('filterStatus').value;
    const typeFilter = document.getElementById('filterType').value;
    const connectionFilter = document.getElementById('filterConnection').value;

    return accounts.filter(account => {
        // Status filter
        if (statusFilter === 'active' && !account.is_active) return false;
        if (statusFilter === 'inactive' && account.is_active) return false;

        // Type filter
        if (typeFilter === 'demo' && !account.is_demo) return false;
        if (typeFilter === 'live' && account.is_demo) return false;

        // Connection filter
        if (connectionFilter !== 'all') {
            const connectionState = connectionStates.get(account.id);
            const isConnected = connectionState?.is_connected || false;

            if (connectionFilter === 'connected' && !isConnected) return false;
            if (connectionFilter === 'disconnected' && isConnected) return false;
        }

        return true;
    });
}

function applyFilters() {
    renderAccountsTable();
}

// ============================================================================
// Modal Functions
// ============================================================================

function openAddAccountModal() {
    document.getElementById('modalTitle').textContent = 'Add New Account';
    document.getElementById('accountForm').reset();
    document.getElementById('accountId').value = '';
    document.getElementById('isDemo').checked = true;
    document.getElementById('isActive').checked = true;
    document.getElementById('accountModal').classList.add('active');
}

function openEditAccountModal(accountId) {
    const account = accounts.find(a => a.id === accountId);
    if (!account) return;

    document.getElementById('modalTitle').textContent = 'Edit Account';
    document.getElementById('accountId').value = account.id;
    document.getElementById('accountNumber').value = account.account_number;
    document.getElementById('accountName').value = account.account_name;
    document.getElementById('platformType').value = account.platform_type || 'MT5';
    document.getElementById('broker').value = account.broker;
    document.getElementById('server').value = account.server;
    document.getElementById('isDemo').checked = account.is_demo;
    document.getElementById('isActive').checked = account.is_active;
    document.getElementById('isDefault').checked = account.is_default;

    document.getElementById('accountModal').classList.add('active');
}

function closeAccountModal() {
    document.getElementById('accountModal').classList.remove('active');
}

async function handleAccountFormSubmit(event) {
    event.preventDefault();

    const accountId = document.getElementById('accountId').value;
    const password = document.getElementById('password').value;
    const accountNumber = parseInt(document.getElementById('accountNumber').value);
    const brokerValue = document.getElementById('broker').value.trim();

    const accountData = {
        account_number: accountNumber,
        login: accountNumber,  // Login same as account number
        account_name: document.getElementById('accountName').value,
        platform_type: document.getElementById('platformType').value,
        broker: brokerValue || 'Unknown',  // Default to 'Unknown' if empty
        server: document.getElementById('server').value,
        currency: 'USD',  // Default currency
        is_demo: document.getElementById('isDemo').checked,
        is_active: document.getElementById('isActive').checked,
        is_default: document.getElementById('isDefault').checked
    };

    // Only include password if provided
    if (password) {
        accountData.password = password;
    }

    try {
        if (accountId) {
            // Update existing account
            await updateAccount(parseInt(accountId), accountData);
        } else {
            // Create new account (password required for new accounts)
            if (!password) {
                showToast('Password is required for new accounts', 'error');
                return;
            }
            await createAccount(accountData);
        }
        closeAccountModal();
    } catch (error) {
        // Error already shown by apiRequest
    }
}

function viewAccountDetails(accountId) {
    const account = accounts.find(a => a.id === accountId);
    const connectionState = connectionStates.get(accountId);

    if (!account) return;

    const detailsHtml = `
        <div class="detail-group">
            <h3>Account Information</h3>
            <div class="detail-row">
                <div class="detail-label">Account Name:</div>
                <div class="detail-value">${account.account_name}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Account Number:</div>
                <div class="detail-value">${account.account_number}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Platform:</div>
                <div class="detail-value">${account.platform_type || 'MT5'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Broker:</div>
                <div class="detail-value">${account.broker}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Server:</div>
                <div class="detail-value">${account.server}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Currency:</div>
                <div class="detail-value">${account.currency}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Type:</div>
                <div class="detail-value">${account.is_demo ? 'Demo' : 'Live'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Status:</div>
                <div class="detail-value">${account.is_active ? 'Active' : 'Inactive'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Default:</div>
                <div class="detail-value">${account.is_default ? 'Yes' : 'No'}</div>
            </div>
        </div>

        ${connectionState ? `
        <div class="detail-group">
            <h3>Connection Status</h3>
            <div class="detail-row">
                <div class="detail-label">Status:</div>
                <div class="detail-value">${connectionState.is_connected ? 'Connected' : 'Disconnected'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Last Connected:</div>
                <div class="detail-value">${connectionState.last_connected_at ? new Date(connectionState.last_connected_at).toLocaleString() : 'Never'}</div>
            </div>
            ${connectionState.connection_error ? `
            <div class="detail-row">
                <div class="detail-label">Error:</div>
                <div class="detail-value" style="color: #ef4444;">${connectionState.connection_error}</div>
            </div>
            ` : ''}
        </div>
        ` : ''}

        <div class="detail-group">
            <h3>Timestamps</h3>
            <div class="detail-row">
                <div class="detail-label">Created:</div>
                <div class="detail-value">${new Date(account.created_at).toLocaleString()}</div>
            </div>
            ${account.updated_at ? `
            <div class="detail-row">
                <div class="detail-label">Last Updated:</div>
                <div class="detail-value">${new Date(account.updated_at).toLocaleString()}</div>
            </div>
            ` : ''}
        </div>

        ${account.description ? `
        <div class="detail-group">
            <h3>Description</h3>
            <p>${account.description}</p>
        </div>
        ` : ''}
    `;

    document.getElementById('accountDetailsContent').innerHTML = detailsHtml;
    document.getElementById('accountDetailsModal').classList.add('active');
}

function closeAccountDetailsModal() {
    document.getElementById('accountDetailsModal').classList.remove('active');
}

// ============================================================================
// WebSocket Functions
// ============================================================================

function connectWebSocket() {
    websocket = new WebSocket(WS_URL);

    websocket.onopen = () => {
        console.log('WebSocket connected');
    };

    websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting in 5 seconds...');
        setTimeout(connectWebSocket, 5000);
    };
}

function handleWebSocketMessage(message) {
    if (message.type === 'account_connection') {
        // Update connection state and refresh table
        loadConnectionStates().then(() => {
            renderAccountsTable();
            updateSummaryCards({
                total: accounts.length,
                active_count: accounts.filter(a => a.is_active).length,
                accounts: accounts
            });
        });

        // Show notification
        const eventType = message.event;
        const accountName = message.data.account_name;

        if (eventType === 'connected') {
            showToast(`${accountName} connected`, 'success');
        } else if (eventType === 'disconnected') {
            showToast(`${accountName} disconnected`, 'info');
        } else if (eventType === 'error') {
            showToast(`${accountName} connection error`, 'error');
        }
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} active`;

    setTimeout(() => {
        toast.classList.remove('active');
    }, 3000);
}

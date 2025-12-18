/**
 * Configuration Settings Manager
 * Manages currencies, preferences, favorites from the config API
 */

// State
let allCurrencies = [];
let filteredCurrencies = [];
let preferences = null;
let stats = null;
let currentEditingSymbol = null;

// DOM Elements
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const lastUpdate = document.getElementById('lastUpdate');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeTabs();
    loadAllData();
});

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
    // Tab switching
    document.querySelectorAll('.config-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Currencies tab
    document.getElementById('currencySearch').addEventListener('input', filterCurrencies);
    document.getElementById('categoryFilter').addEventListener('change', filterCurrencies);
    document.getElementById('statusFilterCurr').addEventListener('change', filterCurrencies);
    document.getElementById('refreshCurrenciesBtn').addEventListener('click', loadCurrencies);
    document.getElementById('addCurrencyBtn').addEventListener('click', () => openModal());

    // Preferences tab
    document.getElementById('preferencesForm').addEventListener('submit', savePreferences);

    // Stats tab
    document.getElementById('exportConfigBtn').addEventListener('click', exportConfig);
    document.getElementById('importConfigBtn').addEventListener('click', importConfig);
    document.getElementById('resetConfigBtn').addEventListener('click', resetConfig);

    // Modal
    document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
    document.getElementById('cancelBtn').addEventListener('click', closeModal);
    document.getElementById('currencyForm').addEventListener('submit', saveCurrency);
    document.getElementById('currencyModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('currencyModal')) {
            closeModal();
        }
    });
}

/**
 * Initialize tabs
 */
function initializeTabs() {
    // Initially show only currencies tab
    switchTab('currencies');
}

/**
 * Switch active tab
 */
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.config-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Load data for the tab if needed
    if (tabName === 'preferences' && !preferences) {
        loadPreferences();
    } else if (tabName === 'favorites') {
        loadFavorites();
    } else if (tabName === 'stats' && !stats) {
        loadStats();
    }
}

/**
 * Load all initial data
 */
async function loadAllData() {
    await loadCurrencies();
    await loadCategories();
}

/**
 * Load currencies from config API
 */
async function loadCurrencies() {
    try {
        updateStatus('loading', 'Loading currencies...');

        const response = await api.request('/config/currencies');

        allCurrencies = response || [];
        filteredCurrencies = [...allCurrencies];

        renderCurrencies();
        updateStatus('success', `Loaded ${allCurrencies.length} currencies`);
        updateLastUpdate();

    } catch (error) {
        console.error('Failed to load currencies:', error);
        updateStatus('error', 'Failed to load currencies');
        showToast('error', 'Load Failed', error.message);
    }
}

/**
 * Load categories for filter
 */
async function loadCategories() {
    try {
        const categories = await api.request('/config/categories');
        const categoryFilter = document.getElementById('categoryFilter');

        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

/**
 * Filter currencies
 */
function filterCurrencies() {
    const search = document.getElementById('currencySearch').value.toLowerCase().trim();
    const category = document.getElementById('categoryFilter').value;
    const status = document.getElementById('statusFilterCurr').value;

    filteredCurrencies = allCurrencies.filter(currency => {
        // Search filter
        if (search && !currency.symbol.toLowerCase().includes(search) &&
            !currency.description.toLowerCase().includes(search)) {
            return false;
        }

        // Category filter
        if (category !== 'all' && currency.category !== category) {
            return false;
        }

        // Status filter
        if (status === 'enabled' && !currency.enabled) {
            return false;
        }
        if (status === 'disabled' && currency.enabled) {
            return false;
        }

        return true;
    });

    renderCurrencies();
}

/**
 * Render currencies grouped by category
 */
function renderCurrencies() {
    const container = document.getElementById('currenciesContainer');

    if (filteredCurrencies.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💱</div>
                <div class="empty-state-title">No Currencies Found</div>
                <div class="empty-state-text">Try adjusting your filters or add a custom currency</div>
            </div>
        `;
        return;
    }

    // Group by category
    const byCategory = {};
    filteredCurrencies.forEach(currency => {
        if (!byCategory[currency.category]) {
            byCategory[currency.category] = [];
        }
        byCategory[currency.category].push(currency);
    });

    // Render each category
    container.innerHTML = Object.entries(byCategory).map(([category, currencies]) => `
        <div class="category-group">
            <h3 class="category-header">${category}</h3>
            <div class="currency-grid">
                ${currencies.map(currency => renderCurrencyCard(currency)).join('')}
            </div>
        </div>
    `).join('');
}

/**
 * Render single currency card
 */
function renderCurrencyCard(currency) {
    return `
        <div class="currency-card">
            <div class="currency-card-header">
                <span class="currency-symbol">${currency.symbol}</span>
                <span class="status-badge ${currency.enabled ? 'enabled' : 'disabled'}">
                    ${currency.enabled ? '✅ Enabled' : '❌ Disabled'}
                </span>
            </div>
            <div class="currency-description">${currency.description}</div>
            <div class="currency-details">
                <div class="currency-detail">
                    <span>Digits:</span>
                    <strong>${currency.digits}</strong>
                </div>
                <div class="currency-detail">
                    <span>Point:</span>
                    <strong>${currency.point}</strong>
                </div>
                <div class="currency-detail">
                    <span>Contract:</span>
                    <strong>${currency.contract_size.toLocaleString()}</strong>
                </div>
                <div class="currency-detail">
                    <span>Lot Range:</span>
                    <strong>${currency.min_lot} - ${currency.max_lot}</strong>
                </div>
                <div class="currency-detail">
                    <span>Spread:</span>
                    <strong>${currency.spread_typical} pips</strong>
                </div>
                <div class="currency-detail">
                    <span>Custom:</span>
                    <strong>${currency.custom ? '✓ Yes' : '✗ No'}</strong>
                </div>
            </div>
            <div class="currency-actions">
                <button class="action-btn action-btn-toggle" onclick="toggleCurrency('${currency.symbol}', ${!currency.enabled})">
                    ${currency.enabled ? '⏸️ Disable' : '▶️ Enable'}
                </button>
                ${currency.custom ? `
                    <button class="action-btn action-btn-edit" onclick="editCurrency('${currency.symbol}')">
                        ✏️ Edit
                    </button>
                    <button class="action-btn action-btn-delete" onclick="deleteCurrency('${currency.symbol}')">
                        🗑️ Delete
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Toggle currency enabled status
 */
async function toggleCurrency(symbol, enable) {
    try {
        const action = enable ? 'enable' : 'disable';
        await api.request(`/config/currencies/${symbol}/${action}`, { method: 'POST' });

        showToast('success', 'Success', `Currency ${symbol} ${enable ? 'enabled' : 'disabled'}`);
        await loadCurrencies();

    } catch (error) {
        console.error(`Failed to toggle currency:`, error);
        showToast('error', 'Action Failed', error.message);
    }
}

/**
 * Edit currency
 */
function editCurrency(symbol) {
    const currency = allCurrencies.find(c => c.symbol === symbol);
    if (!currency || !currency.custom) {
        showToast('error', 'Error', 'Can only edit custom currencies');
        return;
    }

    currentEditingSymbol = symbol;
    document.getElementById('modalTitle').textContent = `Edit ${symbol}`;

    // Populate form
    document.getElementById('symbol').value = currency.symbol;
    document.getElementById('symbol').disabled = true;
    document.getElementById('description').value = currency.description;
    document.getElementById('category').value = currency.category;
    document.getElementById('digits').value = currency.digits;
    document.getElementById('point').value = currency.point;
    document.getElementById('contractSize').value = currency.contract_size;
    document.getElementById('minLot').value = currency.min_lot;
    document.getElementById('maxLot').value = currency.max_lot;
    document.getElementById('lotStep').value = currency.lot_step;
    document.getElementById('spreadTypical').value = currency.spread_typical;
    document.getElementById('enabled').checked = currency.enabled;

    openModal();
}

/**
 * Delete currency
 */
async function deleteCurrency(symbol) {
    if (!confirm(`Delete custom currency ${symbol}? This action cannot be undone.`)) {
        return;
    }

    try {
        await api.request(`/config/currencies/${symbol}`, { method: 'DELETE' });

        showToast('success', 'Deleted', `Currency ${symbol} has been deleted`);
        await loadCurrencies();

    } catch (error) {
        console.error('Failed to delete currency:', error);
        showToast('error', 'Delete Failed', error.message);
    }
}

/**
 * Open modal
 */
function openModal() {
    if (!currentEditingSymbol) {
        // New currency - reset form
        document.getElementById('currencyForm').reset();
        document.getElementById('symbol').disabled = false;
        document.getElementById('modalTitle').textContent = 'Add Custom Currency';

        // Set defaults
        document.getElementById('digits').value = 5;
        document.getElementById('point').value = 0.00001;
        document.getElementById('contractSize').value = 100000;
        document.getElementById('minLot').value = 0.01;
        document.getElementById('maxLot').value = 100.0;
        document.getElementById('lotStep').value = 0.01;
        document.getElementById('spreadTypical').value = 0;
        document.getElementById('enabled').checked = true;
    }

    document.getElementById('currencyModal').classList.add('active');
}

/**
 * Close modal
 */
function closeModal() {
    document.getElementById('currencyModal').classList.remove('active');
    currentEditingSymbol = null;
    document.getElementById('currencyForm').reset();
}

/**
 * Save currency
 */
async function saveCurrency(e) {
    e.preventDefault();

    const formData = {
        symbol: document.getElementById('symbol').value.toUpperCase().trim(),
        description: document.getElementById('description').value.trim(),
        category: document.getElementById('category').value.trim(),
        digits: parseInt(document.getElementById('digits').value),
        point: parseFloat(document.getElementById('point').value),
        contract_size: parseInt(document.getElementById('contractSize').value),
        min_lot: parseFloat(document.getElementById('minLot').value),
        max_lot: parseFloat(document.getElementById('maxLot').value),
        lot_step: parseFloat(document.getElementById('lotStep').value),
        spread_typical: parseFloat(document.getElementById('spreadTypical').value),
        enabled: document.getElementById('enabled').checked
    };

    try {
        await api.request('/config/currencies', {
            method: 'POST',
            body: JSON.stringify(formData)
        });

        showToast('success', currentEditingSymbol ? 'Updated' : 'Created',
                 `Currency ${formData.symbol} ${currentEditingSymbol ? 'updated' : 'created'} successfully`);

        closeModal();
        await loadCurrencies();

    } catch (error) {
        console.error('Failed to save currency:', error);
        showToast('error', 'Save Failed', error.message);
    }
}

/**
 * Load preferences
 */
async function loadPreferences() {
    try {
        preferences = await api.request('/config/preferences');

        document.getElementById('defaultVolume').value = preferences.default_volume;
        document.getElementById('defaultSlPips').value = preferences.default_sl_pips || 0;
        document.getElementById('defaultTpPips').value = preferences.default_tp_pips || 0;
        document.getElementById('maxRiskPercent').value = preferences.max_risk_percent;
        document.getElementById('maxDailyLossPercent').value = preferences.max_daily_loss_percent;
        document.getElementById('maxPositions').value = preferences.max_positions;

    } catch (error) {
        console.error('Failed to load preferences:', error);
        showToast('error', 'Load Failed', error.message);
    }
}

/**
 * Save preferences
 */
async function savePreferences(e) {
    e.preventDefault();

    const updates = {
        default_volume: parseFloat(document.getElementById('defaultVolume').value),
        default_sl_pips: parseFloat(document.getElementById('defaultSlPips').value) || null,
        default_tp_pips: parseFloat(document.getElementById('defaultTpPips').value) || null,
        max_risk_percent: parseFloat(document.getElementById('maxRiskPercent').value),
        max_daily_loss_percent: parseFloat(document.getElementById('maxDailyLossPercent').value),
        max_positions: parseInt(document.getElementById('maxPositions').value)
    };

    try {
        await api.request('/config/preferences', {
            method: 'PUT',
            body: JSON.stringify(updates)
        });

        showToast('success', 'Saved', 'Preferences updated successfully');
        preferences = await api.request('/config/preferences');

    } catch (error) {
        console.error('Failed to save preferences:', error);
        showToast('error', 'Save Failed', error.message);
    }
}

/**
 * Load favorites and recent
 */
async function loadFavorites() {
    try {
        const [favorites, recent] = await Promise.all([
            api.request('/config/favorites'),
            api.request('/config/recent')
        ]);

        document.getElementById('favoritesCount').textContent = favorites.length;
        document.getElementById('recentCount').textContent = recent.length;

        // Render favorites
        const favoritesList = document.getElementById('favoritesList');
        const emptyFavorites = document.getElementById('emptyFavorites');

        if (favorites.length === 0) {
            favoritesList.innerHTML = '';
            emptyFavorites.style.display = 'block';
        } else {
            emptyFavorites.style.display = 'none';
            favoritesList.innerHTML = favorites.map(curr => `
                <div class="favorite-tag">
                    ${curr.symbol}
                    <button onclick="removeFavorite('${curr.symbol}')">×</button>
                </div>
            `).join('');
        }

        // Render recent
        const recentList = document.getElementById('recentList');
        const emptyRecent = document.getElementById('emptyRecent');

        if (recent.length === 0) {
            recentList.innerHTML = '';
            emptyRecent.style.display = 'block';
        } else {
            emptyRecent.style.display = 'none';
            recentList.innerHTML = recent.map(curr => `
                <div class="favorite-tag">
                    ${curr.symbol}
                </div>
            `).join('');
        }

    } catch (error) {
        console.error('Failed to load favorites:', error);
        showToast('error', 'Load Failed', error.message);
    }
}

/**
 * Remove favorite
 */
async function removeFavorite(symbol) {
    try {
        await api.request(`/config/favorites/${symbol}`, { method: 'DELETE' });
        showToast('success', 'Removed', `${symbol} removed from favorites`);
        await loadFavorites();
    } catch (error) {
        console.error('Failed to remove favorite:', error);
        showToast('error', 'Remove Failed', error.message);
    }
}

/**
 * Load statistics
 */
async function loadStats() {
    try {
        stats = await api.request('/config/stats');

        document.getElementById('totalCurrencies').textContent = stats.total_currencies;
        document.getElementById('enabledCurrencies').textContent = stats.enabled_currencies;
        document.getElementById('disabledCurrencies').textContent = stats.disabled_currencies;
        document.getElementById('customCurrencies').textContent = stats.custom_currencies;

        // Render category stats
        const categoryStats = document.getElementById('categoryStats');
        categoryStats.innerHTML = Object.entries(stats.categories).map(([category, data]) => `
            <div class="stat-card">
                <h4>${category}</h4>
                <div class="stat-value">${data.enabled}/${data.total}</div>
                <div class="stat-label">enabled</div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load stats:', error);
        showToast('error', 'Load Failed', error.message);
    }
}

/**
 * Export configuration
 */
async function exportConfig() {
    showToast('warning', 'Not Implemented', 'Export functionality coming soon');
}

/**
 * Import configuration
 */
async function importConfig() {
    showToast('warning', 'Not Implemented', 'Import functionality coming soon');
}

/**
 * Reset configuration
 */
async function resetConfig() {
    if (!confirm('⚠️ Reset all configuration to defaults? This will remove all custom currencies!')) {
        return;
    }

    try {
        await api.request('/config/reset', { method: 'POST' });
        showToast('success', 'Reset', 'Configuration reset to defaults');
        await loadAllData();
        await loadStats();
    } catch (error) {
        console.error('Failed to reset config:', error);
        showToast('error', 'Reset Failed', error.message);
    }
}

/**
 * Update status indicator
 */
function updateStatus(status, message) {
    statusText.textContent = message;

    statusDot.className = 'status-dot';
    if (status === 'success') {
        statusDot.classList.add('connected');
    } else if (status === 'error') {
        statusDot.classList.add('error');
    }
}

/**
 * Update last update timestamp
 */
function updateLastUpdate() {
    const now = new Date();
    lastUpdate.textContent = `Last updated: ${now.toLocaleTimeString()}`;
}

/**
 * Show toast notification
 */
function showToast(type, title, message) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : '⚠️';

    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Make functions globally accessible
window.toggleCurrency = toggleCurrency;
window.editCurrency = editCurrency;
window.deleteCurrency = deleteCurrency;
window.removeFavorite = removeFavorite;

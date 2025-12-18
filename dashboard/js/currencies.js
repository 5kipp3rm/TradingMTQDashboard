/**
 * Currency Configuration Management
 * Handles CRUD operations, filtering, and validation for currency pairs
 */

// API Client (already declared in api.js, so we use the global instance)

// State
let currencies = [];
let filteredCurrencies = [];
let currentEditingSymbol = null;

// DOM Elements
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const lastUpdate = document.getElementById('lastUpdate');

const totalCurrenciesEl = document.getElementById('totalCurrencies');
const enabledCurrenciesEl = document.getElementById('enabledCurrencies');
const disabledCurrenciesEl = document.getElementById('disabledCurrencies');

const searchInput = document.getElementById('searchInput');
const statusFilter = document.getElementById('statusFilter');
const strategyFilter = document.getElementById('strategyFilter');
const refreshBtn = document.getElementById('refreshBtn');

const addCurrencyBtn = document.getElementById('addCurrencyBtn');
const syncToYamlBtn = document.getElementById('syncToYamlBtn');
const reloadFromYamlBtn = document.getElementById('reloadFromYamlBtn');
const exportBtn = document.getElementById('exportBtn');
const importBtn = document.getElementById('importBtn');

const currenciesTableBody = document.getElementById('currenciesTableBody');

const modal = document.getElementById('currencyModal');
const modalTitle = document.getElementById('modalTitle');
const modalCloseBtn = document.getElementById('modalCloseBtn');
const currencyForm = document.getElementById('currencyForm');
const cancelBtn = document.getElementById('cancelBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadCurrencies();
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Filter controls
    searchInput.addEventListener('input', applyFilters);
    statusFilter.addEventListener('change', applyFilters);
    strategyFilter.addEventListener('change', applyFilters);
    refreshBtn.addEventListener('click', loadCurrencies);

    // Action buttons
    addCurrencyBtn.addEventListener('click', () => openModal());
    syncToYamlBtn.addEventListener('click', syncToYaml);
    reloadFromYamlBtn.addEventListener('click', reloadFromYaml);
    exportBtn.addEventListener('click', exportConfiguration);
    importBtn.addEventListener('click', importConfiguration);

    // Modal controls
    modalCloseBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    currencyForm.addEventListener('submit', handleFormSubmit);

    // Close modal on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Form validation
    document.getElementById('fast_period').addEventListener('input', validatePeriods);
    document.getElementById('slow_period').addEventListener('input', validatePeriods);
}

/**
 * Load currencies from API
 */
async function loadCurrencies() {
    try {
        updateStatus('loading', 'Loading currencies...');

        const response = await api.request('/currencies');

        currencies = response.currencies || [];
        filteredCurrencies = [...currencies];

        updateSummaryCards(response);
        applyFilters();
        updateStatus('success', `Loaded ${currencies.length} currencies`);
        updateLastUpdate();

    } catch (error) {
        console.error('Failed to load currencies:', error);
        updateStatus('error', 'Failed to load currencies');
        showToast('error', 'Load Failed', error.message);
        currenciesTableBody.innerHTML = '<tr><td colspan="10" class="loading-cell">Failed to load currencies</td></tr>';
    }
}

/**
 * Update summary cards
 */
function updateSummaryCards(data) {
    totalCurrenciesEl.textContent = data.total || 0;
    enabledCurrenciesEl.textContent = data.enabled_count || 0;
    disabledCurrenciesEl.textContent = (data.total - data.enabled_count) || 0;
}

/**
 * Apply filters to currency list
 */
function applyFilters() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const statusValue = statusFilter.value;
    const strategyValue = strategyFilter.value;

    filteredCurrencies = currencies.filter(currency => {
        // Search filter
        if (searchTerm && !currency.symbol.toLowerCase().includes(searchTerm)) {
            return false;
        }

        // Status filter
        if (statusValue === 'enabled' && !currency.enabled) {
            return false;
        }
        if (statusValue === 'disabled' && currency.enabled) {
            return false;
        }

        // Strategy filter
        if (strategyValue !== 'all' && currency.strategy_type !== strategyValue) {
            return false;
        }

        return true;
    });

    renderTable();
}

/**
 * Render currencies table
 */
function renderTable() {
    if (filteredCurrencies.length === 0) {
        currenciesTableBody.innerHTML = `
            <tr>
                <td colspan="10" class="empty-state">
                    <div class="empty-state-icon">💱</div>
                    <div class="empty-state-title">No Currencies Found</div>
                    <div class="empty-state-text">Try adjusting your filters or add a new currency configuration</div>
                </td>
            </tr>
        `;
        return;
    }

    currenciesTableBody.innerHTML = filteredCurrencies.map(currency => `
        <tr data-symbol="${currency.symbol}">
            <td><strong>${currency.symbol}</strong></td>
            <td>
                <span class="status-badge ${currency.enabled ? 'enabled' : 'disabled'}">
                    ${currency.enabled ? '✅ Enabled' : '❌ Disabled'}
                </span>
            </td>
            <td>
                <span class="strategy-badge">${currency.strategy_type}</span>
            </td>
            <td>${currency.timeframe}</td>
            <td>${currency.risk_percent.toFixed(1)}%</td>
            <td>${currency.fast_period} / ${currency.slow_period}</td>
            <td>${currency.sl_pips} / ${currency.tp_pips}</td>
            <td>${currency.max_total_positions}</td>
            <td>v${currency.config_version}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn action-btn-toggle" onclick="toggleCurrency('${currency.symbol}', ${!currency.enabled})">
                        ${currency.enabled ? '⏸️' : '▶️'}
                    </button>
                    <button class="action-btn action-btn-edit" onclick="editCurrency('${currency.symbol}')">
                        ✏️
                    </button>
                    <button class="action-btn action-btn-validate" onclick="validateCurrency('${currency.symbol}')">
                        ✓
                    </button>
                    <button class="action-btn action-btn-delete" onclick="deleteCurrency('${currency.symbol}')">
                        🗑️
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Toggle currency enabled status
 */
async function toggleCurrency(symbol, enable) {
    try {
        const action = enable ? 'enable' : 'disable';
        await api.request(`/currencies/${symbol}/${action}`, { method: 'POST' });

        showToast('success', 'Success', `Currency ${symbol} ${enable ? 'enabled' : 'disabled'}`);
        await loadCurrencies();

    } catch (error) {
        console.error(`Failed to ${enable ? 'enable' : 'disable'} currency:`, error);
        showToast('error', 'Action Failed', error.message);
    }
}

/**
 * Edit currency
 */
function editCurrency(symbol) {
    const currency = currencies.find(c => c.symbol === symbol);
    if (!currency) {
        showToast('error', 'Error', 'Currency not found');
        return;
    }

    currentEditingSymbol = symbol;
    modalTitle.textContent = `Edit ${symbol}`;

    // Populate form
    document.getElementById('symbol').value = currency.symbol;
    document.getElementById('symbol').disabled = true; // Can't change symbol
    document.getElementById('enabled').checked = currency.enabled;
    document.getElementById('description').value = currency.description || '';
    document.getElementById('risk_percent').value = currency.risk_percent;
    document.getElementById('max_position_size').value = currency.max_position_size;
    document.getElementById('min_position_size').value = currency.min_position_size;
    document.getElementById('strategy_type').value = currency.strategy_type;
    document.getElementById('timeframe').value = currency.timeframe;
    document.getElementById('fast_period').value = currency.fast_period;
    document.getElementById('slow_period').value = currency.slow_period;
    document.getElementById('sl_pips').value = currency.sl_pips;
    document.getElementById('tp_pips').value = currency.tp_pips;
    document.getElementById('cooldown_seconds').value = currency.cooldown_seconds;
    document.getElementById('trade_on_signal_change').checked = currency.trade_on_signal_change;
    document.getElementById('allow_position_stacking').checked = currency.allow_position_stacking;
    document.getElementById('max_positions_same_direction').value = currency.max_positions_same_direction;
    document.getElementById('max_total_positions').value = currency.max_total_positions;
    document.getElementById('stacking_risk_multiplier').value = currency.stacking_risk_multiplier;

    openModal();
}

/**
 * Validate currency configuration
 */
async function validateCurrency(symbol) {
    try {
        const currency = currencies.find(c => c.symbol === symbol);
        if (!currency) {
            showToast('error', 'Error', 'Currency not found');
            return;
        }

        const response = await api.request('/currencies/validate', {
            method: 'POST',
            body: JSON.stringify(currency)
        });

        if (response.is_valid) {
            showToast('success', 'Validation Passed', `${symbol} configuration is valid`);
        } else {
            const errorList = response.errors.join('\n');
            showToast('error', 'Validation Failed', errorList);
        }

    } catch (error) {
        console.error('Validation failed:', error);
        showToast('error', 'Validation Error', error.message);
    }
}

/**
 * Delete currency
 */
async function deleteCurrency(symbol) {
    if (!confirm(`Are you sure you want to delete ${symbol}? This action cannot be undone.`)) {
        return;
    }

    try {
        await api.request(`/currencies/${symbol}`, { method: 'DELETE' });

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
        currencyForm.reset();
        document.getElementById('symbol').disabled = false;
        modalTitle.textContent = 'Add Currency';

        // Set defaults
        document.getElementById('enabled').checked = true;
        document.getElementById('risk_percent').value = 1.0;
        document.getElementById('max_position_size').value = 1.0;
        document.getElementById('min_position_size').value = 0.01;
        document.getElementById('strategy_type').value = 'position';
        document.getElementById('timeframe').value = 'M15';
        document.getElementById('fast_period').value = 10;
        document.getElementById('slow_period').value = 20;
        document.getElementById('sl_pips').value = 20;
        document.getElementById('tp_pips').value = 40;
        document.getElementById('cooldown_seconds').value = 60;
        document.getElementById('trade_on_signal_change').checked = true;
        document.getElementById('allow_position_stacking').checked = false;
        document.getElementById('max_positions_same_direction').value = 1;
        document.getElementById('max_total_positions').value = 5;
        document.getElementById('stacking_risk_multiplier').value = 1.0;
    }

    modal.classList.add('active');
}

/**
 * Close modal
 */
function closeModal() {
    modal.classList.remove('active');
    currentEditingSymbol = null;
    currencyForm.reset();
    clearValidationErrors();
}

/**
 * Handle form submission
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    if (!validateForm()) {
        showToast('error', 'Validation Failed', 'Please fix the errors in the form');
        return;
    }

    const formData = getFormData();

    try {
        if (currentEditingSymbol) {
            // Update existing currency
            await api.request(`/currencies/${currentEditingSymbol}`, {
                method: 'PUT',
                body: JSON.stringify(formData)
            });
            showToast('success', 'Updated', `Currency ${currentEditingSymbol} updated successfully`);
        } else {
            // Create new currency
            await api.request('/currencies', {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            showToast('success', 'Created', `Currency ${formData.symbol} created successfully`);
        }

        closeModal();
        await loadCurrencies();

    } catch (error) {
        console.error('Failed to save currency:', error);
        showToast('error', 'Save Failed', error.message);
    }
}

/**
 * Get form data
 */
function getFormData() {
    return {
        symbol: document.getElementById('symbol').value.toUpperCase().trim(),
        enabled: document.getElementById('enabled').checked,
        description: document.getElementById('description').value.trim() || undefined,
        risk_percent: parseFloat(document.getElementById('risk_percent').value),
        max_position_size: parseFloat(document.getElementById('max_position_size').value),
        min_position_size: parseFloat(document.getElementById('min_position_size').value),
        strategy_type: document.getElementById('strategy_type').value,
        timeframe: document.getElementById('timeframe').value,
        fast_period: parseInt(document.getElementById('fast_period').value),
        slow_period: parseInt(document.getElementById('slow_period').value),
        sl_pips: parseInt(document.getElementById('sl_pips').value),
        tp_pips: parseInt(document.getElementById('tp_pips').value),
        cooldown_seconds: parseInt(document.getElementById('cooldown_seconds').value),
        trade_on_signal_change: document.getElementById('trade_on_signal_change').checked,
        allow_position_stacking: document.getElementById('allow_position_stacking').checked,
        max_positions_same_direction: parseInt(document.getElementById('max_positions_same_direction').value),
        max_total_positions: parseInt(document.getElementById('max_total_positions').value),
        stacking_risk_multiplier: parseFloat(document.getElementById('stacking_risk_multiplier').value)
    };
}

/**
 * Validate form
 */
function validateForm() {
    clearValidationErrors();
    let isValid = true;

    // Validate periods
    const fastPeriod = parseInt(document.getElementById('fast_period').value);
    const slowPeriod = parseInt(document.getElementById('slow_period').value);
    if (fastPeriod >= slowPeriod) {
        showFieldError('slow_period', 'Slow period must be greater than fast period');
        isValid = false;
    }

    // Validate risk percent
    const riskPercent = parseFloat(document.getElementById('risk_percent').value);
    if (riskPercent < 0.1 || riskPercent > 10.0) {
        showFieldError('risk_percent', 'Risk percent must be between 0.1 and 10.0');
        isValid = false;
    }

    // Validate position sizes
    const minPos = parseFloat(document.getElementById('min_position_size').value);
    const maxPos = parseFloat(document.getElementById('max_position_size').value);
    if (minPos > maxPos) {
        showFieldError('min_position_size', 'Min position size must be less than max');
        isValid = false;
    }

    return isValid;
}

/**
 * Validate periods on input
 */
function validatePeriods() {
    const fastPeriod = parseInt(document.getElementById('fast_period').value);
    const slowPeriod = parseInt(document.getElementById('slow_period').value);

    if (fastPeriod && slowPeriod && fastPeriod >= slowPeriod) {
        showFieldError('slow_period', 'Slow period must be greater than fast period');
    } else {
        clearFieldError('slow_period');
    }
}

/**
 * Show field validation error
 */
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const formGroup = field.closest('.form-group');
    formGroup.classList.add('has-error');

    let errorEl = formGroup.querySelector('.validation-error');
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.className = 'validation-error';
        formGroup.appendChild(errorEl);
    }
    errorEl.textContent = message;
}

/**
 * Clear field validation error
 */
function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const formGroup = field.closest('.form-group');
    formGroup.classList.remove('has-error');
}

/**
 * Clear all validation errors
 */
function clearValidationErrors() {
    document.querySelectorAll('.form-group').forEach(group => {
        group.classList.remove('has-error');
    });
}

/**
 * Sync to YAML
 */
async function syncToYaml() {
    if (!confirm('Sync all currencies to YAML file? This will overwrite the current YAML configuration.')) {
        return;
    }

    try {
        const response = await api.request('/currencies/sync-to-yaml', { method: 'POST' });

        if (response.success) {
            showToast('success', 'Synced', `${response.currency_count} currencies synced to YAML`);
        } else {
            showToast('error', 'Sync Failed', 'Failed to sync to YAML');
        }

    } catch (error) {
        console.error('Failed to sync to YAML:', error);
        showToast('error', 'Sync Failed', error.message);
    }
}

/**
 * Reload from YAML
 */
async function reloadFromYaml() {
    if (!confirm('Reload currencies from YAML file? This will update the database with YAML configuration.')) {
        return;
    }

    try {
        const response = await api.request('/currencies/reload', { method: 'POST' });

        showToast('success', 'Reloaded', `Added: ${response.added}, Updated: ${response.updated}`);

        if (response.errors && response.errors.length > 0) {
            console.warn('Reload errors:', response.errors);
            showToast('warning', 'Some Errors', `${response.errors.length} errors occurred`);
        }

        await loadCurrencies();

    } catch (error) {
        console.error('Failed to reload from YAML:', error);
        showToast('error', 'Reload Failed', error.message);
    }
}

/**
 * Export configuration
 */
async function exportConfiguration() {
    showToast('warning', 'Not Implemented', 'Export functionality coming soon');
}

/**
 * Import configuration
 */
async function importConfiguration() {
    showToast('warning', 'Not Implemented', 'Import functionality coming soon');
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
window.validateCurrency = validateCurrency;
window.deleteCurrency = deleteCurrency;

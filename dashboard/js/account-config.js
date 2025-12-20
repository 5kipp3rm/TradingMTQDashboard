/**
 * Account Configuration Management
 * Handles the enhanced configuration UI for trading accounts
 */

// API Configuration
if (typeof API_BASE_URL === 'undefined') {
    var API_BASE_URL = 'http://localhost:8000/api';
}

// Current account being configured
let currentConfigAccountId = null;
let currentConfigAccount = null;
let currencyPairsData = [];

// Default currency pairs
const DEFAULT_CURRENCY_PAIRS = [
    { symbol: 'EURUSD', name: 'Euro / US Dollar' },
    { symbol: 'GBPUSD', name: 'British Pound / US Dollar' },
    { symbol: 'USDJPY', name: 'US Dollar / Japanese Yen' },
    { symbol: 'AUDUSD', name: 'Australian Dollar / US Dollar' },
    { symbol: 'USDCAD', name: 'US Dollar / Canadian Dollar' },
    { symbol: 'NZDUSD', name: 'New Zealand Dollar / US Dollar' },
    { symbol: 'EURJPY', name: 'Euro / Japanese Yen' },
    { symbol: 'GBPJPY', name: 'British Pound / Japanese Yen' },
    { symbol: 'XAUUSD', name: 'Gold / US Dollar' },
];

// ============================================================================
// Modal Management
// ============================================================================

function openAccountConfig(accountId) {
    currentConfigAccountId = accountId;
    currentConfigAccount = accounts.find(a => a.id === accountId);

    if (!currentConfigAccount) {
        showToast('Account not found', 'error');
        return;
    }

    document.getElementById('configModalTitle').textContent =
        `Configure ${currentConfigAccount.account_name}`;
    document.getElementById('configAccountId').value = accountId;

    // Load existing configuration
    loadAccountConfiguration(accountId);

    // Show modal
    document.getElementById('accountConfigModal').classList.add('active');

    // Initialize tab switching
    initializeTabSwitching();
}

function closeAccountConfigModal() {
    document.getElementById('accountConfigModal').classList.remove('active');
    currentConfigAccountId = null;
    currentConfigAccount = null;
    currencyPairsData = [];
}

// ============================================================================
// Tab Management
// ============================================================================

function initializeTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked tab
            button.classList.add('active');
            document.getElementById(`${tabName}Tab`).classList.add('active');
        });
    });
}

// ============================================================================
// Configuration Loading
// ============================================================================

async function loadAccountConfiguration(accountId) {
    try {
        // Load current configuration from API
        const response = await fetch(`${API_BASE_URL}/accounts/${accountId}/config`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const config = await response.json();

        // Populate form with existing configuration
        populateConfigurationForm(config);

    } catch (error) {
        console.error('Failed to load account configuration:', error);

        // Load defaults if no configuration exists
        populateDefaultConfiguration();
    }
}

function populateConfigurationForm(config) {
    // General Settings
    document.getElementById('configSource').value = config.config_source || 'hybrid';
    document.getElementById('configPath').value = config.config_path || '';
    document.getElementById('portable').checked = config.portable !== false;

    // Risk Management
    const risk = config.trading_config?.risk || {};
    document.getElementById('riskPercent').value = risk.risk_percent || 1.0;
    document.getElementById('maxPositions').value = risk.max_positions || 5;
    document.getElementById('maxConcurrentTrades').value = risk.max_concurrent_trades || 15;
    document.getElementById('portfolioRiskPercent').value = risk.portfolio_risk_percent || 10.0;
    document.getElementById('stopLossPips').value = risk.stop_loss_pips || 50;
    document.getElementById('takeProfitPips').value = risk.take_profit_pips || 100;

    // Strategy Settings
    const strategy = config.trading_config?.strategy || {};
    document.getElementById('strategyType').value = strategy.strategy_type || 'SIMPLE_MA';
    document.getElementById('timeframe').value = strategy.timeframe || 'M5';
    document.getElementById('fastPeriod').value = strategy.fast_period || 10;
    document.getElementById('slowPeriod').value = strategy.slow_period || 20;

    // Position Management
    const positionMgmt = config.trading_config?.position_management || {};
    document.getElementById('enableBreakeven').checked = positionMgmt.enable_breakeven !== false;
    document.getElementById('breakevenTrigger').value = positionMgmt.breakeven_trigger_pips || 15;
    document.getElementById('breakevenOffset').value = positionMgmt.breakeven_offset_pips || 2;
    document.getElementById('enableTrailing').checked = positionMgmt.enable_trailing !== false;
    document.getElementById('trailingStart').value = positionMgmt.trailing_start_pips || 20;
    document.getElementById('trailingDistance').value = positionMgmt.trailing_distance_pips || 10;
    document.getElementById('enablePartialClose').checked = positionMgmt.enable_partial_close === true;
    document.getElementById('partialClosePercent').value = positionMgmt.partial_close_percent || 50;
    document.getElementById('partialCloseProfit').value = positionMgmt.partial_close_profit_pips || 25;

    // Currency Pairs
    currencyPairsData = config.trading_config?.currencies || [];
    renderCurrencyPairs();
}

function populateDefaultConfiguration() {
    // Use default values (already set in HTML)
    currencyPairsData = [];
    renderCurrencyPairs();
}

// ============================================================================
// Currency Pairs Management
// ============================================================================

function renderCurrencyPairs() {
    const container = document.getElementById('currencyPairsList');

    if (currencyPairsData.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-coins" style="font-size: 3rem; color: #ccc;"></i>
                <p>No currency pairs configured</p>
                <button type="button" class="btn btn-primary" onclick="loadDefaultPairs()">
                    Load Default Pairs
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = currencyPairsData.map((pair, index) => `
        <div class="currency-pair-card" data-index="${index}">
            <div class="currency-pair-header">
                <div class="currency-pair-title">
                    <h4>${pair.symbol}</h4>
                    <label class="checkbox-label">
                        <input type="checkbox" ${pair.enabled ? 'checked' : ''}
                               onchange="toggleCurrencyPair(${index})">
                        Enabled
                    </label>
                </div>
                <button type="button" class="btn-icon delete" onclick="removeCurrencyPair(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>

            <div class="currency-pair-config ${pair.enabled ? '' : 'disabled'}">
                <div class="form-row">
                    <div class="form-group">
                        <label>Risk Per Trade (%)</label>
                        <input type="number" step="0.1" min="0.1" max="10"
                               value="${pair.risk?.risk_percent || 1.0}"
                               onchange="updateCurrencyPair(${index}, 'risk.risk_percent', this.value)">
                    </div>
                    <div class="form-group">
                        <label>Max Positions</label>
                        <input type="number" min="1" max="10"
                               value="${pair.risk?.max_positions || 3}"
                               onchange="updateCurrencyPair(${index}, 'risk.max_positions', this.value)">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Stop Loss (Pips)</label>
                        <input type="number" min="5" max="500"
                               value="${pair.risk?.stop_loss_pips || 50}"
                               onchange="updateCurrencyPair(${index}, 'risk.stop_loss_pips', this.value)">
                    </div>
                    <div class="form-group">
                        <label>Take Profit (Pips)</label>
                        <input type="number" min="10" max="1000"
                               value="${pair.risk?.take_profit_pips || 100}"
                               onchange="updateCurrencyPair(${index}, 'risk.take_profit_pips', this.value)">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Timeframe</label>
                        <select onchange="updateCurrencyPair(${index}, 'strategy.timeframe', this.value)">
                            <option value="M1" ${pair.strategy?.timeframe === 'M1' ? 'selected' : ''}>M1</option>
                            <option value="M5" ${pair.strategy?.timeframe === 'M5' ? 'selected' : ''}>M5</option>
                            <option value="M15" ${pair.strategy?.timeframe === 'M15' ? 'selected' : ''}>M15</option>
                            <option value="M30" ${pair.strategy?.timeframe === 'M30' ? 'selected' : ''}>M30</option>
                            <option value="H1" ${pair.strategy?.timeframe === 'H1' ? 'selected' : ''}>H1</option>
                            <option value="H4" ${pair.strategy?.timeframe === 'H4' ? 'selected' : ''}>H4</option>
                            <option value="D1" ${pair.strategy?.timeframe === 'D1' ? 'selected' : ''}>D1</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Strategy</label>
                        <select onchange="updateCurrencyPair(${index}, 'strategy.strategy_type', this.value)">
                            <option value="SIMPLE_MA" ${pair.strategy?.strategy_type === 'SIMPLE_MA' ? 'selected' : ''}>Simple MA</option>
                            <option value="RSI" ${pair.strategy?.strategy_type === 'RSI' ? 'selected' : ''}>RSI</option>
                            <option value="MACD" ${pair.strategy?.strategy_type === 'MACD' ? 'selected' : ''}>MACD</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function addCurrencyPair() {
    const symbol = prompt('Enter currency pair symbol (e.g., EURUSD):');

    if (!symbol) return;

    const normalizedSymbol = symbol.toUpperCase().trim();

    // Check if pair already exists
    if (currencyPairsData.some(p => p.symbol === normalizedSymbol)) {
        showToast(`Currency pair ${normalizedSymbol} already exists`, 'warning');
        return;
    }

    // Add new pair with default configuration
    currencyPairsData.push({
        symbol: normalizedSymbol,
        enabled: true,
        risk: {
            risk_percent: 1.0,
            max_positions: 3,
            stop_loss_pips: 50,
            take_profit_pips: 100
        },
        strategy: {
            strategy_type: 'SIMPLE_MA',
            timeframe: 'M5',
            fast_period: 10,
            slow_period: 20
        }
    });

    renderCurrencyPairs();
    showToast(`Added currency pair: ${normalizedSymbol}`, 'success');
}

function loadDefaultPairs() {
    if (currencyPairsData.length > 0) {
        if (!confirm('This will replace existing currency pairs. Continue?')) {
            return;
        }
    }

    currencyPairsData = DEFAULT_CURRENCY_PAIRS.slice(0, 4).map(pair => ({
        symbol: pair.symbol,
        enabled: true,
        risk: {
            risk_percent: 1.0,
            max_positions: 3,
            stop_loss_pips: 50,
            take_profit_pips: 100
        },
        strategy: {
            strategy_type: 'SIMPLE_MA',
            timeframe: 'M5',
            fast_period: 10,
            slow_period: 20
        }
    }));

    renderCurrencyPairs();
    showToast('Loaded default currency pairs', 'success');
}

function removeCurrencyPair(index) {
    if (!confirm(`Remove ${currencyPairsData[index].symbol}?`)) {
        return;
    }

    currencyPairsData.splice(index, 1);
    renderCurrencyPairs();
    showToast('Currency pair removed', 'success');
}

function toggleCurrencyPair(index) {
    currencyPairsData[index].enabled = !currencyPairsData[index].enabled;
    renderCurrencyPairs();
}

function updateCurrencyPair(index, path, value) {
    const keys = path.split('.');
    let obj = currencyPairsData[index];

    // Navigate to the nested property
    for (let i = 0; i < keys.length - 1; i++) {
        if (!obj[keys[i]]) {
            obj[keys[i]] = {};
        }
        obj = obj[keys[i]];
    }

    // Set the value (convert to number if it's a numeric field)
    const numValue = parseFloat(value);
    obj[keys[keys.length - 1]] = isNaN(numValue) ? value : numValue;
}

// ============================================================================
// Form Submission
// ============================================================================

document.getElementById('accountConfigForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveAccountConfiguration();
});

async function saveAccountConfiguration() {
    try {
        showToast('Saving configuration...', 'info');

        const accountId = currentConfigAccountId;

        // Gather all form data
        const configData = {
            config_source: document.getElementById('configSource').value,
            config_path: document.getElementById('configPath').value,
            portable: document.getElementById('portable').checked,
            trading_config: {
                risk: {
                    risk_percent: parseFloat(document.getElementById('riskPercent').value),
                    max_positions: parseInt(document.getElementById('maxPositions').value),
                    max_concurrent_trades: parseInt(document.getElementById('maxConcurrentTrades').value),
                    portfolio_risk_percent: parseFloat(document.getElementById('portfolioRiskPercent').value),
                    stop_loss_pips: parseFloat(document.getElementById('stopLossPips').value),
                    take_profit_pips: parseFloat(document.getElementById('takeProfitPips').value)
                },
                strategy: {
                    strategy_type: document.getElementById('strategyType').value,
                    timeframe: document.getElementById('timeframe').value,
                    fast_period: parseInt(document.getElementById('fastPeriod').value),
                    slow_period: parseInt(document.getElementById('slowPeriod').value)
                },
                position_management: {
                    enable_breakeven: document.getElementById('enableBreakeven').checked,
                    breakeven_trigger_pips: parseFloat(document.getElementById('breakevenTrigger').value),
                    breakeven_offset_pips: parseFloat(document.getElementById('breakevenOffset').value),
                    enable_trailing: document.getElementById('enableTrailing').checked,
                    trailing_start_pips: parseFloat(document.getElementById('trailingStart').value),
                    trailing_distance_pips: parseFloat(document.getElementById('trailingDistance').value),
                    enable_partial_close: document.getElementById('enablePartialClose').checked,
                    partial_close_percent: parseFloat(document.getElementById('partialClosePercent').value),
                    partial_close_profit_pips: parseFloat(document.getElementById('partialCloseProfit').value)
                },
                currencies: currencyPairsData
            }
        };

        // Save configuration
        const response = await fetch(`${API_BASE_URL}/accounts/${accountId}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save configuration');
        }

        const result = await response.json();

        showToast('✅ Configuration saved successfully!', 'success');
        closeAccountConfigModal();

        // Reload accounts to reflect changes
        if (typeof loadAccounts === 'function') {
            await loadAccounts();
        }

    } catch (error) {
        console.error('Failed to save configuration:', error);
        showToast(`Failed to save: ${error.message}`, 'error');
    }
}

// ============================================================================
// Helper Functions
// ============================================================================

function generateYAMLPath() {
    if (!currentConfigAccount) {
        showToast('No account selected', 'error');
        return;
    }

    const accountNumber = currentConfigAccount.account_number;
    const path = `config/accounts/account-${accountNumber}.yml`;
    document.getElementById('configPath').value = path;
    showToast(`Generated path: ${path}`, 'success');
}

async function exportToYAML() {
    try {
        showToast('Exporting configuration to YAML...', 'info');

        const accountId = currentConfigAccountId;
        const outputPath = document.getElementById('configPath').value || null;

        const response = await fetch(`${API_BASE_URL}/accounts/${accountId}/config/export-yaml`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ output_path: outputPath })
        });

        if (!response.ok) {
            throw new Error('Failed to export configuration');
        }

        const result = await response.json();

        showToast(`✅ Exported to: ${result.output_path}`, 'success');
        document.getElementById('configPath').value = result.output_path;

    } catch (error) {
        console.error('Export failed:', error);
        showToast(`Export failed: ${error.message}`, 'error');
    }
}

function previewConfig() {
    // Gather current form data
    const config = {
        risk: {
            risk_percent: parseFloat(document.getElementById('riskPercent').value),
            max_positions: parseInt(document.getElementById('maxPositions').value),
            max_concurrent_trades: parseInt(document.getElementById('maxConcurrentTrades').value),
        },
        currencies: currencyPairsData
    };

    console.log('Current Configuration:', config);
    alert('Configuration preview:\n\n' + JSON.stringify(config, null, 2));
}

// Make functions globally available
window.openAccountConfig = openAccountConfig;
window.closeAccountConfigModal = closeAccountConfigModal;
window.addCurrencyPair = addCurrencyPair;
window.loadDefaultPairs = loadDefaultPairs;
window.removeCurrencyPair = removeCurrencyPair;
window.toggleCurrencyPair = toggleCurrencyPair;
window.updateCurrencyPair = updateCurrencyPair;
window.generateYAMLPath = generateYAMLPath;
window.exportToYAML = exportToYAML;
window.previewConfig = previewConfig;

console.log('Account Configuration module loaded');

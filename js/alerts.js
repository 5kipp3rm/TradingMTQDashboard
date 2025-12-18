/**
 * Alert Settings Management
 */

const API_URL = 'http://localhost:8000/api';

// Alert type display names
const ALERT_TYPE_NAMES = {
    'trade_opened': 'Trade Opened',
    'trade_closed': 'Trade Closed',
    'daily_summary': 'Daily Summary',
    'error_alert': 'Error Alerts',
    'profit_threshold': 'Profit Threshold',
    'loss_threshold': 'Loss Threshold'
};

// Alert type descriptions
const ALERT_TYPE_DESCRIPTIONS = {
    'trade_opened': 'Notify when a new trade is opened',
    'trade_closed': 'Notify when a trade is closed (profit or loss)',
    'daily_summary': 'Daily performance summary email',
    'error_alert': 'System errors and critical issues',
    'profit_threshold': 'Notify when profit exceeds threshold',
    'loss_threshold': 'Notify when loss exceeds threshold'
};

/**
 * Initialize the alerts page
 */
async function initAlertsPage() {
    showNotification('Loading alert configurations...', 'info');

    try {
        // Get available alert types
        const typesResponse = await fetch(`${API_URL}/alerts/types`);
        const typesData = await typesResponse.json();

        // Get existing configurations
        const configsResponse = await fetch(`${API_URL}/alerts/config`);
        const configs = await configsResponse.json();

        // Create a map of existing configs
        const configMap = {};
        configs.forEach(config => {
            configMap[config.alert_type] = config;
        });

        // Render alert configuration cards
        const container = document.getElementById('alert-configs-container');
        container.innerHTML = '';

        typesData.alert_types.forEach(alertType => {
            const config = configMap[alertType] || createDefaultConfig(alertType);
            container.appendChild(createAlertConfigCard(alertType, config));
        });

        hideNotification();
    } catch (error) {
        showNotification(`Error loading configurations: ${error.message}`, 'error');
    }
}

/**
 * Create default configuration for alert type
 */
function createDefaultConfig(alertType) {
    return {
        id: null,
        alert_type: alertType,
        enabled: false,
        email_enabled: true,
        sms_enabled: false,
        websocket_enabled: true,
        email_recipients: [],
        sms_recipients: [],
        profit_threshold: null,
        loss_threshold: null,
        symbol_filter: []
    };
}

/**
 * Create alert configuration card
 */
function createAlertConfigCard(alertType, config) {
    const card = document.createElement('div');
    card.className = 'alert-config-card';
    card.id = `config-${alertType}`;

    const isNew = !config.id;

    card.innerHTML = `
        <div class="alert-config-header">
            <div>
                <h3>${ALERT_TYPE_NAMES[alertType] || alertType}</h3>
                <p style="margin: 5px 0 0 0; color: #888; font-size: 14px;">
                    ${ALERT_TYPE_DESCRIPTIONS[alertType] || ''}
                </p>
            </div>
            <label class="toggle-switch">
                <input type="checkbox" ${config.enabled ? 'checked' : ''}
                       onchange="toggleAlert('${alertType}', this.checked)">
                <span class="toggle-slider"></span>
            </label>
        </div>

        <div class="alert-config-content" style="display: ${config.enabled ? 'block' : 'none'};">
            <div class="form-group">
                <label>Notification Channels</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" ${config.email_enabled ? 'checked' : ''}
                               data-field="email_enabled">
                        Email
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" ${config.websocket_enabled ? 'checked' : ''}
                               data-field="websocket_enabled">
                        Real-time (WebSocket)
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" ${config.sms_enabled ? 'checked' : ''}
                               data-field="sms_enabled" disabled>
                        SMS (Coming Soon)
                    </label>
                </div>
            </div>

            <div class="form-group">
                <label>Email Recipients (comma-separated)</label>
                <input type="text"
                       value="${config.email_recipients.join(', ')}"
                       placeholder="email1@example.com, email2@example.com"
                       data-field="email_recipients">
            </div>

            ${(alertType === 'profit_threshold' || alertType === 'loss_threshold') ? `
            <div class="form-group">
                <label>${alertType === 'profit_threshold' ? 'Profit' : 'Loss'} Threshold ($)</label>
                <input type="number"
                       step="0.01"
                       value="${config[alertType === 'profit_threshold' ? 'profit_threshold' : 'loss_threshold'] || ''}"
                       placeholder="100.00"
                       data-field="${alertType === 'profit_threshold' ? 'profit_threshold' : 'loss_threshold'}">
            </div>
            ` : ''}

            <div class="form-group">
                <label>Symbol Filter (optional, comma-separated)</label>
                <input type="text"
                       value="${config.symbol_filter.join(', ')}"
                       placeholder="EURUSD, GBPUSD"
                       data-field="symbol_filter">
                <small style="color: #888;">Leave empty to receive alerts for all symbols</small>
            </div>

            <button class="save-button" onclick="saveAlertConfig('${alertType}', ${isNew})">
                ${isNew ? 'Create Configuration' : 'Save Changes'}
            </button>
        </div>
    `;

    return card;
}

/**
 * Toggle alert enabled/disabled
 */
async function toggleAlert(alertType, enabled) {
    const card = document.getElementById(`config-${alertType}`);
    const content = card.querySelector('.alert-config-content');

    // Show/hide configuration
    content.style.display = enabled ? 'block' : 'none';

    // If disabling, save the change
    if (!enabled) {
        const config = await getConfigFromCard(alertType);
        config.enabled = false;
        await saveConfig(alertType, config, false);
    }
}

/**
 * Get configuration from card inputs
 */
async function getConfigFromCard(alertType) {
    const card = document.getElementById(`config-${alertType}`);
    const inputs = card.querySelectorAll('[data-field]');

    const config = {
        alert_type: alertType,
        enabled: card.querySelector('.toggle-switch input').checked,
        email_enabled: false,
        sms_enabled: false,
        websocket_enabled: false,
        email_recipients: '',
        sms_recipients: '',
        profit_threshold: null,
        loss_threshold: null,
        symbol_filter: ''
    };

    inputs.forEach(input => {
        const field = input.getAttribute('data-field');

        if (input.type === 'checkbox') {
            config[field] = input.checked;
        } else if (input.type === 'number') {
            config[field] = input.value ? parseFloat(input.value) : null;
        } else {
            config[field] = input.value;
        }
    });

    return config;
}

/**
 * Save alert configuration
 */
async function saveAlertConfig(alertType, isNew) {
    const button = document.querySelector(`#config-${alertType} .save-button`);
    button.disabled = true;
    button.innerHTML = 'Saving... <span class="loading"></span>';

    try {
        const config = await getConfigFromCard(alertType);
        await saveConfig(alertType, config, isNew);

        showNotification('Configuration saved successfully!', 'success');
        button.innerHTML = isNew ? 'Create Configuration' : 'Save Changes';

        // Reload to get the ID if it was a new config
        if (isNew) {
            setTimeout(() => initAlertsPage(), 1000);
        }
    } catch (error) {
        showNotification(`Error saving configuration: ${error.message}`, 'error');
        button.innerHTML = isNew ? 'Create Configuration' : 'Save Changes';
    } finally {
        button.disabled = false;
    }
}

/**
 * Save configuration to API
 */
async function saveConfig(alertType, config, isNew) {
    const url = `${API_URL}/alerts/config${isNew ? '' : `/${alertType}`}`;
    const method = isNew ? 'POST' : 'PUT';

    const response = await fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save configuration');
    }

    return await response.json();
}

/**
 * Send test email
 */
async function sendTestEmail() {
    const emailInput = document.getElementById('test-email');
    const email = emailInput.value.trim();

    if (!email) {
        showNotification('Please enter an email address', 'error');
        return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }

    showNotification('Sending test email...', 'info');

    try {
        const response = await fetch(`${API_URL}/alerts/test-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        });

        const result = await response.json();

        if (result.success) {
            showNotification(`Test email sent to ${email}! Check your inbox.`, 'success');
        } else {
            showNotification(`Failed to send test email: ${result.message}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
}

/**
 * Hide notification message
 */
function hideNotification() {
    const notification = document.getElementById('notification');
    notification.className = 'notification';
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', initAlertsPage);

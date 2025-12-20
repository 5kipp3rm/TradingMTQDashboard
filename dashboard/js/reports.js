/**
 * Reports Management JavaScript
 * Handles report configuration CRUD, quick generation, and history display
 */

// Only declare if not already defined
if (typeof API_BASE_URL === 'undefined') {
    var API_BASE_URL = '/api';
}

// State management
let currentEditingId = null;
let accounts = [];
let reportConfigurations = [];
let reportHistory = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeReportsPage();
});

/**
 * Initialize the reports page
 */
async function initializeReportsPage() {
    // Set default dates for quick generate
    setDefaultDates();

    // Load accounts
    await loadAccounts();

    // Load reports
    await loadReportConfigurations();

    // Load history
    await loadReportHistory();

    // Setup event listeners
    setupEventListeners();

    updateStatus('Ready', 'success');
}

/**
 * Set default dates for quick generate form
 */
function setDefaultDates() {
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);

    document.getElementById('quickEndDate').valueAsDate = today;
    document.getElementById('quickStartDate').valueAsDate = thirtyDaysAgo;
}

/**
 * Load trading accounts
 */
async function loadAccounts() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts`);
        if (!response.ok) throw new Error('Failed to load accounts');

        const data = await response.json();
        accounts = data.accounts || [];

        // Populate account selectors
        populateAccountSelectors();
    } catch (error) {
        console.error('Error loading accounts:', error);
        showMessage('Failed to load accounts', 'error');
    }
}

/**
 * Populate account selector dropdowns
 */
function populateAccountSelectors() {
    const selectors = ['quickAccount', 'reportAccount'];

    selectors.forEach(selectorId => {
        const select = document.getElementById(selectorId);
        if (!select) return;

        // Clear existing options except "All Accounts"
        while (select.options.length > 1) {
            select.remove(1);
        }

        // Add account options
        accounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account.id;
            option.textContent = `${account.account_name} (${account.account_number})`;
            select.appendChild(option);
        });
    });
}

/**
 * Load report configurations
 */
async function loadReportConfigurations() {
    try {
        const showInactive = document.getElementById('showInactive').checked;
        const url = `${API_BASE_URL}/reports/configurations?active_only=${!showInactive}`;

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load reports');

        const data = await response.json();
        reportConfigurations = data.configurations || [];

        renderReportConfigurations();
    } catch (error) {
        console.error('Error loading reports:', error);
        showMessage('Failed to load report configurations', 'error');
    }
}

/**
 * Render report configurations
 */
function renderReportConfigurations() {
    const container = document.getElementById('reportsContainer');
    const emptyState = document.getElementById('emptyState');

    if (reportConfigurations.length === 0) {
        container.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';

    container.innerHTML = reportConfigurations.map(config => `
        <div class="report-card ${!config.is_active ? 'inactive' : ''}">
            <div class="report-card-header">
                <h3 class="report-card-title">${escapeHtml(config.name)}</h3>
                <span class="report-badge ${config.is_active ? 'active' : 'inactive'}">
                    ${config.is_active ? '✓ Active' : '✕ Inactive'}
                </span>
            </div>

            <div class="report-card-body">
                ${config.description ? `<p style="color: #6c757d; margin-bottom: 10px;">${escapeHtml(config.description)}</p>` : ''}

                <div class="report-detail">
                    <span class="report-detail-label">Frequency:</span>
                    <span class="report-detail-value">${formatFrequency(config)}</span>
                </div>
                <div class="report-detail">
                    <span class="report-detail-label">Recipients:</span>
                    <span class="report-detail-value">${config.recipients.split(',').length} email(s)</span>
                </div>
                <div class="report-detail">
                    <span class="report-detail-label">Last Run:</span>
                    <span class="report-detail-value">${config.last_run ? formatDateTime(config.last_run) : 'Never'}</span>
                </div>
                <div class="report-detail">
                    <span class="report-detail-label">Next Run:</span>
                    <span class="report-detail-value">${config.next_run ? formatDateTime(config.next_run) : 'Not scheduled'}</span>
                </div>
                <div class="report-detail">
                    <span class="report-detail-label">Success Rate:</span>
                    <span class="report-detail-value">${calculateSuccessRate(config)}</span>
                </div>
            </div>

            <div class="report-card-footer">
                <button class="btn btn-secondary btn-sm" onclick="editReport(${config.id})">✏️ Edit</button>
                <button class="btn btn-secondary btn-sm" onclick="triggerReportNow(${config.id})">▶️ Run Now</button>
                ${config.is_active
                    ? `<button class="btn btn-secondary btn-sm" onclick="toggleReportStatus(${config.id}, false)">⏸️ Pause</button>`
                    : `<button class="btn btn-primary btn-sm" onclick="toggleReportStatus(${config.id}, true)">▶️ Activate</button>`
                }
                <button class="btn btn-secondary btn-sm" onclick="deleteReport(${config.id})" style="color: #dc3545;">🗑️</button>
            </div>
        </div>
    `).join('');
}

/**
 * Format frequency display
 */
function formatFrequency(config) {
    let freq = config.frequency.charAt(0).toUpperCase() + config.frequency.slice(1);

    if (config.frequency === 'weekly' && config.day_of_week !== null) {
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        freq += ` (${days[config.day_of_week]})`;
    } else if (config.frequency === 'monthly' && config.day_of_month) {
        freq += ` (Day ${config.day_of_month})`;
    }

    if (config.time_of_day) {
        freq += ` at ${config.time_of_day}`;
    }

    return freq;
}

/**
 * Calculate success rate
 */
function calculateSuccessRate(config) {
    if (!config.run_count || config.run_count === 0) return 'N/A';
    // This would need to be calculated from history, for now show run count
    return `${config.run_count} runs`;
}

/**
 * Load report history
 */
async function loadReportHistory() {
    try {
        const filter = document.getElementById('historyFilter').value;
        const limit = document.getElementById('historyLimit').value;

        const params = new URLSearchParams();
        if (filter === 'success') params.append('success_only', 'true');
        params.append('limit', limit);

        const url = `${API_BASE_URL}/reports/history?${params}`;
        const response = await fetch(url);

        if (!response.ok) throw new Error('Failed to load history');

        const data = await response.json();
        reportHistory = data.history || [];

        renderReportHistory();
    } catch (error) {
        console.error('Error loading history:', error);
        showMessage('Failed to load report history', 'error');
    }
}

/**
 * Render report history table
 */
function renderReportHistory() {
    const tbody = document.getElementById('historyTableBody');

    if (reportHistory.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #6c757d;">No history records found</td></tr>';
        return;
    }

    tbody.innerHTML = reportHistory.map(record => `
        <tr>
            <td>${formatDateTime(record.generated_at)}</td>
            <td>${getConfigName(record.config_id)}</td>
            <td>${formatDate(record.report_start_date)} - ${formatDate(record.report_end_date)}</td>
            <td><span class="status-badge ${record.success ? 'success' : 'failed'}">${record.success ? '✓ Success' : '✕ Failed'}</span></td>
            <td><span class="email-badge ${record.email_sent ? 'sent' : 'not-sent'}">${record.email_sent ? '✓ Sent' : '✕ Not sent'}</span></td>
            <td>${formatFileSize(record.file_size)}</td>
            <td>${record.execution_time_ms ? `${record.execution_time_ms}ms` : '-'}</td>
            <td>
                ${record.success && record.file_path
                    ? `<button class="btn btn-secondary btn-sm" onclick="viewReport('${record.file_path}')">👁️</button>`
                    : record.error_message
                        ? `<button class="btn btn-secondary btn-sm" onclick="showError('${escapeHtml(record.error_message)}')">⚠️</button>`
                        : '-'
                }
            </td>
        </tr>
    `).join('');
}

/**
 * Get config name by ID
 */
function getConfigName(configId) {
    const config = reportConfigurations.find(c => c.id === configId);
    return config ? escapeHtml(config.name) : `Config #${configId}`;
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Quick generate form
    document.getElementById('quickGenerateForm').addEventListener('submit', handleQuickGenerate);

    // New report button
    document.getElementById('newReportBtn').addEventListener('click', () => openReportModal());
    document.getElementById('createFirstReport').addEventListener('click', () => openReportModal());

    // Report form
    document.getElementById('reportForm').addEventListener('submit', handleSaveReport);

    // Modal controls
    document.getElementById('closeModal').addEventListener('click', closeReportModal);
    document.getElementById('cancelModal').addEventListener('click', closeReportModal);

    // Frequency change
    document.getElementById('reportFrequency').addEventListener('change', handleFrequencyChange);

    // Refresh buttons
    document.getElementById('refreshReportsBtn').addEventListener('click', loadReportConfigurations);

    // Show inactive toggle
    document.getElementById('showInactive').addEventListener('change', loadReportConfigurations);

    // History filter
    document.getElementById('historyFilter').addEventListener('change', loadReportHistory);
    document.getElementById('historyLimit').addEventListener('change', loadReportHistory);

    // Close modal on outside click
    window.addEventListener('click', (event) => {
        const modal = document.getElementById('reportModal');
        if (event.target === modal) {
            closeReportModal();
        }
    });
}

/**
 * Handle quick generate form submission
 */
async function handleQuickGenerate(e) {
    e.preventDefault();

    const formData = {
        start_date: document.getElementById('quickStartDate').value,
        end_date: document.getElementById('quickEndDate').value,
        account_id: document.getElementById('quickAccount').value || null,
        include_trades: document.getElementById('quickIncludeTrades').checked,
        include_charts: document.getElementById('quickIncludeCharts').checked
    };

    try {
        updateStatus('Generating report...', 'info');

        const response = await fetch(`${API_BASE_URL}/reports/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate report');
        }

        const result = await response.json();

        showMessage(`Report generated successfully! File: ${result.report_path}`, 'success');
        updateStatus('Ready', 'success');

        // Reload history
        await loadReportHistory();
    } catch (error) {
        console.error('Error generating report:', error);
        showMessage(`Failed to generate report: ${error.message}`, 'error');
        updateStatus('Ready', 'success');
    }
}

/**
 * Open report modal for create/edit
 */
function openReportModal(config = null) {
    currentEditingId = config ? config.id : null;

    const modal = document.getElementById('reportModal');
    const title = document.getElementById('modalTitle');
    const saveBtn = document.getElementById('saveReportBtn');

    if (config) {
        title.textContent = 'Edit Report Schedule';
        saveBtn.textContent = 'Update Report';
        populateFormWithConfig(config);
    } else {
        title.textContent = 'Create Report Schedule';
        saveBtn.textContent = 'Create Report';
        document.getElementById('reportForm').reset();
        document.getElementById('reportTimeOfDay').value = '09:00';
        document.getElementById('reportDaysLookback').value = '30';
        handleFrequencyChange(); // Hide conditional fields
    }

    modal.classList.add('show');
}

/**
 * Close report modal
 */
function closeReportModal() {
    const modal = document.getElementById('reportModal');
    modal.classList.remove('show');
    currentEditingId = null;
}

/**
 * Populate form with config data
 */
function populateFormWithConfig(config) {
    document.getElementById('reportName').value = config.name;
    document.getElementById('reportDescription').value = config.description || '';
    document.getElementById('reportFrequency').value = config.frequency;
    document.getElementById('reportDayOfWeek').value = config.day_of_week !== null ? config.day_of_week : '0';
    document.getElementById('reportDayOfMonth').value = config.day_of_month || '1';
    document.getElementById('reportTimeOfDay').value = config.time_of_day || '09:00';
    document.getElementById('reportAccount').value = config.account_id || '';
    document.getElementById('reportDaysLookback').value = config.days_lookback;
    document.getElementById('reportFormat').value = config.report_format;
    document.getElementById('reportIncludeTrades').checked = config.include_trades;
    document.getElementById('reportIncludeCharts').checked = config.include_charts;
    document.getElementById('reportRecipients').value = config.recipients;
    document.getElementById('reportCcRecipients').value = config.cc_recipients || '';
    document.getElementById('reportEmailSubject').value = config.email_subject || '';
    document.getElementById('reportEmailBody').value = config.email_body || '';
    document.getElementById('reportIsActive').checked = config.is_active;

    handleFrequencyChange();
}

/**
 * Handle frequency change to show/hide conditional fields
 */
function handleFrequencyChange() {
    const frequency = document.getElementById('reportFrequency').value;
    const dayOfWeekGroup = document.getElementById('dayOfWeekGroup');
    const dayOfMonthGroup = document.getElementById('dayOfMonthGroup');

    dayOfWeekGroup.style.display = frequency === 'weekly' ? 'block' : 'none';
    dayOfMonthGroup.style.display = frequency === 'monthly' ? 'block' : 'none';
}

/**
 * Handle save report form submission
 */
async function handleSaveReport(e) {
    e.preventDefault();

    const formData = {
        name: document.getElementById('reportName').value,
        description: document.getElementById('reportDescription').value || null,
        frequency: document.getElementById('reportFrequency').value,
        day_of_week: document.getElementById('reportFrequency').value === 'weekly'
            ? parseInt(document.getElementById('reportDayOfWeek').value)
            : null,
        day_of_month: document.getElementById('reportFrequency').value === 'monthly'
            ? parseInt(document.getElementById('reportDayOfMonth').value)
            : null,
        time_of_day: document.getElementById('reportTimeOfDay').value || null,
        report_format: document.getElementById('reportFormat').value,
        include_trades: document.getElementById('reportIncludeTrades').checked,
        include_charts: document.getElementById('reportIncludeCharts').checked,
        days_lookback: parseInt(document.getElementById('reportDaysLookback').value),
        account_id: document.getElementById('reportAccount').value || null,
        recipients: document.getElementById('reportRecipients').value.split(',').map(e => e.trim()),
        cc_recipients: document.getElementById('reportCcRecipients').value
            ? document.getElementById('reportCcRecipients').value.split(',').map(e => e.trim())
            : null,
        email_subject: document.getElementById('reportEmailSubject').value || null,
        email_body: document.getElementById('reportEmailBody').value || null,
        is_active: document.getElementById('reportIsActive').checked
    };

    try {
        let response;
        if (currentEditingId) {
            // Update existing
            response = await fetch(`${API_BASE_URL}/reports/configurations/${currentEditingId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        } else {
            // Create new
            response = await fetch(`${API_BASE_URL}/reports/configurations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save report');
        }

        showMessage(`Report ${currentEditingId ? 'updated' : 'created'} successfully!`, 'success');
        closeReportModal();
        await loadReportConfigurations();
    } catch (error) {
        console.error('Error saving report:', error);
        showMessage(`Failed to save report: ${error.message}`, 'error');
    }
}

/**
 * Edit report
 */
async function editReport(configId) {
    try {
        const response = await fetch(`${API_BASE_URL}/reports/configurations/${configId}`);
        if (!response.ok) throw new Error('Failed to load report');

        const config = await response.json();
        openReportModal(config);
    } catch (error) {
        console.error('Error loading report:', error);
        showMessage('Failed to load report for editing', 'error');
    }
}

/**
 * Delete report
 */
async function deleteReport(configId) {
    if (!confirm('Are you sure you want to delete this report configuration?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/reports/configurations/${configId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete report');

        showMessage('Report deleted successfully', 'success');
        await loadReportConfigurations();
    } catch (error) {
        console.error('Error deleting report:', error);
        showMessage('Failed to delete report', 'error');
    }
}

/**
 * Toggle report status (activate/deactivate)
 */
async function toggleReportStatus(configId, activate) {
    try {
        const endpoint = activate ? 'activate' : 'deactivate';
        const response = await fetch(`${API_BASE_URL}/reports/configurations/${configId}/${endpoint}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error(`Failed to ${endpoint} report`);

        showMessage(`Report ${activate ? 'activated' : 'deactivated'} successfully`, 'success');
        await loadReportConfigurations();
    } catch (error) {
        console.error('Error toggling report status:', error);
        showMessage('Failed to update report status', 'error');
    }
}

/**
 * Trigger report now
 */
async function triggerReportNow(configId) {
    if (!confirm('Generate this report now?')) return;

    try {
        updateStatus('Generating report...', 'info');

        // This would call a trigger endpoint if available
        // For now, we'll use the generate endpoint with config parameters
        showMessage('Manual triggering not yet implemented. Use Quick Generate instead.', 'info');
        updateStatus('Ready', 'success');
    } catch (error) {
        console.error('Error triggering report:', error);
        showMessage('Failed to trigger report', 'error');
        updateStatus('Ready', 'success');
    }
}

/**
 * Utility functions
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatFileSize(bytes) {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateStatus(text, type) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    statusText.textContent = text;

    statusDot.className = 'status-dot';
    if (type === 'success') {
        statusDot.classList.add('status-success');
    } else if (type === 'error') {
        statusDot.classList.add('status-error');
    } else if (type === 'info') {
        statusDot.classList.add('status-info');
    }
}

function showMessage(message, type) {
    // You could implement a toast notification system here
    // For now, we'll use console and basic alert
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Create a temporary message element
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    messageEl.textContent = message;

    const container = document.querySelector('.container');
    container.insertBefore(messageEl, container.firstChild);

    setTimeout(() => {
        messageEl.remove();
    }, 5000);
}

function viewReport(filePath) {
    alert(`Report file: ${filePath}\n\nFile download functionality would be implemented here.`);
}

function showError(errorMessage) {
    alert(`Error Details:\n\n${errorMessage}`);
}

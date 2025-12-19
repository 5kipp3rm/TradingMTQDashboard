/**
 * Worker Connector - Phase 4 Integration
 *
 * Bridges the old session-based connection UI with the new Phase 4 WorkerManagerService.
 * Provides a unified interface for connecting accounts using the multi-instance worker system.
 */

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api'
    : '/api';

class WorkerConnector {
    constructor() {
        this.workerInfoCache = new Map(); // account_id (string) -> WorkerInfo
        this.initialized = false;
    }

    /**
     * Initialize worker connector
     */
    async init() {
        if (this.initialized) return;

        try {
            await this.loadWorkerStatuses();
            this.initialized = true;
            console.log('Worker Connector initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Worker Connector:', error);
        }
    }

    /**
     * Load worker statuses from Phase 4 API
     */
    async loadWorkerStatuses() {
        try {
            const response = await fetch(`${API_BASE_URL}/workers`);
            if (!response.ok) {
                console.warn('Workers API not available, using fallback mode');
                return;
            }

            const workers = await response.json();
            this.workerInfoCache.clear();

            // Cache worker info by account_id
            workers.forEach(worker => {
                this.workerInfoCache.set(worker.account_id, worker);
            });

            console.log(`Loaded ${workers.length} Phase 4 workers`);
        } catch (error) {
            console.error('Error loading worker statuses:', error);
        }
    }

    /**
     * Convert database account_id (int) to Phase 4 account_id (string)
     * Format: "account-{login}" or "account-{account_number}"
     */
    getWorkerAccountId(account) {
        // Try to match against existing worker accounts first
        const login = account.account_number.toString();

        // Common formats to try
        const possibleIds = [
            `account-${login}`,
            `account-${String(login).padStart(3, '0')}`, // account-001, account-002, etc.
            login,
            `acc-${login}`
        ];

        // Check if any worker exists with these IDs
        for (const id of possibleIds) {
            if (this.workerInfoCache.has(id)) {
                return id;
            }
        }

        // If no worker exists yet, use the standard format
        return `account-${login}`;
    }

    /**
     * Check if account has a Phase 4 worker configuration
     * This checks if a YAML config file exists for the account
     */
    async hasWorkerConfig(account) {
        try {
            const accountId = this.getWorkerAccountId(account);
            const response = await fetch(`${API_BASE_URL}/workers/${accountId}/validate`);

            if (response.ok) {
                const validation = await response.json();
                return validation.valid;
            }
            return false;
        } catch (error) {
            console.debug(`No worker config for account ${account.account_number}:`, error);
            return false;
        }
    }

    /**
     * Connect account using Phase 4 worker system
     */
    async connectAccount(account) {
        try {
            const accountId = this.getWorkerAccountId(account);

            console.log(`Connecting Phase 4 worker for account ${account.account_number} (worker ID: ${accountId})`);

            const response = await fetch(`${API_BASE_URL}/workers/${accountId}/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    apply_defaults: true,
                    validate: true
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start worker');
            }

            const workerInfo = await response.json();
            this.workerInfoCache.set(accountId, workerInfo);

            console.log(`✅ Worker started successfully:`, workerInfo);

            return {
                success: true,
                worker_id: workerInfo.worker_id,
                account_id: accountId,
                message: 'Worker started successfully'
            };

        } catch (error) {
            console.error(`Failed to connect account ${account.account_number}:`, error);
            throw error;
        }
    }

    /**
     * Disconnect account using Phase 4 worker system
     */
    async disconnectAccount(account) {
        try {
            const accountId = this.getWorkerAccountId(account);

            console.log(`Disconnecting Phase 4 worker for account ${account.account_number} (worker ID: ${accountId})`);

            const response = await fetch(`${API_BASE_URL}/workers/${accountId}/stop`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    timeout: 5.0
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to stop worker');
            }

            console.log(`✅ Worker stopped successfully`);

            this.workerInfoCache.delete(accountId);

            return {
                success: true,
                message: 'Worker stopped successfully'
            };

        } catch (error) {
            console.error(`Failed to disconnect account ${account.account_number}:`, error);
            throw error;
        }
    }

    /**
     * Get worker connection status
     */
    async getConnectionStatus(account) {
        try {
            const accountId = this.getWorkerAccountId(account);

            const response = await fetch(`${API_BASE_URL}/workers/${accountId}`);

            if (response.status === 404) {
                // Worker doesn't exist yet
                return {
                    is_connected: false,
                    status: 'stopped',
                    account_id: accountId
                };
            }

            if (!response.ok) {
                throw new Error('Failed to get worker status');
            }

            const workerInfo = await response.json();
            this.workerInfoCache.set(accountId, workerInfo);

            return {
                is_connected: workerInfo.status === 'running',
                status: workerInfo.status,
                account_id: accountId,
                worker_id: workerInfo.worker_id,
                started_at: workerInfo.started_at,
                error: workerInfo.error
            };

        } catch (error) {
            console.error(`Failed to get connection status for account ${account.account_number}:`, error);
            return {
                is_connected: false,
                status: 'error',
                error: error.message
            };
        }
    }

    /**
     * Connect all active accounts using Phase 4 workers
     */
    async connectAllAccounts(accounts) {
        const results = {
            total: 0,
            successful: 0,
            failed: 0,
            results: []
        };

        const activeAccounts = accounts.filter(acc => acc.is_active);
        results.total = activeAccounts.length;

        for (const account of activeAccounts) {
            try {
                // Check if worker config exists
                const hasConfig = await this.hasWorkerConfig(account);

                if (!hasConfig) {
                    console.warn(`Skipping account ${account.account_number} - no Phase 4 config found`);
                    results.failed++;
                    results.results.push({
                        account_id: account.id,
                        account_number: account.account_number,
                        success: false,
                        error: 'No Phase 4 configuration found'
                    });
                    continue;
                }

                await this.connectAccount(account);
                results.successful++;
                results.results.push({
                    account_id: account.id,
                    account_number: account.account_number,
                    success: true
                });

            } catch (error) {
                results.failed++;
                results.results.push({
                    account_id: account.id,
                    account_number: account.account_number,
                    success: false,
                    error: error.message
                });
            }
        }

        return results;
    }

    /**
     * Disconnect all active workers
     */
    async disconnectAllWorkers() {
        try {
            const response = await fetch(`${API_BASE_URL}/workers/stop-all`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to stop all workers');
            }

            const result = await response.json();
            this.workerInfoCache.clear();

            console.log(`✅ Stopped ${result.stopped_count} workers`);

            return {
                total: result.stopped_count,
                successful: result.stopped_count,
                failed: 0
            };

        } catch (error) {
            console.error('Failed to disconnect all workers:', error);
            throw error;
        }
    }

    /**
     * Get list of connected workers (for account selection in UI)
     */
    async getConnectedWorkers() {
        await this.loadWorkerStatuses();

        return Array.from(this.workerInfoCache.values())
            .filter(worker => worker.status === 'running')
            .map(worker => ({
                account_id: worker.account_id,
                worker_id: worker.worker_id,
                started_at: worker.started_at
            }));
    }

    /**
     * Validate worker configuration before connecting
     */
    async validateWorkerConfig(account) {
        try {
            const accountId = this.getWorkerAccountId(account);

            const response = await fetch(`${API_BASE_URL}/workers/${accountId}/validate`);

            if (!response.ok) {
                const error = await response.json();
                return {
                    valid: false,
                    errors: [error.detail || 'Validation failed'],
                    warnings: []
                };
            }

            return await response.json();

        } catch (error) {
            console.error('Validation error:', error);
            return {
                valid: false,
                errors: [error.message],
                warnings: []
            };
        }
    }
}

// Global instance
const workerConnector = new WorkerConnector();

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => workerConnector.init());
} else {
    workerConnector.init();
}

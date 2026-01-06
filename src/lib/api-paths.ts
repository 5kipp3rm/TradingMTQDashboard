/**
 * Centralized API Path Constants
 * Single source of truth for all API endpoints
 * 
 * Benefits:
 * - Easy to refactor (change API version in one place)
 * - Type-safe path generation
 * - Self-documenting with JSDoc
 * - Autocomplete support
 * - DRY principle
 */

// ============================================================================
// Base Paths
// ============================================================================

const API_V1 = '';
const API_V2 = '/v2';

// ============================================================================
// V1 API Paths (Legacy)
// ============================================================================

export const V1_PATHS = {
  // Analytics
  analytics: {
    /** GET /analytics/summary */
    summary: '/analytics/summary',
    /** GET /analytics/daily */
    daily: '/analytics/daily',
    /** GET /analytics/metrics */
    metrics: '/analytics/metrics',
  },

  // Trades
  trades: {
    /** GET /trades/ */
    list: '/trades/',
    /** GET /trades/{ticket} */
    byId: (ticket: number) => `/trades/${ticket}`,
    /** GET /trades/statistics */
    statistics: '/trades/statistics',
  },

  // Positions
  positions: {
    /** GET /positions/open */
    open: '/positions/open',
    /** GET /positions/closed */
    closed: '/positions/closed',
    /** POST /positions/open */
    create: '/positions/open',
    /** POST /positions/{ticket}/close */
    close: (ticket: number) => `/positions/${ticket}/close`,
    /** POST /positions/close-all */
    closeAll: '/positions/close-all',
    /** PUT /positions/{ticket}/modify */
    modify: (ticket: number) => `/positions/${ticket}/modify`,
    /** POST /positions/preview */
    preview: '/positions/preview',
  },

  // Accounts (V1)
  accounts: {
    /** GET /accounts */
    list: '/accounts',
    /** GET /accounts/{id} */
    byId: (id: number) => `/accounts/${id}`,
    /** POST /accounts */
    create: '/accounts',
    /** PUT /accounts/{id} */
    update: (id: number) => `/accounts/${id}`,
    /** DELETE /accounts/{id} */
    delete: (id: number) => `/accounts/${id}`,
    /** POST /accounts/{id}/set-default */
    setDefault: (id: number) => `/accounts/${id}/set-default`,
    /** POST /accounts/{id}/activate */
    activate: (id: number) => `/accounts/${id}/activate`,
    /** POST /accounts/{id}/deactivate */
    deactivate: (id: number) => `/accounts/${id}/deactivate`,
    /** GET /accounts/{id}/config */
    config: (id: number) => `/accounts/${id}/config`,
    /** PUT /accounts/{id}/config */
    updateConfig: (id: number) => `/accounts/${id}/config`,
    
    // Account currencies (V1)
    currencies: {
      /** GET /accounts/{id}/currencies */
      list: (accountId: number) => `/accounts/${accountId}/currencies`,
      /** PUT /accounts/{id}/currencies/{symbol} */
      update: (accountId: number, symbol: string) => `/accounts/${accountId}/currencies/${symbol}`,
      /** DELETE /accounts/{id}/currencies/{symbol} */
      delete: (accountId: number, symbol: string) => `/accounts/${accountId}/currencies/${symbol}`,
      /** GET /accounts/{id}/currencies/{symbol}/resolved */
      resolved: (accountId: number, symbol: string) => `/accounts/${accountId}/currencies/${symbol}/resolved`,
    },
  },

  // Account Connections (V1)
  accountConnections: {
    /** POST /accounts/{id}/connect */
    connect: (accountId: number) => `/accounts/${accountId}/connect`,
    /** POST /accounts/{id}/disconnect */
    disconnect: (accountId: number) => `/accounts/${accountId}/disconnect`,
    /** GET /accounts/{id}/status */
    status: (accountId: number) => `/accounts/${accountId}/status`,
    /** POST /accounts/connect-all */
    connectAll: '/accounts/connect-all',
    /** POST /accounts/disconnect-all */
    disconnectAll: '/accounts/disconnect-all',
  },

  // Currencies (V1)
  currencies: {
    /** GET /currencies */
    list: '/currencies',
    /** GET /currencies/{symbol} */
    bySymbol: (symbol: string) => `/currencies/${symbol}`,
    /** POST /currencies */
    create: '/currencies',
    /** PUT /currencies/{symbol} */
    update: (symbol: string) => `/currencies/${symbol}`,
    /** DELETE /currencies/{symbol} */
    delete: (symbol: string) => `/currencies/${symbol}`,
    /** POST /currencies/{symbol}/enable */
    enable: (symbol: string) => `/currencies/${symbol}/enable`,
    /** POST /currencies/{symbol}/disable */
    disable: (symbol: string) => `/currencies/${symbol}/disable`,
    /** POST /currencies/validate */
    validate: '/currencies/validate',
    /** POST /currencies/reload */
    reload: '/currencies/reload',
    /** POST /currencies/export */
    export: '/currencies/export',
    /** GET /available */
    available: '/available',
  },

  // Config
  config: {
    /** GET /config/currencies */
    currencies: '/config/currencies',
    /** POST /config/currencies */
    createCurrency: '/config/currencies',
    /** POST /config/currencies/{symbol}/enable */
    enableCurrency: (symbol: string) => `/config/currencies/${symbol}/enable`,
    /** POST /config/currencies/{symbol}/disable */
    disableCurrency: (symbol: string) => `/config/currencies/${symbol}/disable`,
    /** GET /config/preferences */
    preferences: '/config/preferences',
    /** PUT /config/preferences */
    updatePreferences: '/config/preferences',
    /** GET /config/favorites */
    favorites: '/config/favorites',
    /** POST /config/favorites/{symbol} */
    addFavorite: (symbol: string) => `/config/favorites/${symbol}`,
    /** DELETE /config/favorites/{symbol} */
    removeFavorite: (symbol: string) => `/config/favorites/${symbol}`,
  },

  // Alerts
  alerts: {
    /** GET /alerts */
    list: '/alerts',
    /** GET /alerts/{id} */
    byId: (id: number) => `/alerts/${id}`,
    /** POST /alerts */
    create: '/alerts',
    /** PUT /alerts/{id} */
    update: (id: number) => `/alerts/${id}`,
    /** DELETE /alerts/{id} */
    delete: (id: number) => `/alerts/${id}`,
    /** GET /alerts/history */
    history: '/alerts/history',
    /** GET /alerts/types */
    types: '/alerts/types',
    /** POST /alerts/test-email */
    testEmail: '/alerts/test-email',
  },

  // Charts
  charts: {
    /** GET /charts/equity */
    equity: '/charts/equity',
    /** GET /charts/heatmap */
    heatmap: '/charts/heatmap',
    /** GET /charts/symbol-performance */
    symbolPerformance: '/charts/symbol-performance',
    /** GET /charts/win-loss-analysis */
    winLossAnalysis: '/charts/win-loss-analysis',
    /** GET /charts/monthly-comparison */
    monthlyComparison: '/charts/monthly-comparison',
    /** GET /charts/risk-reward */
    riskReward: '/charts/risk-reward',
  },

  // Reports
  reports: {
    /** GET /reports */
    list: '/reports',
    /** POST /reports */
    create: '/reports',
    /** POST /reports/generate */
    generate: '/reports/generate',
    /** GET /reports/history */
    history: '/reports/history',
  },

  // Health
  health: {
    /** GET /health */
    check: '/health',
    /** GET /health/status */
    status: '/health/status',
  },

  // Trading Control
  tradingControl: {
    /** POST /trading-control/start */
    start: '/trading-control/start',
    /** POST /trading-control/stop */
    stop: '/trading-control/stop',
    /** GET /trading-control/status */
    status: '/trading-control/status',
    /** GET /trading-control/autotrading-status */
    autotradingStatus: '/trading-control/autotrading-status',
  },

  // Workers
  workers: {
    /** GET /workers */
    list: '/workers',
    /** GET /workers/{accountId} */
    byId: (accountId: number) => `/workers/${accountId}`,
    /** POST /workers/{accountId}/start */
    start: (accountId: number) => `/workers/${accountId}/start`,
    /** POST /workers/{accountId}/stop */
    stop: (accountId: number) => `/workers/${accountId}/stop`,
    /** POST /workers/{accountId}/restart */
    restart: (accountId: number) => `/workers/${accountId}/restart`,
    /** POST /workers/start-all */
    startAll: '/workers/start-all',
    /** POST /workers/stop-all */
    stopAll: '/workers/stop-all',
    /** GET /workers/{accountId}/validate */
    validate: (accountId: number) => `/workers/${accountId}/validate`,
    /** GET /workers/validate-all */
    validateAll: '/workers/validate-all',
  },
};

// ============================================================================
// V2 API Paths (OOP-based)
// ============================================================================

const V2_ACCOUNTS_BASE = `${API_V2}/accounts`;

export const V2_PATHS = {
  // Account Management V2
  accounts: {
    // Connection management
    /** POST /v2/accounts/{id}/connect */
    connect: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/connect`,
    /** POST /v2/accounts/{id}/disconnect */
    disconnect: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/disconnect`,
    /** GET /v2/accounts/{id}/status */
    status: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/status`,
    /** GET /v2/accounts/{id}/mt5-info */
    mt5Info: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/mt5-info`,

    // Trading control
    /** POST /v2/accounts/{id}/start-trading */
    startTrading: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/start-trading`,
    /** POST /v2/accounts/{id}/stop-trading */
    stopTrading: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/stop-trading`,
    /** POST /v2/accounts/{id}/pause-trading */
    pauseTrading: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/pause-trading`,
    /** POST /v2/accounts/{id}/resume-trading */
    resumeTrading: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/resume-trading`,

    // Bulk operations
    /** POST /v2/accounts/connect-all */
    connectAll: `${V2_ACCOUNTS_BASE}/connect-all`,
    /** POST /v2/accounts/disconnect-all */
    disconnectAll: `${V2_ACCOUNTS_BASE}/disconnect-all`,
    /** POST /v2/accounts/start-all-trading */
    startAllTrading: `${V2_ACCOUNTS_BASE}/start-all-trading`,
    /** POST /v2/accounts/stop-all-trading */
    stopAllTrading: `${V2_ACCOUNTS_BASE}/stop-all-trading`,

    // Query operations
    /** GET /v2/accounts/status-summary */
    statusSummary: `${V2_ACCOUNTS_BASE}/status-summary`,
    /** GET /v2/accounts/connected */
    connected: `${V2_ACCOUNTS_BASE}/connected`,
    /** GET /v2/accounts/trading */
    trading: `${V2_ACCOUNTS_BASE}/trading`,
  },

  // Currency Management V2
  currencies: {
    /** GET /v2/accounts/{accountId}/currencies */
    list: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/currencies`,
    /** POST /v2/accounts/{accountId}/currencies */
    create: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/currencies`,
    /** GET /v2/accounts/{accountId}/currencies/{symbol} */
    bySymbol: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/currencies/${symbol}`,
    /** PATCH /v2/accounts/{accountId}/currencies/{symbol} */
    update: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/currencies/${symbol}`,
    /** DELETE /v2/accounts/{accountId}/currencies/{symbol} */
    delete: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/currencies/${symbol}`,
    /** GET /v2/accounts/{accountId}/currencies/{symbol}/strategy */
    strategy: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/currencies/${symbol}/strategy`,
    /** PATCH /v2/accounts/{accountId}/currencies/{symbol}/strategy */
    updateStrategy: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/currencies/${symbol}/strategy`,
  },

  // AI Configuration V2
  aiConfig: {
    /** GET /v2/accounts/{accountId}/ai-config */
    get: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/ai-config`,
    /** PATCH /v2/accounts/{accountId}/ai-config */
    update: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/ai-config`,
    
    // ML enhancement
    /** POST /v2/accounts/{accountId}/ai/ml/enable */
    enableML: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/ai/ml/enable`,
    /** POST /v2/accounts/{accountId}/ai/ml/disable */
    disableML: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/ai/ml/disable`,
    
    // LLM sentiment
    /** POST /v2/accounts/{accountId}/ai/llm-sentiment/enable */
    enableLLMSentiment: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/ai/llm-sentiment/enable`,
    /** POST /v2/accounts/{accountId}/ai/llm-sentiment/disable */
    disableLLMSentiment: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/ai/llm-sentiment/disable`,
    
    // LLM analyst
    /** POST /v2/accounts/{accountId}/ai/llm-analyst/enable */
    enableLLMAnalyst: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/ai/llm-analyst/enable`,
    /** POST /v2/accounts/{accountId}/ai/llm-analyst/disable */
    disableLLMAnalyst: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/ai/llm-analyst/disable`,
  },

  // Strategies V2 (Per-Symbol)
  strategies: {
    /** GET /v2/accounts/{accountId}/strategies */
    list: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies`,
    /** POST /v2/accounts/{accountId}/strategies */
    create: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies`,
    /** GET /v2/accounts/{accountId}/strategies/{symbol} */
    bySymbol: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies/${symbol}`,
    /** PATCH /v2/accounts/{accountId}/strategies/{symbol} */
    update: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies/${symbol}`,
    /** DELETE /v2/accounts/{accountId}/strategies/{symbol} */
    delete: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies/${symbol}`,
    
    // Strategy control
    /** POST /v2/accounts/{accountId}/strategies/{symbol}/enable */
    enable: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies/${symbol}/enable`,
    /** POST /v2/accounts/{accountId}/strategies/{symbol}/disable */
    disable: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies/${symbol}/disable`,
    
    // Strategy status & performance
    /** GET /v2/accounts/{accountId}/strategies/{symbol}/status */
    status: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies/${symbol}/status`,
    /** GET /v2/accounts/{accountId}/strategies/{symbol}/performance */
    performance: (accountId: number, symbol: string) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies/${symbol}/performance`,
    
    // Bulk operations
    /** POST /v2/accounts/{accountId}/strategies/bulk-ai-update */
    bulkAiUpdate: (accountId: number) => `${V2_ACCOUNTS_BASE}/${accountId}/strategies/bulk-ai-update`,
  },
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Build query string from parameters
 * @example buildQueryString({ days: 30, account_id: 1 }) => "?days=30&account_id=1"
 */
export function buildQueryString(params?: Record<string, any>): string {
  if (!params) return '';
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      query.append(key, value.toString());
    }
  });
  const queryStr = query.toString();
  return queryStr ? `?${queryStr}` : '';
}

/**
 * Combine path with query parameters
 * @example withQuery('/trades/', { limit: 10 }) => "/trades/?limit=10"
 */
export function withQuery(path: string, params?: Record<string, any>): string {
  return `${path}${buildQueryString(params)}`;
}

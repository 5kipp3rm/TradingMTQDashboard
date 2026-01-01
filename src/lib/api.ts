// API Configuration for TradingMTQ Backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
      }

      // Handle 204 No Content responses (no body to parse)
      if (response.status === 204) {
        return { data: null as T };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

// Analytics API
export const analyticsApi = {
  getOverview: (params?: { days?: number; account_id?: number }) => {
    const query = new URLSearchParams();
    if (params?.days) query.append('days', params.days.toString());
    if (params?.account_id) query.append('account_id', params.account_id.toString());
    // Backend uses /analytics/summary not /analytics/overview
    return apiClient.get(`/analytics/summary${query.toString() ? `?${query}` : ''}`);
  },
  getDaily: (params?: { days?: number; account_id?: number; start_date?: string; end_date?: string }) => {
    const query = new URLSearchParams();
    // Backend uses 'limit' parameter not 'days' for daily endpoint
    if (params?.days) query.append('limit', params.days.toString());
    if (params?.account_id) query.append('account_id', params.account_id.toString());
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    return apiClient.get(`/analytics/daily${query.toString() ? `?${query}` : ''}`);
  },
  getMetrics: (params?: { days?: number; account_id?: number }) => {
    const query = new URLSearchParams();
    if (params?.days) query.append('days', params.days.toString());
    if (params?.account_id) query.append('account_id', params.account_id.toString());
    return apiClient.get(`/analytics/metrics${query.toString() ? `?${query}` : ''}`);
  },
};

// Trades API
export const tradesApi = {
  getAll: (params?: { limit?: number; symbol?: string; status?: string; start_date?: string; end_date?: string; account_id?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.symbol) query.append('symbol', params.symbol);
    if (params?.status) query.append('status', params.status);
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    if (params?.account_id) query.append('account_id', params.account_id.toString());
    // Backend uses /trades/ with trailing slash
    return apiClient.get(`/trades/${query.toString() ? `?${query}` : ''}`);
  },
  getById: (ticket: number) => apiClient.get(`/trades/${ticket}`),
  getStatistics: (days: number = 30) => apiClient.get(`/trades/statistics?days=${days}`),
};

// Positions API
export const positionsApi = {
  getOpen: (params?: { account_id?: number; symbol?: string }) => {
    const query = new URLSearchParams();
    if (params?.account_id) query.append('account_id', params.account_id.toString());
    if (params?.symbol) query.append('symbol', params.symbol);
    return apiClient.get(`/positions/open${query.toString() ? `?${query}` : ''}`);
  },
  open: (params: {
    account_id: number;
    symbol: string;
    order_type: string;
    volume: number;
    stop_loss?: number;
    take_profit?: number;
    comment?: string;
    magic?: number;
    deviation?: number;
  }) => apiClient.post('/positions/open', params),
  close: (ticket: number, account_id: number) =>
    apiClient.post(`/positions/${ticket}/close?account_id=${account_id}`),
  closeAll: (params: { account_id: number; symbol?: string }) =>
    apiClient.post('/positions/close-all', params),
  modify: (ticket: number, account_id: number, params: { stop_loss?: number; take_profit?: number }) =>
    apiClient.put(`/positions/${ticket}/modify?account_id=${account_id}`, params),
  preview: (params: {
    account_id: number;
    symbol: string;
    order_type: string;
    volume: number;
    stop_loss?: number;
    take_profit?: number;
  }) => apiClient.post('/positions/preview', params),
};

// Accounts API
export const accountsApi = {
  getAll: (active_only?: boolean) =>
    apiClient.get(`/accounts${active_only ? '?active_only=true' : ''}`),
  getById: (id: number) => apiClient.get(`/accounts/${id}`),
  create: (account: {
    account_number: number;
    account_name: string;
    broker: string;
    server: string;
    platform_type: string;
    login: number;
    password: string;
    is_demo: boolean;
    is_active: boolean;
    initial_balance?: number;
    currency?: string;
  }) => apiClient.post('/accounts', account),
  update: (id: number, account: any) => apiClient.put(`/accounts/${id}`, account),
  delete: (id: number) => apiClient.delete(`/accounts/${id}`),
  setDefault: (id: number) => apiClient.post(`/accounts/${id}/set-default`),
  activate: (id: number) => apiClient.post(`/accounts/${id}/activate`),
  deactivate: (id: number) => apiClient.post(`/accounts/${id}/deactivate`),
  getConfig: (id: number) => apiClient.get(`/accounts/${id}/config`),
  updateConfig: (id: number, config: any) => apiClient.put(`/accounts/${id}/config`, config),

  // Per-account currency configuration
  getCurrencies: (id: number, enabled_only?: boolean) =>
    apiClient.get(`/accounts/${id}/currencies${enabled_only ? '?enabled_only=true' : ''}`),
  updateCurrency: (id: number, symbol: string, config: any) =>
    apiClient.put(`/accounts/${id}/currencies/${symbol}`, config),
  deleteCurrency: (id: number, symbol: string) =>
    apiClient.delete(`/accounts/${id}/currencies/${symbol}`),
  getResolvedCurrency: (id: number, symbol: string) =>
    apiClient.get(`/accounts/${id}/currencies/${symbol}/resolved`),
};

// Account Connections API
export const accountConnectionsApi = {
  connect: (account_id: number, force?: boolean) =>
    apiClient.post(`/accounts/${account_id}/connect${force ? '?force=true' : ''}`),
  disconnect: (account_id: number) =>
    apiClient.post(`/accounts/${account_id}/disconnect`),
  getStatus: (account_id: number) =>
    apiClient.get(`/accounts/${account_id}/status`),
  connectAll: () => apiClient.post('/accounts/connect-all'),
  disconnectAll: () => apiClient.post('/accounts/disconnect-all'),
};

// Currencies API
export const currenciesApi = {
  getAll: (enabled_only?: boolean) =>
    apiClient.get(`/currencies${enabled_only ? '?enabled_only=true' : ''}`),
  getBySymbol: (symbol: string) => apiClient.get(`/currencies/${symbol}`),
  create: (currency: any) => apiClient.post('/currencies', currency),
  update: (symbol: string, config: any) => apiClient.put(`/currencies/${symbol}`, config),
  delete: (symbol: string) => apiClient.delete(`/currencies/${symbol}`),
  enable: (symbol: string) => apiClient.post(`/currencies/${symbol}/enable`),
  disable: (symbol: string) => apiClient.post(`/currencies/${symbol}/disable`),
  validate: (currency: any) => apiClient.post('/currencies/validate', currency),
  reload: () => apiClient.post('/currencies/reload'),
  export: () => apiClient.post('/currencies/export'),
  // Available currencies from master database
  getAvailable: (params?: { category?: string; active_only?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.category) query.append('category', params.category);
    if (params?.active_only !== undefined) query.append('active_only', params.active_only.toString());
    return apiClient.get(`/available${query.toString() ? `?${query}` : ''}`);
  },
};

// Config API
export const configApi = {
  getCurrencies: () => apiClient.get('/config/currencies'),
  createCurrency: (currency: any) => apiClient.post('/config/currencies', currency),
  enableCurrency: (symbol: string) => apiClient.post(`/config/currencies/${symbol}/enable`),
  disableCurrency: (symbol: string) => apiClient.post(`/config/currencies/${symbol}/disable`),
  getPreferences: () => apiClient.get('/config/preferences'),
  updatePreferences: (prefs: any) => apiClient.put('/config/preferences', prefs),
  getFavorites: () => apiClient.get('/config/favorites'),
  addFavorite: (symbol: string) => apiClient.post(`/config/favorites/${symbol}`),
  removeFavorite: (symbol: string) => apiClient.delete(`/config/favorites/${symbol}`),
};

// Alerts API
export const alertsApi = {
  getAll: () => apiClient.get('/alerts'),
  getById: (id: number) => apiClient.get(`/alerts/${id}`),
  create: (alert: any) => apiClient.post('/alerts', alert),
  update: (id: number, alert: any) => apiClient.put(`/alerts/${id}`, alert),
  delete: (id: number) => apiClient.delete(`/alerts/${id}`),
  getHistory: (params?: { limit?: number; alert_type?: string; delivered_only?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.alert_type) query.append('alert_type', params.alert_type);
    if (params?.delivered_only) query.append('delivered_only', 'true');
    return apiClient.get(`/alerts/history${query.toString() ? `?${query}` : ''}`);
  },
  getTypes: () => apiClient.get('/alerts/types'),
  testEmail: (email: string) => apiClient.post('/alerts/test-email', { email }),
};

// Charts API
export const chartsApi = {
  getEquity: (params?: { start_date?: string; end_date?: string; interval?: string; account_id?: number }) => {
    const query = new URLSearchParams();
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    if (params?.interval) query.append('interval', params.interval);
    if (params?.account_id) query.append('account_id', params.account_id.toString());
    return apiClient.get(`/charts/equity${query.toString() ? `?${query}` : ''}`);
  },
  getHeatmap: () => apiClient.get('/charts/heatmap'),
  getSymbolPerformance: (top_n: number = 10) =>
    apiClient.get(`/charts/symbol-performance?top_n=${top_n}`),
  getWinLossAnalysis: () => apiClient.get('/charts/win-loss-analysis'),
  getMonthlyComparison: (months: number = 12) =>
    apiClient.get(`/charts/monthly-comparison?months=${months}`),
  getRiskReward: () => apiClient.get('/charts/risk-reward'),
};

// Reports API
export const reportsApi = {
  getAll: () => apiClient.get('/reports'),
  create: (report: any) => apiClient.post('/reports', report),
  generate: (params: { start_date: string; end_date: string; include_trades?: boolean; include_charts?: boolean }) =>
    apiClient.post('/reports/generate', params),
  getHistory: () => apiClient.get('/reports/history'),
};

// Health API
export const healthApi = {
  check: () => apiClient.get('/health'),
  getStatus: () => apiClient.get('/health/status'),
};

// Trading Control API
export const tradingControlApi = {
  start: (params: { account_id: number; currency_symbols?: string[]; check_autotrading?: boolean }) =>
    apiClient.post('/trading-control/start', params),
  stop: (account_id: number) => apiClient.post('/trading-control/stop', { account_id }),
  getStatus: (account_id: number) =>
    apiClient.get(`/trading-control/status?account_id=${account_id}`),
  getAutoTradingStatus: (account_id: number) =>
    apiClient.get(`/trading-control/autotrading-status?account_id=${account_id}`),
};

// Workers API
export const workersApi = {
  getAll: () => apiClient.get('/workers'),
  getById: (account_id: number) => apiClient.get(`/workers/${account_id}`),
  start: (account_id: number, params?: { apply_defaults?: boolean; validate?: boolean }) =>
    apiClient.post(`/workers/${account_id}/start`, params || {}),
  stop: (account_id: number) => apiClient.post(`/workers/${account_id}/stop`),
  restart: (account_id: number) => apiClient.post(`/workers/${account_id}/restart`),
  startAll: () => apiClient.post('/workers/start-all'),
  stopAll: () => apiClient.post('/workers/stop-all'),
  validate: (account_id: number) => apiClient.get(`/workers/${account_id}/validate`),
  validateAll: () => apiClient.get('/workers/validate-all'),
};

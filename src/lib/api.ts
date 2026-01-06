// API Configuration for TradingMTQ Backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

import { V1_PATHS, buildQueryString, withQuery } from './api-paths';

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

  async patch<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
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
  getOverview: (params?: { days?: number; account_id?: number }) =>
    apiClient.get(withQuery(V1_PATHS.analytics.summary, params)),
  
  getDaily: (params?: { days?: number; account_id?: number; start_date?: string; end_date?: string }) => {
    // Backend uses 'limit' parameter not 'days' for daily endpoint
    const adjustedParams = params?.days 
      ? { ...params, limit: params.days, days: undefined }
      : params;
    return apiClient.get(withQuery(V1_PATHS.analytics.daily, adjustedParams));
  },
  
  getMetrics: (params?: { days?: number; account_id?: number }) =>
    apiClient.get(withQuery(V1_PATHS.analytics.metrics, params)),
};

// Trades API
export const tradesApi = {
  getAll: (params?: { limit?: number; symbol?: string; status?: string; start_date?: string; end_date?: string; account_id?: number }) =>
    apiClient.get(withQuery(V1_PATHS.trades.list, params)),
  
  getById: (ticket: number) => 
    apiClient.get(V1_PATHS.trades.byId(ticket)),
  
  getStatistics: (days: number = 30) => 
    apiClient.get(withQuery(V1_PATHS.trades.statistics, { days })),
};

// Positions API
export const positionsApi = {
  getOpen: (params?: { account_id?: number; symbol?: string }) =>
    apiClient.get(withQuery(V1_PATHS.positions.open, params)),
  
  getClosed: (params?: { account_id?: number; symbol?: string; limit?: number }) =>
    apiClient.get(withQuery(V1_PATHS.positions.closed, params)),
  
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
  }) => apiClient.post(V1_PATHS.positions.create, params),
  
  close: (ticket: number, account_id: number) =>
    apiClient.post(withQuery(V1_PATHS.positions.close(ticket), { account_id })),
  
  closeAll: (params: { account_id: number; symbol?: string }) =>
    apiClient.post(V1_PATHS.positions.closeAll, params),
  
  modify: (ticket: number, account_id: number, params: { stop_loss?: number; take_profit?: number }) =>
    apiClient.put(withQuery(V1_PATHS.positions.modify(ticket), { account_id }), params),
  
  preview: (params: {
    account_id: number;
    symbol: string;
    order_type: string;
    volume: number;
    stop_loss?: number;
    take_profit?: number;
  }) => apiClient.post(V1_PATHS.positions.preview, params),
};

// Accounts API
export const accountsApi = {
  getAll: (active_only?: boolean) =>
    apiClient.get(withQuery(V1_PATHS.accounts.list, active_only ? { active_only: true } : undefined)),
  
  getById: (id: number) => 
    apiClient.get(V1_PATHS.accounts.byId(id)),
  
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
  }) => apiClient.post(V1_PATHS.accounts.create, account),
  
  update: (id: number, account: any) => 
    apiClient.put(V1_PATHS.accounts.update(id), account),
  
  delete: (id: number) => 
    apiClient.delete(V1_PATHS.accounts.delete(id)),
  
  setDefault: (id: number) => 
    apiClient.post(V1_PATHS.accounts.setDefault(id)),
  
  activate: (id: number) => 
    apiClient.post(V1_PATHS.accounts.activate(id)),
  
  deactivate: (id: number) => 
    apiClient.post(V1_PATHS.accounts.deactivate(id)),
  
  getConfig: (id: number) => 
    apiClient.get(V1_PATHS.accounts.config(id)),
  
  updateConfig: (id: number, config: any) => 
    apiClient.put(V1_PATHS.accounts.updateConfig(id), config),

  // Per-account currency configuration
  getCurrencies: (id: number, enabled_only?: boolean) =>
    apiClient.get(withQuery(V1_PATHS.accounts.currencies.list(id), enabled_only ? { enabled_only: true } : undefined)),
  
  updateCurrency: (id: number, symbol: string, config: any) =>
    apiClient.put(V1_PATHS.accounts.currencies.update(id, symbol), config),
  
  deleteCurrency: (id: number, symbol: string) =>
    apiClient.delete(V1_PATHS.accounts.currencies.delete(id, symbol)),
  
  getResolvedCurrency: (id: number, symbol: string) =>
    apiClient.get(V1_PATHS.accounts.currencies.resolved(id, symbol)),
};

// Account Connections API
export const accountConnectionsApi = {
  connect: (account_id: number, force?: boolean) =>
    apiClient.post(withQuery(V1_PATHS.accountConnections.connect(account_id), force ? { force: true } : undefined)),
  
  disconnect: (account_id: number) =>
    apiClient.post(V1_PATHS.accountConnections.disconnect(account_id)),
  
  getStatus: (account_id: number) =>
    apiClient.get(V1_PATHS.accountConnections.status(account_id)),
  
  connectAll: () => 
    apiClient.post(V1_PATHS.accountConnections.connectAll),
  
  disconnectAll: () => 
    apiClient.post(V1_PATHS.accountConnections.disconnectAll),
};

// Currencies API
export const currenciesApi = {
  getAll: (enabled_only?: boolean) =>
    apiClient.get(withQuery(V1_PATHS.currencies.list, enabled_only ? { enabled_only: true } : undefined)),
  
  getBySymbol: (symbol: string) => 
    apiClient.get(V1_PATHS.currencies.bySymbol(symbol)),
  
  create: (currency: any) => 
    apiClient.post(V1_PATHS.currencies.create, currency),
  
  update: (symbol: string, config: any) => 
    apiClient.put(V1_PATHS.currencies.update(symbol), config),
  
  delete: (symbol: string) => 
    apiClient.delete(V1_PATHS.currencies.delete(symbol)),
  
  enable: (symbol: string) => 
    apiClient.post(V1_PATHS.currencies.enable(symbol)),
  
  disable: (symbol: string) => 
    apiClient.post(V1_PATHS.currencies.disable(symbol)),
  
  validate: (currency: any) => 
    apiClient.post(V1_PATHS.currencies.validate, currency),
  
  reload: () => 
    apiClient.post(V1_PATHS.currencies.reload),
  
  export: () => 
    apiClient.post(V1_PATHS.currencies.export),
  
  // Available currencies from master database
  getAvailable: (params?: { category?: string; active_only?: boolean }) =>
    apiClient.get(withQuery(V1_PATHS.currencies.available, params)),
};

// Config API
export const configApi = {
  getCurrencies: () => 
    apiClient.get(V1_PATHS.config.currencies),
  
  createCurrency: (currency: any) => 
    apiClient.post(V1_PATHS.config.createCurrency, currency),
  
  enableCurrency: (symbol: string) => 
    apiClient.post(V1_PATHS.config.enableCurrency(symbol)),
  
  disableCurrency: (symbol: string) => 
    apiClient.post(V1_PATHS.config.disableCurrency(symbol)),
  
  getPreferences: () => 
    apiClient.get(V1_PATHS.config.preferences),
  
  updatePreferences: (prefs: any) => 
    apiClient.put(V1_PATHS.config.updatePreferences, prefs),
  
  getFavorites: () => 
    apiClient.get(V1_PATHS.config.favorites),
  
  addFavorite: (symbol: string) => 
    apiClient.post(V1_PATHS.config.addFavorite(symbol)),
  
  removeFavorite: (symbol: string) => 
    apiClient.delete(V1_PATHS.config.removeFavorite(symbol)),
};

// Alerts API
export const alertsApi = {
  getAll: () => 
    apiClient.get(V1_PATHS.alerts.list),
  
  getById: (id: number) => 
    apiClient.get(V1_PATHS.alerts.byId(id)),
  
  create: (alert: any) => 
    apiClient.post(V1_PATHS.alerts.create, alert),
  
  update: (id: number, alert: any) => 
    apiClient.put(V1_PATHS.alerts.update(id), alert),
  
  delete: (id: number) => 
    apiClient.delete(V1_PATHS.alerts.delete(id)),
  
  getHistory: (params?: { limit?: number; alert_type?: string; delivered_only?: boolean }) =>
    apiClient.get(withQuery(V1_PATHS.alerts.history, params)),
  
  getTypes: () => 
    apiClient.get(V1_PATHS.alerts.types),
  
  testEmail: (email: string) => 
    apiClient.post(V1_PATHS.alerts.testEmail, { email }),
};

// Charts API
export const chartsApi = {
  getEquity: (params?: { start_date?: string; end_date?: string; interval?: string; account_id?: number }) =>
    apiClient.get(withQuery(V1_PATHS.charts.equity, params)),
  
  getHeatmap: () => 
    apiClient.get(V1_PATHS.charts.heatmap),
  
  getSymbolPerformance: (top_n: number = 10) =>
    apiClient.get(withQuery(V1_PATHS.charts.symbolPerformance, { top_n })),
  
  getWinLossAnalysis: () => 
    apiClient.get(V1_PATHS.charts.winLossAnalysis),
  
  getMonthlyComparison: (months: number = 12) =>
    apiClient.get(withQuery(V1_PATHS.charts.monthlyComparison, { months })),
  
  getRiskReward: () => 
    apiClient.get(V1_PATHS.charts.riskReward),
};

// Reports API
export const reportsApi = {
  getAll: () => 
    apiClient.get(V1_PATHS.reports.list),
  
  create: (report: any) => 
    apiClient.post(V1_PATHS.reports.create, report),
  
  generate: (params: { start_date: string; end_date: string; include_trades?: boolean; include_charts?: boolean }) =>
    apiClient.post(V1_PATHS.reports.generate, params),
  
  getHistory: () => 
    apiClient.get(V1_PATHS.reports.history),
};

// Health API
export const healthApi = {
  check: () => 
    apiClient.get(V1_PATHS.health.check),
  
  getStatus: () => 
    apiClient.get(V1_PATHS.health.status),
};

// Trading Control API
export const tradingControlApi = {
  start: (params: { account_id: number; currency_symbols?: string[]; check_autotrading?: boolean }) =>
    apiClient.post(V1_PATHS.tradingControl.start, params),
  
  stop: (account_id: number) => 
    apiClient.post(V1_PATHS.tradingControl.stop, { account_id }),
  
  getStatus: (account_id: number) =>
    apiClient.get(withQuery(V1_PATHS.tradingControl.status, { account_id })),
  
  getAutoTradingStatus: (account_id: number) =>
    apiClient.get(withQuery(V1_PATHS.tradingControl.autotradingStatus, { account_id })),
};

// Workers API
export const workersApi = {
  getAll: () => 
    apiClient.get(V1_PATHS.workers.list),
  
  getById: (account_id: number) => 
    apiClient.get(V1_PATHS.workers.byId(account_id)),
  
  start: (account_id: number, params?: { apply_defaults?: boolean; validate?: boolean }) =>
    apiClient.post(V1_PATHS.workers.start(account_id), params || {}),
  
  stop: (account_id: number) => 
    apiClient.post(V1_PATHS.workers.stop(account_id)),
  
  restart: (account_id: number) => 
    apiClient.post(V1_PATHS.workers.restart(account_id)),
  
  startAll: () => 
    apiClient.post(V1_PATHS.workers.startAll),
  
  stopAll: () => 
    apiClient.post(V1_PATHS.workers.stopAll),
  
  validate: (account_id: number) => 
    apiClient.get(V1_PATHS.workers.validate(account_id)),
  
  validateAll: () => 
    apiClient.get(V1_PATHS.workers.validateAll),
};

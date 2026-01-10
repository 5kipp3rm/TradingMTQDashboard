/**
 * Phase 5 Frontend: V2 API Client
 *
 * API client for new OOP-based v2 endpoints
 */

import { apiClient, ApiResponse } from './api';
import { V2_PATHS } from './api-paths';

// ============================================================================
// Types
// ============================================================================

export interface AccountStatus {
  id: number;
  name: string;
  state: string;
  is_connected: boolean;
  is_trading: boolean;
  currencies: string[];
  active_currencies: number;
  last_error: string | null;
  config: {
    max_concurrent_trades: number;
    portfolio_risk: number;
    check_interval: number;
  };
  ai_pipeline?: {
    enhancers: Array<{
      name: string;
      enabled: boolean;
      type: string;
    }>;
    filters: Array<{
      name: string;
      enabled: boolean;
      type: string;
    }>;
    total_enhancers: number;
    total_filters: number;
    active_enhancers: number;
    active_filters: number;
  };
}

export interface OperationResponse {
  success: boolean;
  error?: string;
}

export interface BulkOperationResponse {
  results: Record<string, {
    success: boolean;
    error?: string;
  }>;
}

export interface StatusSummary {
  total_accounts: number;
  connected: number;
  trading: number;
  by_state: Record<string, number>;
  accounts: Array<{
    id: number;
    name: string;
    state: string;
    currencies: number;
  }>;
}

export interface ConnectedAccount {
  id: number;
  name: string;
  state: string;
}

export interface TradingAccount {
  id: number;
  name: string;
  currencies: number;
}

export interface CurrencyConfig {
  symbol: string;
  enabled: boolean;
  strategy_type: string;
  strategy_params: Record<string, any>;
  risk_percent: number;
  timeframe: string;
  sl_pips: number;
  tp_pips: number;
  max_position_size: number;
  min_position_size: number;
  max_positions: number;
  allow_stacking: boolean;
}

export interface CurrencyConfigRequest {
  symbol: string;
  enabled?: boolean;
  strategy: {
    strategy_type: string;
    params: Record<string, any>;
  };
  risk_percent: number;
  timeframe?: string;
  sl_pips: number;
  tp_pips: number;
  max_position_size?: number;
  min_position_size?: number;
  max_positions?: number;
  allow_stacking?: boolean;
}

export interface AIConfig {
  use_ml_enhancement: boolean;
  ml_model_type?: string;
  ml_model_params?: Record<string, any>;
  use_llm_sentiment: boolean;
  llm_sentiment_provider?: string;
  llm_sentiment_model?: string;
  use_llm_analyst: boolean;
  llm_analyst_provider?: string;
  llm_analyst_model?: string;
}

export interface AIConfigUpdate {
  use_ml_enhancement?: boolean;
  ml_model_type?: string;
  ml_model_params?: Record<string, any>;
  use_llm_sentiment?: boolean;
  llm_sentiment_provider?: string;
  llm_sentiment_model?: string;
  llm_sentiment_api_key?: string;
  use_llm_analyst?: boolean;
  llm_analyst_provider?: string;
  llm_analyst_model?: string;
  llm_analyst_api_key?: string;
}

export interface MT5AccountInfo {
  login: number;
  server: string;
  name: string;
  company: string;
  currency: string;
  balance: number;
  equity: number;
  profit: number;
  margin: number;
  margin_free: number;
  margin_level: number;
  leverage: number;
  trade_allowed: boolean;
}

export interface MLEnableRequest {
  ml_model_type: string;
  ml_model_params?: Record<string, any>;
}

export interface LLMEnableRequest {
  provider: string;
  model: string;
  api_key: string;
}

// ============================================================================
// Account Management V2 API
// ============================================================================

export const accountsV2Api = {
  // Account CRUD
  getById: (accountId: number): Promise<ApiResponse<any>> =>
    apiClient.get(V2_PATHS.accounts.byId(accountId)),

  // Connection management
  connect: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.connect(accountId)),

  disconnect: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.disconnect(accountId)),

  getStatus: (accountId: number): Promise<ApiResponse<AccountStatus>> =>
    apiClient.get(V2_PATHS.accounts.status(accountId)),

  getMT5Info: (accountId: number): Promise<ApiResponse<MT5AccountInfo>> =>
    apiClient.get(V2_PATHS.accounts.mt5Info(accountId)),

  // Trading control
  startTrading: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.startTrading(accountId)),

  stopTrading: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.stopTrading(accountId)),

  pauseTrading: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.pauseTrading(accountId)),

  resumeTrading: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.resumeTrading(accountId)),

  // Bulk operations
  connectAll: (): Promise<ApiResponse<BulkOperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.connectAll),

  disconnectAll: (): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.disconnectAll),

  startAllTrading: (): Promise<ApiResponse<BulkOperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.startAllTrading),

  stopAllTrading: (): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.accounts.stopAllTrading),

  // Query operations
  getStatusSummary: (): Promise<ApiResponse<StatusSummary>> =>
    apiClient.get(V2_PATHS.accounts.statusSummary),

  getConnected: (): Promise<ApiResponse<{ count: number; accounts: ConnectedAccount[] }>> =>
    apiClient.get(V2_PATHS.accounts.connected),

  getTrading: (): Promise<ApiResponse<{ count: number; accounts: TradingAccount[] }>> =>
    apiClient.get(V2_PATHS.accounts.trading),
};

// ============================================================================
// Currency Management V2 API
// ============================================================================

export const currenciesV2Api = {
  // List currencies for account
  list: (accountId: number): Promise<ApiResponse<CurrencyConfig[]>> =>
    apiClient.get(V2_PATHS.currencies.list(accountId)),

  // Alias for list (for backward compatibility)
  getAll: (accountId: number): Promise<ApiResponse<CurrencyConfig[]>> =>
    apiClient.get(V2_PATHS.currencies.list(accountId)),

  // Add currency to account
  add: (accountId: number, config: CurrencyConfigRequest): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.currencies.create(accountId), config),

  // Get specific currency config
  get: (accountId: number, symbol: string): Promise<ApiResponse<CurrencyConfig>> =>
    apiClient.get(V2_PATHS.currencies.bySymbol(accountId, symbol)),

  // Update currency config (partial)
  update: (accountId: number, symbol: string, config: Partial<CurrencyConfigRequest>): Promise<ApiResponse<OperationResponse>> =>
    apiClient.patch(V2_PATHS.currencies.update(accountId, symbol), config),

  // Remove currency from account
  remove: (accountId: number, symbol: string): Promise<ApiResponse<OperationResponse>> =>
    apiClient.delete(V2_PATHS.currencies.delete(accountId, symbol)),

  // Get strategy for currency
  getStrategy: (accountId: number, symbol: string): Promise<ApiResponse<{ strategy_type: string; params: Record<string, any> }>> =>
    apiClient.get(V2_PATHS.currencies.strategy(accountId, symbol)),

  // Update strategy for currency
  updateStrategy: (accountId: number, symbol: string, strategy: { strategy_type: string; params: Record<string, any> }): Promise<ApiResponse<OperationResponse>> =>
    apiClient.patch(V2_PATHS.currencies.updateStrategy(accountId, symbol), strategy),
};

// ============================================================================
// AI Configuration V2 API
// ============================================================================

export const aiConfigV2Api = {
  // Get AI config
  get: (accountId: number): Promise<ApiResponse<AIConfig>> =>
    apiClient.get(V2_PATHS.aiConfig.get(accountId)),

  // Update AI config
  update: (accountId: number, config: AIConfigUpdate): Promise<ApiResponse<OperationResponse>> =>
    apiClient.patch(V2_PATHS.aiConfig.update(accountId), config),

  // ML enhancement
  enableML: (accountId: number, config: MLEnableRequest): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.aiConfig.enableML(accountId), config),

  disableML: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.aiConfig.disableML(accountId)),

  // LLM sentiment
  enableLLMSentiment: (accountId: number, config: LLMEnableRequest): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.aiConfig.enableLLMSentiment(accountId), config),

  disableLLMSentiment: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.aiConfig.disableLLMSentiment(accountId)),

  // LLM analyst
  enableLLMAnalyst: (accountId: number, config: LLMEnableRequest): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.aiConfig.enableLLMAnalyst(accountId), config),

  disableLLMAnalyst: (accountId: number): Promise<ApiResponse<OperationResponse>> =>
    apiClient.post(V2_PATHS.aiConfig.disableLLMAnalyst(accountId)),
};

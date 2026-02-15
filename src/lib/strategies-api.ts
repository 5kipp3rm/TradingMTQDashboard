/**
 * Strategies API Client
 * Phase 5: Frontend integration for per-symbol strategy management with AI config
 */

import { apiClient, ApiResponse } from './api';
import { V2_PATHS } from './api-paths';

// ============================================================================
// Types
// ============================================================================

export interface Strategy {
  id: number;
  account_id: number;
  symbol: string;
  strategy_type: string;
  execution_mode: 'python' | 'ea' | 'hybrid';
  enabled: boolean;
  strategy_params: Record<string, any>;
  
  // Risk Management
  risk_percent: number;
  sl_pips: number;
  tp_pips: number;
  max_position_size: number;
  min_position_size: number;
  
  // Trading Rules
  timeframe: string;
  max_positions: number;
  allow_stacking: boolean;
  
  // Phase 4b: Per-Symbol AI Configuration
  use_ml_enhancement?: boolean;
  ml_model_type?: 'lstm' | 'random_forest' | null;
  ml_model_params?: Record<string, any> | null;
  
  use_llm_sentiment?: boolean;
  llm_sentiment_provider?: 'openai' | 'anthropic' | null;
  llm_sentiment_model?: string | null;
  
  use_llm_analyst?: boolean;
  llm_analyst_provider?: 'openai' | 'anthropic' | null;
  llm_analyst_model?: string | null;
  
  // Metadata
  created_at?: string;
  updated_at?: string;
}

export interface StrategyListResponse {
  account_id: number;
  total_strategies: number;
  enabled_count: number;
  disabled_count: number;
  execution_modes: Record<string, number>;
  strategies: Strategy[];
}

export interface CreateStrategyRequest {
  symbol: string;
  strategy_type: string;
  execution_mode?: 'python' | 'ea' | 'hybrid';
  enabled?: boolean;
  strategy_params?: Record<string, any>;
  
  // AI Configuration (optional)
  use_ml_enhancement?: boolean;
  ml_model_type?: 'lstm' | 'random_forest';
  ml_model_params?: Record<string, any>;
  
  use_llm_sentiment?: boolean;
  llm_sentiment_provider?: 'openai' | 'anthropic';
  llm_sentiment_model?: string;
  
  use_llm_analyst?: boolean;
  llm_analyst_provider?: 'openai' | 'anthropic';
  llm_analyst_model?: string;
}

export interface UpdateStrategyRequest {
  strategy_type?: string;
  execution_mode?: 'python' | 'ea' | 'hybrid';
  enabled?: boolean;
  strategy_params?: Record<string, any>;
  
  // AI Configuration updates
  use_ml_enhancement?: boolean;
  ml_model_type?: 'lstm' | 'random_forest' | null;
  ml_model_params?: Record<string, any> | null;
  
  use_llm_sentiment?: boolean;
  llm_sentiment_provider?: 'openai' | 'anthropic' | null;
  llm_sentiment_model?: string | null;
  
  use_llm_analyst?: boolean;
  llm_analyst_provider?: 'openai' | 'anthropic' | null;
  llm_analyst_model?: string | null;
}

export interface StrategyStatus {
  symbol: string;
  strategy_type: string;
  execution_mode: string;
  enabled: boolean;
  running: boolean;
  positions_count: number;
  execution_count: number;
  error_count: number;
  last_execution: string | null;
  last_error: string | null;
  
  // AI Status
  ml_enabled: boolean;
  llm_sentiment_enabled: boolean;
  llm_analyst_enabled: boolean;
}

export interface StrategyPerformance {
  symbol: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_profit: number;
  average_profit: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

// ============================================================================
// Strategies API
// ============================================================================

export const strategiesApi = {
  /**
   * List all strategies for an account
   */
  list: (accountId: number): Promise<ApiResponse<StrategyListResponse>> =>
    apiClient.get(V2_PATHS.strategies.list(accountId)),

  /**
   * Create a new strategy
   */
  create: (accountId: number, data: CreateStrategyRequest): Promise<ApiResponse<Strategy>> =>
    apiClient.post(V2_PATHS.strategies.create(accountId), data),

  /**
   * Get specific strategy
   */
  get: (accountId: number, symbol: string): Promise<ApiResponse<Strategy>> =>
    apiClient.get(V2_PATHS.strategies.bySymbol(accountId, symbol)),

  /**
   * Update strategy configuration (partial update)
   */
  update: (accountId: number, symbol: string, data: UpdateStrategyRequest): Promise<ApiResponse<Strategy>> =>
    apiClient.patch(V2_PATHS.strategies.update(accountId, symbol), data),

  /**
   * Delete strategy
   */
  delete: (accountId: number, symbol: string): Promise<ApiResponse<{ success: boolean }>> =>
    apiClient.delete(V2_PATHS.strategies.delete(accountId, symbol)),

  /**
   * Get strategy status (runtime state)
   */
  getStatus: (accountId: number, symbol: string): Promise<ApiResponse<StrategyStatus>> =>
    apiClient.get(V2_PATHS.strategies.status(accountId, symbol)),

  /**
   * Get strategy performance metrics
   */
  getPerformance: (accountId: number, symbol: string): Promise<ApiResponse<StrategyPerformance>> =>
    apiClient.get(V2_PATHS.strategies.performance(accountId, symbol)),

  /**
   * Enable strategy
   */
  enable: (accountId: number, symbol: string): Promise<ApiResponse<{ success: boolean }>> =>
    apiClient.post(V2_PATHS.strategies.enable(accountId, symbol)),

  /**
   * Disable strategy
   */
  disable: (accountId: number, symbol: string): Promise<ApiResponse<{ success: boolean }>> =>
    apiClient.post(V2_PATHS.strategies.disable(accountId, symbol)),

  // ========================================================================
  // AI Configuration Methods
  // ========================================================================

  /**
   * Update ML configuration for a strategy
   */
  updateMLConfig: (accountId: number, symbol: string, config: {
    use_ml_enhancement: boolean;
    ml_model_type?: 'lstm' | 'random_forest';
    ml_model_params?: Record<string, any>;
  }): Promise<ApiResponse<Strategy>> =>
    apiClient.patch(V2_PATHS.strategies.update(accountId, symbol), config),

  /**
   * Update LLM Sentiment configuration
   */
  updateSentimentConfig: (accountId: number, symbol: string, config: {
    use_llm_sentiment: boolean;
    llm_sentiment_provider?: 'openai' | 'anthropic';
    llm_sentiment_model?: string;
  }): Promise<ApiResponse<Strategy>> =>
    apiClient.patch(V2_PATHS.strategies.update(accountId, symbol), config),

  /**
   * Update LLM Analyst configuration
   */
  updateAnalystConfig: (accountId: number, symbol: string, config: {
    use_llm_analyst: boolean;
    llm_analyst_provider?: 'openai' | 'anthropic';
    llm_analyst_model?: string;
  }): Promise<ApiResponse<Strategy>> =>
    apiClient.patch(V2_PATHS.strategies.update(accountId, symbol), config),

  /**
   * Bulk enable/disable AI feature across strategies
   */
  bulkUpdateAI: (accountId: number, feature: 'ml' | 'sentiment' | 'analyst', enabled: boolean): Promise<ApiResponse<{
    updated: number;
    errors: Array<{ symbol: string; error: string }>;
  }>> =>
    apiClient.post(V2_PATHS.strategies.bulkAiUpdate(accountId), {
      feature,
      enabled
    }),
};

// ============================================================================
// Strategy Types & Execution Modes
// ============================================================================

export const STRATEGY_TYPES = [
  { value: 'SimpleMA', label: 'Simple MA Crossover', description: 'Moving average crossover strategy' },
  { value: 'RSI', label: 'RSI Strategy', description: 'RSI overbought/oversold signals' },
  { value: 'MACD', label: 'MACD Strategy', description: 'MACD signal line crossover' },
  { value: 'BBands', label: 'Bollinger Bands', description: 'Bollinger Bands breakout/reversion' },
  { value: 'MultiIndicator', label: 'Multi-Indicator', description: 'Combines multiple indicators' },
  { value: 'ML', label: 'ML-Enhanced', description: 'Machine learning enhanced signals' },
] as const;

export const EXECUTION_MODES = [
  { value: 'python', label: 'Python', description: 'Execute directly via Python MT5 API' },
  { value: 'ea', label: 'Expert Advisor', description: 'Execute via MQL5 EA in MT5 terminal' },
  { value: 'hybrid', label: 'Hybrid', description: 'Python analysis + EA execution' },
] as const;

export const ML_MODEL_TYPES = [
  { value: 'lstm', label: 'LSTM', description: 'Long Short-Term Memory neural network' },
  { value: 'random_forest', label: 'Random Forest', description: 'Ensemble decision tree classifier' },
] as const;

export const LLM_PROVIDERS = [
  { value: 'openai', label: 'OpenAI', models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
  { value: 'anthropic', label: 'Anthropic', models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'] },
] as const;

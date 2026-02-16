/**
 * Crypto Trading Types
 *
 * TypeScript interfaces for cryptocurrency trading features.
 */

export interface CryptoAccount {
  account_id: number;
  account_name: string;
  exchange: string;
  testnet: boolean;
  is_active: boolean;
  auto_connect: boolean;
  balance_summary?: BalanceSummary;
  connection_status: string;
  created_at: string;
  updated_at: string;
  description?: string;
}

export interface BalanceSummary {
  total_assets: number;
  balances: Balance[];
  timestamp: string;
}

export interface Balance {
  asset: string;
  free: string;
  locked: string;
  total: string;
  usd_value?: string;
}

export interface CryptoPosition {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  position_value: number;
  opened_at: string;
}

export interface PositionSummary {
  total_positions: number;
  total_value: number;
  total_unrealized_pnl: number;
  total_unrealized_pnl_percent: number;
  positions: CryptoPosition[];
  timestamp: string;
}

export interface CryptoOrder {
  order_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  order_type: 'MARKET' | 'LIMIT';
  status: string;
  quantity: number;
  filled_quantity: number;
  price?: number;
  average_fill_price?: number;
  commission?: number;
  commission_asset?: string;
  created_at: string;
  updated_at?: string;
}

export interface OrderListResponse {
  total_orders: number;
  orders: CryptoOrder[];
  has_more: boolean;
  timestamp: string;
}

export interface MarketTicker {
  symbol: string;
  last_price: number;
  bid_price: number;
  ask_price: number;
  high_24h: number;
  low_24h: number;
  volume_24h: number;
  price_change_24h: number;
  price_change_percent_24h: number;
  timestamp: string;
}

export interface PortfolioSummary {
  account_id: number;
  total_balance_usd: number;
  total_positions: number;
  open_positions_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  realized_pnl_today: number;
  realized_pnl_week: number;
  realized_pnl_month: number;
  top_gainers: PositionPnL[];
  top_losers: PositionPnL[];
  timestamp: string;
}

export interface PositionPnL {
  symbol: string;
  pnl: number;
  pnl_percent: number;
  value: number;
}

export interface PerformanceMetrics {
  period: 'daily' | 'weekly' | 'monthly';
  total_return: number;
  total_return_percent: number;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio?: number;
  max_drawdown: number;
  max_drawdown_percent: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  timestamp: string;
}

export interface Exchange {
  exchange: string;
  name: string;
  status: string;
  features: string[];
  base_currencies: string[];
  fee_tier: string;
}

export interface Symbol {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  status: string;
  min_order_quantity: number;
  max_order_quantity: number;
  min_notional: number;
  price_precision: number;
  quantity_precision: number;
}

// Request types
export interface CreateAccountRequest {
  account_name: string;
  exchange: string;
  api_key: string;
  api_secret: string;
  testnet: boolean;
  is_active?: boolean;
  auto_connect?: boolean;
  description?: string;
}

export interface UpdateAccountRequest {
  account_name?: string;
  api_key?: string;
  api_secret?: string;
  testnet?: boolean;
  is_active?: boolean;
  auto_connect?: boolean;
  description?: string;
}

export interface PlaceOrderRequest {
  symbol: string;
  side: 'BUY' | 'SELL';
  order_type: 'MARKET' | 'LIMIT';
  quantity: number;
  price?: number;
}

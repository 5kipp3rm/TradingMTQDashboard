export interface Trade {
  ticket: number;
  symbol: string;
  type: 'buy' | 'sell';
  entryTime: string;
  exitTime?: string;
  entryPrice: number;
  exitPrice?: number;
  volume: number;
  profit: number;
  pips: number;
  status: 'open' | 'closed' | 'pending';
}

export interface Position {
  ticket: number;
  symbol: string;
  type: 'buy' | 'sell';
  volume: number;
  openPrice: number;
  currentPrice: number;
  sl: number | null;
  tp: number | null;
  profit: number;
  openTime: string;
  closeTime?: string;
  account_id?: number;
  account_name?: string;
}

export interface DailyPerformance {
  date: string;
  trades: number;
  winners: number;
  losers: number;
  netProfit: number;
  winRate: number;
  profitFactor: number;
}

export interface DashboardSummary {
  totalTrades: number;
  netProfit: number;
  winRate: number;
  avgDailyProfit: number;
}

export interface ChartDataPoint {
  date: string;
  value: number;
}

export interface Account {
  id: string;
  account_number: number;
  account_name: string;
  broker: string;
  server: string;
  platform_type: string;
  login: number;
  is_active: boolean;
  is_default: boolean;
  is_demo: boolean;
  auto_connect: boolean;
  currency: string;
  initial_balance?: number;
  description?: string;
  created_at: string;
  updated_at?: string;
  last_connected?: string;

  // Legacy/compatibility properties (computed from above)
  name?: string;  // alias for account_name
  balance?: number;  // can be initial_balance or real-time balance
  equity?: number;  // real-time value
  margin?: number;  // real-time value
  freeMargin?: number;  // real-time value
  leverage?: number;  // real-time value
  isActive?: boolean;  // alias for is_active
}

export interface CurrencyPair {
  symbol: string;
  description: string;
  bid: number;
  ask: number;
  spread: number;
  enabled: boolean;
  point?: number;  // Symbol point value (e.g., 0.0001 for EURUSD, 0.01 for XAUUSD)
}

export interface Alert {
  id: string;
  symbol: string;
  condition: 'above' | 'below' | 'cross';
  price: number;
  triggered: boolean;
  createdAt: string;
  triggeredAt?: string;
}

export interface QuickTradeParams {
  symbol: string;
  volume: number;
  type: 'buy' | 'sell';
  sl?: number;
  tp?: number;
  comment?: string;
}

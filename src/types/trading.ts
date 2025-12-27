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
  name: string;
  broker: string;
  balance: number;
  equity: number;
  margin: number;
  freeMargin: number;
  leverage: number;
  currency: string;
  isActive: boolean;
}

export interface CurrencyPair {
  symbol: string;
  description: string;
  bid: number;
  ask: number;
  spread: number;
  enabled: boolean;
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

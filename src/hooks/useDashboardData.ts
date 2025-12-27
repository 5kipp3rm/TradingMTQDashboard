import { useState, useCallback } from "react";
import type {
  DashboardSummary,
  Trade,
  Position,
  DailyPerformance,
  ChartDataPoint,
  CurrencyPair,
} from "@/types/trading";

// Mock data generator
const generateMockData = (period: number) => {
  const now = new Date();
  
  const summary: DashboardSummary = {
    totalTrades: Math.floor(Math.random() * 500) + 100,
    netProfit: (Math.random() - 0.3) * 10000,
    winRate: Math.random() * 30 + 50,
    avgDailyProfit: (Math.random() - 0.3) * 500,
  };

  const trades: Trade[] = Array.from({ length: 50 }, (_, i) => ({
    ticket: 1000000 + i,
    symbol: ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"][Math.floor(Math.random() * 4)],
    type: Math.random() > 0.5 ? "buy" : "sell",
    entryTime: new Date(now.getTime() - Math.random() * period * 24 * 60 * 60 * 1000).toISOString(),
    exitTime: Math.random() > 0.2 ? new Date(now.getTime() - Math.random() * period * 24 * 60 * 60 * 1000 * 0.5).toISOString() : undefined,
    entryPrice: 1.0800 + Math.random() * 0.05,
    exitPrice: 1.0800 + Math.random() * 0.05,
    volume: Math.floor(Math.random() * 10) / 10 + 0.1,
    profit: (Math.random() - 0.4) * 500,
    pips: (Math.random() - 0.4) * 100,
    status: Math.random() > 0.2 ? "closed" : "open",
  }));

  const positions: Position[] = Array.from({ length: Math.floor(Math.random() * 5) }, (_, i) => ({
    ticket: 2000000 + i,
    symbol: ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"][Math.floor(Math.random() * 4)],
    type: Math.random() > 0.5 ? "buy" : "sell",
    volume: Math.floor(Math.random() * 10) / 10 + 0.1,
    openPrice: 1.0800 + Math.random() * 0.05,
    currentPrice: 1.0800 + Math.random() * 0.05,
    sl: Math.random() > 0.5 ? 1.0700 + Math.random() * 0.05 : null,
    tp: Math.random() > 0.5 ? 1.0900 + Math.random() * 0.05 : null,
    profit: (Math.random() - 0.4) * 200,
    openTime: new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
  }));

  const dailyPerformance: DailyPerformance[] = Array.from({ length: Math.min(period, 30) }, (_, i) => {
    const winners = Math.floor(Math.random() * 10);
    const losers = Math.floor(Math.random() * 5);
    return {
      date: new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
      trades: winners + losers,
      winners,
      losers,
      netProfit: (Math.random() - 0.3) * 1000,
      winRate: winners / (winners + losers) * 100 || 0,
      profitFactor: Math.random() * 2 + 0.5,
    };
  });

  const profitData: ChartDataPoint[] = Array.from({ length: Math.min(period, 30) }, (_, i) => ({
    date: new Date(now.getTime() - (Math.min(period, 30) - 1 - i) * 24 * 60 * 60 * 1000)
      .toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    value: Math.random() * 5000 + i * 100,
  }));

  const winRateData: ChartDataPoint[] = Array.from({ length: Math.min(period, 30) }, (_, i) => ({
    date: new Date(now.getTime() - (Math.min(period, 30) - 1 - i) * 24 * 60 * 60 * 1000)
      .toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    value: Math.random() * 30 + 50,
  }));

  return { summary, trades, positions, dailyPerformance, profitData, winRateData };
};

const mockCurrencies: CurrencyPair[] = [
  { symbol: "EURUSD", description: "Euro / US Dollar", bid: 1.0850, ask: 1.0852, spread: 2, enabled: true },
  { symbol: "GBPUSD", description: "British Pound / US Dollar", bid: 1.2650, ask: 1.2653, spread: 3, enabled: true },
  { symbol: "USDJPY", description: "US Dollar / Japanese Yen", bid: 149.50, ask: 149.53, spread: 3, enabled: true },
  { symbol: "AUDUSD", description: "Australian Dollar / US Dollar", bid: 0.6520, ask: 0.6522, spread: 2, enabled: true },
  { symbol: "USDCAD", description: "US Dollar / Canadian Dollar", bid: 1.3580, ask: 1.3583, spread: 3, enabled: true },
  { symbol: "NZDUSD", description: "New Zealand Dollar / US Dollar", bid: 0.6120, ask: 0.6122, spread: 2, enabled: true },
  { symbol: "USDCHF", description: "US Dollar / Swiss Franc", bid: 0.8750, ask: 0.8753, spread: 3, enabled: true },
  { symbol: "XAUUSD", description: "Gold / US Dollar", bid: 2050.50, ask: 2051.00, spread: 50, enabled: true },
];

export function useDashboardData(period: number) {
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState(() => generateMockData(period));
  const [lastUpdate, setLastUpdate] = useState<Date | null>(new Date());
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "disconnected" | "connecting">("connected");

  const refresh = useCallback(() => {
    setIsLoading(true);
    setConnectionStatus("connecting");
    
    // Simulate API call
    setTimeout(() => {
      setData(generateMockData(period));
      setLastUpdate(new Date());
      setConnectionStatus("connected");
      setIsLoading(false);
    }, 500);
  }, [period]);

  const currencies = mockCurrencies;

  return {
    ...data,
    currencies,
    isLoading,
    lastUpdate,
    connectionStatus,
    refresh,
  };
}

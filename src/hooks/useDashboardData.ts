import { useState, useCallback, useEffect } from "react";
import type {
  DashboardSummary,
  Trade,
  Position,
  DailyPerformance,
  ChartDataPoint,
  CurrencyPair,
} from "@/types/trading";
import { analyticsApi, tradesApi, positionsApi, currenciesApi } from "@/lib/api";

export function useDashboardData(period: number, selectedAccountId?: string) {
  const [summary, setSummary] = useState<DashboardSummary>({
    totalTrades: 0,
    netProfit: 0,
    winRate: 0,
    avgDailyProfit: 0,
  });
  const [trades, setTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [dailyPerformance, setDailyPerformance] = useState<DailyPerformance[]>([]);
  const [profitData, setProfitData] = useState<ChartDataPoint[]>([]);
  const [winRateData, setWinRateData] = useState<ChartDataPoint[]>([]);
  const [currencies, setCurrencies] = useState<CurrencyPair[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "disconnected" | "connecting">("disconnected");

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setConnectionStatus("connecting");

    try {
      // Determine account_id parameter (undefined if "all", number if specific account)
      const accountIdParam = selectedAccountId && selectedAccountId !== "all"
        ? parseInt(selectedAccountId, 10)
        : undefined;

      // Fetch all data in parallel
      const [overviewRes, dailyRes, tradesRes, positionsRes, currenciesRes] = await Promise.all([
        analyticsApi.getOverview({ days: period, account_id: accountIdParam }),
        analyticsApi.getDaily({ days: period, account_id: accountIdParam }),
        tradesApi.getAll({ limit: 100, account_id: accountIdParam }),
        positionsApi.getOpen(accountIdParam ? { account_id: accountIdParam } : undefined),
        currenciesApi.getAll(),
      ]);

      // Handle analytics overview
      if (overviewRes.data) {
        const overviewData = overviewRes.data as any;
        setSummary({
          totalTrades: overviewData.total_trades || 0,
          netProfit: overviewData.net_profit || 0,
          winRate: overviewData.win_rate || 0,
          avgDailyProfit: overviewData.avg_daily_profit || 0,
        });
      } else {
        console.error("Analytics overview error:", overviewRes.error);
      }

      // Handle daily performance
      if (dailyRes.data) {
        const dailyResponse = dailyRes.data as any;
        // Backend returns {records: [...]} not a plain array
        const dailyData = dailyResponse.records || dailyResponse || [];
        setDailyPerformance(
          dailyData.map((d: any) => ({
            date: d.date,
            trades: d.total_trades || d.trades || 0,
            winners: d.winning_trades || d.winners || 0,
            losers: d.losing_trades || d.losers || 0,
            netProfit: d.net_profit || 0,
            winRate: d.win_rate || 0,
            profitFactor: d.profit_factor || 0,
          }))
        );

        // Generate chart data from daily performance
        setProfitData(
          dailyData.map((d: any) => ({
            date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            value: d.net_profit || 0,
          }))
        );

        setWinRateData(
          dailyData.map((d: any) => ({
            date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            value: d.win_rate || 0,
          }))
        );
      } else {
        console.error("Daily performance error:", dailyRes.error);
      }

      // Handle trades
      if (tradesRes.data) {
        const tradesData = (tradesRes.data as any).trades || [];
        setTrades(
          tradesData.map((t: any) => ({
            ticket: t.ticket,
            symbol: t.symbol,
            type: t.type?.toLowerCase() as "buy" | "sell",
            entryTime: t.open_time,
            exitTime: t.close_time,
            entryPrice: t.open_price,
            exitPrice: t.close_price,
            volume: t.volume,
            profit: t.profit || 0,
            pips: t.pips || 0,
            status: (t.status?.toLowerCase() || (t.close_time ? "closed" : "open")) as "open" | "closed" | "pending",
          }))
        );
      } else {
        console.error("Trades error:", tradesRes.error);
      }

      // Handle positions
      if (positionsRes.data) {
        // API returns List[PositionInfo] directly, not wrapped in an object
        const positionsData = Array.isArray(positionsRes.data) ? positionsRes.data : [];
        setPositions(
          positionsData.map((p: any) => ({
            ticket: p.ticket,
            symbol: p.symbol,
            type: p.type?.toLowerCase() as "buy" | "sell",
            volume: p.volume,
            openPrice: p.price_open,
            currentPrice: p.price_current || p.price_open,
            sl: p.sl || null,
            tp: p.tp || null,
            profit: p.profit || 0,
            openTime: p.open_time,
          }))
        );
      } else {
        console.error("Positions error:", positionsRes.error);
      }

      // Handle currencies
      if (currenciesRes.data) {
        const currenciesData = (currenciesRes.data as any).currencies || [];
        setCurrencies(
          currenciesData.map((c: any) => ({
            symbol: c.symbol,
            description: c.description || c.symbol,
            bid: c.bid || 0,
            ask: c.ask || 0,
            spread: c.spread || 0,
            enabled: c.enabled !== undefined ? c.enabled : true,
          }))
        );
      } else {
        console.error("Currencies error:", currenciesRes.error);
      }

      setLastUpdate(new Date());
      setConnectionStatus("connected");
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      setConnectionStatus("disconnected");
    } finally {
      setIsLoading(false);
    }
  }, [period, selectedAccountId]);

  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  // Fetch data on mount and when period changes
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    summary,
    trades,
    positions,
    dailyPerformance,
    profitData,
    winRateData,
    currencies,
    isLoading,
    lastUpdate,
    connectionStatus,
    refresh,
  };
}

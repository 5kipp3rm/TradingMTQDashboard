import { useState, useCallback, useEffect } from "react";
import type {
  DashboardSummary,
  Trade,
  Position,
  DailyPerformance,
  ChartDataPoint,
  CurrencyPair,
} from "@/types/trading";
import { analyticsApi, tradesApi, positionsApi } from "@/lib/api";
import { currenciesV2Api } from "@/lib/api-v2";
import {
  calculateSummary,
  calculateCumulativeProfit,
  calculateWinRateTrend,
  calculateDailyPerformance,
  calculateEquityCurve,
  calculateProfitByCurrency,
  calculateWinLossDistribution,
  calculateMonthlyPerformance,
  filterByDateRange,
} from "@/utils/analyticsCalculator";
import { useWebSocket } from "./useWebSocket";
import { useIncrementalData } from "./useIncrementalData";

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
  const [equityCurve, setEquityCurve] = useState<ChartDataPoint[]>([]);
  const [profitByCurrency, setProfitByCurrency] = useState<any[]>([]);
  const [winLossDistribution, setWinLossDistribution] = useState<any[]>([]);
  const [monthlyPerformance, setMonthlyPerformance] = useState<any[]>([]);
  const [currencies, setCurrencies] = useState<CurrencyPair[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "disconnected" | "connecting">("disconnected");

  // Use incremental data fetching
  const {
    getClosedPositionsIncremental,
    addClosedPosition,
    getCachedClosedPositions,
  } = useIncrementalData();

  // Calculate chart data from closed positions
  const updateChartsFromClosedPositions = useCallback((closedPositions: Position[]) => {
    const filteredPositions = filterByDateRange(
      closedPositions.filter(p => p.closeTime) as any,
      period
    );

    const allClosedWithTime = closedPositions.filter(p => p.closeTime) as any;

    // Update summary
    const calculatedSummary = calculateSummary(filteredPositions);
    setSummary(calculatedSummary);

    // Update charts
    setProfitData(calculateCumulativeProfit(filteredPositions));
    setWinRateData(calculateWinRateTrend(filteredPositions));
    setEquityCurve(calculateEquityCurve(allClosedWithTime, 10000));
    setProfitByCurrency(calculateProfitByCurrency(filteredPositions));
    setWinLossDistribution(calculateWinLossDistribution(filteredPositions));
    setMonthlyPerformance(calculateMonthlyPerformance(allClosedWithTime));
    setDailyPerformance(calculateDailyPerformance(filteredPositions));
  }, [period]);

  // WebSocket connection for real-time updates
  const wsUrl = `ws://localhost:8000/api/ws/dashboard${selectedAccountId && selectedAccountId !== "all" ? `?account_id=${selectedAccountId}` : ""}`;
  
  useWebSocket(wsUrl, {
    enabled: false, // Temporarily disabled - causing console spam
    onPositionUpdate: (updatedPosition: any) => {
      // Update position in state
      setPositions(prev => 
        prev.map(p => p.ticket === updatedPosition.ticket ? {
          ...p,
          currentPrice: updatedPosition.price_current,
          profit: updatedPosition.profit,
        } : p)
      );
    },
    onPositionClosed: (closedPosition: any) => {
      // Remove from open positions
      setPositions(prev => prev.filter(p => p.ticket !== closedPosition.ticket));
      
      // Add to closed positions cache
      const position: Position = {
        ticket: closedPosition.ticket,
        symbol: closedPosition.symbol,
        type: closedPosition.type?.toLowerCase() as "buy" | "sell",
        volume: closedPosition.volume,
        openPrice: closedPosition.price_open,
        currentPrice: closedPosition.price_current,
        sl: closedPosition.sl,
        tp: closedPosition.tp,
        profit: closedPosition.profit,
        openTime: closedPosition.time_open,
        closeTime: closedPosition.time_close,
        account_id: closedPosition.account_id,
      };
      
      addClosedPosition(position);
      
      // Recalculate charts with updated closed positions
      const allClosed = getCachedClosedPositions();
      updateChartsFromClosedPositions(allClosed);
    },
    onConnectionChange: (status) => {
      setConnectionStatus(status);
    },
    autoReconnect: true,
  });

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setConnectionStatus("connecting");

    try {
      // Determine account_id parameter (undefined if "all", number if specific account)
      const accountIdParam = selectedAccountId && selectedAccountId !== "all"
        ? parseInt(selectedAccountId, 10)
        : undefined;

      // Fetch closed positions incrementally (with caching)
      const closedPositions = await getClosedPositionsIncremental(async (params) => {
        const res = await positionsApi.getClosed({
          account_id: accountIdParam,
          limit: params.limit,
        });
        return Array.isArray(res.data) ? res.data : [];
      });

      console.log("Closed positions (from cache or API):", closedPositions.length);

      // Fetch all other data in parallel
      // Only fetch currencies if we have a valid account_id
      const fetchPromises = [
        analyticsApi.getOverview({ days: period, account_id: accountIdParam }),
        analyticsApi.getDaily({ days: period, account_id: accountIdParam }),
        tradesApi.getAll({ limit: 100, account_id: accountIdParam }),
        positionsApi.getOpen(accountIdParam ? { account_id: accountIdParam } : undefined),
      ];
      
      // Only fetch currencies if we have a specific account
      if (accountIdParam) {
        fetchPromises.push(currenciesV2Api.getAll(accountIdParam));
      }
      
      const results = await Promise.all(fetchPromises);
      const [overviewRes, dailyRes, tradesRes, positionsRes, currenciesRes] = results;

      // Get closed positions data for calculations
      const closedPositionsData = closedPositions;
      console.log("Closed positions from API:", closedPositionsData.length);
      
      const closedPositionsWithTime = closedPositionsData
        .filter((p: any) => p.close_time || p.time_close)
        .map((p: any) => ({
          ticket: p.ticket,
          symbol: p.symbol,
          type: p.type?.toLowerCase() as "buy" | "sell",
          volume: p.volume,
          openPrice: p.price_open || p.open_price,
          currentPrice: p.price_current || p.current_price || p.close_price,
          sl: p.sl || null,
          tp: p.tp || null,
          profit: p.profit || 0,
          openTime: p.open_time || p.time_open,
          closeTime: p.close_time || p.time_close,
          account_id: p.account_id,
        }));

      console.log("Closed positions with time:", closedPositionsWithTime.length);

      // Filter by date range
      const filteredClosedPositions = filterByDateRange(closedPositionsWithTime, period);
      console.log("Filtered closed positions:", filteredClosedPositions.length, "for period:", period, "days");

      // Handle analytics overview - use calculated data as fallback
      if (overviewRes.data && (overviewRes.data as any).total_trades > 0) {
        const overviewData = overviewRes.data as any;
        console.log("Using backend analytics overview:", overviewData);
        setSummary({
          totalTrades: overviewData.total_trades || 0,
          netProfit: overviewData.net_profit || 0,
          winRate: overviewData.win_rate || 0,
          avgDailyProfit: overviewData.avg_daily_profit || 0,
        });
      } else {
        // Fallback: Calculate from closed positions
        console.log("Using calculated metrics from closed positions");
        const calculatedSummary = calculateSummary(filteredClosedPositions);
        console.log("Calculated summary:", calculatedSummary);
        setSummary(calculatedSummary);
      }

      // Handle daily performance - use calculated data as fallback
      if (dailyRes.data) {
        const dailyResponse = dailyRes.data as any;
        const dailyData = dailyResponse.records || dailyResponse || [];
        
        if (dailyData.length > 0) {
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
          // Fallback: Calculate from closed positions
          console.log("Using calculated daily performance from closed positions");
          const calculatedDaily = calculateDailyPerformance(filteredClosedPositions);
          setDailyPerformance(calculatedDaily);
          
          const calculatedProfit = calculateCumulativeProfit(filteredClosedPositions);
          setProfitData(calculatedProfit);
          
          const calculatedWinRate = calculateWinRateTrend(filteredClosedPositions);
          setWinRateData(calculatedWinRate);
          
          // Calculate new chart data (use all closed positions, not just filtered, for better equity curve)
          const equityCurveData = calculateEquityCurve(closedPositionsWithTime, 10000);
          setEquityCurve(equityCurveData);
          
          const currencyData = calculateProfitByCurrency(filteredClosedPositions);
          setProfitByCurrency(currencyData);
          
          const winLossData = calculateWinLossDistribution(filteredClosedPositions);
          setWinLossDistribution(winLossData);
          
          const monthlyData = calculateMonthlyPerformance(closedPositionsWithTime);
          setMonthlyPerformance(monthlyData);
        }
      } else {
        // Fallback: Calculate from closed positions
        console.log("Using calculated analytics from closed positions");
        const calculatedDaily = calculateDailyPerformance(filteredClosedPositions);
        setDailyPerformance(calculatedDaily);
        
        const calculatedProfit = calculateCumulativeProfit(filteredClosedPositions);
        setProfitData(calculatedProfit);
        
        const calculatedWinRate = calculateWinRateTrend(filteredClosedPositions);
        setWinRateData(calculatedWinRate);
        
        // Calculate new chart data (use all closed positions, not just filtered, for better equity curve)
        const equityCurveData = calculateEquityCurve(closedPositionsWithTime, 10000);
        setEquityCurve(equityCurveData);
        
        const currencyData = calculateProfitByCurrency(filteredClosedPositions);
        setProfitByCurrency(currencyData);
        
        const winLossData = calculateWinLossDistribution(filteredClosedPositions);
        setWinLossDistribution(winLossData);
        
        const monthlyData = calculateMonthlyPerformance(closedPositionsWithTime);
        setMonthlyPerformance(monthlyData);
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
            account_id: p.account_id,
            account_name: p.account_name,
          }))
        );
      } else {
        console.error("Positions error:", positionsRes.error);
      }

      // Handle currencies - v2 API returns array directly
      if (currenciesRes && currenciesRes.data) {
        const currenciesData = Array.isArray(currenciesRes.data) ? currenciesRes.data : [];
        setCurrencies(
          currenciesData.map((c: any) => ({
            symbol: c.symbol,
            description: c.symbol, // v2 doesn't have description
            bid: 0, // v2 doesn't have pricing info
            ask: 0,
            spread: 0,
            enabled: c.enabled !== undefined ? c.enabled : true,
            point: c.point || 0.0001,  // Default to EURUSD point if not provided
          }))
        );
      } else {
        // No account or failed to fetch currencies
        if (currenciesRes?.error) {
          console.error("Currencies error:", currenciesRes.error);
        }
        setCurrencies([]);
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

  // Fetch data on mount and when account changes
  useEffect(() => {
    fetchData();
  }, [selectedAccountId]);

  // When period changes, recalculate from cached closed positions (no API call)
  useEffect(() => {
    const cached = getCachedClosedPositions();
    if (cached.length > 0) {
      updateChartsFromClosedPositions(cached);
    }
  }, [period, updateChartsFromClosedPositions, getCachedClosedPositions]);

  return {
    summary,
    trades,
    positions,
    dailyPerformance,
    profitData,
    winRateData,
    equityCurve,
    profitByCurrency,
    winLossDistribution,
    monthlyPerformance,
    currencies,
    isLoading,
    lastUpdate,
    connectionStatus,
    refresh,
  };
}

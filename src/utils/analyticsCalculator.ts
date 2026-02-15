/**
 * Analytics Calculator
 * 
 * Calculates trading metrics from closed positions data.
 * Used as fallback when backend analytics are not available.
 */

import type { Position, DashboardSummary, ChartDataPoint, DailyPerformance } from "@/types/trading";

interface PositionWithClose extends Position {
  closeTime: string;
}

/**
 * Calculate summary metrics from closed positions
 */
export function calculateSummary(closedPositions: PositionWithClose[]): DashboardSummary {
  if (closedPositions.length === 0) {
    return {
      totalTrades: 0,
      netProfit: 0,
      winRate: 0,
      avgDailyProfit: 0,
    };
  }

  const totalTrades = closedPositions.length;
  const netProfit = closedPositions.reduce((sum, pos) => sum + pos.profit, 0);
  const winningTrades = closedPositions.filter(pos => pos.profit > 0).length;
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;

  // Calculate avg daily profit
  const dates = new Set(
    closedPositions.map(pos => new Date(pos.closeTime).toDateString())
  );
  const tradingDays = dates.size;
  const avgDailyProfit = tradingDays > 0 ? netProfit / tradingDays : 0;

  return {
    totalTrades,
    netProfit,
    winRate,
    avgDailyProfit,
  };
}

/**
 * Calculate cumulative profit data for chart
 */
export function calculateCumulativeProfit(closedPositions: PositionWithClose[]): ChartDataPoint[] {
  if (closedPositions.length === 0) {
    return [];
  }

  // Sort by close time
  const sorted = [...closedPositions].sort((a, b) => 
    new Date(a.closeTime).getTime() - new Date(b.closeTime).getTime()
  );

  // Group by date first to get daily profits
  const dailyProfits = new Map<string, number>();
  
  sorted.forEach(pos => {
    const dateKey = new Date(pos.closeTime).toISOString().split('T')[0]; // YYYY-MM-DD
    const current = dailyProfits.get(dateKey) || 0;
    dailyProfits.set(dateKey, current + pos.profit);
  });

  // Sort dates and calculate cumulative
  const sortedDates = Array.from(dailyProfits.keys()).sort();
  let cumulativeProfit = 0;
  
  return sortedDates.map(dateKey => {
    cumulativeProfit += dailyProfits.get(dateKey) || 0;
    const date = new Date(dateKey).toLocaleDateString("en-US", { 
      month: "short", 
      day: "numeric" 
    });
    return {
      date,
      value: cumulativeProfit,
    };
  });
}

/**
 * Calculate win rate trend data for chart
 */
export function calculateWinRateTrend(closedPositions: PositionWithClose[]): ChartDataPoint[] {
  if (closedPositions.length === 0) {
    return [];
  }

  // Sort by close time
  const sorted = [...closedPositions].sort((a, b) => 
    new Date(a.closeTime).getTime() - new Date(b.closeTime).getTime()
  );

  // Group by date
  const dailyTrades = new Map<string, { wins: number; total: number }>();

  sorted.forEach(pos => {
    const date = new Date(pos.closeTime).toLocaleDateString("en-US", { 
      month: "short", 
      day: "numeric" 
    });
    
    const current = dailyTrades.get(date) || { wins: 0, total: 0 };
    current.total += 1;
    if (pos.profit > 0) {
      current.wins += 1;
    }
    dailyTrades.set(date, current);
  });

  return Array.from(dailyTrades.entries()).map(([date, data]) => ({
    date,
    value: data.total > 0 ? (data.wins / data.total) * 100 : 0,
  }));
}

/**
 * Calculate daily performance data
 */
export function calculateDailyPerformance(closedPositions: PositionWithClose[]): DailyPerformance[] {
  if (closedPositions.length === 0) {
    return [];
  }

  // Sort by close time
  const sorted = [...closedPositions].sort((a, b) => 
    new Date(a.closeTime).getTime() - new Date(b.closeTime).getTime()
  );

  // Group by date
  const dailyData = new Map<string, {
    trades: number;
    winners: number;
    losers: number;
    netProfit: number;
  }>();

  sorted.forEach(pos => {
    const date = new Date(pos.closeTime).toISOString().split('T')[0];
    
    const current = dailyData.get(date) || {
      trades: 0,
      winners: 0,
      losers: 0,
      netProfit: 0,
    };
    
    current.trades += 1;
    current.netProfit += pos.profit;
    
    if (pos.profit > 0) {
      current.winners += 1;
    } else if (pos.profit < 0) {
      current.losers += 1;
    }
    
    dailyData.set(date, current);
  });

  return Array.from(dailyData.entries()).map(([date, data]) => {
    const winRate = data.trades > 0 ? (data.winners / data.trades) * 100 : 0;
    const grossProfit = sorted
      .filter(pos => new Date(pos.closeTime).toISOString().split('T')[0] === date && pos.profit > 0)
      .reduce((sum, pos) => sum + pos.profit, 0);
    const grossLoss = Math.abs(sorted
      .filter(pos => new Date(pos.closeTime).toISOString().split('T')[0] === date && pos.profit < 0)
      .reduce((sum, pos) => sum + pos.profit, 0));
    const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 999 : 0;

    return {
      date,
      trades: data.trades,
      winners: data.winners,
      losers: data.losers,
      netProfit: data.netProfit,
      winRate,
      profitFactor,
    };
  }).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

/**
 * Filter positions by date range
 */
export function filterByDateRange(
  positions: PositionWithClose[],
  days: number
): PositionWithClose[] {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);
  
  return positions.filter(pos => 
    new Date(pos.closeTime) >= cutoffDate
  );
}

/**
 * Calculate equity curve data
 */
export function calculateEquityCurve(
  closedPositions: PositionWithClose[],
  initialBalance: number = 10000
): ChartDataPoint[] {
  if (closedPositions.length === 0) {
    return [];
  }

  // Sort by close time
  const sorted = [...closedPositions].sort((a, b) => 
    new Date(a.closeTime).getTime() - new Date(b.closeTime).getTime()
  );

  let equity = initialBalance;
  const equityCurve: ChartDataPoint[] = [];

  sorted.forEach(pos => {
    equity += pos.profit;
    const date = new Date(pos.closeTime).toLocaleDateString("en-US", { 
      month: "short", 
      day: "numeric" 
    });
    equityCurve.push({
      date,
      value: equity,
    });
  });

  return equityCurve;
}

/**
 * Calculate profit by currency pair
 */
export function calculateProfitByCurrency(
  closedPositions: PositionWithClose[]
): Array<{ symbol: string; profit: number; trades: number }> {
  if (closedPositions.length === 0) {
    return [];
  }

  const currencyMap = new Map<string, { profit: number; trades: number }>();

  closedPositions.forEach(pos => {
    const current = currencyMap.get(pos.symbol) || { profit: 0, trades: 0 };
    current.profit += pos.profit;
    current.trades += 1;
    currencyMap.set(pos.symbol, current);
  });

  return Array.from(currencyMap.entries())
    .map(([symbol, data]) => ({
      symbol,
      profit: data.profit,
      trades: data.trades,
    }))
    .sort((a, b) => b.profit - a.profit); // Sort by profit descending
}

/**
 * Calculate win/loss distribution
 */
export function calculateWinLossDistribution(
  closedPositions: PositionWithClose[]
): Array<{ name: string; value: number; count: number }> {
  if (closedPositions.length === 0) {
    return [];
  }

  let winners = 0;
  let losers = 0;
  let breakEven = 0;
  let winValue = 0;
  let lossValue = 0;

  closedPositions.forEach(pos => {
    if (pos.profit > 0) {
      winners += 1;
      winValue += pos.profit;
    } else if (pos.profit < 0) {
      losers += 1;
      lossValue += Math.abs(pos.profit);
    } else {
      breakEven += 1;
    }
  });

  const result = [];
  if (winners > 0) result.push({ name: "Winners", value: winValue, count: winners });
  if (losers > 0) result.push({ name: "Losers", value: lossValue, count: losers });
  if (breakEven > 0) result.push({ name: "Break Even", value: 0, count: breakEven });

  return result;
}

/**
 * Calculate monthly performance
 */
export function calculateMonthlyPerformance(
  closedPositions: PositionWithClose[]
): Array<{ month: string; profit: number; trades: number; winRate: number }> {
  if (closedPositions.length === 0) {
    return [];
  }

  const monthlyMap = new Map<string, {
    profit: number;
    trades: number;
    winners: number;
  }>();

  closedPositions.forEach(pos => {
    const date = new Date(pos.closeTime);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const monthLabel = date.toLocaleDateString("en-US", { year: "numeric", month: "short" });

    const current = monthlyMap.get(monthKey) || { profit: 0, trades: 0, winners: 0 };
    current.profit += pos.profit;
    current.trades += 1;
    if (pos.profit > 0) current.winners += 1;
    monthlyMap.set(monthKey, current);
  });

  return Array.from(monthlyMap.entries())
    .map(([key, data]) => {
      const [year, month] = key.split('-');
      const date = new Date(parseInt(year), parseInt(month) - 1);
      return {
        month: date.toLocaleDateString("en-US", { year: "numeric", month: "short" }),
        profit: data.profit,
        trades: data.trades,
        winRate: data.trades > 0 ? (data.winners / data.trades) * 100 : 0,
      };
    })
    .sort((a, b) => {
      // Sort chronologically
      const aDate = new Date(a.month);
      const bDate = new Date(b.month);
      return aDate.getTime() - bDate.getTime();
    });
}

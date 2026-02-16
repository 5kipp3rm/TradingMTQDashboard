import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";
import { usePortfolioSummary, usePerformanceMetrics } from "@/hooks/useCryptoAPI";
import { BarChart3, TrendingUp, TrendingDown, Target, Award, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface PerformanceMetricsProps {
  accountId: number;
}

export function PerformanceMetrics({ accountId }: PerformanceMetricsProps) {
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('monthly');
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolioSummary(accountId);
  const { data: performance, isLoading: performanceLoading } = usePerformanceMetrics(accountId, period);

  const formatCurrency = (value: number) => {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const isLoading = portfolioLoading || performanceLoading;

  return (
    <div className="space-y-6">
      {/* Portfolio Summary */}
      {portfolio && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="card-glow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">Total Balance</p>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </div>
              <p className="text-2xl font-bold font-mono">${formatCurrency(portfolio.total_balance_usd)}</p>
            </CardContent>
          </Card>

          <Card className="card-glow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">Open Positions</p>
                <Target className="h-4 w-4 text-muted-foreground" />
              </div>
              <p className="text-2xl font-bold">{portfolio.total_positions}</p>
              <p className="text-xs text-muted-foreground mt-1">
                ${formatCurrency(portfolio.open_positions_value)} value
              </p>
            </CardContent>
          </Card>

          <Card className="card-glow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">Unrealized P&L</p>
                {portfolio.unrealized_pnl >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-success" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-destructive" />
                )}
              </div>
              <p
                className={cn(
                  "text-2xl font-bold font-mono",
                  portfolio.unrealized_pnl >= 0 ? "text-success" : "text-destructive"
                )}
              >
                ${formatCurrency(Math.abs(portfolio.unrealized_pnl))}
              </p>
              <p
                className={cn(
                  "text-xs font-mono mt-1",
                  portfolio.unrealized_pnl >= 0 ? "text-success" : "text-destructive"
                )}
              >
                {formatPercent(portfolio.unrealized_pnl_percent)}
              </p>
            </CardContent>
          </Card>

          <Card className="card-glow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">Realized P&L (Month)</p>
                <Award className="h-4 w-4 text-muted-foreground" />
              </div>
              <p
                className={cn(
                  "text-2xl font-bold font-mono",
                  portfolio.realized_pnl_month >= 0 ? "text-success" : "text-destructive"
                )}
              >
                ${formatCurrency(Math.abs(portfolio.realized_pnl_month))}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Performance Metrics */}
      <Card className="card-glow">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Performance Metrics
            </CardTitle>
            <Select value={period} onValueChange={(v) => setPeriod(v as 'daily' | 'weekly' | 'monthly')}>
              <SelectTrigger className="w-[130px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <BarChart3 className="h-6 w-6 animate-pulse text-muted-foreground" />
            </div>
          ) : performance ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Total Return */}
              <div className="bg-muted rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-1">Total Return</p>
                <p
                  className={cn(
                    "text-lg font-bold font-mono",
                    performance.total_return >= 0 ? "text-success" : "text-destructive"
                  )}
                >
                  ${formatCurrency(Math.abs(performance.total_return))}
                </p>
                <p
                  className={cn(
                    "text-xs font-mono",
                    performance.total_return >= 0 ? "text-success" : "text-destructive"
                  )}
                >
                  {formatPercent(performance.total_return_percent)}
                </p>
              </div>

              {/* Win Rate */}
              <div className="bg-muted rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-1">Win Rate</p>
                <p className="text-lg font-bold font-mono">{performance.win_rate.toFixed(1)}%</p>
                <p className="text-xs text-muted-foreground">
                  {performance.winning_trades}/{performance.total_trades} trades
                </p>
              </div>

              {/* Profit Factor */}
              <div className="bg-muted rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-1">Profit Factor</p>
                <p className="text-lg font-bold font-mono">
                  {performance.profit_factor.toFixed(2)}
                </p>
                <Badge variant="outline" className="text-xs mt-1">
                  {performance.profit_factor >= 2 ? 'Excellent' : performance.profit_factor >= 1.5 ? 'Good' : 'Fair'}
                </Badge>
              </div>

              {/* Max Drawdown */}
              <div className="bg-muted rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-1">Max Drawdown</p>
                <p className="text-lg font-bold font-mono text-destructive">
                  ${formatCurrency(Math.abs(performance.max_drawdown))}
                </p>
                <p className="text-xs font-mono text-destructive">
                  {formatPercent(performance.max_drawdown_percent)}
                </p>
              </div>

              {/* Average Win */}
              <div className="bg-success/10 rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-1">Avg Win</p>
                <p className="text-lg font-bold font-mono text-success">
                  ${formatCurrency(performance.avg_win)}
                </p>
              </div>

              {/* Average Loss */}
              <div className="bg-destructive/10 rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-1">Avg Loss</p>
                <p className="text-lg font-bold font-mono text-destructive">
                  ${formatCurrency(Math.abs(performance.avg_loss))}
                </p>
              </div>

              {/* Largest Win */}
              <div className="bg-success/10 rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-1">Largest Win</p>
                <p className="text-lg font-bold font-mono text-success">
                  ${formatCurrency(performance.largest_win)}
                </p>
              </div>

              {/* Largest Loss */}
              <div className="bg-destructive/10 rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-1">Largest Loss</p>
                <p className="text-lg font-bold font-mono text-destructive">
                  ${formatCurrency(Math.abs(performance.largest_loss))}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <AlertCircle className="h-12 w-12 mb-3 opacity-50" />
              <p className="text-sm">No performance data available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Gainers and Losers */}
      {portfolio && (portfolio.top_gainers.length > 0 || portfolio.top_losers.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Gainers */}
          {portfolio.top_gainers.length > 0 && (
            <Card className="card-glow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-success">
                  <TrendingUp className="h-5 w-5" />
                  Top Gainers
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {portfolio.top_gainers.map((position) => (
                    <div key={position.symbol} className="flex items-center justify-between bg-success/10 rounded-lg p-3">
                      <div>
                        <p className="font-semibold font-mono">{position.symbol}</p>
                        <p className="text-xs text-muted-foreground">${formatCurrency(position.value)}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold font-mono text-success">${formatCurrency(position.pnl)}</p>
                        <p className="text-xs font-mono text-success">{formatPercent(position.pnl_percent)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Top Losers */}
          {portfolio.top_losers.length > 0 && (
            <Card className="card-glow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <TrendingDown className="h-5 w-5" />
                  Top Losers
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {portfolio.top_losers.map((position) => (
                    <div key={position.symbol} className="flex items-center justify-between bg-destructive/10 rounded-lg p-3">
                      <div>
                        <p className="font-semibold font-mono">{position.symbol}</p>
                        <p className="text-xs text-muted-foreground">${formatCurrency(position.value)}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold font-mono text-destructive">${formatCurrency(Math.abs(position.pnl))}</p>
                        <p className="text-xs font-mono text-destructive">{formatPercent(position.pnl_percent)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

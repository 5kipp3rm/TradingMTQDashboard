import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { usePositions } from "@/hooks/useCryptoAPI";
import { TrendingUp, TrendingDown, RefreshCw, Package } from "lucide-react";
import { cn } from "@/lib/utils";

interface PositionListProps {
  accountId: number;
  refreshInterval?: number;
}

export function PositionList({ accountId, refreshInterval = 5000 }: PositionListProps) {
  const { data: positionData, isLoading, refetch } = usePositions(accountId, refreshInterval);

  const positions = positionData?.positions || [];
  const totalValue = positionData?.total_value || 0;
  const totalPnL = positionData?.total_unrealized_pnl || 0;
  const totalPnLPercent = positionData?.total_unrealized_pnl_percent || 0;

  const formatCurrency = (value: number) => {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <Card className="card-glow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Open Positions
            <Badge variant="outline" className="ml-2">
              {positions.length}
            </Badge>
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex gap-4 mt-2">
          <div>
            <p className="text-xs text-muted-foreground">Total Value</p>
            <p className="text-sm font-semibold font-mono">${formatCurrency(totalValue)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total P&L</p>
            <p
              className={cn(
                "text-sm font-semibold font-mono",
                totalPnL >= 0 ? "text-success" : "text-destructive"
              )}
            >
              ${formatCurrency(totalPnL)} ({formatPercent(totalPnLPercent)})
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : positions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Package className="h-12 w-12 mb-3 opacity-50" />
            <p className="text-sm">No open positions</p>
          </div>
        ) : (
          <div className="space-y-3">
            {positions.map((position) => {
              const isProfitable = position.unrealized_pnl >= 0;
              return (
                <Card key={position.symbol} className="bg-muted/50">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      {/* Left: Symbol and Side */}
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold">{position.symbol}</h4>
                          <Badge
                            variant={position.side === 'BUY' ? 'default' : 'destructive'}
                            className="text-xs"
                          >
                            {position.side}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          Qty: {position.quantity}
                        </p>
                      </div>

                      {/* Right: P&L */}
                      <div className="text-right">
                        <div className="flex items-center gap-1">
                          {isProfitable ? (
                            <TrendingUp className="h-4 w-4 text-success" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-destructive" />
                          )}
                          <span
                            className={cn(
                              "font-semibold font-mono text-sm",
                              isProfitable ? "text-success" : "text-destructive"
                            )}
                          >
                            ${formatCurrency(Math.abs(position.unrealized_pnl))}
                          </span>
                        </div>
                        <p
                          className={cn(
                            "text-xs font-mono",
                            isProfitable ? "text-success" : "text-destructive"
                          )}
                        >
                          {formatPercent(position.unrealized_pnl_percent)}
                        </p>
                      </div>
                    </div>

                    {/* Price Details */}
                    <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t border-border">
                      <div>
                        <p className="text-xs text-muted-foreground">Entry</p>
                        <p className="text-xs font-mono">${formatCurrency(position.entry_price)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Current</p>
                        <p className="text-xs font-mono">${formatCurrency(position.current_price)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Value</p>
                        <p className="text-xs font-mono">${formatCurrency(position.position_value)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

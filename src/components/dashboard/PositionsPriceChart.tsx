import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { Position } from "@/types/trading";
import {
  calculateAllPositionMetrics,
  type PositionMetrics,
} from "@/utils/positionCalculator";

interface PositionsPriceChartProps {
  positions: Position[];
  isLoading?: boolean;
}

/**
 * Shows each open position as a visual bar with Entry, Current, TP, and SL price levels.
 */
export function PositionsPriceChart({
  positions,
  isLoading,
}: PositionsPriceChartProps) {
  // Filter to positions that have at least SL or TP set
  const positionsWithLevels = positions.filter(
    (p) => (p.sl != null && p.sl > 0) || (p.tp != null && p.tp > 0)
  );

  const [selectedSymbol, setSelectedSymbol] = useState<string>("all");

  const symbols = useMemo(() => {
    const s = [...new Set(positionsWithLevels.map((p) => p.symbol))];
    return s.sort();
  }, [positionsWithLevels]);

  const filteredPositions = useMemo(() => {
    if (selectedSymbol === "all") return positionsWithLevels;
    return positionsWithLevels.filter((p) => p.symbol === selectedSymbol);
  }, [positionsWithLevels, selectedSymbol]);

  const allMetrics = useMemo(
    () => calculateAllPositionMetrics(filteredPositions),
    [filteredPositions]
  );

  if (isLoading) {
    return (
      <Card className="card-glow mb-5">
        <CardHeader>
          <CardTitle>📊 Position Levels (Entry / TP / SL)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[350px] bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  if (positionsWithLevels.length === 0) {
    return (
      <Card className="card-glow mb-5">
        <CardHeader>
          <CardTitle>📊 Position Levels (Entry / TP / SL)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">No positions with TP/SL set</p>
              <p className="text-sm">
                Set Take Profit or Stop Loss on your positions to see the price
                level chart
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="card-glow mb-5">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>📊 Position Levels (Entry / TP / SL)</CardTitle>
        {symbols.length > 1 && (
          <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Symbol" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Symbols</SelectItem>
              {symbols.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </CardHeader>
      <CardContent>
        {/* ----- Per-position cards with visual level bars ----- */}
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
          {allMetrics.map((m) => (
            <PositionLevelCard key={m.position.ticket} metrics={m} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Single position card with a mini visual price-level bar            */
/* ------------------------------------------------------------------ */

function PositionLevelCard({ metrics }: { metrics: PositionMetrics }) {
  const pos = metrics.position;
  const isBuy = pos.type === "buy";

  // Collect all price levels
  const levels: { price: number; label: string; color: string }[] = [];
  if (pos.sl != null && pos.sl > 0)
    levels.push({ price: pos.sl, label: "SL", color: "#ef4444" }); // red
  levels.push({ price: pos.openPrice, label: "Entry", color: "#6b7280" }); // gray
  levels.push({
    price: pos.currentPrice,
    label: "Current",
    color: pos.profit >= 0 ? "#22c55e" : "#ef4444",
  });
  if (pos.tp != null && pos.tp > 0)
    levels.push({ price: pos.tp, label: "TP", color: "#22c55e" }); // green

  // Sort ascending for the bar
  const sorted = [...levels].sort((a, b) => a.price - b.price);
  const minPrice = sorted[0].price;
  const maxPrice = sorted[sorted.length - 1].price;
  const range = maxPrice - minPrice || 1;

  return (
    <div className="border rounded-lg p-4 bg-card/50 hover:bg-card transition-colors">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{pos.symbol}</span>
          <span
            className={cn(
              "text-xs font-semibold px-1.5 py-0.5 rounded",
              isBuy
                ? "bg-emerald-500/20 text-emerald-400"
                : "bg-red-500/20 text-red-400"
            )}
          >
            {pos.type.toUpperCase()}
          </span>
          <span className="text-xs text-muted-foreground">
            #{pos.ticket}
          </span>
        </div>
        <span
          className={cn(
            "font-mono font-semibold text-sm",
            pos.profit >= 0 ? "text-emerald-400" : "text-red-400"
          )}
        >
          {pos.profit >= 0 ? "+" : ""}${pos.profit.toFixed(2)}
        </span>
      </div>

      {/* Visual price bar */}
      <div className="relative h-8 bg-muted rounded-full overflow-hidden mb-3">
        {sorted.map((level, i) => {
          const pct = ((level.price - minPrice) / range) * 100;
          return (
            <div
              key={level.label}
              className="absolute top-0 bottom-0 flex items-center"
              style={{ left: `${Math.min(Math.max(pct, 2), 98)}%` }}
            >
              <div
                className="w-0.5 h-full"
                style={{ backgroundColor: level.color }}
              />
              <span
                className="absolute -top-5 text-[10px] font-semibold whitespace-nowrap"
                style={{
                  color: level.color,
                  transform: "translateX(-50%)",
                }}
              >
                {level.label}
              </span>
            </div>
          );
        })}
        {/* Fill region from SL to current (shows progress) */}
        {pos.sl != null && pos.sl > 0 && (
          <div
            className="absolute top-0 bottom-0 opacity-15 rounded-full"
            style={{
              left: `${((Math.min(pos.sl, pos.currentPrice) - minPrice) / range) * 100}%`,
              width: `${(Math.abs(pos.currentPrice - pos.sl) / range) * 100}%`,
              backgroundColor: pos.profit >= 0 ? "#22c55e" : "#ef4444",
            }}
          />
        )}
      </div>

      {/* Price levels row */}
      <div className="grid grid-cols-4 gap-1 text-xs mb-3">
        <div className="text-center">
          <div className="text-red-400 font-semibold">SL</div>
          <div className="font-mono">
            {pos.sl != null && pos.sl > 0 ? pos.sl.toFixed(5) : "—"}
          </div>
        </div>
        <div className="text-center">
          <div className="text-muted-foreground font-semibold">Entry</div>
          <div className="font-mono">{pos.openPrice.toFixed(5)}</div>
        </div>
        <div className="text-center">
          <div
            className={cn(
              "font-semibold",
              pos.profit >= 0 ? "text-emerald-400" : "text-red-400"
            )}
          >
            Current
          </div>
          <div className="font-mono">{pos.currentPrice.toFixed(5)}</div>
        </div>
        <div className="text-center">
          <div className="text-emerald-400 font-semibold">TP</div>
          <div className="font-mono">
            {pos.tp != null && pos.tp > 0 ? pos.tp.toFixed(5) : "—"}
          </div>
        </div>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs border-t pt-2">
        {/* Distance to TP */}
        {metrics.tpPips != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">To TP:</span>
            <span className="font-mono text-emerald-400">
              {metrics.tpPips} pips
            </span>
          </div>
        )}
        {/* Distance to SL */}
        {metrics.slPips != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">To SL:</span>
            <span className="font-mono text-red-400">
              {metrics.slPips} pips
            </span>
          </div>
        )}
        {/* Potential TP profit */}
        {metrics.tpPotentialProfit != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">TP Profit:</span>
            <span className="font-mono text-emerald-400">
              +${metrics.tpPotentialProfit.toFixed(2)}
            </span>
          </div>
        )}
        {/* Potential SL loss */}
        {metrics.slPotentialLoss != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">SL Loss:</span>
            <span className="font-mono text-red-400">
              ${metrics.slPotentialLoss.toFixed(2)}
            </span>
          </div>
        )}
        {/* Risk:Reward */}
        {metrics.riskReward != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">R:R Ratio:</span>
            <span className="font-mono font-semibold">
              1:{metrics.riskReward}
            </span>
          </div>
        )}
        {/* Progress toward TP */}
        {metrics.tpProgress != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">TP Progress:</span>
            <span
              className={cn(
                "font-mono font-semibold",
                metrics.tpProgress >= 0 ? "text-emerald-400" : "text-red-400"
              )}
            >
              {metrics.tpProgress.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

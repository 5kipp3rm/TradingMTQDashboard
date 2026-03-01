import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import type { Position } from "@/types/trading";

const COLOR_PROFIT = "#10b981"; // emerald-500
const COLOR_LOSS = "#ef4444";   // red-500

interface PositionProfitLossChartProps {
  positions: Position[];
  isLoading?: boolean;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const entry = payload[0].payload;
  return (
    <div
      style={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
      className="rounded-lg p-3 shadow-lg text-sm min-w-[160px]"
    >
      <p className="font-semibold mb-1" style={{ color: "hsl(var(--foreground))" }}>
        {entry.symbol}
      </p>
      <p className="text-xs mb-2" style={{ color: "hsl(var(--muted-foreground))" }}>
        #{entry.ticket} · {entry.side} · {entry.volume} lot{entry.volume !== 1 ? "s" : ""}
      </p>
      <p style={{ color: entry.profit >= 0 ? COLOR_PROFIT : COLOR_LOSS, fontWeight: 600 }}>
        {entry.profit >= 0 ? "+" : ""}${entry.profit.toFixed(2)}
      </p>
    </div>
  );
};

export function PositionProfitLossChart({ positions, isLoading }: PositionProfitLossChartProps) {
  const chartData = positions.map((p) => ({
    label: p.symbol,
    ticket: p.ticket,
    symbol: p.symbol,
    side: p.type.toUpperCase(),
    volume: p.volume,
    profit: p.profit,
  }));

  const totalProfit = positions.filter((p) => p.profit > 0).reduce((s, p) => s + p.profit, 0);
  const totalLoss = positions.filter((p) => p.profit < 0).reduce((s, p) => s + p.profit, 0);
  const profitCount = positions.filter((p) => p.profit > 0).length;
  const lossCount = positions.filter((p) => p.profit <= 0).length;

  // Grow height with number of positions (min 220px)
  const chartHeight = Math.max(220, chartData.length * 44);

  return (
    <Card className="card-glow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle>Open Positions — Profit vs Loss</CardTitle>
          {positions.length > 0 && (
            <div className="flex gap-4 text-sm">
              <span>
                <span style={{ color: COLOR_PROFIT }} className="font-semibold">
                  +${totalProfit.toFixed(2)}
                </span>
                <span className="text-muted-foreground ml-1">({profitCount})</span>
              </span>
              <span>
                <span style={{ color: COLOR_LOSS }} className="font-semibold">
                  ${totalLoss.toFixed(2)}
                </span>
                <span className="text-muted-foreground ml-1">({lossCount})</span>
              </span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[220px] bg-muted animate-pulse rounded" />
        ) : chartData.length === 0 ? (
          <div className="h-[220px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">No open positions</p>
              <p className="text-sm">Open a trade to track live P&amp;L</p>
            </div>
          </div>
        ) : (
          <div style={{ height: chartHeight }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 4, right: 40, left: 8, bottom: 4 }}
                barCategoryGap="25%"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
                <XAxis
                  type="number"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <YAxis
                  type="category"
                  dataKey="label"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  width={64}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }} />
                <ReferenceLine x={0} stroke="hsl(var(--border))" strokeWidth={1.5} />
                <Bar dataKey="profit" radius={4} maxBarSize={28} label={{ position: "right", fontSize: 11, formatter: (v: number) => `$${v.toFixed(2)}`, fill: "hsl(var(--muted-foreground))" }}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.profit > 0 ? COLOR_PROFIT : COLOR_LOSS}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

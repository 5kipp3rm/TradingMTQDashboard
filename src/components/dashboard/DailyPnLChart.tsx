import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from "recharts";
import type { DailyPerformance } from "@/types/trading";

const COLOR_PROFIT = "#10b981"; // emerald-500
const COLOR_LOSS = "#ef4444";   // red-500

interface DailyPnLChartProps {
  data: DailyPerformance[];
  isLoading?: boolean;
}

interface ChartEntry {
  date: string;
  profit: number | null;
  loss: number | null;
  net: number;
  trades: number;
  winners: number;
  losers: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;
  const entry: ChartEntry = payload[0]?.payload;
  const profit = entry.profit ?? 0;
  const loss = Math.abs(entry.loss ?? 0);
  const net = entry.net;

  return (
    <div
      style={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
      className="rounded-lg p-3 shadow-lg text-sm"
    >
      <p className="font-semibold mb-2" style={{ color: "hsl(var(--foreground))" }}>
        {label}
      </p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span style={{ color: "hsl(var(--muted-foreground))" }}>Gross Profit</span>
          <span style={{ color: COLOR_PROFIT }}>${profit.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span style={{ color: "hsl(var(--muted-foreground))" }}>Gross Loss</span>
          <span style={{ color: COLOR_LOSS }}>-${loss.toFixed(2)}</span>
        </div>
        <div
          className="flex justify-between gap-4 pt-1 mt-1"
          style={{ borderTop: "1px solid hsl(var(--border))" }}
        >
          <span style={{ color: "hsl(var(--muted-foreground))" }}>Net</span>
          <span style={{ color: net >= 0 ? COLOR_PROFIT : COLOR_LOSS, fontWeight: 600 }}>
            {net >= 0 ? "+" : ""}${net.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between gap-4 text-xs" style={{ color: "hsl(var(--muted-foreground))" }}>
          <span>{entry.winners}W / {entry.losers}L</span>
          <span>{entry.trades} trades</span>
        </div>
      </div>
    </div>
  );
};

export function DailyPnLChart({ data, isLoading }: DailyPnLChartProps) {
  const chartData: ChartEntry[] = [...data]
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((d) => {
      const grossProfit = d.grossProfit ?? (d.netProfit > 0 ? d.netProfit : 0);
      const grossLoss = d.grossLoss ?? (d.netProfit < 0 ? Math.abs(d.netProfit) : 0);
      return {
        date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        profit: grossProfit > 0 ? grossProfit : null,
        loss: grossLoss > 0 ? -grossLoss : null,
        net: d.netProfit,
        trades: d.trades,
        winners: d.winners,
        losers: d.losers,
      };
    });

  const hasData = chartData.some((d) => d.profit !== null || d.loss !== null);

  return (
    <Card className="card-glow">
      <CardHeader>
        <CardTitle>Daily P&amp;L Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[300px] bg-muted animate-pulse rounded" />
        ) : !hasData ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">No data in this period</p>
              <p className="text-sm">Close positions to see daily profit &amp; loss</p>
            </div>
          </div>
        ) : (
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }} barCategoryGap="30%">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }} />
                <Legend
                  formatter={(value) => (
                    <span style={{ color: "hsl(var(--muted-foreground))", fontSize: 12 }}>
                      {value === "profit" ? "Gross Profit" : "Gross Loss"}
                    </span>
                  )}
                />
                <ReferenceLine y={0} stroke="hsl(var(--border))" strokeWidth={1.5} />
                <Bar dataKey="profit" fill={COLOR_PROFIT} radius={[4, 4, 0, 0]} maxBarSize={32} />
                <Bar dataKey="loss" fill={COLOR_LOSS} radius={[0, 0, 4, 4]} maxBarSize={32} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

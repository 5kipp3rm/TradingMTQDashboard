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
} from "recharts";

interface MonthlyPerformanceData {
  month: string;
  profit: number;
  trades: number;
  winRate: number;
}

interface MonthlyPerformanceChartProps {
  data: MonthlyPerformanceData[];
  isLoading?: boolean;
}

export function MonthlyPerformanceChart({ data, isLoading }: MonthlyPerformanceChartProps) {
  return (
    <Card className="card-glow">
      <CardHeader>
        <CardTitle>Monthly Performance</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[300px] bg-muted animate-pulse rounded" />
        ) : data.length === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">No monthly data available</p>
              <p className="text-sm">Trade for a full month to see monthly breakdown</p>
            </div>
          </div>
        ) : (
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="month"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickLine={false}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickLine={false}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  labelStyle={{ color: "hsl(var(--foreground))" }}
                  content={({ active, payload }) => {
                    if (!active || !payload || !payload.length) return null;
                    const data = payload[0].payload;
                    return (
                      <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
                        <p className="font-semibold mb-2">{data.month}</p>
                        <div className="space-y-1 text-sm">
                          <p>
                            <span className="text-muted-foreground">Profit:</span>{" "}
                            <span className={data.profit >= 0 ? "text-success" : "text-destructive"}>
                              ${data.profit.toFixed(2)}
                            </span>
                          </p>
                          <p>
                            <span className="text-muted-foreground">Trades:</span> {data.trades}
                          </p>
                          <p>
                            <span className="text-muted-foreground">Win Rate:</span> {data.winRate.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    );
                  }}
                />
                <Bar dataKey="profit" radius={[8, 8, 0, 0]}>
                  {data.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.profit >= 0 ? "hsl(var(--success))" : "hsl(var(--destructive))"}
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

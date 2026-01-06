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

interface ProfitByCurrencyData {
  symbol: string;
  profit: number;
  trades: number;
}

interface ProfitByCurrencyChartProps {
  data: ProfitByCurrencyData[];
  isLoading?: boolean;
}

export function ProfitByCurrencyChart({ data, isLoading }: ProfitByCurrencyChartProps) {
  return (
    <Card className="card-glow">
      <CardHeader>
        <CardTitle>Profit by Currency Pair</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[300px] bg-muted animate-pulse rounded" />
        ) : data.length === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">No currency data available</p>
              <p className="text-sm">Trade different currency pairs to see breakdown</p>
            </div>
          </div>
        ) : (
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="symbol"
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
                  formatter={(value: number, name: string, props: any) => {
                    if (name === "profit") {
                      return [`$${value.toFixed(2)}`, "Profit"];
                    }
                    return [value, "Trades"];
                  }}
                  content={({ active, payload }) => {
                    if (!active || !payload || !payload.length) return null;
                    const data = payload[0].payload;
                    return (
                      <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
                        <p className="font-semibold mb-1">{data.symbol}</p>
                        <p className="text-sm">
                          <span className="text-muted-foreground">Profit:</span>{" "}
                          <span className={data.profit >= 0 ? "text-success" : "text-destructive"}>
                            ${data.profit.toFixed(2)}
                          </span>
                        </p>
                        <p className="text-sm">
                          <span className="text-muted-foreground">Trades:</span> {data.trades}
                        </p>
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

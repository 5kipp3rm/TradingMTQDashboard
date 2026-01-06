import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface WinLossData {
  name: string;
  value: number;
  count: number;
}

interface WinLossDistributionChartProps {
  data: WinLossData[];
  isLoading?: boolean;
}

const COLORS = {
  Winners: "hsl(var(--success))",
  Losers: "hsl(var(--destructive))",
  "Break Even": "hsl(var(--muted))",
};

export function WinLossDistributionChart({ data, isLoading }: WinLossDistributionChartProps) {
  const totalTrades = data.reduce((sum, item) => sum + item.count, 0);

  return (
    <Card className="card-glow">
      <CardHeader>
        <CardTitle>Win/Loss Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[300px] bg-muted animate-pulse rounded" />
        ) : data.length === 0 || totalTrades === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">No distribution data available</p>
              <p className="text-sm">Close positions to see win/loss breakdown</p>
            </div>
          </div>
        ) : (
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  formatter={(value: number, name: string, props: any) => {
                    const percentage = ((value / totalTrades) * 100).toFixed(1);
                    return [
                      `${value} trades (${percentage}%) - $${props.payload.value.toFixed(2)}`,
                      props.payload.name,
                    ];
                  }}
                />
                <Legend 
                  verticalAlign="bottom" 
                  height={36}
                  formatter={(value, entry: any) => {
                    const data = entry.payload;
                    return `${value}: ${data.count} ($${data.value.toFixed(2)})`;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

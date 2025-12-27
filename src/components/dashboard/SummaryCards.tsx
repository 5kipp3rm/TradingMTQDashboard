import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { TrendingUp, DollarSign, Target, BarChart3 } from "lucide-react";
import type { DashboardSummary } from "@/types/trading";

interface SummaryCardsProps {
  summary: DashboardSummary;
  isLoading?: boolean;
}

export function SummaryCards({ summary, isLoading }: SummaryCardsProps) {
  const cards = [
    {
      title: "Total Trades",
      value: summary.totalTrades,
      format: (v: number) => v.toLocaleString(),
      icon: TrendingUp,
      label: "Executed",
    },
    {
      title: "Net Profit",
      value: summary.netProfit,
      format: (v: number) => `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      icon: DollarSign,
      label: "USD",
      colorClass: summary.netProfit >= 0 ? "text-profit" : "text-loss",
    },
    {
      title: "Win Rate",
      value: summary.winRate,
      format: (v: number) => `${v.toFixed(1)}%`,
      icon: Target,
      label: "Percentage",
    },
    {
      title: "Avg Daily Profit",
      value: summary.avgDailyProfit,
      format: (v: number) => `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      icon: BarChart3,
      label: "USD/Day",
      colorClass: summary.avgDailyProfit >= 0 ? "text-profit" : "text-loss",
    },
  ];

  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.title} className="card-glow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
              <Icon className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-9 bg-muted animate-pulse rounded" />
              ) : (
                <>
                  <div className={cn("metric-value", card.colorClass)}>
                    {card.format(card.value)}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{card.label}</p>
                </>
              )}
            </CardContent>
          </Card>
        );
      })}
    </section>
  );
}

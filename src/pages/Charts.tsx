import { useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { EquityCurveChart } from "@/components/dashboard/EquityCurveChart";
import { ProfitByCurrencyChart } from "@/components/dashboard/ProfitByCurrencyChart";
import { WinLossDistributionChart } from "@/components/dashboard/WinLossDistributionChart";
import { MonthlyPerformanceChart } from "@/components/dashboard/MonthlyPerformanceChart";
import { ProfitChart } from "@/components/dashboard/ProfitChart";
import { WinRateChart } from "@/components/dashboard/WinRateChart";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useAccounts } from "@/contexts/AccountsContext";

const Charts = () => {
  const [period, setPeriod] = useState(30);
  const { selectedAccountId } = useAccounts();
  
  const {
    profitData,
    winRateData,
    equityCurve,
    profitByCurrency,
    winLossDistribution,
    monthlyPerformance,
    isLoading,
    refresh,
  } = useDashboardData(period, selectedAccountId);

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={period}
          onPeriodChange={setPeriod}
          onRefresh={refresh}
          onQuickTrade={() => {}}
        />

        <h2 className="text-2xl font-bold mb-6">Advanced Charts</h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <EquityCurveChart data={equityCurve} isLoading={isLoading} initialBalance={10000} />
          <ProfitByCurrencyChart data={profitByCurrency} isLoading={isLoading} />
          <WinLossDistributionChart data={winLossDistribution} isLoading={isLoading} />
          <MonthlyPerformanceChart data={monthlyPerformance} isLoading={isLoading} />
          <ProfitChart data={profitData} isLoading={isLoading} />
          <WinRateChart data={winRateData} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
};

export default Charts;

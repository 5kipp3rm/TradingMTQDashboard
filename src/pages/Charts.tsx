import { useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { EquityCurveChart } from "@/components/dashboard/EquityCurveChart";
import { ProfitByCurrencyChart } from "@/components/dashboard/ProfitByCurrencyChart";
import { WinLossDistributionChart } from "@/components/dashboard/WinLossDistributionChart";
import { MonthlyPerformanceChart } from "@/components/dashboard/MonthlyPerformanceChart";
import { ProfitChart } from "@/components/dashboard/ProfitChart";
import { WinRateChart } from "@/components/dashboard/WinRateChart";
import { IchimokuChart } from "@/components/dashboard/IchimokuChart";
import { IchimokuPanel } from "@/components/dashboard/IchimokuPanel";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useIchimoku } from "@/hooks/useIchimoku";
import { useAccounts } from "@/contexts/AccountsContext";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

const TIMEFRAMES = [
  { value: "M5", label: "5 Min" },
  { value: "M15", label: "15 Min" },
  { value: "M30", label: "30 Min" },
  { value: "H1", label: "1 Hour" },
  { value: "H4", label: "4 Hours" },
  { value: "D1", label: "Daily" },
  { value: "W1", label: "Weekly" },
];

const POPULAR_SYMBOLS = [
  "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
  "AUDUSD", "NZDUSD", "USDCAD",
  "XAUUSD", "XAGUSD", "BTCUSD",
];

const Charts = () => {
  const [period, setPeriod] = useState(30);
  const { selectedAccountId } = useAccounts();

  // Ichimoku controls
  const [ichSymbol, setIchSymbol] = useState("EURUSD");
  const [ichTimeframe, setIchTimeframe] = useState("H1");
  const [ichCustomSymbol, setIchCustomSymbol] = useState("");

  const ichimokuParams = selectedAccountId && selectedAccountId !== "all"
    ? {
        accountId: selectedAccountId,
        symbol: ichSymbol,
        timeframe: ichTimeframe,
        count: 200,
        includeRaw: true,
      }
    : null;

  const {
    data: ichimokuData,
    chartData: ichimokuChartData,
    isLoading: ichimokuLoading,
    error: ichimokuError,
    refresh: refreshIchimoku,
  } = useIchimoku(ichimokuParams);

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

  const handleCustomSymbol = () => {
    const s = ichCustomSymbol.trim().toUpperCase();
    if (s) {
      setIchSymbol(s);
      setIchCustomSymbol("");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={period}
          onPeriodChange={setPeriod}
          onRefresh={refresh}
          onQuickTrade={() => {}}
        />

        {/* ============================================================ */}
        {/* Ichimoku Kinko Hyo Section                                    */}
        {/* ============================================================ */}
        <div className="mb-8">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h2 className="text-2xl font-bold">Ichimoku Kinko Hyo</h2>

            <div className="flex flex-wrap items-center gap-2">
              {/* Symbol quick-select */}
              <Select value={ichSymbol} onValueChange={setIchSymbol}>
                <SelectTrigger className="w-[130px] h-9 text-xs">
                  <SelectValue placeholder="Symbol" />
                </SelectTrigger>
                <SelectContent>
                  {POPULAR_SYMBOLS.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Custom symbol input */}
              <div className="flex gap-1">
                <Input
                  className="w-[100px] h-9 text-xs"
                  placeholder="Custom…"
                  value={ichCustomSymbol}
                  onChange={(e) => setIchCustomSymbol(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCustomSymbol()}
                />
              </div>

              {/* Timeframe selector */}
              <Select value={ichTimeframe} onValueChange={setIchTimeframe}>
                <SelectTrigger className="w-[110px] h-9 text-xs">
                  <SelectValue placeholder="Timeframe" />
                </SelectTrigger>
                <SelectContent>
                  {TIMEFRAMES.map((tf) => (
                    <SelectItem key={tf.value} value={tf.value}>{tf.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="sm"
                onClick={refreshIchimoku}
                disabled={ichimokuLoading}
                className="h-9"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${ichimokuLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          {selectedAccountId === "all" && (
            <div className="rounded-md border border-yellow-500/30 bg-yellow-500/10 p-3 text-sm text-yellow-200 mb-4">
              ⚠️ Select a specific account (not "All") to load Ichimoku data.
            </div>
          )}

          {ichimokuError && (
            <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300 mb-4">
              {ichimokuError}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5">
            <IchimokuChart
              data={ichimokuChartData}
              response={ichimokuData}
              isLoading={ichimokuLoading}
            />
            <IchimokuPanel
              data={ichimokuData}
              isLoading={ichimokuLoading}
            />
          </div>
        </div>

        {/* ============================================================ */}
        {/* Existing Performance Charts                                   */}
        {/* ============================================================ */}
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

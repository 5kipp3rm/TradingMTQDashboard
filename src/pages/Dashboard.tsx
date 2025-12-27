import { useState, useEffect } from "react";
import { Header } from "@/components/dashboard/Header";
import { StatusBar } from "@/components/dashboard/StatusBar";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { ProfitChart } from "@/components/dashboard/ProfitChart";
import { WinRateChart } from "@/components/dashboard/WinRateChart";
import { PositionsTable } from "@/components/dashboard/PositionsTable";
import { TradesTable } from "@/components/dashboard/TradesTable";
import { DailyPerformanceTable } from "@/components/dashboard/DailyPerformanceTable";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useToast } from "@/hooks/use-toast";
import type { QuickTradeParams } from "@/types/trading";

const Dashboard = () => {
  const [period, setPeriod] = useState(30);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);
  const { toast } = useToast();
  
  const {
    summary,
    trades,
    positions,
    dailyPerformance,
    profitData,
    winRateData,
    currencies,
    isLoading,
    lastUpdate,
    connectionStatus,
    refresh,
  } = useDashboardData(period);

  useEffect(() => {
    refresh();
  }, [period]);

  const handleExportCSV = () => {
    const headers = ["Ticket", "Symbol", "Type", "Entry Time", "Exit Time", "Profit", "Pips", "Status"];
    const rows = trades.map((t) => [
      t.ticket,
      t.symbol,
      t.type,
      t.entryTime,
      t.exitTime || "",
      t.profit.toFixed(2),
      t.pips.toFixed(1),
      t.status,
    ]);
    
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trades_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    
    toast({
      title: "Export Complete",
      description: "Trades exported to CSV successfully.",
    });
  };

  const handleClosePosition = (ticket: number) => {
    toast({
      title: "Position Closed",
      description: `Position #${ticket} has been closed.`,
    });
    refresh();
  };

  const handleCloseAll = () => {
    toast({
      title: "All Positions Closed",
      description: `${positions.length} positions have been closed.`,
    });
    refresh();
  };

  const handleQuickTrade = (params: QuickTradeParams) => {
    toast({
      title: "Trade Executed",
      description: `${params.type.toUpperCase()} ${params.volume} lots of ${params.symbol}`,
    });
    refresh();
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={period}
          onPeriodChange={setPeriod}
          onRefresh={refresh}
          onQuickTrade={() => setQuickTradeOpen(true)}
        />
        
        <StatusBar status={connectionStatus} lastUpdate={lastUpdate} />
        
        <SummaryCards summary={summary} isLoading={isLoading} />
        
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
          <ProfitChart data={profitData} isLoading={isLoading} />
          <WinRateChart data={winRateData} isLoading={isLoading} />
        </section>
        
        <PositionsTable
          positions={positions}
          isLoading={isLoading}
          onRefresh={refresh}
          onClosePosition={handleClosePosition}
          onCloseAll={handleCloseAll}
        />
        
        <TradesTable
          trades={trades}
          isLoading={isLoading}
          onExport={handleExportCSV}
        />
        
        <DailyPerformanceTable
          data={dailyPerformance}
          isLoading={isLoading}
        />
        
        <QuickTradeModal
          open={quickTradeOpen}
          onClose={() => setQuickTradeOpen(false)}
          currencies={currencies}
          onTrade={handleQuickTrade}
        />
      </div>
    </div>
  );
};

export default Dashboard;

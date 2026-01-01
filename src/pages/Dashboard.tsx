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
import { useAccounts } from "@/contexts/AccountsContext";
import { useToast } from "@/hooks/use-toast";
import { positionsApi } from "@/lib/api";
import type { QuickTradeParams } from "@/types/trading";

const Dashboard = () => {
  const [period, setPeriod] = useState(30);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);
  const { selectedAccountId } = useAccounts();
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
  } = useDashboardData(period, selectedAccountId);

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

  const handleClosePosition = async (ticket: number) => {
    try {
      // Get first active account ID (you may want to pass this as a parameter)
      const accountId = 1; // TODO: Get from selected account context

      const response = await positionsApi.close(ticket, accountId);

      if (response.error) {
        toast({
          title: "Error",
          description: response.error || "Failed to close position",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Position Closed",
          description: `Position #${ticket} has been closed successfully.`,
        });
        refresh();
      }
    } catch (error) {
      console.error("Failed to close position:", error);
      toast({
        title: "Error",
        description: "Failed to close position",
        variant: "destructive",
      });
    }
  };

  const handleCloseAll = async () => {
    try {
      // Get first active account ID
      const accountId = 1; // TODO: Get from selected account context

      const response = await positionsApi.closeAll({ account_id: accountId });

      if (response.error) {
        toast({
          title: "Error",
          description: response.error || "Failed to close all positions",
          variant: "destructive",
        });
      } else {
        const result = response.data as any;
        toast({
          title: "All Positions Closed",
          description: `Successfully closed ${result.closed_count || positions.length} positions.`,
        });
        refresh();
      }
    } catch (error) {
      console.error("Failed to close all positions:", error);
      toast({
        title: "Error",
        description: "Failed to close all positions",
        variant: "destructive",
      });
    }
  };

  const handleQuickTrade = async (params: QuickTradeParams) => {
    try {
      // Get first active account ID
      const accountId = 1; // TODO: Get from selected account context

      const response = await positionsApi.open({
        account_id: accountId,
        symbol: params.symbol,
        order_type: params.type.toUpperCase(),
        volume: params.volume,
        stop_loss: params.sl,
        take_profit: params.tp,
        comment: params.comment,
      });

      if (response.error) {
        toast({
          title: "Trade Failed",
          description: response.error || "Failed to execute trade",
          variant: "destructive",
        });
      } else {
        const result = response.data as any;
        toast({
          title: "Trade Executed",
          description: `${params.type.toUpperCase()} ${params.volume} lots of ${params.symbol} - Ticket #${result.ticket}`,
        });
        refresh();
      }
    } catch (error) {
      console.error("Failed to execute trade:", error);
      toast({
        title: "Error",
        description: "Failed to execute trade",
        variant: "destructive",
      });
    }
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

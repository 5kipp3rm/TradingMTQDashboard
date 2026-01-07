import { useState, useEffect } from "react";
import { Header } from "@/components/dashboard/Header";
import { StatusBar } from "@/components/dashboard/StatusBar";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { ProfitChart } from "@/components/dashboard/ProfitChart";
import { WinRateChart } from "@/components/dashboard/WinRateChart";
import { PositionsTable } from "@/components/dashboard/PositionsTable";
import { ClosedPositionsTable } from "@/components/dashboard/ClosedPositionsTable";
import { TradesTable } from "@/components/dashboard/TradesTable";
import { DailyPerformanceTable } from "@/components/dashboard/DailyPerformanceTable";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useAccounts } from "@/contexts/AccountsContext";
import { useToast } from "@/hooks/use-toast";
import { positionsApi } from "@/lib/api";
import type { QuickTradeParams, Position } from "@/types/trading";

const Dashboard = () => {
  const [period, setPeriod] = useState(30);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);
  const [closedPositions, setClosedPositions] = useState<Position[]>([]);
  const [closeAllConfirmOpen, setCloseAllConfirmOpen] = useState(false);
  const [closePositionConfirm, setClosePositionConfirm] = useState<{ open: boolean; ticket: number | null; accountId: number | null }>({ open: false, ticket: null, accountId: null });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5); // seconds
  const [livePositions, setLivePositions] = useState<Position[] | null>(null); // For auto-refresh updates
  const { selectedAccountId } = useAccounts();
  const { toast } = useToast();

  const {
    summary,
    trades,
    positions: hookPositions,
    dailyPerformance,
    profitData,
    winRateData,
    currencies,
    isLoading,
    lastUpdate,
    connectionStatus,
    refresh,
  } = useDashboardData(period, selectedAccountId);

  // Use live positions if available, otherwise use hook positions
  const positions = livePositions || hookPositions;

  // Reset live positions when hook positions update
  useEffect(() => {
    setLivePositions(null);
  }, [hookPositions]);

  useEffect(() => {
    refresh();
  }, [period]);

  // Auto-refresh positions
  useEffect(() => {
    if (!autoRefresh) return;

    const intervalId = setInterval(() => {
      // Only refresh positions, not full dashboard
      refreshPositions();
    }, refreshInterval * 1000);

    return () => clearInterval(intervalId);
  }, [autoRefresh, refreshInterval, selectedAccountId]);

  const refreshPositions = async () => {
    try {
      const accountIdParam = selectedAccountId && selectedAccountId !== "all"
        ? parseInt(selectedAccountId, 10)
        : undefined;
      
      const positionsRes = await positionsApi.getOpen(accountIdParam ? { account_id: accountIdParam } : undefined);
      
      if (positionsRes.data) {
        const positionsData = Array.isArray(positionsRes.data) ? positionsRes.data : [];
        const newPositions = positionsData.map((p: any) => ({
          ticket: p.ticket,
          symbol: p.symbol,
          type: p.type?.toLowerCase() as "buy" | "sell",
          volume: p.volume,
          openPrice: p.price_open,
          currentPrice: p.price_current || p.price_open,
          sl: p.sl || null,
          tp: p.tp || null,
          profit: p.profit || 0,
          openTime: p.open_time,
          account_id: p.account_id,
          account_name: p.account_name,
        }));
        
        // Update positions state directly without full page refresh
        setLivePositions(newPositions);
      }
    } catch (error) {
      console.error("Failed to refresh positions:", error);
    }
  };

  // Fetch closed positions
  const fetchClosedPositions = async () => {
    try {
      const response = await positionsApi.getClosed({
        account_id: selectedAccountId && selectedAccountId !== "all" 
          ? parseInt(selectedAccountId, 10) 
          : undefined,
        limit: 50
      });

      if (response.data) {
        const closedData = Array.isArray(response.data) ? response.data : [];
        setClosedPositions(
          closedData.map((p: any) => ({
            ticket: p.ticket,
            symbol: p.symbol,
            type: p.type?.toLowerCase() as "buy" | "sell",
            volume: p.volume,
            openPrice: p.price_open,
            currentPrice: p.price_current || p.price_open,
            sl: p.sl || null,
            tp: p.tp || null,
            profit: p.profit || 0,
            openTime: p.time_open,
            closeTime: p.time_close,
          }))
        );
      }
    } catch (error) {
      console.error("Failed to fetch closed positions:", error);
    }
  };

  useEffect(() => {
    fetchClosedPositions();
  }, [selectedAccountId]);

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

  const handleClosePosition = async (ticket: number, account_id?: number) => {
    try {
      // Find position to get its account_id if not provided
      if (!account_id) {
        const position = positions.find(p => p.ticket === ticket);
        account_id = position?.account_id;
      }

      // If still no account_id, try selectedAccountId
      if (!account_id) {
        if (selectedAccountId && selectedAccountId !== "all") {
          account_id = parseInt(selectedAccountId, 10);
        } else {
          toast({
            title: "Error",
            description: "Cannot determine account for this position",
            variant: "destructive",
          });
          return;
        }
      }

      const response = await positionsApi.close(ticket, account_id);

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
        fetchClosedPositions(); // Update closed positions table
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

  const confirmCloseAll = () => {
    setCloseAllConfirmOpen(true);
  };

  const handleCloseAll = async () => {
    try {
      // Use selected account from context
      const accountId = selectedAccountId === "all" ? undefined : parseInt(selectedAccountId);

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
      // Use selected account from context
      const accountId = selectedAccountId === "all" ? 1 : parseInt(selectedAccountId);

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
          autoRefresh={autoRefresh}
          onRefresh={refresh}
          onClosePosition={(ticket, accountId) => setClosePositionConfirm({ open: true, ticket, accountId: accountId || null })}
          onCloseAll={confirmCloseAll}
        />
        
        <ClosedPositionsTable
          positions={closedPositions}
          isLoading={isLoading}
          onRefresh={fetchClosedPositions}
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

        {/* Confirmation Dialogs */}
        <AlertDialog open={closeAllConfirmOpen} onOpenChange={setCloseAllConfirmOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Close All Positions?</AlertDialogTitle>
              <AlertDialogDescription>
                This will close all {positions.length} open positions{selectedAccountId !== "all" ? ` for the selected account` : ` across all accounts`}. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={() => { handleCloseAll(); setCloseAllConfirmOpen(false); }}>
                Close All Positions
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <AlertDialog open={closePositionConfirm.open} onOpenChange={(open) => setClosePositionConfirm({ open, ticket: null, accountId: null })}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Close Position?</AlertDialogTitle>
              <AlertDialogDescription>
                This will close position #{closePositionConfirm.ticket}. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={() => {
                if (closePositionConfirm.ticket) {
                  handleClosePosition(closePositionConfirm.ticket, closePositionConfirm.accountId || undefined);
                }
                setClosePositionConfirm({ open: false, ticket: null, accountId: null });
              }}>
                Close Position
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
};

export default Dashboard;

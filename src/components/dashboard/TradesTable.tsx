import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TablePagination } from "@/components/ui/table-pagination";
import { cn } from "@/lib/utils";
import { Download } from "lucide-react";
import type { Trade } from "@/types/trading";

interface TradesTableProps {
  trades: Trade[];
  isLoading?: boolean;
  onExport: () => void;
}

export function TradesTable({ trades, isLoading, onExport }: TradesTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const totalPages = Math.ceil(trades.length / pageSize);
  const paginatedTrades = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return trades.slice(startIndex, startIndex + pageSize);
  }, [trades, currentPage, pageSize]);

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(1);
  };

  return (
    <Card className="card-glow mb-5">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Trades</CardTitle>
        <Button variant="outline" size="sm" onClick={onExport}>
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="trading-table">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Symbol</th>
                <th>Type</th>
                <th>Entry Time</th>
                <th>Exit Time</th>
                <th>Profit</th>
                <th>Pips</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-muted-foreground">
                    Loading trades...
                  </td>
                </tr>
              ) : trades.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-muted-foreground">
                    No trades found
                  </td>
                </tr>
              ) : (
                paginatedTrades.map((trade) => (
                  <tr key={trade.ticket}>
                    <td className="font-mono">{trade.ticket}</td>
                    <td className="font-semibold">{trade.symbol}</td>
                    <td>
                      <span className={trade.type === "buy" ? "badge-buy" : "badge-sell"}>
                        {trade.type}
                      </span>
                    </td>
                    <td className="text-muted-foreground">{new Date(trade.entryTime).toLocaleString()}</td>
                    <td className="text-muted-foreground">
                      {trade.exitTime ? new Date(trade.exitTime).toLocaleString() : "-"}
                    </td>
                    <td className={cn("font-mono font-semibold", trade.profit >= 0 ? "text-profit" : "text-loss")}>
                      ${trade.profit.toFixed(2)}
                    </td>
                    <td className={cn("font-mono", trade.pips >= 0 ? "text-profit" : "text-loss")}>
                      {trade.pips.toFixed(1)}
                    </td>
                    <td>
                      <span className={cn(
                        "px-2 py-0.5 rounded text-xs font-semibold",
                        trade.status === "closed" ? "bg-muted text-muted-foreground" :
                        trade.status === "open" ? "bg-primary/20 text-primary" :
                        "bg-warning/20 text-warning"
                      )}>
                        {trade.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && trades.length > 0 && (
          <TablePagination
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            totalItems={trades.length}
            onPageChange={setCurrentPage}
            onPageSizeChange={handlePageSizeChange}
          />
        )}
      </CardContent>
    </Card>
  );
}

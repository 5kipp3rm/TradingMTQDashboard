import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TablePagination } from "@/components/ui/table-pagination";
import { cn } from "@/lib/utils";
import { RefreshCw, X } from "lucide-react";
import type { Position } from "@/types/trading";

interface PositionsTableProps {
  positions: Position[];
  isLoading?: boolean;
  autoRefresh?: boolean;
  onRefresh: () => void;
  onClosePosition: (ticket: number, accountId?: number) => void;
  onCloseAll: () => void;
}

export function PositionsTable({
  positions,
  isLoading,
  autoRefresh = false,
  onRefresh,
  onClosePosition,
  onCloseAll,
}: PositionsTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const totalPages = Math.ceil(positions.length / pageSize);
  const paginatedPositions = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return positions.slice(startIndex, startIndex + pageSize);
  }, [positions, currentPage, pageSize]);

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(1);
  };

  return (
    <Card className="card-glow mb-5">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <span>💹</span> Open Positions
          {autoRefresh && (
            <span className="text-xs text-muted-foreground font-normal">
              (Auto-refreshing)
            </span>
          )}
        </CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={onCloseAll}
            disabled={positions.length === 0}
          >
            <X className="h-4 w-4 mr-2" />
            Close All
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="trading-table">
            <thead>
              <tr>
                <th>Account</th>
                <th>Ticket</th>
                <th>Symbol</th>
                <th>Type</th>
                <th>Volume</th>
                <th>Open Price</th>
                <th>Current Price</th>
                <th>SL</th>
                <th>TP</th>
                <th>Profit</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={11} className="text-center py-8 text-muted-foreground">
                    Loading positions...
                  </td>
                </tr>
              ) : positions.length === 0 ? (
                <tr>
                  <td colSpan={11} className="text-center py-8 text-muted-foreground">
                    No open positions
                  </td>
                </tr>
              ) : (
                paginatedPositions.map((position) => (
                  <tr key={position.ticket}>
                    <td className="text-xs text-muted-foreground">{position.account_name || 'N/A'}</td>
                    <td className="font-mono">{position.ticket}</td>
                    <td className="font-semibold">{position.symbol}</td>
                    <td>
                      <span className={position.type === "buy" ? "badge-buy" : "badge-sell"}>
                        {position.type}
                      </span>
                    </td>
                    <td className="font-mono">{position.volume.toFixed(2)}</td>
                    <td className="font-mono">{position.openPrice.toFixed(5)}</td>
                    <td className="font-mono">{position.currentPrice.toFixed(5)}</td>
                    <td className="font-mono text-muted-foreground">
                      {position.sl?.toFixed(5) || "-"}
                    </td>
                    <td className="font-mono text-muted-foreground">
                      {position.tp?.toFixed(5) || "-"}
                    </td>
                    <td className={cn("font-mono font-semibold", position.profit >= 0 ? "text-profit" : "text-loss")}>
                      ${position.profit.toFixed(2)}
                    </td>
                    <td>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onClosePosition(position.ticket, position.account_id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && positions.length > 0 && (
          <TablePagination
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            totalItems={positions.length}
            onPageChange={setCurrentPage}
            onPageSizeChange={handlePageSizeChange}
          />
        )}
      </CardContent>
    </Card>
  );
}

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TablePagination } from "@/components/ui/table-pagination";
import { cn } from "@/lib/utils";
import { History, RefreshCw } from "lucide-react";
import type { Position } from "@/types/trading";

interface ClosedPositionsTableProps {
  positions: Position[];
  isLoading?: boolean;
  onRefresh: () => void;
}

export function ClosedPositionsTable({
  positions,
  isLoading,
  onRefresh,
}: ClosedPositionsTableProps) {
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
          <History className="h-5 w-5" />
          Recently Closed Positions
        </CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="trading-table">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Symbol</th>
                <th>Type</th>
                <th>Volume</th>
                <th>Open Price</th>
                <th>Close Price</th>
                <th>Open Time</th>
                <th>Close Time</th>
                <th>Profit</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-muted-foreground">
                    Loading closed positions...
                  </td>
                </tr>
              ) : positions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-muted-foreground">
                    No recently closed positions
                  </td>
                </tr>
              ) : (
                paginatedPositions.map((position) => (
                  <tr key={position.ticket}>
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
                    <td className="text-muted-foreground text-sm">
                      {position.openTime ? new Date(position.openTime).toLocaleString() : "-"}
                    </td>
                    <td className="text-muted-foreground text-sm">
                      {position.closeTime ? new Date(position.closeTime).toLocaleString() : "-"}
                    </td>
                    <td className={cn("font-mono font-semibold", position.profit >= 0 ? "text-profit" : "text-loss")}>
                      ${position.profit.toFixed(2)}
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

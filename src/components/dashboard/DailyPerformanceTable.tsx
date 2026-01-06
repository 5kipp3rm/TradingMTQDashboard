import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TablePagination } from "@/components/ui/table-pagination";
import { cn } from "@/lib/utils";
import type { DailyPerformance } from "@/types/trading";

interface DailyPerformanceTableProps {
  data: DailyPerformance[];
  isLoading?: boolean;
}

export function DailyPerformanceTable({ data, isLoading }: DailyPerformanceTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const totalPages = Math.ceil(data.length / pageSize);
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return data.slice(startIndex, startIndex + pageSize);
  }, [data, currentPage, pageSize]);

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(1);
  };

  return (
    <Card className="card-glow">
      <CardHeader>
        <CardTitle>Daily Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="trading-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Trades</th>
                <th>Winners</th>
                <th>Losers</th>
                <th>Net Profit</th>
                <th>Win Rate</th>
                <th>Profit Factor</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-muted-foreground">
                    Loading daily data...
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-muted-foreground">
                    No data available
                  </td>
                </tr>
              ) : (
                paginatedData.map((day) => (
                  <tr key={day.date}>
                    <td className="font-semibold">{new Date(day.date).toLocaleDateString()}</td>
                    <td className="font-mono">{day.trades}</td>
                    <td className="font-mono text-profit">{day.winners}</td>
                    <td className="font-mono text-loss">{day.losers}</td>
                    <td className={cn("font-mono font-semibold", day.netProfit >= 0 ? "text-profit" : "text-loss")}>
                      ${day.netProfit.toFixed(2)}
                    </td>
                    <td className="font-mono">{day.winRate.toFixed(1)}%</td>
                    <td className="font-mono">{day.profitFactor.toFixed(2)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && data.length > 0 && (
          <TablePagination
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            totalItems={data.length}
            onPageChange={setCurrentPage}
            onPageSizeChange={handlePageSizeChange}
          />
        )}
      </CardContent>
    </Card>
  );
}

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/dashboard/Header";
import { Download, FileText, Calendar, Loader2, AlertCircle, CheckCircle2, XCircle } from "lucide-react";
import { reportsApi, analyticsApi } from "@/lib/api";
import { format, subDays, startOfDay, endOfDay, startOfMonth, startOfWeek } from "date-fns";

interface ReportHistory {
  id: number;
  config_id?: number;
  generated_at: string;
  success: boolean;
  file_path?: string;
  file_size?: number;
  error_message?: string;
  report_start_date?: string;
  report_end_date?: string;
}

interface PerformanceMetrics {
  total_profit: number;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
}

const Reports = () => {
  const [history, setHistory] = useState<ReportHistory[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reportTypes = [
    {
      id: "daily",
      name: "Daily Report",
      description: "Summary of today's trading activity",
      getDateRange: () => ({
        start_date: format(startOfDay(new Date()), 'yyyy-MM-dd'),
        end_date: format(endOfDay(new Date()), 'yyyy-MM-dd')
      })
    },
    {
      id: "weekly",
      name: "Weekly Report",
      description: "Week-over-week performance analysis",
      getDateRange: () => ({
        start_date: format(startOfWeek(new Date()), 'yyyy-MM-dd'),
        end_date: format(new Date(), 'yyyy-MM-dd')
      })
    },
    {
      id: "monthly",
      name: "Monthly Report",
      description: "Comprehensive monthly statistics",
      getDateRange: () => ({
        start_date: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
        end_date: format(new Date(), 'yyyy-MM-dd')
      })
    },
    {
      id: "custom",
      name: "Last 30 Days",
      description: "Performance report for last 30 days",
      getDateRange: () => ({
        start_date: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
        end_date: format(new Date(), 'yyyy-MM-dd')
      })
    },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch report history and analytics in parallel
      const [historyRes, analyticsRes] = await Promise.all([
        reportsApi.getHistory({ limit: 10, success_only: false }),
        analyticsApi.getOverview({ days: 30 })
      ]);

      if (historyRes.data) {
        const historyData = historyRes.data as { history?: ReportHistory[] };
        setHistory(historyData.history || []);
      }

      if (analyticsRes.data) {
        const data = analyticsRes.data as any;
        // Calculate win rate from winning_days/total_days if available
        const winRate = data.win_rate ??
          (data.total_days > 0 ? data.winning_days / data.total_days : 0);

        setMetrics({
          total_profit: data.total_profit ?? data.net_profit ?? 0,
          total_trades: data.total_trades ?? 0,
          win_rate: winRate,
          profit_factor: data.profit_factor ?? 0
        });
      } else {
        // Set default metrics if no data
        setMetrics({
          total_profit: 0,
          total_trades: 0,
          win_rate: 0,
          profit_factor: 0
        });
      }
    } catch (err) {
      console.error('Failed to fetch reports data:', err);
      setError('Failed to load reports data');
      // Set default metrics on error
      setMetrics({
        total_profit: 0,
        total_trades: 0,
        win_rate: 0,
        profit_factor: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (reportType: typeof reportTypes[0]) => {
    setGenerating(reportType.id);
    setError(null);

    try {
      const dateRange = reportType.getDateRange();
      const response = await reportsApi.generate({
        ...dateRange,
        include_trades: true,
        include_charts: false
      });

      if (response.error) {
        throw new Error(response.error);
      }

      // Refresh history to show new report
      await fetchData();
    } catch (err) {
      console.error('Failed to generate report:', err);
      setError(`Failed to generate ${reportType.name}`);
    } finally {
      setGenerating(null);
    }
  };

  const handleDownload = (historyId: number) => {
    const url = reportsApi.getDownloadUrl(historyId);
    window.open(url, '_blank');
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatReportName = (report: ReportHistory) => {
    if (report.report_start_date && report.report_end_date) {
      const start = new Date(report.report_start_date);
      const end = new Date(report.report_end_date);
      return `Report ${format(start, 'MMM d')} - ${format(end, 'MMM d, yyyy')}`;
    }
    return `Report #${report.id}`;
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={30}
          onPeriodChange={() => {}}
          onRefresh={fetchData}
          onQuickTrade={() => {}}
        />

        <h2 className="text-2xl font-bold mb-6">Reports</h2>

        {error && (
          <div className="mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-6">
          <Card className="card-glow">
            <CardHeader>
              <CardTitle>Generate Report</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {reportTypes.map((report) => (
                  <div
                    key={report.id}
                    onClick={() => !generating && handleGenerateReport(report)}
                    className={`p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer ${
                      generating === report.id ? 'opacity-50 cursor-wait' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {generating === report.id ? (
                        <Loader2 className="h-5 w-5 text-primary mt-0.5 animate-spin" />
                      ) : (
                        <FileText className="h-5 w-5 text-primary mt-0.5" />
                      )}
                      <div>
                        <p className="font-semibold">{report.name}</p>
                        <p className="text-sm text-muted-foreground">{report.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="card-glow">
            <CardHeader>
              <CardTitle>Recent Reports</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : history.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No reports generated yet. Click on a report type above to generate one.
                </div>
              ) : (
                <div className="space-y-3">
                  {history.map((report) => (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-4 rounded-lg bg-muted/30"
                    >
                      <div className="flex items-center gap-3">
                        {report.success ? (
                          <CheckCircle2 className="h-5 w-5 text-profit" />
                        ) : (
                          <XCircle className="h-5 w-5 text-loss" />
                        )}
                        <div>
                          <p className="font-semibold">{formatReportName(report)}</p>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Calendar className="h-3 w-3" />
                            {format(new Date(report.generated_at), 'MMM d, yyyy HH:mm')}
                            {report.success && (
                              <>
                                <span>•</span>
                                {formatFileSize(report.file_size)}
                              </>
                            )}
                          </div>
                          {!report.success && report.error_message && (
                            <p className="text-xs text-loss mt-1">{report.error_message}</p>
                          )}
                        </div>
                      </div>
                      {report.success && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDownload(report.id)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="card-glow">
          <CardHeader>
            <CardTitle>Performance Summary (Last 30 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <p className={`text-3xl font-bold font-mono ${
                    (metrics?.total_profit || 0) >= 0 ? 'text-profit' : 'text-loss'
                  }`}>
                    ${(metrics?.total_profit || 0).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })}
                  </p>
                  <p className="text-sm text-muted-foreground">Total Profit (MTD)</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold font-mono">
                    {metrics?.total_trades || 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Total Trades</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold font-mono">
                    {((metrics?.win_rate || 0) * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-muted-foreground">Win Rate</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold font-mono">
                    {(metrics?.profit_factor || 0).toFixed(2)}
                  </p>
                  <p className="text-sm text-muted-foreground">Profit Factor</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Reports;

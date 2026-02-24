import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { Header } from "@/components/dashboard/Header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import {
  RefreshCw,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowUpDown,
  Trash2,
  Server,
  Zap,
  TrendingUp,
  Users,
} from "lucide-react";

// ============================================================================
// Types
// ============================================================================

interface EndpointMetrics {
  total: number;
  success: number;
  client_error: number;
  server_error: number;
  avg_time_ms: number;
  min_time_ms: number;
  max_time_ms: number;
  last_request: string | null;
}

interface GlobalMetrics {
  total_requests: number;
  success: number;
  client_error: number;
  server_error: number;
  avg_time_ms: number;
}

interface MetricsResponse {
  uptime_seconds: number;
  started_at: string;
  global: GlobalMetrics;
  endpoints: Record<string, EndpointMetrics>;
}

// ============================================================================
// Helpers
// ============================================================================

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  if (m > 0) parts.push(`${m}m`);
  parts.push(`${s}s`);
  return parts.join(" ");
}

function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

function successRate(e: EndpointMetrics | GlobalMetrics): number {
  const total = "total" in e ? e.total : (e as GlobalMetrics).total_requests;
  return total > 0 ? (e.success / total) * 100 : 100;
}

function speedBadge(ms: number) {
  if (ms <= 50)
    return (
      <Badge variant="default" className="bg-emerald-600">
        {ms}ms
      </Badge>
    );
  if (ms <= 200)
    return (
      <Badge variant="secondary">
        {ms}ms
      </Badge>
    );
  return (
    <Badge variant="destructive">
      {ms}ms
    </Badge>
  );
}

// ============================================================================
// Sort logic
// ============================================================================

type SortField =
  | "endpoint"
  | "total"
  | "success_rate"
  | "avg_time"
  | "last_request";

function sortEntries(
  entries: [string, EndpointMetrics][],
  field: SortField,
  asc: boolean
): [string, EndpointMetrics][] {
  const sorted = [...entries].sort((a, b) => {
    switch (field) {
      case "endpoint":
        return a[0].localeCompare(b[0]);
      case "total":
        return a[1].total - b[1].total;
      case "success_rate":
        return successRate(a[1]) - successRate(b[1]);
      case "avg_time":
        return a[1].avg_time_ms - b[1].avg_time_ms;
      case "last_request": {
        const ta = a[1].last_request
          ? new Date(a[1].last_request).getTime()
          : 0;
        const tb = b[1].last_request
          ? new Date(b[1].last_request).getTime()
          : 0;
        return ta - tb;
      }
      default:
        return 0;
    }
  });
  return asc ? sorted : sorted.reverse();
}

// ============================================================================
// Component
// ============================================================================

export default function Admin() {
  const { toast } = useToast();
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [sortField, setSortField] = useState<SortField>("total");
  const [sortAsc, setSortAsc] = useState(false);

  const fetchMetrics = useCallback(
    async (reset = false) => {
      setLoading(true);
      try {
        const url = reset ? "/api/v2/metrics?reset=true" : "/api/v2/metrics";
        const baseUrl =
          import.meta.env.VITE_API_URL?.replace("/api", "") ||
          "http://localhost:8000";
        const res = await fetch(`${baseUrl}${url}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: MetricsResponse = await res.json();
        setMetrics(data);
        if (reset) {
          toast({
            title: "Metrics reset",
            description: "All counters have been zeroed.",
          });
        }
      } catch (err: any) {
        toast({
          title: "Failed to fetch metrics",
          description: err.message,
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    },
    [toast]
  );

  // Initial fetch + auto-refresh every 10s
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = setInterval(() => fetchMetrics(), 10_000);
    return () => clearInterval(timer);
  }, [autoRefresh, fetchMetrics]);

  // Toggle sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const SortHeader = ({
    field,
    children,
  }: {
    field: SortField;
    children: React.ReactNode;
  }) => (
    <TableHead
      className="cursor-pointer select-none hover:text-foreground"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortField === field && (
          <ArrowUpDown className="h-3 w-3 text-primary" />
        )}
      </div>
    </TableHead>
  );

  // ---------- Derived data ----------
  const g = metrics?.global;
  const endpoints = metrics
    ? sortEntries(Object.entries(metrics.endpoints), sortField, sortAsc)
    : [];

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      <Header
        period={30}
        onPeriodChange={() => {}}
        onRefresh={() => fetchMetrics()}
        onQuickTrade={() => {}}
      />

      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Server className="h-6 w-6 text-primary" />
          <h2 className="text-2xl font-bold">Admin Panel</h2>
          {metrics && (
            <Badge variant="outline" className="ml-2">
              <Clock className="h-3 w-3 mr-1" />
              Uptime {formatUptime(metrics.uptime_seconds)}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link to="/admin/users">
              <Users className="h-4 w-4 mr-1" />
              Manage Users
            </Link>
          </Button>
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className="h-4 w-4 mr-1" />
            {autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchMetrics()}
            disabled={loading}
          >
            <RefreshCw
              className={`h-4 w-4 mr-1 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => fetchMetrics(true)}
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Reset Counters
          </Button>
        </div>
      </div>

      {/* Global summary cards */}
      {g && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Requests</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                <span className="text-3xl font-bold">
                  {g.total_requests.toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Success (2xx)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-500" />
                <span className="text-3xl font-bold text-emerald-600">
                  {g.success.toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Client Errors (4xx)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                <span className="text-3xl font-bold text-yellow-600">
                  {g.client_error.toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Server Errors (5xx)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-500" />
                <span className="text-3xl font-bold text-red-600">
                  {g.server_error.toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Avg Response</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-500" />
                <span className="text-3xl font-bold">{g.avg_time_ms}ms</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Success rate bar */}
      {g && g.total_requests > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Overall Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Progress
                value={successRate(g)}
                className="flex-1 h-3"
              />
              <span className="text-lg font-bold">
                {successRate(g).toFixed(1)}%
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Endpoint table */}
      <Card>
        <CardHeader>
          <CardTitle>Endpoint Breakdown</CardTitle>
          <CardDescription>
            {endpoints.length} endpoint{endpoints.length !== 1 ? "s" : ""}{" "}
            tracked · click headers to sort
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <SortHeader field="endpoint">Endpoint</SortHeader>
                  <SortHeader field="total">Requests</SortHeader>
                  <SortHeader field="success_rate">Success Rate</SortHeader>
                  <TableHead>2xx</TableHead>
                  <TableHead>4xx</TableHead>
                  <TableHead>5xx</TableHead>
                  <SortHeader field="avg_time">Avg</SortHeader>
                  <TableHead>Min</TableHead>
                  <TableHead>Max</TableHead>
                  <SortHeader field="last_request">Last Hit</SortHeader>
                </TableRow>
              </TableHeader>
              <TableBody>
                {endpoints.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
                      No requests recorded yet. Start using the API!
                    </TableCell>
                  </TableRow>
                )}
                {endpoints.map(([key, e]) => {
                  const rate = successRate(e);
                  return (
                    <TableRow key={key}>
                      <TableCell className="font-mono text-xs whitespace-nowrap">
                        {(() => {
                          const [method, ...rest] = key.split(" ");
                          const path = rest.join(" ");
                          const methodColor =
                            method === "GET"
                              ? "text-emerald-600"
                              : method === "POST"
                              ? "text-blue-600"
                              : method === "PATCH"
                              ? "text-yellow-600"
                              : method === "DELETE"
                              ? "text-red-600"
                              : "text-muted-foreground";
                          return (
                            <>
                              <span className={`font-bold ${methodColor}`}>
                                {method}
                              </span>{" "}
                              {path}
                            </>
                          );
                        })()}
                      </TableCell>
                      <TableCell className="font-bold">
                        {e.total.toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={rate} className="w-16 h-2" />
                          <span
                            className={`text-xs font-medium ${
                              rate === 100
                                ? "text-emerald-600"
                                : rate >= 90
                                ? "text-yellow-600"
                                : "text-red-600"
                            }`}
                          >
                            {rate.toFixed(0)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-emerald-600">
                        {e.success}
                      </TableCell>
                      <TableCell className="text-yellow-600">
                        {e.client_error || "—"}
                      </TableCell>
                      <TableCell className="text-red-600">
                        {e.server_error || "—"}
                      </TableCell>
                      <TableCell>{speedBadge(e.avg_time_ms)}</TableCell>
                      <TableCell className="text-muted-foreground text-xs">
                        {e.min_time_ms}ms
                      </TableCell>
                      <TableCell className="text-muted-foreground text-xs">
                        {e.max_time_ms}ms
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                        {timeAgo(e.last_request)}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

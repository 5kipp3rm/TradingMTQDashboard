import { useState, useEffect } from "react";
import { Header } from "@/components/dashboard/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAccounts } from "@/contexts/AccountsContext";
import { useToast } from "@/hooks/use-toast";
import { Search, RefreshCw, Filter, Download, FileText, AlertTriangle, Info, CheckCircle } from "lucide-react";

interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  correlation_id?: string;
  account_id?: number;
  event_type?: string;
  symbol?: string;
  method?: string;
  path?: string;
  status_code?: number;
  duration?: number;
  client?: string;
  extra?: Record<string, any>;
}

interface LogsResponse {
  logs: LogEntry[];
  total: number;
  filtered: number;
  page: number;
  page_size: number;
  log_type?: string;
  account_id?: number;
}

interface LogTypeInfo {
  name: string;
  display_name: string;
  file_pattern: string;
  description: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const Logs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logTypes, setLogTypes] = useState<LogTypeInfo[]>([]);
  const [selectedLogType, setSelectedLogType] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedLevel, setSelectedLevel] = useState<string | undefined>(undefined);
  const [days, setDays] = useState(7);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(100);
  const [totalLogs, setTotalLogs] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [period, setPeriod] = useState(30);
  const { selectedAccountId } = useAccounts();
  const { toast } = useToast();

  // Fetch log types on mount
  useEffect(() => {
    fetchLogTypes();
  }, []);

  // Fetch logs when filters change
  useEffect(() => {
    fetchLogs();
  }, [selectedLogType, selectedAccountId, selectedLevel, days, page]);

  const fetchLogTypes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/logs/types`);
      const data = await response.json();
      setLogTypes(data.log_types || []);
    } catch (error) {
      console.error("Failed to fetch log types:", error);
      toast({
        title: "Error",
        description: "Failed to load log types",
        variant: "destructive",
      });
    }
  };

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        log_type: selectedLogType,
        days: days.toString(),
        limit: pageSize.toString(),
        page: page.toString(),
      });

      if (selectedAccountId && selectedAccountId !== "all") {
        params.append("account_id", selectedAccountId);
      }

      if (searchTerm) {
        params.append("search", searchTerm);
      }

      if (selectedLevel) {
        params.append("level", selectedLevel);
      }

      const url = `${API_BASE_URL}/logs?${params.toString()}`;
      console.log("Fetching logs from:", url);

      const response = await fetch(url);
      const data: LogsResponse = await response.json();

      console.log("Logs response:", data);
      console.log("Number of logs:", data.logs?.length);

      setLogs(data.logs || []);
      setTotalLogs(data.total || 0);
    } catch (error) {
      console.error("Failed to fetch logs:", error);
      toast({
        title: "Error",
        description: "Failed to load logs",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchLogs();
  };

  const handleExportCSV = () => {
    const headers = ["Timestamp", "Level", "Logger", "Message", "Account ID", "Symbol", "Correlation ID"];
    const rows = logs.map((log) => [
      log.timestamp,
      log.level,
      log.logger,
      log.message.replace(/,/g, ";"), // Escape commas
      log.account_id || "",
      log.symbol || "",
      log.correlation_id || "",
    ]);

    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `logs_${selectedLogType}_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();

    toast({
      title: "Export Complete",
      description: `${logs.length} logs exported to CSV successfully.`,
    });
  };

  const getLevelIcon = (level: string) => {
    switch (level.toUpperCase()) {
      case "ERROR":
        return <AlertTriangle className="h-4 w-4 text-destructive" />;
      case "WARNING":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case "INFO":
        return <Info className="h-4 w-4 text-blue-500" />;
      case "DEBUG":
        return <FileText className="h-4 w-4 text-muted-foreground" />;
      default:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  };

  const getLevelBadgeVariant = (level: string) => {
    switch (level.toUpperCase()) {
      case "ERROR":
        return "destructive";
      case "WARNING":
        return "secondary";
      default:
        return "outline";
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
      <Header
        period={period}
        onPeriodChange={setPeriod}
        onRefresh={fetchLogs}
        onQuickTrade={() => {}}
      />

      <div className="space-y-6">
        {/* Filters Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Application Logs</CardTitle>
                <CardDescription>
                  View and filter backend logs, trading activity, and system events
                </CardDescription>
              </div>
              <Button onClick={handleExportCSV} variant="outline" className="gap-2">
                <Download className="h-4 w-4" />
                Export CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Log Type Filter */}
              <Select value={selectedLogType} onValueChange={setSelectedLogType}>
                <SelectTrigger>
                  <SelectValue placeholder="Log Type" />
                </SelectTrigger>
                <SelectContent>
                  {logTypes.map((type) => (
                    <SelectItem key={type.name} value={type.name}>
                      {type.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Level Filter */}
              <Select value={selectedLevel || "all"} onValueChange={(v) => setSelectedLevel(v === "all" ? undefined : v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Log Level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="DEBUG">Debug</SelectItem>
                  <SelectItem value="INFO">Info</SelectItem>
                  <SelectItem value="WARNING">Warning</SelectItem>
                  <SelectItem value="ERROR">Error</SelectItem>
                </SelectContent>
              </Select>

              {/* Days Filter */}
              <Select value={days.toString()} onValueChange={(v) => setDays(Number(v))}>
                <SelectTrigger>
                  <SelectValue placeholder="Time Range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Last 24 Hours</SelectItem>
                  <SelectItem value="3">Last 3 Days</SelectItem>
                  <SelectItem value="7">Last 7 Days</SelectItem>
                  <SelectItem value="14">Last 14 Days</SelectItem>
                  <SelectItem value="30">Last 30 Days</SelectItem>
                </SelectContent>
              </Select>

              {/* Search Input */}
              <div className="col-span-1 md:col-span-2 lg:col-span-2 flex gap-2">
                <Input
                  placeholder="Search logs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                  className="flex-1"
                />
                <Button onClick={handleSearch} size="icon">
                  <Search className="h-4 w-4" />
                </Button>
                <Button onClick={fetchLogs} size="icon" variant="outline">
                  <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
                </Button>
              </div>
            </div>

            {/* Stats */}
            <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
              <span>Total Logs: {totalLogs}</span>
              <span>•</span>
              <span>Showing: {logs.length}</span>
              <span>•</span>
              <span>
                Page {page} of {Math.ceil(totalLogs / pageSize)}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Logs Table */}
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50 border-b">
                  <tr>
                    <th className="text-left p-4 font-medium text-sm">Timestamp</th>
                    <th className="text-left p-4 font-medium text-sm">Level</th>
                    <th className="text-left p-4 font-medium text-sm">Logger</th>
                    <th className="text-left p-4 font-medium text-sm">Message</th>
                    <th className="text-left p-4 font-medium text-sm">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr>
                      <td colSpan={5} className="text-center p-8 text-muted-foreground">
                        Loading logs...
                      </td>
                    </tr>
                  ) : logs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center p-8 text-muted-foreground">
                        No logs found matching your filters
                      </td>
                    </tr>
                  ) : (
                    logs.map((log, index) => (
                      <tr key={index} className="border-b hover:bg-muted/30 transition-colors">
                        <td className="p-4 text-sm font-mono text-muted-foreground">
                          {formatTimestamp(log.timestamp)}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            {getLevelIcon(log.level)}
                            <Badge variant={getLevelBadgeVariant(log.level)} className="text-xs">
                              {log.level}
                            </Badge>
                          </div>
                        </td>
                        <td className="p-4 text-sm font-mono text-muted-foreground">
                          {log.logger.split('.').pop()}
                        </td>
                        <td className="p-4 text-sm">
                          <div className="max-w-2xl">
                            <p className="break-words">{log.message}</p>
                            {log.symbol && (
                              <Badge variant="outline" className="mt-1 text-xs">
                                {log.symbol}
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex flex-col gap-1 text-xs text-muted-foreground">
                            {log.account_id && <span>Account: {log.account_id}</span>}
                            {log.event_type && <span>Event: {log.event_type}</span>}
                            {log.method && log.path && (
                              <span className="font-mono">
                                {log.method} {log.path}
                              </span>
                            )}
                            {log.status_code && (
                              <span>
                                Status: {log.status_code}
                                {log.duration && ` (${log.duration.toFixed(3)}s)`}
                              </span>
                            )}
                            {log.correlation_id && (
                              <span className="font-mono text-[10px]" title={log.correlation_id}>
                                {log.correlation_id.slice(0, 8)}...
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalLogs > pageSize && (
              <div className="flex items-center justify-between p-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {Math.ceil(totalLogs / pageSize)}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.min(Math.ceil(totalLogs / pageSize), p + 1))}
                  disabled={page >= Math.ceil(totalLogs / pageSize)}
                >
                  Next
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      </div>
    </div>
  );
};

export default Logs;

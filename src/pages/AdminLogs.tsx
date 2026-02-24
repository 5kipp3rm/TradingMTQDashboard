/**
 * Admin: System Logs Viewer
 *
 * View, filter, and browse application logs.
 */

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/dashboard/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { getAccessToken } from "@/lib/auth";
import { ScrollText, RefreshCw, ArrowLeft, Search } from "lucide-react";
import { Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "/api";

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  module?: string;
  [key: string]: any;
}

interface LogType {
  name: string;
  description?: string;
}

export default function AdminLogs() {
  const { toast } = useToast();
  const [logTypes, setLogTypes] = useState<LogType[]>([]);
  const [selectedType, setSelectedType] = useState("all");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState("all");
  const [limit, setLimit] = useState(100);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);

  const headers = () => ({
    Authorization: `Bearer ${getAccessToken()}`,
  });

  const fetchLogTypes = useCallback(async () => {
    try {
      const res = await fetch(`${API}/logs/types`, { headers: headers() });
      if (res.ok) {
        const data = await res.json();
        setLogTypes(Array.isArray(data) ? data : data.types || []);
      }
    } catch { /* ignore */ }
  }, []);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedType !== "all") params.set("log_type", selectedType);
      if (levelFilter !== "all") params.set("level", levelFilter);
      if (searchQuery) params.set("search", searchQuery);
      params.set("limit", limit.toString());

      const res = await fetch(`${API}/logs?${params}`, { headers: headers() });
      if (res.ok) {
        const data = await res.json();
        setLogs(Array.isArray(data) ? data : data.entries || data.logs || []);
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [selectedType, levelFilter, searchQuery, limit, toast]);

  useEffect(() => { fetchLogTypes(); }, [fetchLogTypes]);
  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const levelBadge = (level: string) => {
    switch (level?.toUpperCase()) {
      case "ERROR": case "CRITICAL": return <Badge variant="destructive" className="text-xs">{level}</Badge>;
      case "WARNING": case "WARN": return <Badge className="bg-yellow-600 text-xs">{level}</Badge>;
      case "INFO": return <Badge className="bg-blue-600 text-xs">{level}</Badge>;
      case "DEBUG": return <Badge variant="secondary" className="text-xs">{level}</Badge>;
      default: return <Badge variant="outline" className="text-xs">{level}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full py-5 px-4 lg:px-8">
        <Header period={30} onPeriodChange={() => {}} onRefresh={fetchLogs} onQuickTrade={() => setQuickTradeOpen(true)} />

        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/admin"><ArrowLeft className="h-4 w-4 mr-1" />Admin</Link>
          </Button>
          <ScrollText className="h-6 w-6 text-cyan-500" />
          <h2 className="text-2xl font-bold">System Logs</h2>
        </div>

        {/* Filters */}
        <Card className="mb-5">
          <CardContent className="pt-6">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="space-y-1">
                <Label className="text-xs">Log Type</Label>
                <Select value={selectedType} onValueChange={setSelectedType}>
                  <SelectTrigger className="w-[160px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    {logTypes.map((t) => (
                      <SelectItem key={typeof t === "string" ? t : t.name} value={typeof t === "string" ? t : t.name}>
                        {typeof t === "string" ? t : t.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Level</Label>
                <Select value={levelFilter} onValueChange={setLevelFilter}>
                  <SelectTrigger className="w-[130px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Levels</SelectItem>
                    <SelectItem value="DEBUG">DEBUG</SelectItem>
                    <SelectItem value="INFO">INFO</SelectItem>
                    <SelectItem value="WARNING">WARNING</SelectItem>
                    <SelectItem value="ERROR">ERROR</SelectItem>
                    <SelectItem value="CRITICAL">CRITICAL</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Limit</Label>
                <Select value={limit.toString()} onValueChange={(v) => setLimit(parseInt(v))}>
                  <SelectTrigger className="w-[100px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="250">250</SelectItem>
                    <SelectItem value="500">500</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1 flex-1 min-w-[200px]">
                <Label className="text-xs">Search</Label>
                <div className="relative">
                  <Search className="h-4 w-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search log messages..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-8"
                  />
                </div>
              </div>
              <Button variant="outline" onClick={fetchLogs} disabled={loading}>
                <RefreshCw className={`h-4 w-4 mr-1 ${loading ? "animate-spin" : ""}`} />Refresh
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Log Entries */}
        <Card>
          <CardHeader>
            <CardTitle>Log Entries</CardTitle>
            <CardDescription>{logs.length} entries loaded</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[600px] overflow-auto">
              <div className="font-mono text-xs space-y-0.5 p-4">
                {logs.length === 0 && !loading && (
                  <p className="text-center text-muted-foreground py-8">No log entries found</p>
                )}
                {loading && logs.length === 0 && (
                  <div className="flex justify-center py-8"><RefreshCw className="h-5 w-5 animate-spin" /></div>
                )}
                {logs.map((entry, i) => (
                  <div key={i} className="flex gap-2 items-start py-1 px-2 rounded hover:bg-muted/50 border-b border-border/30">
                    <span className="text-muted-foreground whitespace-nowrap shrink-0">
                      {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : "—"}
                    </span>
                    {levelBadge(entry.level || "INFO")}
                    {entry.module && <span className="text-muted-foreground shrink-0">[{entry.module}]</span>}
                    <span className="break-all">{entry.message}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <QuickTradeModal open={quickTradeOpen} onClose={() => setQuickTradeOpen(false)} currencies={[]} onTrade={() => {}} />
      </div>
    </div>
  );
}

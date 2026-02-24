/**
 * Admin: Workers Management
 *
 * View, start, stop, and restart background workers.
 */

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/dashboard/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { getAccessToken } from "@/lib/auth";
import { Cpu, Play, Square, RotateCcw, RefreshCw, ArrowLeft, PlayCircle, StopCircle } from "lucide-react";
import { Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "/api";

interface Worker {
  name: string;
  status: string;
  account_id?: string;
  account_name?: string;
  uptime_seconds?: number;
  last_error?: string;
  config?: Record<string, any>;
}

export default function AdminWorkers() {
  const { toast } = useToast();
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);

  const headers = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${getAccessToken()}`,
  });

  const fetchWorkers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/workers/`, { headers: headers() });
      if (res.ok) {
        const data = await res.json();
        setWorkers(data.workers || data.items || (Array.isArray(data) ? data : []));
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { fetchWorkers(); }, [fetchWorkers]);

  const workerAction = async (name: string, action: "start" | "stop" | "restart") => {
    setActionLoading(`${name}-${action}`);
    try {
      const res = await fetch(`${API}/workers/${name}/${action}`, {
        method: "POST",
        headers: headers(),
      });
      if (res.ok) {
        toast({ title: "Success", description: `Worker ${name} ${action}ed.` });
        setTimeout(fetchWorkers, 1000);
      } else {
        const err = await res.json();
        throw new Error(err.detail || `Failed to ${action} worker`);
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  const bulkAction = async (action: "start-all" | "stop-all") => {
    setActionLoading(action);
    try {
      const res = await fetch(`${API}/workers/${action}`, {
        method: "POST",
        headers: headers(),
      });
      if (res.ok) {
        toast({ title: "Success", description: `All workers ${action === "start-all" ? "started" : "stopped"}.` });
        setTimeout(fetchWorkers, 1000);
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  const statusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "running": return <Badge className="bg-emerald-600">Running</Badge>;
      case "stopped": return <Badge variant="secondary">Stopped</Badge>;
      case "error": return <Badge variant="destructive">Error</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatUptime = (seconds?: number) => {
    if (!seconds) return "—";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h}h ${m}m ${s}s`;
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full py-5 px-4 lg:px-8">
        <Header period={30} onPeriodChange={() => {}} onRefresh={fetchWorkers} onQuickTrade={() => setQuickTradeOpen(true)} />

        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/admin"><ArrowLeft className="h-4 w-4 mr-1" />Admin</Link>
          </Button>
          <Cpu className="h-6 w-6 text-orange-500" />
          <h2 className="text-2xl font-bold">Workers Management</h2>
          <div className="flex gap-2 ml-auto">
            <Button variant="outline" size="sm" onClick={() => bulkAction("start-all")} disabled={actionLoading !== null}>
              <PlayCircle className="h-4 w-4 mr-1" />Start All
            </Button>
            <Button variant="outline" size="sm" onClick={() => bulkAction("stop-all")} disabled={actionLoading !== null}>
              <StopCircle className="h-4 w-4 mr-1" />Stop All
            </Button>
            <Button variant="outline" size="sm" onClick={fetchWorkers} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-1 ${loading ? "animate-spin" : ""}`} />Refresh
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Background Workers</CardTitle>
            <CardDescription>{workers.length} worker(s) registered</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Worker Name</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Uptime</TableHead>
                  <TableHead>Last Error</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workers.length === 0 && !loading && (
                  <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">No workers found</TableCell></TableRow>
                )}
                {loading && workers.length === 0 && (
                  <TableRow><TableCell colSpan={6} className="text-center py-8"><RefreshCw className="h-5 w-5 animate-spin mx-auto" /></TableCell></TableRow>
                )}
                {workers.map((w) => (
                  <TableRow key={w.name}>
                    <TableCell className="font-medium">{w.name}</TableCell>
                    <TableCell>{w.account_name || w.account_id || "—"}</TableCell>
                    <TableCell>{statusBadge(w.status)}</TableCell>
                    <TableCell className="text-sm">{formatUptime(w.uptime_seconds)}</TableCell>
                    <TableCell className="text-xs text-red-500 max-w-[200px] truncate">{w.last_error || "—"}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost" size="sm" title="Start"
                          onClick={() => workerAction(w.name, "start")}
                          disabled={actionLoading !== null}
                        >
                          <Play className="h-4 w-4 text-emerald-500" />
                        </Button>
                        <Button
                          variant="ghost" size="sm" title="Stop"
                          onClick={() => workerAction(w.name, "stop")}
                          disabled={actionLoading !== null}
                        >
                          <Square className="h-4 w-4 text-red-500" />
                        </Button>
                        <Button
                          variant="ghost" size="sm" title="Restart"
                          onClick={() => workerAction(w.name, "restart")}
                          disabled={actionLoading !== null}
                        >
                          <RotateCcw className="h-4 w-4 text-blue-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <QuickTradeModal open={quickTradeOpen} onClose={() => setQuickTradeOpen(false)} currencies={[]} onTrade={() => {}} />
      </div>
    </div>
  );
}

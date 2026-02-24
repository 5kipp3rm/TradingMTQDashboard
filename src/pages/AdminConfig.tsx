/**
 * Admin: System Configuration
 *
 * View and manage runtime configuration, import/export settings.
 */

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/dashboard/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { getAccessToken } from "@/lib/auth";
import { Settings, RefreshCw, Download, Upload, RotateCcw, ArrowLeft, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "/api";

interface ConfigStats {
  total_currencies: number;
  enabled_currencies: number;
  disabled_currencies: number;
  categories: Record<string, number>;
  favorites_count: number;
  recent_count: number;
}

export default function AdminConfig() {
  const { toast } = useToast();
  const [stats, setStats] = useState<ConfigStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);

  const headers = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${getAccessToken()}`,
  });

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/config/stats`, { headers: headers() });
      if (res.ok) setStats(await res.json());
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  const handleExport = async () => {
    try {
      const res = await fetch(`${API}/config/export`, { method: "POST", headers: headers() });
      if (res.ok) {
        const data = await res.json();
        toast({ title: "Exported", description: data.message || "Configuration exported successfully." });
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
  };

  const handleImport = async () => {
    try {
      const res = await fetch(`${API}/config/import`, { method: "POST", headers: headers() });
      if (res.ok) {
        const data = await res.json();
        toast({ title: "Imported", description: data.message || "Configuration imported." });
        fetchStats();
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
  };

  const handleReset = async () => {
    if (!confirm("Are you sure you want to reset configuration to defaults?")) return;
    setResetting(true);
    try {
      const res = await fetch(`${API}/config/reset`, { method: "POST", headers: headers() });
      if (res.ok) {
        toast({ title: "Reset", description: "Configuration reset to defaults." });
        fetchStats();
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full py-5 px-4 lg:px-8">
        <Header period={30} onPeriodChange={() => {}} onRefresh={fetchStats} onQuickTrade={() => setQuickTradeOpen(true)} />

        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/admin"><ArrowLeft className="h-4 w-4 mr-1" />Admin</Link>
          </Button>
          <Settings className="h-6 w-6 text-purple-500" />
          <h2 className="text-2xl font-bold">System Configuration</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Stats Card */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration Overview</CardTitle>
              <CardDescription>Current system configuration statistics</CardDescription>
            </CardHeader>
            <CardContent>
              {stats ? (
                <div className="space-y-3">
                  <div className="flex justify-between"><span className="text-muted-foreground">Total Currencies</span><Badge>{stats.total_currencies}</Badge></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Enabled</span><Badge variant="default" className="bg-emerald-600">{stats.enabled_currencies}</Badge></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Disabled</span><Badge variant="secondary">{stats.disabled_currencies}</Badge></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Favorites</span><Badge variant="outline">{stats.favorites_count}</Badge></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Recent</span><Badge variant="outline">{stats.recent_count}</Badge></div>
                </div>
              ) : loading ? (
                <div className="flex justify-center py-8"><RefreshCw className="h-6 w-6 animate-spin" /></div>
              ) : (
                <p className="text-muted-foreground">Failed to load stats</p>
              )}
            </CardContent>
          </Card>

          {/* Categories Card */}
          <Card>
            <CardHeader>
              <CardTitle>Currency Categories</CardTitle>
            </CardHeader>
            <CardContent>
              {stats?.categories ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead className="text-right">Count</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(stats.categories).map(([cat, count]) => (
                      <TableRow key={cat}>
                        <TableCell className="capitalize">{cat}</TableCell>
                        <TableCell className="text-right font-mono">{count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-muted-foreground text-sm">No categories data</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <Card className="mt-5">
          <CardHeader>
            <CardTitle>Configuration Actions</CardTitle>
            <CardDescription>Import, export, or reset system configuration</CardDescription>
          </CardHeader>
          <CardContent>
            <Alert className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                These actions affect the runtime configuration. Use with caution.
              </AlertDescription>
            </Alert>
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={handleExport}>
                <Download className="h-4 w-4 mr-2" />Export Config
              </Button>
              <Button variant="outline" onClick={handleImport}>
                <Upload className="h-4 w-4 mr-2" />Import Config
              </Button>
              <Button variant="destructive" onClick={handleReset} disabled={resetting}>
                <RotateCcw className="h-4 w-4 mr-2" />{resetting ? "Resetting..." : "Reset to Defaults"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <QuickTradeModal open={quickTradeOpen} onClose={() => setQuickTradeOpen(false)} currencies={[]} onTrade={() => {}} />
      </div>
    </div>
  );
}

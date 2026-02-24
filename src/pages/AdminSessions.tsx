/**
 * Admin: Active Sessions
 *
 * View and manage active user sessions (refresh tokens).
 */

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/dashboard/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { getAccessToken } from "@/lib/auth";
import { Shield, ArrowLeft, RefreshCw, Trash2, UserX } from "lucide-react";
import { Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "/api";

interface Session {
  id: number;
  user_id: number;
  username: string;
  role: string;
  created_at: string;
  expires_at: string;
  device_info?: string;
}

export default function AdminSessions() {
  const { toast } = useToast();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<Session | null>(null);
  const [revokeAllUser, setRevokeAllUser] = useState<{ user_id: number; username: string } | null>(null);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);

  const authHeaders = () => ({
    Authorization: `Bearer ${getAccessToken()}`,
    "Content-Type": "application/json",
  });

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/auth/sessions`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setSessions(Array.isArray(data) ? data : data.sessions || []);
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
    setLoading(false);
  }, [toast]);

  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  const revokeSession = async (sessionId: number) => {
    try {
      const res = await fetch(`${API}/auth/sessions/${sessionId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error("Failed to revoke session");
      toast({ title: "Revoked", description: "Session has been revoked" });
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
    setRevokeTarget(null);
  };

  const revokeAllForUser = async (userId: number) => {
    try {
      const res = await fetch(`${API}/auth/sessions?target_user_id=${userId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error("Failed to revoke sessions");
      toast({ title: "Revoked", description: "All sessions for user have been revoked" });
      setSessions((prev) => prev.filter((s) => s.user_id !== userId));
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
    setRevokeAllUser(null);
  };

  const roleBadge = (role: string) => {
    switch (role) {
      case "admin": return <Badge variant="destructive">{role}</Badge>;
      case "trader": return <Badge className="bg-blue-600">{role}</Badge>;
      default: return <Badge variant="secondary">{role}</Badge>;
    }
  };

  // Group sessions by user for the "revoke all" action
  const userSessionCounts: Record<number, { username: string; count: number }> = {};
  sessions.forEach((s) => {
    if (!userSessionCounts[s.user_id]) {
      userSessionCounts[s.user_id] = { username: s.username, count: 0 };
    }
    userSessionCounts[s.user_id].count++;
  });

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full py-5 px-4 lg:px-8">
        <Header period={30} onPeriodChange={() => {}} onRefresh={fetchSessions} onQuickTrade={() => setQuickTradeOpen(true)} />

        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/admin"><ArrowLeft className="h-4 w-4 mr-1" />Admin</Link>
          </Button>
          <Shield className="h-6 w-6 text-red-500" />
          <h2 className="text-2xl font-bold">Active Sessions</h2>
          <div className="ml-auto">
            <Button variant="outline" size="sm" onClick={fetchSessions} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-1 ${loading ? "animate-spin" : ""}`} />Refresh
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-3xl font-bold">{sessions.length}</p>
              <p className="text-sm text-muted-foreground">Active Sessions</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-3xl font-bold">{Object.keys(userSessionCounts).length}</p>
              <p className="text-sm text-muted-foreground">Unique Users</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-3xl font-bold">
                {sessions.filter((s) => s.role === "admin").length}
              </p>
              <p className="text-sm text-muted-foreground">Admin Sessions</p>
            </CardContent>
          </Card>
        </div>

        {/* Sessions Table */}
        <Card>
          <CardHeader>
            <CardTitle>Session List</CardTitle>
            <CardDescription>Active refresh token sessions</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Expires</TableHead>
                  <TableHead>Device</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.length === 0 && !loading && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                      No active sessions found
                    </TableCell>
                  </TableRow>
                )}
                {sessions.map((session) => (
                  <TableRow key={session.id}>
                    <TableCell className="font-medium">{session.username}</TableCell>
                    <TableCell>{roleBadge(session.role)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(session.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(session.expires_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {session.device_info || "—"}
                    </TableCell>
                    <TableCell className="text-right space-x-1">
                      <Button variant="ghost" size="icon" title="Revoke session"
                        onClick={() => setRevokeTarget(session)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                      {userSessionCounts[session.user_id]?.count > 1 && (
                        <Button variant="ghost" size="icon" title="Revoke all sessions for user"
                          onClick={() => setRevokeAllUser({ user_id: session.user_id, username: session.username })}>
                          <UserX className="h-4 w-4 text-orange-500" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Revoke Single Session Dialog */}
        <Dialog open={!!revokeTarget} onOpenChange={(o) => !o && setRevokeTarget(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Revoke Session</DialogTitle>
              <DialogDescription>
                This will immediately revoke {revokeTarget?.username}&apos;s session.
                They will need to log in again.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setRevokeTarget(null)}>Cancel</Button>
              <Button variant="destructive" onClick={() => revokeTarget && revokeSession(revokeTarget.id)}>
                Revoke
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Revoke All Sessions Dialog */}
        <Dialog open={!!revokeAllUser} onOpenChange={(o) => !o && setRevokeAllUser(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Revoke All Sessions</DialogTitle>
              <DialogDescription>
                This will revoke ALL {revokeAllUser && userSessionCounts[revokeAllUser.user_id]?.count} active
                sessions for <strong>{revokeAllUser?.username}</strong>. They will be logged out everywhere.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setRevokeAllUser(null)}>Cancel</Button>
              <Button variant="destructive" onClick={() => revokeAllUser && revokeAllForUser(revokeAllUser.user_id)}>
                Revoke All
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <QuickTradeModal open={quickTradeOpen} onClose={() => setQuickTradeOpen(false)} currencies={[]} onTrade={() => {}} />
      </div>
    </div>
  );
}

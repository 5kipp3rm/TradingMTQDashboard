/**
 * Admin: Account Ownership Management
 *
 * View all trading accounts with owner info, reassign ownership.
 */

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/dashboard/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { getAccessToken } from "@/lib/auth";
import { Wallet, RefreshCw, UserCheck, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "/api";

interface AccountWithOwner {
  id: string;
  account_number: number;
  account_name: string;
  broker: string;
  server: string;
  is_active: boolean;
  currency: string;
  initial_balance: number | null;
  owner_user_id: number | null;
  owner_username: string | null;
  created_at: string;
}

interface UserOption {
  id: number;
  username: string;
  role: string;
}

export default function AdminAccounts() {
  const { toast } = useToast();
  const [accounts, setAccounts] = useState<AccountWithOwner[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [reassignOpen, setReassignOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<AccountWithOwner | null>(null);
  const [newOwnerId, setNewOwnerId] = useState("");
  const [saving, setSaving] = useState(false);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);

  const headers = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${getAccessToken()}`,
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [accRes, usersRes] = await Promise.all([
        fetch(`${API}/v2/accounts/admin/all`, { headers: headers() }),
        fetch(`${API}/v2/users/`, { headers: headers() }),
      ]);
      if (accRes.ok) {
        const data = await accRes.json();
        setAccounts(data.items || []);
      }
      if (usersRes.ok) {
        setUsers(await usersRes.json());
      }
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleReassign = async () => {
    if (!selectedAccount || !newOwnerId) return;
    setSaving(true);
    try {
      const res = await fetch(`${API}/v2/accounts/${selectedAccount.id}/reassign`, {
        method: "PUT",
        headers: headers(),
        body: JSON.stringify({ new_owner_user_id: parseInt(newOwnerId) }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to reassign");
      }
      toast({ title: "Success", description: "Account ownership reassigned." });
      setReassignOpen(false);
      fetchData();
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full py-5 px-4 lg:px-8">
        <Header period={30} onPeriodChange={() => {}} onRefresh={fetchData} onQuickTrade={() => setQuickTradeOpen(true)} />

        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/admin"><ArrowLeft className="h-4 w-4 mr-1" />Admin</Link>
          </Button>
          <Wallet className="h-6 w-6 text-amber-500" />
          <h2 className="text-2xl font-bold">Account Ownership</h2>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? "animate-spin" : ""}`} />Refresh
          </Button>
        </div>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account</TableHead>
                  <TableHead>Broker</TableHead>
                  <TableHead>Currency</TableHead>
                  <TableHead>Balance</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.length === 0 && !loading && (
                  <TableRow><TableCell colSpan={7} className="text-center py-8 text-muted-foreground">No accounts found</TableCell></TableRow>
                )}
                {accounts.map((acc) => (
                  <TableRow key={acc.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{acc.account_name}</p>
                        <p className="text-xs text-muted-foreground">#{acc.account_number}</p>
                      </div>
                    </TableCell>
                    <TableCell>{acc.broker}</TableCell>
                    <TableCell>{acc.currency}</TableCell>
                    <TableCell className="font-mono">{acc.initial_balance != null ? `$${acc.initial_balance.toLocaleString()}` : "—"}</TableCell>
                    <TableCell>
                      <Badge variant={acc.is_active ? "default" : "secondary"}>{acc.is_active ? "Active" : "Inactive"}</Badge>
                    </TableCell>
                    <TableCell>
                      {acc.owner_username ? (
                        <Badge variant="outline">{acc.owner_username}</Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">Unassigned</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => { setSelectedAccount(acc); setNewOwnerId(acc.owner_user_id?.toString() || ""); setReassignOpen(true); }}
                      >
                        <UserCheck className="h-4 w-4 mr-1" />Reassign
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Dialog open={reassignOpen} onOpenChange={setReassignOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reassign Account Owner</DialogTitle>
              <DialogDescription>
                Change the owner of "{selectedAccount?.account_name}"
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-2">
              <Select value={newOwnerId} onValueChange={setNewOwnerId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select new owner" />
                </SelectTrigger>
                <SelectContent>
                  {users.map((u) => (
                    <SelectItem key={u.id} value={u.id.toString()}>
                      {u.username} ({u.role})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setReassignOpen(false)}>Cancel</Button>
                <Button onClick={handleReassign} disabled={saving || !newOwnerId}>
                  {saving ? "Saving..." : "Reassign"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <QuickTradeModal open={quickTradeOpen} onClose={() => setQuickTradeOpen(false)} currencies={[]} onTrade={() => {}} />
      </div>
    </div>
  );
}

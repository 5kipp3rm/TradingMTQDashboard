/**
 * User Management Page (Admin Only)
 *
 * CRUD interface for managing users via /api/v2/users endpoints.
 */

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/dashboard/Header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import {
  Users,
  Plus,
  Pencil,
  Trash2,
  KeyRound,
  Shield,
  ShieldCheck,
  Eye,
  Loader2,
} from "lucide-react";

// ============================================================================
// Types
// ============================================================================

interface UserData {
  id: number;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

// ============================================================================
// Component
// ============================================================================

export default function UserManagement() {
  const { toast } = useToast();
  const [users, setUsers] = useState<UserData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  // Dialog states
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [resetPwOpen, setResetPwOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserData | null>(null);

  // Form states
  const [formUsername, setFormUsername] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formRole, setFormRole] = useState("viewer");
  const [formIsActive, setFormIsActive] = useState(true);
  const [formResetPassword, setFormResetPassword] = useState("");
  const [formMustChange, setFormMustChange] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // ---------------------------------------------------------------
  // Fetch users
  // ---------------------------------------------------------------

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await apiClient.get<UserData[]>("/v2/users");
      setUsers(data);
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Failed to load users",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // ---------------------------------------------------------------
  // Create user
  // ---------------------------------------------------------------

  const handleCreate = async () => {
    setIsSaving(true);
    try {
      await apiClient.post("/v2/users", {
        username: formUsername,
        password: formPassword,
        email: formEmail || null,
        role: formRole,
      });
      toast({ title: "User created", description: `User "${formUsername}" created successfully.` });
      setCreateOpen(false);
      resetForm();
      fetchUsers();
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setIsSaving(false);
    }
  };

  // ---------------------------------------------------------------
  // Edit user
  // ---------------------------------------------------------------

  const openEdit = (user: UserData) => {
    setSelectedUser(user);
    setFormEmail(user.email || "");
    setFormRole(user.role);
    setFormIsActive(user.is_active);
    setEditOpen(true);
  };

  const handleEdit = async () => {
    if (!selectedUser) return;
    setIsSaving(true);
    try {
      await apiClient.put(`/v2/users/${selectedUser.id}`, {
        email: formEmail || null,
        role: formRole,
        is_active: formIsActive,
      });
      toast({ title: "User updated", description: `User "${selectedUser.username}" updated.` });
      setEditOpen(false);
      resetForm();
      fetchUsers();
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setIsSaving(false);
    }
  };

  // ---------------------------------------------------------------
  // Reset password
  // ---------------------------------------------------------------

  const openResetPw = (user: UserData) => {
    setSelectedUser(user);
    setFormResetPassword("");
    setFormMustChange(true);
    setResetPwOpen(true);
  };

  const handleResetPassword = async () => {
    if (!selectedUser) return;
    setIsSaving(true);
    try {
      await apiClient.post(`/v2/users/${selectedUser.id}/reset-password`, {
        new_password: formResetPassword,
        must_change_password: formMustChange,
      });
      toast({ title: "Password reset", description: `Password reset for "${selectedUser.username}".` });
      setResetPwOpen(false);
      resetForm();
      fetchUsers();
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setIsSaving(false);
    }
  };

  // ---------------------------------------------------------------
  // Delete user
  // ---------------------------------------------------------------

  const openDelete = (user: UserData) => {
    setSelectedUser(user);
    setDeleteOpen(true);
  };

  const handleDelete = async () => {
    if (!selectedUser) return;
    setIsSaving(true);
    try {
      await apiClient.delete(`/v2/users/${selectedUser.id}`);
      toast({ title: "User deleted", description: `User "${selectedUser.username}" deleted.` });
      setDeleteOpen(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setIsSaving(false);
    }
  };

  // ---------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------

  const resetForm = () => {
    setFormUsername("");
    setFormEmail("");
    setFormPassword("");
    setFormRole("viewer");
    setFormIsActive(true);
    setFormResetPassword("");
    setFormMustChange(true);
    setSelectedUser(null);
  };

  const roleBadge = (role: string) => {
    const variants: Record<string, { icon: typeof Shield; color: string }> = {
      admin: { icon: ShieldCheck, color: "bg-red-500/20 text-red-400 border-red-500/30" },
      trader: { icon: Shield, color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
      viewer: { icon: Eye, color: "bg-green-500/20 text-green-400 border-green-500/30" },
    };
    const v = variants[role] || variants.viewer;
    const Icon = v.icon;
    return (
      <Badge variant="outline" className={`gap-1 ${v.color}`}>
        <Icon className="h-3 w-3" />
        {role}
      </Badge>
    );
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    return new Date(dateStr).toLocaleString();
  };

  // ---------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------

  return (
    <div className="min-h-screen bg-background p-4 md:p-6 lg:p-8">
      <Header
        period={period}
        onPeriodChange={setPeriod}
        onRefresh={fetchUsers}
        onQuickTrade={() => {}}
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users className="h-6 w-6 text-primary" />
              <div>
                <CardTitle>User Management</CardTitle>
                <CardDescription>Manage users, roles, and access permissions</CardDescription>
              </div>
            </div>
            <Button onClick={() => { resetForm(); setCreateOpen(true); }} className="gap-2">
              <Plus className="h-4 w-4" />
              Add User
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Username</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                      No users found
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-mono text-sm">{user.id}</TableCell>
                      <TableCell className="font-medium">{user.username}</TableCell>
                      <TableCell className="text-muted-foreground">{user.email || "—"}</TableCell>
                      <TableCell>{roleBadge(user.role)}</TableCell>
                      <TableCell>
                        <Badge variant={user.is_active ? "default" : "secondary"}>
                          {user.is_active ? "Active" : "Inactive"}
                        </Badge>
                        {user.must_change_password && (
                          <Badge variant="outline" className="ml-1 text-yellow-500 border-yellow-500/30">
                            Must change pw
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(user.last_login_at)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(user.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" onClick={() => openEdit(user)} title="Edit user">
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => openResetPw(user)} title="Reset password">
                            <KeyRound className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => openDelete(user)} title="Delete user" className="text-destructive hover:text-destructive">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* ============================================================ */}
      {/* Create User Dialog */}
      {/* ============================================================ */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
            <DialogDescription>Add a new user to the system.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="create-username">Username</Label>
              <Input
                id="create-username"
                placeholder="john_doe"
                value={formUsername}
                onChange={(e) => setFormUsername(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-email">Email (optional)</Label>
              <Input
                id="create-email"
                type="email"
                placeholder="john@example.com"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-password">Password</Label>
              <Input
                id="create-password"
                type="password"
                placeholder="Min. 8 characters"
                value={formPassword}
                onChange={(e) => setFormPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-role">Role</Label>
              <Select value={formRole} onValueChange={setFormRole}>
                <SelectTrigger id="create-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="viewer">Viewer — Read-only access</SelectItem>
                  <SelectItem value="trader">Trader — Can manage trades</SelectItem>
                  <SelectItem value="admin">Admin — Full access</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!formUsername || !formPassword || isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Create User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ============================================================ */}
      {/* Edit User Dialog */}
      {/* ============================================================ */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User: {selectedUser?.username}</DialogTitle>
            <DialogDescription>Update user details and permissions.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="edit-email">Email</Label>
              <Input
                id="edit-email"
                type="email"
                placeholder="john@example.com"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-role">Role</Label>
              <Select value={formRole} onValueChange={setFormRole}>
                <SelectTrigger id="edit-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="viewer">Viewer</SelectItem>
                  <SelectItem value="trader">Trader</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-3">
              <Label htmlFor="edit-active">Active</Label>
              <input
                id="edit-active"
                type="checkbox"
                checked={formIsActive}
                onChange={(e) => setFormIsActive(e.target.checked)}
                className="h-4 w-4"
              />
              <span className="text-sm text-muted-foreground">
                {formIsActive ? "User can log in" : "User is locked out"}
              </span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)}>Cancel</Button>
            <Button onClick={handleEdit} disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ============================================================ */}
      {/* Reset Password Dialog */}
      {/* ============================================================ */}
      <Dialog open={resetPwOpen} onOpenChange={setResetPwOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Password: {selectedUser?.username}</DialogTitle>
            <DialogDescription>Set a new password for this user.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="reset-password">New Password</Label>
              <Input
                id="reset-password"
                type="password"
                placeholder="Min. 8 characters"
                value={formResetPassword}
                onChange={(e) => setFormResetPassword(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-3">
              <Label htmlFor="reset-must-change">Require password change on login</Label>
              <input
                id="reset-must-change"
                type="checkbox"
                checked={formMustChange}
                onChange={(e) => setFormMustChange(e.target.checked)}
                className="h-4 w-4"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setResetPwOpen(false)}>Cancel</Button>
            <Button onClick={handleResetPassword} disabled={!formResetPassword || formResetPassword.length < 8 || isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Reset Password
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ============================================================ */}
      {/* Delete Confirmation */}
      {/* ============================================================ */}
      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User: {selectedUser?.username}?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The user will be permanently removed and all their
              refresh tokens will be revoked.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

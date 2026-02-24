import { useState, type FormEvent } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { BarChart3, Users, Coins, Settings, LineChart, Bell, FileText, RefreshCw, Zap, Wallet, ScrollText, Brain, Shield, LogOut, User, KeyRound, UserCog, Home, Eye, EyeOff, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { useAccounts } from "@/contexts/AccountsContext";
import { useAuth } from "@/contexts/AuthContext";
import { authApi } from "@/lib/auth";
import { RoleGuard } from "@/components/RoleGuard";
import { DateRangePicker } from "@/components/dashboard/DateRangePicker";
import type { DateRange } from "@/types/trading";

interface HeaderProps {
  period: number;
  onPeriodChange: (period: number) => void;
  onRefresh: () => void;
  onQuickTrade: () => void;
  dateRange?: DateRange;
  onDateRangeChange?: (range: DateRange | undefined) => void;
}

const navItems = [
  { path: "/accounts", label: "Accounts", icon: Users },
  { path: "/currencies", label: "Currencies", icon: Coins },
  { path: "/strategies", label: "Strategies", icon: Brain },
  { path: "/config", label: "Settings", icon: Settings },
  { path: "/charts", label: "Charts", icon: LineChart },
  { path: "/alerts", label: "Alerts", icon: Bell },
  { path: "/reports", label: "Reports", icon: FileText },
  { path: "/logs", label: "Logs", icon: ScrollText },
  { path: "/admin", label: "Admin", icon: Shield, adminOnly: true },
];

export function Header({ 
  period, 
  onPeriodChange, 
  onRefresh, 
  onQuickTrade,
  dateRange,
  onDateRangeChange,
}: HeaderProps) {
  const location = useLocation();
  const { accounts, selectedAccountId, setSelectedAccountId } = useAccounts();
  const { user, logout, hasRole } = useAuth();
  const activeAccounts = accounts.filter(acc => acc.isActive);

  // ── Change Password Dialog State ──
  const [pwDialogOpen, setPwDialogOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [pwSaving, setPwSaving] = useState(false);
  const [pwSuccess, setPwSuccess] = useState("");
  const [pwError, setPwError] = useState("");

  const resetPwDialog = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setShowCurrentPw(false);
    setShowNewPw(false);
    setPwSaving(false);
    setPwSuccess("");
    setPwError("");
  };

  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setPwError("");
    setPwSuccess("");

    if (newPassword !== confirmPassword) {
      setPwError("New passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setPwError("Password must be at least 8 characters.");
      return;
    }

    setPwSaving(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      setPwSuccess("Password changed successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPwError(err instanceof Error ? err.message : "Failed to change password");
    } finally {
      setPwSaving(false);
    }
  };

  const roleBadgeColor = {
    admin: "bg-red-500/20 text-red-400",
    trader: "bg-blue-500/20 text-blue-400",
    viewer: "bg-green-500/20 text-green-400",
  }[user?.role ?? "viewer"];

  return (
    <header className="bg-card rounded-xl p-6 mb-5 shadow-lg">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-3">
          <BarChart3 className="h-8 w-8 text-primary" />
          <h1 className="text-2xl font-bold text-foreground">TradingMTQ Analytics</h1>
        </Link>
        
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={onQuickTrade} className="gap-2">
            <Zap className="h-4 w-4" />
            Quick Trade
          </Button>
          
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            // Hide admin-only nav items from non-admin users
            if (item.adminOnly && !hasRole("admin")) {
              return null;
            }

            return (
              <Button
                key={item.path}
                variant={isActive ? "secondary" : "ghost"}
                size="sm"
                asChild
              >
                <Link to={item.path} className="gap-2">
                  <Icon className="h-4 w-4" />
                  <span className="hidden lg:inline">{item.label}</span>
                </Link>
              </Button>
            );
          })}
          
          <Select value={selectedAccountId} onValueChange={setSelectedAccountId}>
            <SelectTrigger className="w-[200px]">
              <Wallet className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Select Account" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Accounts</SelectItem>
              {activeAccounts.map((account) => (
                <SelectItem key={account.id} value={account.id}>
                  {account.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select 
            value={dateRange ? "custom" : period.toString()} 
            onValueChange={(v) => {
              if (v === "custom") {
                const to = new Date();
                const from = new Date();
                from.setDate(from.getDate() - 30);
                onDateRangeChange?.({ from, to });
                return;
              }
              onDateRangeChange?.(undefined);
              onPeriodChange(Number(v));
            }}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 Days</SelectItem>
              <SelectItem value="30">Last 30 Days</SelectItem>
              <SelectItem value="90">Last 90 Days</SelectItem>
              <SelectItem value="365">Last Year</SelectItem>
              <SelectItem value="custom">Custom Range</SelectItem>
            </SelectContent>
          </Select>

          {dateRange !== undefined && (
            <DateRangePicker
              dateRange={dateRange}
              onDateRangeChange={(range) => onDateRangeChange?.(range)}
            />
          )}
          
          <Button variant="outline" size="icon" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>

          {/* User menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2 ml-2">
                <User className="h-4 w-4" />
                <span className="hidden md:inline">{user?.username}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="flex flex-col gap-1">
                <span className="font-semibold">{user?.username}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full w-fit ${roleBadgeColor}`}>
                  {user?.role}
                </span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer gap-2" asChild>
                <Link to="/">
                  <Home className="h-4 w-4" />
                  Back to Home
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer gap-2" asChild>
                <Link to="/settings">
                  <UserCog className="h-4 w-4" />
                  Account Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer gap-2" onClick={() => { resetPwDialog(); setPwDialogOpen(true); }}>
                <KeyRound className="h-4 w-4" />
                Change Password
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer gap-2 text-destructive focus:text-destructive" onClick={logout}>
                <LogOut className="h-4 w-4" />
                Log Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Change Password Dialog */}
      <Dialog open={pwDialogOpen} onOpenChange={(open) => { setPwDialogOpen(open); if (!open) resetPwDialog(); }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5" />
              Change Password
            </DialogTitle>
            <DialogDescription>
              Enter your current password and choose a new one.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handlePasswordSubmit} className="space-y-4 mt-2">
            {pwSuccess && (
              <Alert className="border-green-500/50 bg-green-500/10">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <AlertDescription className="text-green-400">{pwSuccess}</AlertDescription>
              </Alert>
            )}
            {pwError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{pwError}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="header-current-pw">Current Password</Label>
              <div className="relative">
                <Input
                  id="header-current-pw"
                  type={showCurrentPw ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                  onClick={() => setShowCurrentPw(!showCurrentPw)}
                >
                  {showCurrentPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="header-new-pw">New Password</Label>
              <div className="relative">
                <Input
                  id="header-new-pw"
                  type={showNewPw ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                  onClick={() => setShowNewPw(!showNewPw)}
                >
                  {showNewPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                At least 8 characters with uppercase, lowercase, and a number.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="header-confirm-pw">Confirm New Password</Label>
              <Input
                id="header-confirm-pw"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setPwDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={pwSaving || !currentPassword || !newPassword || !confirmPassword}>
                {pwSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Change Password
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </header>
  );
}

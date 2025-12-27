import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BarChart3, Users, Coins, Settings, LineChart, Bell, FileText, RefreshCw, Zap, Wallet } from "lucide-react";
import { useAccounts } from "@/contexts/AccountsContext";

interface HeaderProps {
  period: number;
  onPeriodChange: (period: number) => void;
  onRefresh: () => void;
  onQuickTrade: () => void;
}

const navItems = [
  { path: "/accounts", label: "Accounts", icon: Users },
  { path: "/currencies", label: "Strategies", icon: Coins },
  { path: "/config", label: "Settings", icon: Settings },
  { path: "/charts", label: "Charts", icon: LineChart },
  { path: "/alerts", label: "Alerts", icon: Bell },
  { path: "/reports", label: "Reports", icon: FileText },
];

export function Header({ 
  period, 
  onPeriodChange, 
  onRefresh, 
  onQuickTrade,
}: HeaderProps) {
  const location = useLocation();
  const { accounts, selectedAccountId, setSelectedAccountId } = useAccounts();
  const activeAccounts = accounts.filter(acc => acc.isActive);

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
          
          <Select value={period.toString()} onValueChange={(v) => onPeriodChange(Number(v))}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 Days</SelectItem>
              <SelectItem value="30">Last 30 Days</SelectItem>
              <SelectItem value="90">Last 90 Days</SelectItem>
              <SelectItem value="365">Last Year</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" size="icon" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}

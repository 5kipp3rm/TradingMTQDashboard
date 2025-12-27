import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Header } from "@/components/dashboard/Header";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { AddAccountModal } from "@/components/accounts/AddAccountModal";
import { Plus, Edit, Trash2, Check, Link, Eye } from "lucide-react";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import type { CurrencyPair } from "@/types/trading";

const mockAccounts = [
  { id: "1", name: "Main Trading", broker: "IC Markets", balance: 10500.50, equity: 10750.25, isActive: true },
  { id: "2", name: "Scalping Account", broker: "Pepperstone", balance: 5200.00, equity: 5180.75, isActive: false },
  { id: "3", name: "Swing Trading", broker: "OANDA", balance: 25000.00, equity: 25500.00, isActive: false },
];

const mockCurrencies: CurrencyPair[] = [
  { symbol: "EURUSD", description: "Euro/US Dollar", bid: 1.08520, ask: 1.08535, spread: 1.5, enabled: true },
  { symbol: "GBPUSD", description: "British Pound/US Dollar", bid: 1.26340, ask: 1.26360, spread: 2.0, enabled: true },
  { symbol: "USDJPY", description: "US Dollar/Japanese Yen", bid: 149.850, ask: 149.865, spread: 1.5, enabled: true },
];

const Accounts = () => {
  const [accounts, setAccounts] = useState(mockAccounts);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);
  const [addAccountOpen, setAddAccountOpen] = useState(false);
  const { toast } = useToast();

  const handleAddAccount = (account: { 
    name: string; 
    loginNumber: string; 
    platform: string; 
    server: string; 
    password: string; 
    broker: string; 
    isDemo: boolean; 
    isDefault: boolean; 
  }) => {
    const newAccount = {
      id: Date.now().toString(),
      name: account.name,
      broker: account.broker || "Unknown",
      platform: account.platform,
      server: account.server,
      isDemo: account.isDemo,
      balance: 0,
      equity: 0,
      isActive: account.isDefault,
    };
    
    // If setting as default, make all others inactive
    if (account.isDefault) {
      setAccounts(prev => [...prev.map(acc => ({ ...acc, isActive: false })), newAccount]);
    } else {
      setAccounts([...accounts, newAccount]);
    }
    
    toast({
      title: "Account Added",
      description: `${account.name} has been added successfully.`,
    });
  };

  const handleConnect = (id: string) => {
    toast({
      title: "Connecting...",
      description: "Attempting to connect to the trading server.",
    });
  };

  const handleViewFull = (id: string) => {
    toast({
      title: "View Account",
      description: "Opening full account details.",
    });
  };

  const handleEdit = (id: string) => {
    toast({
      title: "Edit Account",
      description: "Opening account editor.",
    });
  };

  const handleDelete = (id: string) => {
    setAccounts(accounts.filter(acc => acc.id !== id));
    toast({
      title: "Account Deleted",
      description: "The account has been removed.",
    });
  };

  const handleQuickTrade = (params: { symbol: string; volume: number; type: "buy" | "sell" }) => {
    toast({
      title: "Trade Executed",
      description: `${params.type.toUpperCase()} ${params.volume} lots of ${params.symbol}`,
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={30}
          onPeriodChange={() => {}}
          onRefresh={() => {}}
          onQuickTrade={() => setQuickTradeOpen(true)}
        />

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Trading Accounts</h2>
          <Button onClick={() => setAddAccountOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Account
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {accounts.map((account) => (
            <Card key={account.id} className={`card-glow ${account.isActive ? "ring-2 ring-primary" : ""}`}>
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{account.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">{account.broker}</p>
                </div>
                {account.isActive && (
                  <Badge variant="default" className="bg-success">
                    <Check className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Balance</span>
                    <span className="font-mono font-semibold">${account.balance.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Equity</span>
                    <span className="font-mono font-semibold">${account.equity.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">P/L</span>
                    <span className={`font-mono font-semibold ${account.equity >= account.balance ? "text-profit" : "text-loss"}`}>
                      ${(account.equity - account.balance).toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
                  <div className="flex gap-1">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => handleConnect(account.id)}
                      title="Connect"
                    >
                      <Link className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => handleEdit(account.id)}
                      title="Edit"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => handleViewFull(account.id)}
                      title="View Full"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="text-destructive hover:text-destructive"
                    onClick={() => handleDelete(account.id)}
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <QuickTradeModal
          open={quickTradeOpen}
          onClose={() => setQuickTradeOpen(false)}
          currencies={mockCurrencies}
          onTrade={handleQuickTrade}
        />

        <AddAccountModal
          open={addAccountOpen}
          onClose={() => setAddAccountOpen(false)}
          onAdd={handleAddAccount}
        />
      </div>
    </div>
  );
};

export default Accounts;

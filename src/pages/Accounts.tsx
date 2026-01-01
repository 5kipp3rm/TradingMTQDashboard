import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Header } from "@/components/dashboard/Header";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { AddAccountModal } from "@/components/accounts/AddAccountModal";
import { EditAccountModal } from "@/components/accounts/EditAccountModal";
import { ViewAccountModal } from "@/components/accounts/ViewAccountModal";
import { Plus, Edit, Trash2, Check, Link, Eye } from "lucide-react";
import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { useAccounts } from "@/contexts/AccountsContext";
import { accountsApi, accountConnectionsApi, currenciesApi } from "@/lib/api";
import type { CurrencyPair, Account } from "@/types/trading";

const Accounts = () => {
  const { accounts, refreshAccounts, isLoading } = useAccounts();
  const [currencies, setCurrencies] = useState<CurrencyPair[]>([]);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);
  const [addAccountOpen, setAddAccountOpen] = useState(false);
  const [editAccountOpen, setEditAccountOpen] = useState(false);
  const [viewAccountOpen, setViewAccountOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const fetchCurrencies = async () => {
      const response = await currenciesApi.getAll();
      if (response.data) {
        const formattedCurrencies = (response.data as any).currencies?.map((c: any) => ({
          symbol: c.symbol,
          description: c.description || c.symbol,
          bid: c.bid || 0,
          ask: c.ask || 0,
          spread: c.spread || 0,
          enabled: c.enabled,
        })) || [];
        setCurrencies(formattedCurrencies);
      }
    };
    fetchCurrencies();
  }, []);

  const handleAddAccount = async (account: {
    name: string;
    loginNumber: string;
    platform: string;
    server: string;
    password: string;
    broker: string;
    isDemo: boolean;
    isDefault: boolean;
  }) => {
    const response = await accountsApi.create({
      account_name: account.name,
      account_number: parseInt(account.loginNumber, 10),
      broker: account.broker,
      server: account.server,
      platform_type: account.platform,
      login: parseInt(account.loginNumber, 10),
      password: account.password,
      is_demo: account.isDemo,
      is_active: true,
      is_default: account.isDefault,
      currency: 'USD',
    });
    
    if (response.data) {
      await refreshAccounts();
      toast({
        title: "Account Added",
        description: `${account.name} has been added successfully.`,
      });
    } else {
      toast({
        title: "Error",
        description: response.error || "Failed to add account",
        variant: "destructive",
      });
    }
  };

  const handleConnect = async (id: string) => {
    const response = await accountConnectionsApi.connect(parseInt(id, 10));
    if (response.data) {
      await refreshAccounts();
      toast({
        title: "Connected",
        description: "Successfully connected to the trading server.",
      });
    } else {
      toast({
        title: "Connection Failed",
        description: response.error || "Failed to connect to trading server",
        variant: "destructive",
      });
    }
  };

  const handleViewFull = (id: string) => {
    const account = accounts.find((a) => a.id === id);
    if (account) {
      setSelectedAccount(account);
      setViewAccountOpen(true);
    }
  };

  const handleEdit = (id: string) => {
    const account = accounts.find((a) => a.id === id);
    if (account) {
      setSelectedAccount(account);
      setEditAccountOpen(true);
    }
  };

  const handleSaveEdit = async (id: string, updates: any) => {
    const response = await accountsApi.update(parseInt(id, 10), updates);
    if (response.data) {
      await refreshAccounts();
      toast({
        title: "Account Updated",
        description: "Account has been updated successfully.",
      });
    } else {
      toast({
        title: "Error",
        description: response.error || "Failed to update account",
        variant: "destructive",
      });
    }
  };

  const handleDelete = async (id: string) => {
    const response = await accountsApi.delete(parseInt(id, 10));
    if (!response.error) {
      await refreshAccounts();
      toast({
        title: "Account Deleted",
        description: "The account has been removed.",
      });
    } else {
      toast({
        title: "Error",
        description: response.error || "Failed to delete account",
        variant: "destructive",
      });
    }
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
                    <span className="font-mono font-semibold">
                      ${account.initial_balance ? Number(account.initial_balance).toLocaleString() : '0.00'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Currency</span>
                    <span className="font-mono font-semibold">{account.currency || 'USD'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Broker</span>
                    <span className="font-mono text-sm">{account.broker}</span>
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
          currencies={currencies}
          onTrade={handleQuickTrade}
        />

        <AddAccountModal
          open={addAccountOpen}
          onClose={() => setAddAccountOpen(false)}
          onAdd={handleAddAccount}
        />

        <EditAccountModal
          open={editAccountOpen}
          onClose={() => {
            setEditAccountOpen(false);
            setSelectedAccount(null);
          }}
          account={selectedAccount}
          onSave={handleSaveEdit}
        />

        <ViewAccountModal
          open={viewAccountOpen}
          onClose={() => {
            setViewAccountOpen(false);
            setSelectedAccount(null);
          }}
          account={selectedAccount}
        />
      </div>
    </div>
  );
};

export default Accounts;

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/dashboard/Header";
import { PositionList } from "@/components/crypto/PositionList";
import { OrderForm } from "@/components/crypto/OrderForm";
import { MarketDataWidget } from "@/components/crypto/MarketDataWidget";
import { PerformanceMetrics } from "@/components/crypto/PerformanceMetrics";
import { useState } from "react";
import { useCryptoAccounts } from "@/hooks/useCryptoAPI";
import { useToast } from "@/hooks/use-toast";
import { AlertCircle, TrendingUp, Wallet } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const CryptoTrading = () => {
  const { data: accounts, isLoading } = useCryptoAccounts();
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const { toast } = useToast();

  // Filter active accounts
  const activeAccounts = accounts?.filter((acc) => acc.is_active) || [];

  // Auto-select first active account if none selected
  if (activeAccounts.length > 0 && selectedAccountId === null) {
    setSelectedAccountId(activeAccounts[0].account_id);
  }

  const selectedAccount = accounts?.find((acc) => acc.account_id === selectedAccountId);

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1600px]">
        <Header
          period={30}
          onPeriodChange={() => {}}
          onRefresh={() => {}}
          onQuickTrade={() => {}}
        />

        {/* Account Selection and Summary */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <TrendingUp className="h-6 w-6" />
              Crypto Trading Dashboard
            </h2>
            <Select
              value={selectedAccountId?.toString() || ""}
              onValueChange={(value) => setSelectedAccountId(parseInt(value, 10))}
            >
              <SelectTrigger className="w-[250px]">
                <Wallet className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Select Account" />
              </SelectTrigger>
              <SelectContent>
                {activeAccounts.map((account) => (
                  <SelectItem key={account.account_id} value={account.account_id.toString()}>
                    {account.account_name} ({account.exchange})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedAccount && (
            <Card className="card-glow">
              <CardContent className="py-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Exchange</p>
                    <div className="flex items-center gap-2 mt-1">
                      <p className="text-lg font-semibold">{selectedAccount.exchange}</p>
                      {selectedAccount.testnet && (
                        <Badge variant="outline" className="text-xs">
                          Testnet
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Assets</p>
                    <p className="text-lg font-semibold font-mono mt-1">
                      ${selectedAccount.balance_summary?.total_assets.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      }) || '0.00'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Connection</p>
                    <div className="mt-1">
                      <Badge
                        variant="outline"
                        className={
                          selectedAccount.connection_status === 'connected'
                            ? 'bg-success'
                            : 'bg-destructive'
                        }
                      >
                        {selectedAccount.connection_status}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Balances</p>
                    <p className="text-lg font-semibold mt-1">
                      {selectedAccount.balance_summary?.balances.length || 0} assets
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {selectedAccountId ? (
          <>
            {/* Performance Metrics */}
            <div className="mb-6">
              <PerformanceMetrics accountId={selectedAccountId} />
            </div>

            {/* Main Trading Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Positions (2/3 width) */}
              <div className="lg:col-span-2 space-y-6">
                <PositionList accountId={selectedAccountId} />
              </div>

              {/* Right Column: Trading Interface (1/3 width) */}
              <div className="space-y-6">
                <OrderForm accountId={selectedAccountId} />
                <MarketDataWidget />
              </div>
            </div>
          </>
        ) : (
          <Card className="card-glow">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Active Account Selected</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Please select a crypto trading account or create one to start trading
              </p>
              <Button onClick={() => (window.location.href = '/crypto-accounts')}>
                Go to Crypto Accounts
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default CryptoTrading;

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Header } from "@/components/dashboard/Header";
import { AddCurrencyModal } from "@/components/currencies/AddCurrencyModal";
import { useState, useEffect } from "react";
import { useAccounts } from "@/contexts/AccountsContext";
import { useToast } from "@/hooks/use-toast";
import { currenciesV2Api } from "@/lib/api-v2";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
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
import { ChevronDown, ChevronUp, Settings2, Plus, Trash2 } from "lucide-react";

interface CurrencyRisk {
  risk_percent: number;
  max_positions: number;
  stop_loss_pips: number;
  take_profit_pips: number;
}

interface CurrencyStrategy {
  strategy_type: string;
  timeframe: string;
  fast_period: number;
  slow_period: number;
}

interface CurrencyConfig {
  symbol: string;
  description: string;
  enabled: boolean;
  risk: CurrencyRisk;
  strategy: CurrencyStrategy;
}

interface AccountCurrencies {
  [accountId: string]: CurrencyConfig[];
}

export default function Currencies() {
  const { accounts, selectedAccountId, selectAccount } = useAccounts();
  const { toast } = useToast();

  // Strategy types will be loaded from API
  const [strategyTypes, setStrategyTypes] = useState<Array<{ value: string; label: string }>>([
    { value: "SimpleMA", label: "Simple MA Crossover" }, // Fallback default
  ]);

  // Load available strategies on mount
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v2/strategies/available');
        if (response.ok) {
          const data = await response.json();
          setStrategyTypes(data.strategies.map((s: any) => ({
            value: s.value,
            label: s.label
          })));
        }
      } catch (error) {
        console.error('Failed to load strategies:', error);
      }
    };
    loadStrategies();
  }, []);

  const timeframes = [
    { value: "M1", label: "1 Minute" },
    { value: "M5", label: "5 Minutes" },
    { value: "M15", label: "15 Minutes" },
    { value: "M30", label: "30 Minutes" },
    { value: "H1", label: "1 Hour" },
    { value: "H4", label: "4 Hours" },
    { value: "D1", label: "Daily" },
  ];

  const [currenciesPerAccount, setCurrenciesPerAccount] = useState<AccountCurrencies>({});
  const [isLoading, setIsLoading] = useState(true);
  const [expandedSymbol, setExpandedSymbol] = useState<string | null>(null);
  const [addCurrencyOpen, setAddCurrencyOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [currencyToDelete, setCurrencyToDelete] = useState<{ symbol: string; description: string } | null>(null);

  useEffect(() => {
    const fetchCurrencies = async () => {
      setIsLoading(true);
      try {
        // Fetch currencies for the selected account
        const accountIdToFetch = selectedAccountId === "all"
          ? (accounts[0]?.id ? Number(accounts[0].id) : null)
          : Number(selectedAccountId);

        if (!accountIdToFetch) {
          setIsLoading(false);
          return;
        }

        const response = await currenciesV2Api.getAll(accountIdToFetch);
        if (response.data) {
          const apiCurrencies = response.data || [];

          const formattedCurrencies: CurrencyConfig[] = apiCurrencies.map((c: any) => ({
            symbol: c.symbol,
            description: c.description || c.symbol,
            enabled: c.enabled !== undefined ? c.enabled : false,
            risk: {
              risk_percent: c.risk_percent || 1.0,
              max_positions: c.max_position_size || 3,
              stop_loss_pips: c.sl_pips || 50,
              take_profit_pips: c.tp_pips || 100,
            },
            strategy: {
              strategy_type: c.strategy_type || "SimpleMA",
              timeframe: c.timeframe || "M5",
              fast_period: c.fast_period || 10,
              slow_period: c.slow_period || 20,
            },
          }));

          setCurrenciesPerAccount((prev) => ({
            ...prev,
            [accountIdToFetch]: formattedCurrencies,
          }));
        } else {
          toast({
            title: "Error",
            description: response.error || "Failed to fetch currencies",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Failed to fetch currencies:", error);
        toast({
          title: "Error",
          description: "Failed to fetch currencies from API",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (accounts.length > 0) {
      fetchCurrencies();
    }
  }, [accounts, selectedAccountId, toast]);

  const currentAccountId = selectedAccountId === "all" ? accounts[0]?.id || "1" : selectedAccountId;
  const currencies = currenciesPerAccount[currentAccountId] || [];

  const toggleCurrency = async (symbol: string) => {
    const currency = currencies.find((c) => c.symbol === symbol);
    if (!currency) return;

    const newEnabled = !currency.enabled;
    const accountId = Number(currentAccountId);

    // Optimistic update
    setCurrenciesPerAccount((prev) => ({
      ...prev,
      [currentAccountId]: prev[currentAccountId].map((c) =>
        c.symbol === symbol ? { ...c, enabled: newEnabled } : c
      ),
    }));

    // Call per-account API to update enabled status
    try {
      const response = await currenciesV2Api.update(accountId, symbol, {
        symbol,
        enabled: newEnabled,
        strategy: {
          strategy_type: 'SimpleMA',
          params: {}
        },
        risk_percent: 1.0,
        sl_pips: 50,
        tp_pips: 100,
      });

      if (response.error) {
        // Revert on error
        setCurrenciesPerAccount((prev) => ({
          ...prev,
          [currentAccountId]: prev[currentAccountId].map((c) =>
            c.symbol === symbol ? { ...c, enabled: !newEnabled } : c
          ),
        }));
        toast({
          title: "Error",
          description: response.error || "Failed to update currency",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Failed to toggle currency:", error);
      // Revert on error
      setCurrenciesPerAccount((prev) => ({
        ...prev,
        [currentAccountId]: prev[currentAccountId].map((c) =>
          c.symbol === symbol ? { ...c, enabled: !newEnabled } : c
        ),
      }));
      toast({
        title: "Error",
        description: "Failed to update currency status",
        variant: "destructive",
      });
    }
  };

  const updateCurrencyRisk = (symbol: string, key: keyof CurrencyRisk, value: number) => {
    setCurrenciesPerAccount((prev) => ({
      ...prev,
      [currentAccountId]: prev[currentAccountId].map((c) =>
        c.symbol === symbol ? { ...c, risk: { ...c.risk, [key]: value } } : c
      ),
    }));
  };

  const updateCurrencyStrategy = (symbol: string, key: keyof CurrencyStrategy, value: string | number) => {
    setCurrenciesPerAccount((prev) => ({
      ...prev,
      [currentAccountId]: prev[currentAccountId].map((c) =>
        c.symbol === symbol ? { ...c, strategy: { ...c.strategy, [key]: value } } : c
      ),
    }));
  };

  const handleSave = async () => {
    const currenciesToSave = currencies;
    const accountId = Number(currentAccountId);

    try {
      // Save all currencies for this account
      const savePromises = currenciesToSave.map((currency) =>
        currenciesV2Api.update(accountId, currency.symbol, {
          symbol: currency.symbol,
          enabled: currency.enabled,
          risk_percent: currency.risk.risk_percent,
          max_position_size: currency.risk.max_positions,
          min_position_size: 0.01,
          strategy: {
            strategy_type: currency.strategy.strategy_type,
            params: {
              timeframe: currency.strategy.timeframe,
              fast_period: currency.strategy.fast_period,
              slow_period: currency.strategy.slow_period,
            }
          },
          timeframe: currency.strategy.timeframe,
          sl_pips: currency.risk.stop_loss_pips,
          tp_pips: currency.risk.take_profit_pips,
        })
      );

      const results = await Promise.all(savePromises);
      const errors = results.filter((r) => r.error);

      if (errors.length > 0) {
        toast({
          title: "Partial Save",
          description: `Saved ${results.length - errors.length} currencies, ${errors.length} failed`,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Settings Saved",
          description: "Currency settings have been saved successfully.",
        });
      }
    } catch (error) {
      console.error("Failed to save currencies:", error);
      toast({
        title: "Error",
        description: "Failed to save currency settings",
        variant: "destructive",
      });
    }
  };

  const handleAddCurrency = async (currency: {
    symbol: string;
    enabled: boolean;
    risk_percent: number;
    max_position_size: number;
    min_position_size: number;
    strategy_type: string;
    timeframe: string;
    fast_period: number;
    slow_period: number;
    sl_pips: number;
    tp_pips: number;
  }) => {
    const accountId = Number(currentAccountId);

    try {
      // Add currency to specific account (hybrid architecture - per-account config)
      const accountResponse = await currenciesV2Api.add(accountId, {
        symbol: currency.symbol,
        enabled: currency.enabled,
        risk_percent: currency.risk_percent,
        strategy: {
          strategy_type: currency.strategy_type,
          params: {}
        },
        sl_pips: currency.sl_pips,
        tp_pips: currency.tp_pips,
        timeframe: currency.timeframe,
        max_position_size: currency.max_position_size,
        min_position_size: currency.min_position_size,
        max_positions: currency.max_positions,
        allow_stacking: currency.allow_stacking,
      });

      if (accountResponse.error) {
        toast({
          title: "Error",
          description: accountResponse.error || "Failed to add currency to account",
          variant: "destructive",
        });
        return;
      }

      // Refresh currencies list
      const response = await currenciesV2Api.getAll(accountId);
      if (response.data) {
        const apiCurrencies = response.data || [];

        const formattedCurrencies: CurrencyConfig[] = apiCurrencies.map((c: any) => ({
          symbol: c.symbol,
          description: c.description || c.symbol,
          enabled: c.enabled !== undefined ? c.enabled : false,
          risk: {
            risk_percent: c.risk_percent || 1.0,
            max_positions: c.max_position_size || 3,
            stop_loss_pips: c.sl_pips || 50,
            take_profit_pips: c.tp_pips || 100,
          },
          strategy: {
            strategy_type: c.strategy_type || "SimpleMA",
            timeframe: c.timeframe || "M5",
            fast_period: c.fast_period || 10,
            slow_period: c.slow_period || 20,
          },
        }));

        setCurrenciesPerAccount((prev) => ({
          ...prev,
          [accountId]: formattedCurrencies,
        }));
      }

      toast({
        title: "Currency Added",
        description: `${currency.symbol} has been added successfully to ${selectedAccount?.name || "account"}.`,
      });
    } catch (error) {
      console.error("Failed to add currency:", error);
      toast({
        title: "Error",
        description: "Failed to add currency to account",
        variant: "destructive",
      });
    }
  };

  const handleDeleteCurrency = async () => {
    if (!currencyToDelete) return;

    const accountId = Number(currentAccountId);

    try {
      const response = await currenciesV2Api.remove(accountId, currencyToDelete.symbol);

      if (response.error) {
        toast({
          title: "Error",
          description: response.error || "Failed to delete currency",
          variant: "destructive",
        });
        return;
      }

      // Refresh currencies list
      const updatedResponse = await currenciesV2Api.getAll(accountId);
      if (updatedResponse.data) {
        const apiCurrencies = updatedResponse.data || [];

        const formattedCurrencies: CurrencyConfig[] = apiCurrencies.map((c: any) => ({
          symbol: c.symbol,
          description: c.description || c.symbol,
          enabled: c.enabled !== undefined ? c.enabled : false,
          risk: {
            risk_percent: c.risk_percent || 1.0,
            max_positions: c.max_position_size || 3,
            stop_loss_pips: c.sl_pips || 50,
            take_profit_pips: c.tp_pips || 100,
          },
          strategy: {
            strategy_type: c.strategy_type || "SimpleMA",
            timeframe: c.timeframe || "M5",
            fast_period: c.fast_period || 10,
            slow_period: c.slow_period || 20,
          },
        }));

        setCurrenciesPerAccount((prev) => ({
          ...prev,
          [accountId]: formattedCurrencies,
        }));
      }

      toast({
        title: "Currency Deleted",
        description: `${currencyToDelete.symbol} has been removed from ${selectedAccount?.name || "account"}.`,
      });
    } catch (error) {
      console.error("Failed to delete currency:", error);
      toast({
        title: "Error",
        description: "Failed to delete currency",
        variant: "destructive",
      });
    } finally {
      setDeleteDialogOpen(false);
      setCurrencyToDelete(null);
    }
  };

  const selectedAccount = accounts.find((acc) => acc.id === currentAccountId);

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={30}
          onPeriodChange={() => {}}
          onRefresh={() => {}}
          onQuickTrade={() => {}}
        />

        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Trading Strategies</h2>
            {selectedAccount && (
              <p className="text-sm text-muted-foreground">
                Configuring: {selectedAccount.name}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setAddCurrencyOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Currency
            </Button>
            <Button onClick={handleSave}>Save Changes</Button>
          </div>
        </div>

        <Card className="card-glow">
          <CardHeader>
            <CardTitle>Currency Pairs & Strategy Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {currencies.map((currency) => (
                <Collapsible
                  key={currency.symbol}
                  open={expandedSymbol === currency.symbol}
                  onOpenChange={(open) => setExpandedSymbol(open ? currency.symbol : null)}
                >
                  <div className="rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors overflow-hidden">
                    <div className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-4">
                        <Switch
                          checked={currency.enabled}
                          onCheckedChange={() => toggleCurrency(currency.symbol)}
                        />
                        <div>
                          <p className="font-semibold">{currency.symbol}</p>
                          <p className="text-sm text-muted-foreground">{currency.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right text-sm hidden sm:block">
                          <p className="text-muted-foreground">
                            {strategyTypes.find((s) => s.value === currency.strategy.strategy_type)?.label}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {currency.strategy.timeframe} • Risk: {currency.risk.risk_percent}%
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setCurrencyToDelete({ symbol: currency.symbol, description: currency.description });
                            setDeleteDialogOpen(true);
                          }}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                        <CollapsibleTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <Settings2 className="h-4 w-4 mr-1" />
                            {expandedSymbol === currency.symbol ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                          </Button>
                        </CollapsibleTrigger>
                      </div>
                    </div>

                    <CollapsibleContent>
                      <div className="border-t border-border/50 p-4 bg-muted/20">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {/* Risk Settings */}
                          <div className="space-y-4">
                            <h4 className="font-semibold text-sm flex items-center gap-2">
                              <span>⚠️</span> Risk Settings
                            </h4>
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <Label className="text-xs">Risk %</Label>
                                <Input
                                  type="number"
                                  step="0.1"
                                  min="0.1"
                                  max="10"
                                  value={currency.risk.risk_percent}
                                  onChange={(e) =>
                                    updateCurrencyRisk(currency.symbol, "risk_percent", Number(e.target.value))
                                  }
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Max Positions</Label>
                                <Input
                                  type="number"
                                  min="1"
                                  max="20"
                                  value={currency.risk.max_positions}
                                  onChange={(e) =>
                                    updateCurrencyRisk(currency.symbol, "max_positions", Number(e.target.value))
                                  }
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Stop Loss (pips)</Label>
                                <Input
                                  type="number"
                                  min="5"
                                  max="500"
                                  value={currency.risk.stop_loss_pips}
                                  onChange={(e) =>
                                    updateCurrencyRisk(currency.symbol, "stop_loss_pips", Number(e.target.value))
                                  }
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Take Profit (pips)</Label>
                                <Input
                                  type="number"
                                  min="5"
                                  max="1000"
                                  value={currency.risk.take_profit_pips}
                                  onChange={(e) =>
                                    updateCurrencyRisk(currency.symbol, "take_profit_pips", Number(e.target.value))
                                  }
                                />
                              </div>
                            </div>
                          </div>

                          {/* Strategy Settings */}
                          <div className="space-y-4">
                            <h4 className="font-semibold text-sm flex items-center gap-2">
                              <span>📈</span> Strategy Settings
                            </h4>
                            <div className="grid grid-cols-2 gap-3">
                              <div className="col-span-2">
                                <Label className="text-xs">Strategy Type</Label>
                                <Select
                                  value={currency.strategy.strategy_type}
                                  onValueChange={(value) =>
                                    updateCurrencyStrategy(currency.symbol, "strategy_type", value)
                                  }
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {strategyTypes.map((type) => (
                                      <SelectItem key={type.value} value={type.value}>
                                        {type.label}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label className="text-xs">Timeframe</Label>
                                <Select
                                  value={currency.strategy.timeframe}
                                  onValueChange={(value) =>
                                    updateCurrencyStrategy(currency.symbol, "timeframe", value)
                                  }
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {timeframes.map((tf) => (
                                      <SelectItem key={tf.value} value={tf.value}>
                                        {tf.label}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label className="text-xs">Fast Period</Label>
                                <Input
                                  type="number"
                                  min="2"
                                  max="100"
                                  value={currency.strategy.fast_period}
                                  onChange={(e) =>
                                    updateCurrencyStrategy(currency.symbol, "fast_period", Number(e.target.value))
                                  }
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Slow Period</Label>
                                <Input
                                  type="number"
                                  min="5"
                                  max="200"
                                  value={currency.strategy.slow_period}
                                  onChange={(e) =>
                                    updateCurrencyStrategy(currency.symbol, "slow_period", Number(e.target.value))
                                  }
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CollapsibleContent>
                  </div>
                </Collapsible>
              ))}
            </div>
          </CardContent>
        </Card>

        <AddCurrencyModal
          open={addCurrencyOpen}
          onClose={() => setAddCurrencyOpen(false)}
          onAdd={handleAddCurrency}
        />

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Currency Pair</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete <strong>{currencyToDelete?.symbol}</strong>{" "}
                ({currencyToDelete?.description}) from {selectedAccount?.name || "this account"}?
                <br />
                <br />
                This action cannot be undone. All configuration settings for this currency pair will be removed.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeleteCurrency}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}

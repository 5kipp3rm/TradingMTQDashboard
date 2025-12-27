import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Header } from "@/components/dashboard/Header";
import { useState } from "react";
import { useAccounts } from "@/contexts/AccountsContext";
import { useToast } from "@/hooks/use-toast";
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
import { ChevronDown, ChevronUp, Settings2 } from "lucide-react";

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

const defaultCurrencies: CurrencyConfig[] = [
  {
    symbol: "EURUSD",
    description: "Euro / US Dollar",
    enabled: true,
    risk: { risk_percent: 1, max_positions: 3, stop_loss_pips: 50, take_profit_pips: 100 },
    strategy: { strategy_type: "simple_ma", timeframe: "M5", fast_period: 10, slow_period: 20 },
  },
  {
    symbol: "GBPUSD",
    description: "British Pound / US Dollar",
    enabled: true,
    risk: { risk_percent: 1, max_positions: 3, stop_loss_pips: 60, take_profit_pips: 120 },
    strategy: { strategy_type: "simple_ma", timeframe: "M15", fast_period: 8, slow_period: 21 },
  },
  {
    symbol: "USDJPY",
    description: "US Dollar / Japanese Yen",
    enabled: true,
    risk: { risk_percent: 1, max_positions: 3, stop_loss_pips: 40, take_profit_pips: 80 },
    strategy: { strategy_type: "rsi_divergence", timeframe: "H1", fast_period: 14, slow_period: 28 },
  },
  {
    symbol: "AUDUSD",
    description: "Australian Dollar / US Dollar",
    enabled: true,
    risk: { risk_percent: 0.5, max_positions: 2, stop_loss_pips: 45, take_profit_pips: 90 },
    strategy: { strategy_type: "breakout", timeframe: "M30", fast_period: 12, slow_period: 26 },
  },
  {
    symbol: "USDCAD",
    description: "US Dollar / Canadian Dollar",
    enabled: false,
    risk: { risk_percent: 1, max_positions: 3, stop_loss_pips: 50, take_profit_pips: 100 },
    strategy: { strategy_type: "simple_ma", timeframe: "M5", fast_period: 10, slow_period: 20 },
  },
  {
    symbol: "NZDUSD",
    description: "New Zealand Dollar / US Dollar",
    enabled: false,
    risk: { risk_percent: 1, max_positions: 3, stop_loss_pips: 50, take_profit_pips: 100 },
    strategy: { strategy_type: "simple_ma", timeframe: "M5", fast_period: 10, slow_period: 20 },
  },
  {
    symbol: "USDCHF",
    description: "US Dollar / Swiss Franc",
    enabled: false,
    risk: { risk_percent: 1, max_positions: 3, stop_loss_pips: 50, take_profit_pips: 100 },
    strategy: { strategy_type: "simple_ma", timeframe: "M5", fast_period: 10, slow_period: 20 },
  },
  {
    symbol: "XAUUSD",
    description: "Gold / US Dollar",
    enabled: true,
    risk: { risk_percent: 2, max_positions: 2, stop_loss_pips: 100, take_profit_pips: 200 },
    strategy: { strategy_type: "trend_following", timeframe: "H4", fast_period: 20, slow_period: 50 },
  },
];

const strategyTypes = [
  { value: "simple_ma", label: "Simple MA Crossover" },
  { value: "rsi_divergence", label: "RSI Divergence" },
  { value: "breakout", label: "Breakout Strategy" },
  { value: "trend_following", label: "Trend Following" },
  { value: "scalping", label: "Scalping" },
  { value: "mean_reversion", label: "Mean Reversion" },
];

const timeframes = [
  { value: "M1", label: "1 Minute" },
  { value: "M5", label: "5 Minutes" },
  { value: "M15", label: "15 Minutes" },
  { value: "M30", label: "30 Minutes" },
  { value: "H1", label: "1 Hour" },
  { value: "H4", label: "4 Hours" },
  { value: "D1", label: "Daily" },
];

const Currencies = () => {
  const { accounts, selectedAccountId } = useAccounts();
  const { toast } = useToast();
  const [currenciesPerAccount, setCurrenciesPerAccount] = useState<AccountCurrencies>({
    "1": [...defaultCurrencies],
    "2": [...defaultCurrencies],
    "3": [...defaultCurrencies],
  });
  const [expandedSymbol, setExpandedSymbol] = useState<string | null>(null);

  const currentAccountId = selectedAccountId === "all" ? "1" : selectedAccountId;
  const currencies = currenciesPerAccount[currentAccountId] || defaultCurrencies;

  const toggleCurrency = (symbol: string) => {
    setCurrenciesPerAccount((prev) => ({
      ...prev,
      [currentAccountId]: prev[currentAccountId].map((c) =>
        c.symbol === symbol ? { ...c, enabled: !c.enabled } : c
      ),
    }));
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

  const handleSave = () => {
    toast({
      title: "Settings Saved",
      description: "Currency settings have been saved successfully.",
    });
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
          <Button onClick={handleSave}>Save Changes</Button>
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
      </div>
    </div>
  );
};

export default Currencies;

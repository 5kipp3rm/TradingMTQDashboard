import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { currenciesV2Api } from "@/lib/api-v2";
import type { CurrencyConfig, StrategyConfigRequest } from "@/lib/api-v2";

interface CurrencyConfigModalProps {
  open: boolean;
  onClose: () => void;
  accountId: number;
  currency?: CurrencyConfig | null;
  onSuccess?: () => void;
}

interface StrategyParams {
  [key: string]: number;
}

const STRATEGY_TYPES = [
  { value: "SimpleMA", label: "Simple Moving Average", params: ["fast_period", "slow_period"] },
  { value: "RSI", label: "RSI Strategy", params: ["period", "overbought", "oversold"] },
  { value: "MACD", label: "MACD Strategy", params: ["fast_period", "slow_period", "signal_period"] },
  { value: "BBands", label: "Bollinger Bands", params: ["period", "std_dev"] },
  { value: "Stochastic", label: "Stochastic Oscillator", params: ["k_period", "d_period", "overbought", "oversold"] },
];

const TIMEFRAMES = [
  { value: "M1", label: "1 Minute" },
  { value: "M5", label: "5 Minutes" },
  { value: "M15", label: "15 Minutes" },
  { value: "M30", label: "30 Minutes" },
  { value: "H1", label: "1 Hour" },
  { value: "H4", label: "4 Hours" },
  { value: "D1", label: "1 Day" },
  { value: "W1", label: "1 Week" },
];

export const CurrencyConfigModal = ({
  open,
  onClose,
  accountId,
  currency,
  onSuccess,
}: CurrencyConfigModalProps) => {
  const { toast } = useToast();
  const isEdit = !!currency;

  // Form state
  const [symbol, setSymbol] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [strategyType, setStrategyType] = useState("SimpleMA");
  const [strategyParams, setStrategyParams] = useState<StrategyParams>({});
  const [riskPercent, setRiskPercent] = useState("1.0");
  const [timeframe, setTimeframe] = useState("H1");
  const [slPips, setSlPips] = useState("50");
  const [tpPips, setTpPips] = useState("100");
  const [maxPositionSize, setMaxPositionSize] = useState("1.0");
  const [minPositionSize, setMinPositionSize] = useState("0.01");
  const [maxPositions, setMaxPositions] = useState("5");
  const [allowStacking, setAllowStacking] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form when currency prop changes
  useEffect(() => {
    if (currency) {
      setSymbol(currency.symbol);
      setEnabled(currency.enabled);
      setStrategyType(currency.strategy_type);
      setStrategyParams(currency.strategy_params);
      setRiskPercent(currency.risk_percent.toString());
      setTimeframe(currency.timeframe);
      setSlPips(currency.sl_pips.toString());
      setTpPips(currency.tp_pips.toString());
      setMaxPositionSize(currency.max_position_size.toString());
      setMinPositionSize(currency.min_position_size.toString());
      setMaxPositions(currency.max_positions.toString());
      setAllowStacking(currency.allow_stacking);
    } else {
      // Reset form for new currency
      setSymbol("");
      setEnabled(true);
      setStrategyType("SimpleMA");
      setStrategyParams({ fast_period: 10, slow_period: 20 });
      setRiskPercent("1.0");
      setTimeframe("H1");
      setSlPips("50");
      setTpPips("100");
      setMaxPositionSize("1.0");
      setMinPositionSize("0.01");
      setMaxPositions("5");
      setAllowStacking(false);
    }
  }, [currency, open]);

  // Initialize default strategy params when strategy type changes
  useEffect(() => {
    const strategy = STRATEGY_TYPES.find((s) => s.value === strategyType);
    if (strategy && !isEdit) {
      const defaultParams: StrategyParams = {};

      if (strategyType === "SimpleMA") {
        defaultParams.fast_period = 10;
        defaultParams.slow_period = 20;
      } else if (strategyType === "RSI") {
        defaultParams.period = 14;
        defaultParams.overbought = 70;
        defaultParams.oversold = 30;
      } else if (strategyType === "MACD") {
        defaultParams.fast_period = 12;
        defaultParams.slow_period = 26;
        defaultParams.signal_period = 9;
      } else if (strategyType === "BBands") {
        defaultParams.period = 20;
        defaultParams.std_dev = 2;
      } else if (strategyType === "Stochastic") {
        defaultParams.k_period = 14;
        defaultParams.d_period = 3;
        defaultParams.overbought = 80;
        defaultParams.oversold = 20;
      }

      setStrategyParams(defaultParams);
    }
  }, [strategyType, isEdit]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const strategyConfig: StrategyConfigRequest = {
        strategy_type: strategyType,
        params: strategyParams,
      };

      if (isEdit) {
        // Update existing currency
        const response = await currenciesV2Api.update(accountId, symbol, {
          enabled,
          strategy: strategyConfig,
          risk_percent: parseFloat(riskPercent),
          timeframe,
          sl_pips: parseInt(slPips, 10),
          tp_pips: parseInt(tpPips, 10),
          max_position_size: parseFloat(maxPositionSize),
          min_position_size: parseFloat(minPositionSize),
          max_positions: parseInt(maxPositions, 10),
          allow_stacking: allowStacking,
        });

        if (response.data?.success) {
          toast({
            title: "Success",
            description: `Currency ${symbol} updated successfully`,
          });
          onSuccess?.();
          onClose();
        } else {
          toast({
            title: "Error",
            description: response.error || "Failed to update currency",
            variant: "destructive",
          });
        }
      } else {
        // Add new currency
        const response = await currenciesV2Api.add(accountId, {
          symbol: symbol.toUpperCase(),
          enabled,
          strategy: strategyConfig,
          risk_percent: parseFloat(riskPercent),
          timeframe,
          sl_pips: parseInt(slPips, 10),
          tp_pips: parseInt(tpPips, 10),
          max_position_size: parseFloat(maxPositionSize),
          min_position_size: parseFloat(minPositionSize),
          max_positions: parseInt(maxPositions, 10),
          allow_stacking: allowStacking,
        });

        if (response.data?.success) {
          toast({
            title: "Success",
            description: `Currency ${symbol} added successfully`,
          });
          onSuccess?.();
          onClose();
        } else {
          toast({
            title: "Error",
            description: response.error || "Failed to add currency",
            variant: "destructive",
          });
        }
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateStrategyParam = (paramName: string, value: string) => {
    setStrategyParams({
      ...strategyParams,
      [paramName]: parseFloat(value) || 0,
    });
  };

  const currentStrategy = STRATEGY_TYPES.find((s) => s.value === strategyType);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? `Edit ${symbol}` : "Add Currency"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Modify currency pair trading settings" : "Configure a new currency pair for trading"}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Symbol */}
          <div className="space-y-2">
            <Label htmlFor="symbol">Currency Symbol</Label>
            <Input
              id="symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="EURUSD"
              maxLength={6}
              disabled={isEdit}
              required
            />
            <p className="text-xs text-muted-foreground">
              6-letter currency pair (e.g., EURUSD, GBPUSD)
            </p>
          </div>

          {/* Enabled */}
          <div className="flex items-center space-x-2">
            <Switch id="enabled" checked={enabled} onCheckedChange={setEnabled} />
            <Label htmlFor="enabled">Enabled</Label>
          </div>

          {/* Strategy Configuration */}
          <div className="space-y-4 p-4 border rounded-lg">
            <h3 className="font-semibold">Strategy Configuration</h3>

            <div className="space-y-2">
              <Label htmlFor="strategy-type">Strategy Type</Label>
              <Select value={strategyType} onValueChange={setStrategyType}>
                <SelectTrigger id="strategy-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STRATEGY_TYPES.map((strategy) => (
                    <SelectItem key={strategy.value} value={strategy.value}>
                      {strategy.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Strategy Parameters */}
            {currentStrategy && (
              <div className="grid grid-cols-2 gap-4">
                {currentStrategy.params.map((paramName) => (
                  <div key={paramName} className="space-y-2">
                    <Label htmlFor={paramName}>
                      {paramName.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </Label>
                    <Input
                      id={paramName}
                      type="number"
                      value={strategyParams[paramName] || ""}
                      onChange={(e) => updateStrategyParam(paramName, e.target.value)}
                      required
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Risk Management */}
          <div className="space-y-4 p-4 border rounded-lg">
            <h3 className="font-semibold">Risk Management</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="risk-percent">Risk Per Trade (%)</Label>
                <Input
                  id="risk-percent"
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10"
                  value={riskPercent}
                  onChange={(e) => setRiskPercent(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="timeframe">Timeframe</Label>
                <Select value={timeframe} onValueChange={setTimeframe}>
                  <SelectTrigger id="timeframe">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEFRAMES.map((tf) => (
                      <SelectItem key={tf.value} value={tf.value}>
                        {tf.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="sl-pips">Stop Loss (pips)</Label>
                <Input
                  id="sl-pips"
                  type="number"
                  min="1"
                  value={slPips}
                  onChange={(e) => setSlPips(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="tp-pips">Take Profit (pips)</Label>
                <Input
                  id="tp-pips"
                  type="number"
                  min="1"
                  value={tpPips}
                  onChange={(e) => setTpPips(e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* Position Management */}
          <div className="space-y-4 p-4 border rounded-lg">
            <h3 className="font-semibold">Position Management</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="max-position">Max Position Size (lots)</Label>
                <Input
                  id="max-position"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={maxPositionSize}
                  onChange={(e) => setMaxPositionSize(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="min-position">Min Position Size (lots)</Label>
                <Input
                  id="min-position"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={minPositionSize}
                  onChange={(e) => setMinPositionSize(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-positions">Max Positions</Label>
                <Input
                  id="max-positions"
                  type="number"
                  min="1"
                  value={maxPositions}
                  onChange={(e) => setMaxPositions(e.target.value)}
                  required
                />
              </div>

              <div className="flex items-center space-x-2 pt-8">
                <Switch
                  id="allow-stacking"
                  checked={allowStacking}
                  onCheckedChange={setAllowStacking}
                />
                <Label htmlFor="allow-stacking">Allow Stacking</Label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : isEdit ? "Update" : "Add Currency"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

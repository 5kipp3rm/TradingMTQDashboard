import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Plus, Loader2 } from "lucide-react";

interface AddCurrencyModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (currency: {
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
  }) => void;
}

// These will be loaded dynamically from the API
interface StrategyType {
  value: string;
  label: string;
  description?: string;
}

interface Timeframe {
  value: string;
  label: string;
  minutes?: number;
}

interface AvailableCurrency {
  id: number;
  symbol: string;
  description: string;
  category: string;
  base_currency: string;
  quote_currency: string;
  pip_value: number;
  decimal_places: number;
  min_lot_size: number;
  max_lot_size: number;
  typical_spread: number | null;
  is_active: boolean;
}

const currencyCategories = [
  { value: "all", label: "All Categories" },
  { value: "major", label: "Major Pairs" },
  { value: "cross", label: "Cross Pairs" },
  { value: "exotic", label: "Exotic Pairs" },
  { value: "commodity", label: "Commodities" },
  { value: "crypto", label: "Cryptocurrencies" },
  { value: "index", label: "Indices" },
];

export function AddCurrencyModal({ open, onClose, onAdd }: AddCurrencyModalProps) {
  const [symbol, setSymbol] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [riskPercent, setRiskPercent] = useState(1.0);
  const [maxPositionSize, setMaxPositionSize] = useState(0.1);
  const [minPositionSize, setMinPositionSize] = useState(0.01);
  const [strategyType, setStrategyType] = useState("SimpleMA");
  const [timeframe, setTimeframe] = useState("M5");
  const [fastPeriod, setFastPeriod] = useState(10);
  const [slowPeriod, setSlowPeriod] = useState(20);
  const [slPips, setSlPips] = useState(50);
  const [tpPips, setTpPips] = useState(100);

  const [selectedCategory, setSelectedCategory] = useState("all");
  const [availableCurrencies, setAvailableCurrencies] = useState<AvailableCurrency[]>([]);
  const [isLoadingCurrencies, setIsLoadingCurrencies] = useState(false);

  // Dynamic data from API
  const [strategyTypes, setStrategyTypes] = useState<StrategyType[]>([]);
  const [timeframes, setTimeframes] = useState<Timeframe[]>([]);
  const [isLoadingStrategies, setIsLoadingStrategies] = useState(false);

  // Load strategies and timeframes on mount
  useEffect(() => {
    const loadMetadata = async () => {
      setIsLoadingStrategies(true);
      try {
        // Load strategies
        const strategiesResponse = await fetch('http://localhost:8000/api/v2/strategies/available');
        if (strategiesResponse.ok) {
          const strategiesData = await strategiesResponse.json();
          setStrategyTypes(strategiesData.strategies.map((s: any) => ({
            value: s.value,
            label: s.label,
            description: s.description
          })));
        }

        // Load timeframes
        const timeframesResponse = await fetch('http://localhost:8000/api/v2/strategies/timeframes');
        if (timeframesResponse.ok) {
          const timeframesData = await timeframesResponse.json();
          setTimeframes(timeframesData.timeframes);
        }
      } catch (error) {
        console.error("Failed to load strategies/timeframes:", error);
        // Fallback to defaults if API fails
        setStrategyTypes([{ value: "SimpleMA", label: "Simple MA Crossover" }]);
        setTimeframes([{ value: "M5", label: "5 Minutes" }]);
      } finally {
        setIsLoadingStrategies(false);
      }
    };

    loadMetadata();
  }, []); // Load once on mount

  // Load available currencies from API when modal opens or category changes
  useEffect(() => {
    if (open) {
      loadAvailableCurrencies(selectedCategory);
    }
  }, [open, selectedCategory]);

  const loadAvailableCurrencies = async (category: string) => {
    setIsLoadingCurrencies(true);
    try {
      // TODO: Migrate to v2 API - need endpoint for available currency symbols
      // For now, use hardcoded common forex pairs
      const commonPairs = [
        { id: 1, symbol: "EURUSD", description: "Euro vs US Dollar", category: "major", base_currency: "EUR", quote_currency: "USD", pip_value: 0.0001, decimal_places: 5, min_lot_size: 0.01, max_lot_size: 100, typical_spread: 1.5, is_active: true },
        { id: 2, symbol: "GBPUSD", description: "British Pound vs US Dollar", category: "major", base_currency: "GBP", quote_currency: "USD", pip_value: 0.0001, decimal_places: 5, min_lot_size: 0.01, max_lot_size: 100, typical_spread: 2.0, is_active: true },
        { id: 3, symbol: "USDJPY", description: "US Dollar vs Japanese Yen", category: "major", base_currency: "USD", quote_currency: "JPY", pip_value: 0.01, decimal_places: 3, min_lot_size: 0.01, max_lot_size: 100, typical_spread: 1.8, is_active: true },
        { id: 4, symbol: "AUDUSD", description: "Australian Dollar vs US Dollar", category: "major", base_currency: "AUD", quote_currency: "USD", pip_value: 0.0001, decimal_places: 5, min_lot_size: 0.01, max_lot_size: 100, typical_spread: 2.2, is_active: true },
      ];
      const filtered = category === "all" ? commonPairs : commonPairs.filter(p => p.category === category);
      setAvailableCurrencies(filtered);
    } catch (error) {
      console.error("Failed to load available currencies:", error);
    } finally {
      setIsLoadingCurrencies(false);
    }
  };

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    setSymbol(""); // Clear selected symbol when category changes
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd({
      symbol: symbol.toUpperCase(),
      enabled,
      risk_percent: riskPercent,
      max_position_size: maxPositionSize,
      min_position_size: minPositionSize,
      strategy_type: strategyType,
      timeframe,
      fast_period: fastPeriod,
      slow_period: slowPeriod,
      sl_pips: slPips,
      tp_pips: tpPips,
    });
    resetForm();
    onClose();
  };

  const resetForm = () => {
    setSymbol("");
    setSelectedCategory("all");
    setEnabled(true);
    setRiskPercent(1.0);
    setMaxPositionSize(0.1);
    setMinPositionSize(0.01);
    setStrategyType("SimpleMA");
    setTimeframe("M5");
    setFastPeriod(10);
    setSlowPeriod(20);
    setSlPips(50);
    setTpPips(100);
  };

  const isValid = symbol && fastPeriod > 0 && slowPeriod > fastPeriod && slPips > 0 && tpPips > 0;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Add Currency Pair
          </DialogTitle>
          <DialogDescription>
            Select a currency pair category and configure trading parameters for your account.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Category Selection */}
          <div>
            <Label htmlFor="category">Category</Label>
            <Select value={selectedCategory} onValueChange={handleCategoryChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                {currencyCategories.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground mt-1">
              Filter currency pairs by category
            </p>
          </div>

          {/* Currency Symbol */}
          <div>
            <Label htmlFor="symbol">Currency Pair</Label>
            <Select value={symbol} onValueChange={setSymbol} disabled={isLoadingCurrencies}>
              <SelectTrigger>
                {isLoadingCurrencies ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading...
                  </span>
                ) : (
                  <SelectValue placeholder="Select a currency pair" />
                )}
              </SelectTrigger>
              <SelectContent>
                {availableCurrencies.length === 0 ? (
                  <div className="px-2 py-6 text-center text-sm text-muted-foreground">
                    No currencies available
                  </div>
                ) : (
                  availableCurrencies.map((currency) => (
                    <SelectItem key={currency.id} value={currency.symbol}>
                      <div className="flex flex-col">
                        <span className="font-medium">{currency.symbol}</span>
                        {currency.description && (
                          <span className="text-xs text-muted-foreground">
                            {currency.description}
                          </span>
                        )}
                      </div>
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
            {availableCurrencies.length > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {availableCurrencies.length} {selectedCategory !== "all" ? selectedCategory : "total"} pairs available
              </p>
            )}
          </div>

          {/* Enabled Checkbox */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="enabled"
              checked={enabled}
              onCheckedChange={(checked) => setEnabled(checked as boolean)}
            />
            <Label htmlFor="enabled" className="text-sm font-normal cursor-pointer">
              Enable trading for this currency pair
            </Label>
          </div>

          {/* Risk Settings */}
          <div className="space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <span>⚠️</span> Risk Management
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="riskPercent">Risk % per Trade</Label>
                <Input
                  id="riskPercent"
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10"
                  value={riskPercent}
                  onChange={(e) => setRiskPercent(Number(e.target.value))}
                />
              </div>
              <div>
                <Label htmlFor="maxPositionSize">Max Position Size (lots)</Label>
                <Input
                  id="maxPositionSize"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={maxPositionSize}
                  onChange={(e) => setMaxPositionSize(Number(e.target.value))}
                />
              </div>
              <div>
                <Label htmlFor="slPips">Stop Loss (pips)</Label>
                <Input
                  id="slPips"
                  type="number"
                  min="5"
                  max="500"
                  value={slPips}
                  onChange={(e) => setSlPips(Number(e.target.value))}
                />
              </div>
              <div>
                <Label htmlFor="tpPips">Take Profit (pips)</Label>
                <Input
                  id="tpPips"
                  type="number"
                  min="5"
                  max="1000"
                  value={tpPips}
                  onChange={(e) => setTpPips(Number(e.target.value))}
                />
              </div>
            </div>
          </div>

          {/* Strategy Settings */}
          <div className="space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <span>📈</span> Strategy Configuration
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="strategyType">Strategy Type</Label>
                <Select value={strategyType} onValueChange={setStrategyType}>
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
                <Label htmlFor="timeframe">Timeframe</Label>
                <Select value={timeframe} onValueChange={setTimeframe}>
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
                <Label htmlFor="fastPeriod">Fast MA Period</Label>
                <Input
                  id="fastPeriod"
                  type="number"
                  min="2"
                  max="100"
                  value={fastPeriod}
                  onChange={(e) => setFastPeriod(Number(e.target.value))}
                />
              </div>
              <div className="col-span-2">
                <Label htmlFor="slowPeriod">Slow MA Period</Label>
                <Input
                  id="slowPeriod"
                  type="number"
                  min="5"
                  max="200"
                  value={slowPeriod}
                  onChange={(e) => setSlowPeriod(Number(e.target.value))}
                />
                {slowPeriod <= fastPeriod && (
                  <p className="text-xs text-destructive mt-1">
                    Slow period must be greater than fast period
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid}>
              Add Currency
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

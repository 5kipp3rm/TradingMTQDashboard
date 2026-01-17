/**
 * CreateStrategyDialog Component
 * Modal for creating new strategy configurations
 */

import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import { strategiesApi, STRATEGY_TYPES, EXECUTION_MODES } from '@/lib/strategies-api';
import { currenciesV2Api } from '@/lib/api-v2';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface CreateStrategyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountId: number;
}

export default function CreateStrategyDialog({ open, onOpenChange, accountId }: CreateStrategyDialogProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Form state
  const [strategyName, setStrategyName] = useState('');
  const [marketType, setMarketType] = useState('Forex');
  const [symbol, setSymbol] = useState('');
  const [strategyType, setStrategyType] = useState('SimpleMA');
  const [direction, setDirection] = useState('Both');
  const [executionMode, setExecutionMode] = useState<'python' | 'ea' | 'hybrid'>('python');
  
  // Risk management state
  const [takeProfit, setTakeProfit] = useState(2);
  const [stopLoss, setStopLoss] = useState(1);
  const [positionSize, setPositionSize] = useState(5);
  const [maxTradesPerDay, setMaxTradesPerDay] = useState('5');
  
  // Conditions
  const [entryConditions, setEntryConditions] = useState('');
  const [exitConditions, setExitConditions] = useState('');
  
  const [availableCurrencies, setAvailableCurrencies] = useState<Array<{ symbol: string; description: string }>>([]);
  const [loadingCurrencies, setLoadingCurrencies] = useState(false);

  // Load available currencies when dialog opens or market type changes
  useEffect(() => {
    if (open) {
      loadCurrencies();
    }
  }, [open, marketType]);

  const loadCurrencies = async () => {
    setLoadingCurrencies(true);
    setSymbol(''); // Reset selected symbol when market type changes
    try {
      const response = await currenciesV2Api.getAll(accountId);
      if (response.data) {
        const currencies = response.data || [];
        setAvailableCurrencies(currencies.map((c: any) => ({
          symbol: c.symbol,
          description: c.description || c.symbol
        })));
      }
    } catch (error) {
      console.error('Failed to load currencies:', error);
      toast({
        variant: 'destructive',
        title: 'Error Loading Currencies',
        description: 'Failed to load available currency pairs',
      });
      setAvailableCurrencies([]);
    } finally {
      setLoadingCurrencies(false);
    }
  };

  const createMutation = useMutation({
    mutationFn: () =>
      strategiesApi.create(accountId, {
        symbol: symbol.toUpperCase(),
        strategy_type: strategyType,
        execution_mode: executionMode,
        enabled: true,
        strategy_params: {
          direction: direction.toLowerCase(),
          entry_conditions: entryConditions,
          exit_conditions: exitConditions,
        },
        // Risk management from sliders
        risk_percent: positionSize,
        sl_pips: stopLoss * 50, // Convert percentage to pips
        tp_pips: takeProfit * 50, // Convert percentage to pips
        // Other fields
        timeframe: 'H1',
        max_positions: parseInt(maxTradesPerDay) || 5,
        max_position_size: 1.0,
        min_position_size: 0.01,
        allow_stacking: false,
      }),
    onSuccess: () => {
      // Invalidate and refetch strategies immediately
      queryClient.invalidateQueries({ 
        queryKey: ['strategies', accountId],
        refetchType: 'active'
      });
      
      toast({
        title: 'Strategy Created',
        description: `${symbol.toUpperCase()} strategy added successfully`,
      });
      
      // Close dialog after a brief delay to ensure refetch completes
      setTimeout(() => {
        handleClose();
      }, 300);
    },
    onError: (error: Error) => {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message,
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!symbol.trim()) {
      toast({
        variant: 'destructive',
        title: 'Validation Error',
        description: 'Symbol is required',
      });
      return;
    }

    createMutation.mutate();
  };

  const handleClose = () => {
    setStrategyName('');
    setMarketType('Forex');
    setSymbol('');
    setStrategyType('SimpleMA');
    setDirection('Both');
    setExecutionMode('python');
    setTakeProfit(2);
    setStopLoss(1);
    setPositionSize(5);
    setMaxTradesPerDay('5');
    setEntryConditions('');
    setExitConditions('');
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Strategy</DialogTitle>
          <DialogDescription>
            Configure a new trading strategy with risk management parameters
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-6 py-4">
            {/* Strategy Name */}
            <div className="space-y-2">
              <Label htmlFor="strategy-name">Strategy Name</Label>
              <Input
                id="strategy-name"
                placeholder="My Trading Strategy"
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
              />
            </div>

            {/* Market Type & Asset Pair - Side by Side */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="market-type">Market Type</Label>
                <Select value={marketType} onValueChange={setMarketType}>
                  <SelectTrigger id="market-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Forex">Forex</SelectItem>
                    <SelectItem value="Crypto">Crypto</SelectItem>
                    <SelectItem value="Stocks">Stocks</SelectItem>
                    <SelectItem value="Commodities">Commodities</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="symbol">Asset Pair</Label>
                <Select value={symbol} onValueChange={setSymbol} disabled={loadingCurrencies}>
                  <SelectTrigger id="symbol">
                    <SelectValue placeholder={loadingCurrencies ? "Loading..." : "EUR/USD"} />
                  </SelectTrigger>
                  <SelectContent>
                    {availableCurrencies.length === 0 && !loadingCurrencies ? (
                      <div className="p-2 text-sm text-muted-foreground text-center">
                        No currency pairs configured.<br/>
                        Please add currencies first.
                      </div>
                    ) : (
                      availableCurrencies.map((currency) => (
                        <SelectItem key={currency.symbol} value={currency.symbol}>
                          {currency.symbol}
                          {currency.description && currency.description !== currency.symbol && 
                            <span className="text-xs text-muted-foreground ml-2">- {currency.description}</span>
                          }
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Strategy Type & Direction - Side by Side */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="strategy-type">Strategy Type</Label>
                <Select value={strategyType} onValueChange={setStrategyType}>
                  <SelectTrigger id="strategy-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STRATEGY_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="direction">Direction</Label>
                <Select value={direction} onValueChange={setDirection}>
                  <SelectTrigger id="direction">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Both">Both</SelectItem>
                    <SelectItem value="Long">Long Only</SelectItem>
                    <SelectItem value="Short">Short Only</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Risk Management Section */}
            <div className="space-y-4 border-t pt-4">
              <h3 className="font-semibold text-sm">Risk Management</h3>

              {/* Take Profit */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label htmlFor="take-profit">Take Profit</Label>
                  <span className="text-sm text-green-600 font-medium">{takeProfit}%</span>
                </div>
                <Slider
                  id="take-profit"
                  value={[takeProfit]}
                  onValueChange={(v) => setTakeProfit(v[0])}
                  min={0.5}
                  max={10}
                  step={0.5}
                  className="w-full"
                />
              </div>

              {/* Stop Loss */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label htmlFor="stop-loss">Stop Loss</Label>
                  <span className="text-sm text-red-600 font-medium">{stopLoss}%</span>
                </div>
                <Slider
                  id="stop-loss"
                  value={[stopLoss]}
                  onValueChange={(v) => setStopLoss(v[0])}
                  min={0.5}
                  max={5}
                  step={0.25}
                  className="w-full"
                />
              </div>

              {/* Position Size */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label htmlFor="position-size">Position Size</Label>
                  <span className="text-sm text-muted-foreground font-medium">{positionSize}% of portfolio</span>
                </div>
                <Slider
                  id="position-size"
                  value={[positionSize]}
                  onValueChange={(v) => setPositionSize(v[0])}
                  min={1}
                  max={20}
                  step={1}
                  className="w-full"
                />
              </div>

              {/* Max Trades Per Day */}
              <div className="space-y-2">
                <Label htmlFor="max-trades">Max Trades Per Day</Label>
                <Input
                  id="max-trades"
                  type="number"
                  min="1"
                  max="50"
                  value={maxTradesPerDay}
                  onChange={(e) => setMaxTradesPerDay(e.target.value)}
                  placeholder="5"
                />
              </div>
            </div>

            {/* Entry Conditions */}
            <div className="space-y-2">
              <Label htmlFor="entry-conditions">Entry Conditions (Optional)</Label>
              <Textarea
                id="entry-conditions"
                placeholder="Describe when to enter a trade..."
                value={entryConditions}
                onChange={(e) => setEntryConditions(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>

            {/* Exit Conditions */}
            <div className="space-y-2">
              <Label htmlFor="exit-conditions">Exit Conditions (Optional)</Label>
              <Textarea
                id="exit-conditions"
                placeholder="Describe when to exit a trade..."
                value={exitConditions}
                onChange={(e) => setExitConditions(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              <Plus className="h-4 w-4 mr-2" />
              {createMutation.isPending ? 'Creating...' : 'Create Strategy'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

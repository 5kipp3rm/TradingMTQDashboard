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

  const [symbol, setSymbol] = useState('');
  const [strategyType, setStrategyType] = useState('SimpleMA');
  const [executionMode, setExecutionMode] = useState<'python' | 'ea' | 'hybrid'>('python');
  const [availableCurrencies, setAvailableCurrencies] = useState<Array<{ symbol: string; description: string }>>([]);
  const [loadingCurrencies, setLoadingCurrencies] = useState(false);

  // Load available currencies when dialog opens
  useEffect(() => {
    if (open) {
      loadCurrencies();
    }
  }, [open]);

  const loadCurrencies = async () => {
    setLoadingCurrencies(true);
    try {
      const response = await currenciesV2Api.getAll(accountId); // Get account's configured currencies
      if (response.data) {
        const currencies = response.data || [];
        setAvailableCurrencies(currencies.map((c: any) => ({
          symbol: c.symbol,
          description: c.symbol
        })));
      }
    } catch (error) {
      console.error('Failed to load currencies:', error);
      // Fallback to common pairs if API fails
      setAvailableCurrencies([
        { symbol: 'EURUSD', description: 'EUR/USD - Euro vs US Dollar' },
        { symbol: 'GBPUSD', description: 'GBP/USD - British Pound vs US Dollar' },
        { symbol: 'USDJPY', description: 'USD/JPY - US Dollar vs Japanese Yen' },
        { symbol: 'AUDUSD', description: 'AUD/USD - Australian Dollar vs US Dollar' },
      ]);
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
        strategy_params: {},
        // Required risk management fields
        risk_percent: 2.0,
        sl_pips: 50,
        tp_pips: 100,
        // Optional fields with defaults
        timeframe: 'H1',
        max_positions: 5,
        max_position_size: 1.0,
        min_position_size: 0.01,
        allow_stacking: false,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies', accountId] });
      toast({
        title: 'Strategy Created',
        description: `${symbol.toUpperCase()} strategy added successfully`,
      });
      handleClose();
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
    setSymbol('');
    setStrategyType('SimpleMA');
    setExecutionMode('python');
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Strategy</DialogTitle>
          <DialogDescription>
            Add a new trading strategy for a currency pair
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            {/* Symbol - Dropdown of available currency pairs from database */}
            <div className="space-y-2">
              <Label htmlFor="symbol">Currency Pair *</Label>
              <Select value={symbol} onValueChange={setSymbol} disabled={loadingCurrencies}>
                <SelectTrigger id="symbol">
                  <SelectValue placeholder={loadingCurrencies ? "Loading currencies..." : "Select a currency pair"} />
                </SelectTrigger>
                <SelectContent>
                  {availableCurrencies.length === 0 && !loadingCurrencies ? (
                    <div className="p-2 text-sm text-muted-foreground text-center">
                      No currencies available
                    </div>
                  ) : (
                    availableCurrencies.map((currency) => (
                      <SelectItem key={currency.symbol} value={currency.symbol}>
                        {currency.symbol} - {currency.description}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {availableCurrencies.length > 0 
                  ? `${availableCurrencies.length} currency pairs available`
                  : 'Select from available forex pairs'}
              </p>
            </div>

            {/* Strategy Type */}
            <div className="space-y-2">
              <Label htmlFor="strategy-type">Strategy Type *</Label>
              <Select value={strategyType} onValueChange={setStrategyType}>
                <SelectTrigger id="strategy-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STRATEGY_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <div>
                        <div className="font-medium">{type.label}</div>
                        <div className="text-xs text-gray-500">{type.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Execution Mode */}
            <div className="space-y-2">
              <Label htmlFor="execution-mode">Execution Mode *</Label>
              <Select value={executionMode} onValueChange={(v) => setExecutionMode(v as any)}>
                <SelectTrigger id="execution-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EXECUTION_MODES.map((mode) => (
                    <SelectItem key={mode.value} value={mode.value}>
                      <div>
                        <div className="font-medium">{mode.label}</div>
                        <div className="text-xs text-gray-500">{mode.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
              <p className="text-blue-800">
                💡 <strong>Tip:</strong> You can configure AI features (ML/LLM) after creating the strategy.
              </p>
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

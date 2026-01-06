/**
 * Strategies Page - Phase 5 Frontend
 * Visual management interface for per-symbol strategies and AI configuration
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, RefreshCw, Filter, Search } from 'lucide-react';
import { Header } from '@/components/dashboard/Header';
import { useAccounts } from '@/contexts/AccountsContext';
import { strategiesApi, Strategy } from '@/lib/strategies-api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import StrategyCard from '@/components/strategies/StrategyCard';
import CreateStrategyDialog from '@/components/strategies/CreateStrategyDialog';

export default function Strategies() {
  const { selectedAccountId, setSelectedAccountId, accounts } = useAccounts();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [period, setPeriod] = useState(30);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterEnabled, setFilterEnabled] = useState<string>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);

  // Auto-select first active account if "all" is selected
  useEffect(() => {
    if (selectedAccountId === 'all' && accounts.length > 0) {
      const firstActiveAccount = accounts.find(acc => acc.isActive);
      if (firstActiveAccount) {
        setSelectedAccountId(firstActiveAccount.id);
      }
    }
  }, [selectedAccountId, accounts, setSelectedAccountId]);

  // Fetch strategies
  const { data: response, isLoading, error } = useQuery({
    queryKey: ['strategies', selectedAccountId],
    queryFn: () => strategiesApi.list(Number(selectedAccountId)),
    enabled: selectedAccountId !== 'all' && selectedAccountId !== null,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const strategies = response?.data?.strategies || [];

  // Filter strategies
  const filteredStrategies = strategies.filter((strategy) => {
    const matchesSearch = strategy.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          strategy.strategy_type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || strategy.strategy_type === filterType;
    const matchesEnabled = filterEnabled === 'all' || 
                          (filterEnabled === 'enabled' && strategy.enabled) ||
                          (filterEnabled === 'disabled' && !strategy.enabled);
    return matchesSearch && matchesType && matchesEnabled;
  });

  // Refresh strategies
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['strategies', selectedAccountId] });
    toast({
      title: 'Refreshed',
      description: 'Strategy list updated',
    });
  };

  const handleQuickTrade = () => {
    setQuickTradeOpen(true);
  };

  // Stats - use backend summary data when available
  const stats = {
    total: response?.data?.total_strategies ?? strategies.length,
    enabled: response?.data?.enabled_count ?? strategies.filter(s => s.enabled).length,
    mlEnabled: strategies.filter(s => s.use_ml_enhancement).length,
    llmEnabled: strategies.filter(s => s.use_llm_sentiment || s.use_llm_analyst).length,
  };

  if (selectedAccountId === 'all' || selectedAccountId === null) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container py-5 max-w-[1400px]">
          <Header
            period={period}
            onPeriodChange={setPeriod}
            onRefresh={handleRefresh}
            onQuickTrade={handleQuickTrade}
          />
          <div className="flex items-center justify-center h-64">
            <Card className="w-full max-w-md">
              <CardContent className="pt-6 text-center">
                <h2 className="text-2xl font-semibold mb-2">No Account Selected</h2>
                <p className="text-muted-foreground mb-4">Please select an account from the dropdown in the header to view strategies</p>
                {accounts.length === 0 && (
                  <p className="text-sm text-muted-foreground">No accounts found. Create an account first.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={period}
          onPeriodChange={setPeriod}
          onRefresh={handleRefresh}
          onQuickTrade={handleQuickTrade}
        />
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Strategy Management</h1>
            <p className="text-muted-foreground mt-1">Configure and monitor per-symbol trading strategies with AI enhancement</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Strategy
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Strategies</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Enabled</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.enabled}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">ML Enhanced</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{stats.mlEnabled}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">LLM Powered</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">{stats.llmEnabled}</div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex gap-4 items-center">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search by symbol or strategy type..."
                    className="pl-10"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Strategy Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="SimpleMA">Simple MA</SelectItem>
                  <SelectItem value="RSI">RSI</SelectItem>
                  <SelectItem value="MACD">MACD</SelectItem>
                  <SelectItem value="BBands">Bollinger Bands</SelectItem>
                  <SelectItem value="MultiIndicator">Multi-Indicator</SelectItem>
                  <SelectItem value="ML">ML-Enhanced</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterEnabled} onValueChange={setFilterEnabled}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="enabled">Enabled</SelectItem>
                  <SelectItem value="disabled">Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Strategies Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">Failed to load strategies: {(error as Error).message}</p>
            </CardContent>
          </Card>
        ) : filteredStrategies.length === 0 ? (
          <Card>
            <CardContent className="pt-16 pb-16 text-center">
              <Filter className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Strategies Found</h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm || filterType !== 'all' || filterEnabled !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Create your first strategy to get started'}
              </p>
              {strategies.length === 0 && (
                <Button onClick={() => setCreateDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Strategy
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredStrategies.map((strategy) => (
              <StrategyCard
                key={strategy.symbol}
                strategy={strategy}
                accountId={Number(selectedAccountId)}
              />
            ))}
          </div>
        )}

        {/* Create Strategy Dialog */}
        <CreateStrategyDialog
          open={createDialogOpen}
          onOpenChange={setCreateDialogOpen}
          accountId={Number(selectedAccountId)}
        />
        </div>
      </div>
    </div>
  );
}

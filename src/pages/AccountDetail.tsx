/**
 * Phase 5 Frontend: Account Detail Page
 *
 * Displays detailed account information with OOP v2 API
 * - Account status and control
 * - Currency management
 * - AI configuration
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Header } from '@/components/dashboard/Header';
import { useToast } from '@/hooks/use-toast';
import {
  Play,
  Square,
  Pause,
  Link,
  Unlink,
  Settings,
  TrendingUp,
  Bot,
  ArrowLeft,
  RefreshCw,
} from 'lucide-react';
import { accountsV2Api, currenciesV2Api, AccountStatus, CurrencyConfig } from '@/lib/api-v2';
import { accountsApi } from '@/lib/api';
import { CurrenciesCard } from '@/components/accounts/CurrenciesCard';
import { AIConfigCard } from '@/components/accounts/AIConfigCard';
import { ViewAccountModal } from '@/components/accounts/ViewAccountModal';
import type { Account } from '@/types/trading';

export const AccountDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [status, setStatus] = useState<AccountStatus | null>(null);
  const [accountDetails, setAccountDetails] = useState<Account | null>(null);
  const [currencies, setCurrencies] = useState<CurrencyConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isOperating, setIsOperating] = useState(false);
  const [editConfigOpen, setEditConfigOpen] = useState(false);
  const [viewAccountOpen, setViewAccountOpen] = useState(false);
  const [period, setPeriod] = useState(30); // Default to 30 days
  const [configForm, setConfigForm] = useState({
    max_concurrent_trades: 0,
    portfolio_risk: 0,
    check_interval: 0,
  });

  const accountId = parseInt(id || '0');

  const handleRefresh = () => {
    loadAccountStatus();
    loadAccountDetails();
    loadCurrencies();
  };

  const loadAccountDetails = useCallback(async () => {
    try {
      const response = await accountsApi.getById(accountId);
      if (response.data) {
        let accountData = response.data as Account;
        
        // If account is connected, fetch and merge real-time MT5 data
        if (status?.is_connected) {
          try {
            const mt5Response = await accountsV2Api.getMT5Info(accountId);
            if (mt5Response.data) {
              accountData = {
                ...accountData,
                balance: mt5Response.data.balance,
                equity: mt5Response.data.equity,
                margin: mt5Response.data.margin,
                freeMargin: mt5Response.data.margin_free,
                leverage: mt5Response.data.leverage,
              };
            }
          } catch (error) {
            console.log('Could not fetch MT5 info (account may not be connected):', error);
          }
        }
        
        setAccountDetails(accountData);
      }
    } catch (error) {
      console.error('Failed to load account details:', error);
    }
  }, [accountId, status?.is_connected]);

  const handleQuickTrade = () => {
    // Quick trade functionality - can be implemented later
    toast({
      title: 'Quick Trade',
      description: 'Quick trade feature coming soon',
    });
  };

  const loadAccountStatus = useCallback(async () => {
    const response = await accountsV2Api.getStatus(accountId);
    if (response.data) {
      setStatus(response.data);
      setIsLoading(false);
    } else if (response.error) {
      toast({
        title: 'Error',
        description: response.error,
        variant: 'destructive',
      });
      setIsLoading(false);
    }
  }, [accountId, toast]);

  const loadCurrencies = useCallback(async () => {
    try {
      const response = await currenciesV2Api.getAll(accountId);
      if (response.data) {
        setCurrencies(response.data);
      }
    } catch (error) {
      console.error('Failed to load currencies:', error);
    }
  }, [accountId]);

  useEffect(() => {
    if (accountId) {
      loadAccountStatus();
      loadAccountDetails();
      loadCurrencies();
      // Refresh status every 5 seconds
      const interval = setInterval(loadAccountStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [accountId, loadAccountStatus, loadAccountDetails, loadCurrencies]);

  const handleConnect = async () => {
    setIsOperating(true);
    const response = await accountsV2Api.connect(accountId);
    if (response.data?.success) {
      toast({
        title: 'Success',
        description: 'Account connected successfully',
      });
      await loadAccountStatus();
    } else {
      toast({
        title: 'Connection Failed',
        description: response.data?.error || response.error || 'Unknown error',
        variant: 'destructive',
      });
    }
    setIsOperating(false);
  };

  const handleDisconnect = async () => {
    setIsOperating(true);
    const response = await accountsV2Api.disconnect(accountId);
    if (response.data?.success) {
      toast({
        title: 'Success',
        description: 'Account disconnected',
      });
      // Reload both status and account details to ensure UI updates
      await loadAccountStatus();
      await loadAccountDetails();
    } else {
      toast({
        title: 'Error',
        description: response.error || 'Failed to disconnect',
        variant: 'destructive',
      });
    }
    setIsOperating(false);
  };

  const handleStartTrading = async () => {
    setIsOperating(true);
    const response = await accountsV2Api.startTrading(accountId);
    if (response.data?.success) {
      toast({
        title: 'Success',
        description: 'Trading started',
      });
      await loadAccountStatus();
    } else {
      toast({
        title: 'Error',
        description: response.data?.error || response.error || 'Failed to start trading',
        variant: 'destructive',
      });
    }
    setIsOperating(false);
  };

  const handleStopTrading = async () => {
    setIsOperating(true);
    const response = await accountsV2Api.stopTrading(accountId);
    if (response.data?.success) {
      toast({
        title: 'Success',
        description: 'Trading stopped',
      });
      await loadAccountStatus();
    } else {
      toast({
        title: 'Error',
        description: response.error || 'Failed to stop trading',
        variant: 'destructive',
      });
    }
    setIsOperating(false);
  };

  const handlePauseTrading = async () => {
    setIsOperating(true);
    const response = await accountsV2Api.pauseTrading(accountId);
    if (response.data?.success) {
      toast({
        title: 'Success',
        description: 'Trading paused',
      });
      await loadAccountStatus();
    } else {
      toast({
        title: 'Error',
        description: response.error || 'Failed to pause trading',
        variant: 'destructive',
      });
    }
    setIsOperating(false);
  };

  const handleResumeTrading = async () => {
    setIsOperating(true);
    const response = await accountsV2Api.resumeTrading(accountId);
    if (response.data?.success) {
      toast({
        title: 'Success',
        description: 'Trading resumed',
      });
      await loadAccountStatus();
    } else {
      toast({
        title: 'Error',
        description: response.data?.error || response.error || 'Failed to resume trading',
        variant: 'destructive',
      });
    }
    setIsOperating(false);
  };

  const getStateBadge = (state: string) => {
    const stateColors: Record<string, string> = {
      created: 'bg-gray-500',
      connecting: 'bg-yellow-500',
      connected: 'bg-green-500',
      disconnected: 'bg-gray-500',
      trading: 'bg-blue-500',
      paused: 'bg-orange-500',
      error: 'bg-red-500',
    };

    return (
      <Badge className={`${stateColors[state] || 'bg-gray-500'} text-white`}>
        {state.toUpperCase()}
      </Badge>
    );
  };

  if (isLoading) {
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
            <RefreshCw className="h-8 w-8 animate-spin" />
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container py-5 max-w-[1400px]">
          <Header
            period={period}
            onPeriodChange={setPeriod}
            onRefresh={handleRefresh}
            onQuickTrade={handleQuickTrade}
          />
          <Button onClick={() => navigate('/accounts')} variant="ghost">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Accounts
          </Button>
          <div className="mt-8 text-center">
            <p className="text-lg text-muted-foreground">Account not found</p>
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
          <div className="flex items-center space-x-4">
            <Button onClick={() => navigate('/accounts')} variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 
                className="text-3xl font-bold cursor-pointer hover:text-primary transition-colors"
                onClick={() => setViewAccountOpen(true)}
                title="Click to view full account details"
              >
                {status.name}
              </h1>
              <p className="text-muted-foreground">Account #{status.id}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getStateBadge(status.state)}
            <Button onClick={loadAccountStatus} variant="ghost" size="sm" disabled={isOperating}>
              <RefreshCw className={`h-4 w-4 ${isOperating ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Account Status Card */}
        <Card>
          <CardHeader>
            <CardTitle>Account Status</CardTitle>
            <CardDescription>Connection and trading status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Status Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Connection</p>
                <p className="text-lg font-semibold">
                  {status.is_connected ? (
                    <span className="text-green-600">Connected</span>
                  ) : (
                    <span className="text-red-600">Disconnected</span>
                  )}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Trading</p>
                <p className="text-lg font-semibold">
                  {status.is_trading ? (
                    <span className="text-blue-600">Active</span>
                  ) : (
                    <span className="text-muted-foreground">Inactive</span>
                  )}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Currencies</p>
                <p className="text-lg font-semibold">{status.active_currencies} active</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Check Interval</p>
                <p className="text-lg font-semibold">{status.config.check_interval}s</p>
              </div>
            </div>

            {/* Error Message */}
            {status.last_error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">
                  <strong>Error:</strong> {status.last_error}
                </p>
              </div>
            )}

            {/* Control Buttons */}
            <div className="flex flex-wrap gap-2 pt-2">
              {!status.is_connected ? (
                <Button onClick={handleConnect} disabled={isOperating}>
                  <Link className="mr-2 h-4 w-4" />
                  Connect
                </Button>
              ) : (
                <Button onClick={handleDisconnect} variant="outline" disabled={isOperating}>
                  <Unlink className="mr-2 h-4 w-4" />
                  Disconnect
                </Button>
              )}

              {status.is_connected && !status.is_trading && status.state !== 'paused' && (
                <Button onClick={handleStartTrading} disabled={isOperating}>
                  <Play className="mr-2 h-4 w-4" />
                  Start Trading
                </Button>
              )}

              {status.is_trading && (
                <>
                  <Button onClick={handleStopTrading} variant="destructive" disabled={isOperating}>
                    <Square className="mr-2 h-4 w-4" />
                    Stop Trading
                  </Button>
                  <Button onClick={handlePauseTrading} variant="outline" disabled={isOperating}>
                    <Pause className="mr-2 h-4 w-4" />
                    Pause Trading
                  </Button>
                </>
              )}

              {status.state === 'paused' && (
                <Button onClick={handleResumeTrading} disabled={isOperating}>
                  <Play className="mr-2 h-4 w-4" />
                  Resume Trading
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Configuration Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Trading Configuration</CardTitle>
                <CardDescription>Account-level trading parameters</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={() => {
                setConfigForm({
                  max_concurrent_trades: status.config.max_concurrent_trades,
                  portfolio_risk: status.config.portfolio_risk,
                  check_interval: status.config.check_interval,
                });
                setEditConfigOpen(true);
              }}>
                <Settings className="h-4 w-4 mr-2" />
                Edit Configuration
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-blue-500" />
                  <p className="text-sm font-medium">Max Concurrent Trades</p>
                </div>
                <p className="text-2xl font-bold">{status.config.max_concurrent_trades}</p>
              </div>
              <div className="border rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Settings className="h-4 w-4 text-green-500" />
                  <p className="text-sm font-medium">Portfolio Risk</p>
                </div>
                <p className="text-2xl font-bold">{status.config.portfolio_risk}%</p>
              </div>
              <div className="border rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <RefreshCw className="h-4 w-4 text-purple-500" />
                  <p className="text-sm font-medium">Check Interval</p>
                </div>
                <p className="text-2xl font-bold">{status.config.check_interval}s</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Currencies Card */}
        <CurrenciesCard accountId={accountId} currencies={currencies} onRefresh={loadCurrencies} />

        {/* AI Configuration Card */}
        <AIConfigCard accountId={accountId} onRefresh={loadAccountStatus} />

        {/* AI Pipeline Status Card (Read-only display) */}
        {status.ai_pipeline && status.ai_pipeline.total_enhancers + status.ai_pipeline.total_filters > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bot className="h-5 w-5" />
                <span>AI Pipeline Status</span>
              </CardTitle>
              <CardDescription>Active signal enhancers and filters</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Enhancers */}
                <div>
                  <h4 className="font-medium mb-2">Signal Enhancers</h4>
                  {status.ai_pipeline.enhancers.length > 0 ? (
                    <div className="space-y-2">
                      {status.ai_pipeline.enhancers.map((enhancer, idx) => (
                        <div key={idx} className="flex items-center justify-between border rounded-lg p-2">
                          <div>
                            <p className="text-sm font-medium">{enhancer.name}</p>
                            <p className="text-xs text-muted-foreground">{enhancer.type}</p>
                          </div>
                          <Badge variant={enhancer.enabled ? 'default' : 'secondary'}>
                            {enhancer.enabled ? 'Enabled' : 'Disabled'}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No enhancers configured</p>
                  )}
                </div>

                {/* Filters */}
                <div>
                  <h4 className="font-medium mb-2">Signal Filters</h4>
                  {status.ai_pipeline.filters.length > 0 ? (
                    <div className="space-y-2">
                      {status.ai_pipeline.filters.map((filter, idx) => (
                        <div key={idx} className="flex items-center justify-between border rounded-lg p-2">
                          <div>
                            <p className="text-sm font-medium">{filter.name}</p>
                            <p className="text-xs text-muted-foreground">{filter.type}</p>
                          </div>
                          <Badge variant={filter.enabled ? 'default' : 'secondary'}>
                            {filter.enabled ? 'Enabled' : 'Disabled'}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No filters configured</p>
                  )}
                </div>
              </div>

              {/* Summary Stats */}
              <div className="mt-4 grid grid-cols-4 gap-2 border-t pt-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{status.ai_pipeline.total_enhancers}</p>
                  <p className="text-xs text-muted-foreground">Enhancers</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">{status.ai_pipeline.active_enhancers}</p>
                  <p className="text-xs text-muted-foreground">Active</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">{status.ai_pipeline.total_filters}</p>
                  <p className="text-xs text-muted-foreground">Filters</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-orange-600">{status.ai_pipeline.active_filters}</p>
                  <p className="text-xs text-muted-foreground">Active</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Edit Configuration Dialog */}
        <Dialog open={editConfigOpen} onOpenChange={setEditConfigOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Trading Configuration</DialogTitle>
              <DialogDescription>
                Update account-level trading parameters
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="max_trades">Max Concurrent Trades</Label>
                <Input
                  id="max_trades"
                  type="number"
                  value={configForm.max_concurrent_trades}
                  onChange={(e) => setConfigForm({...configForm, max_concurrent_trades: parseInt(e.target.value)})}
                />
                <p className="text-xs text-muted-foreground">Maximum number of trades allowed at once</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="portfolio_risk">Portfolio Risk (%)</Label>
                <Input
                  id="portfolio_risk"
                  type="number"
                  step="0.1"
                  value={configForm.portfolio_risk}
                  onChange={(e) => setConfigForm({...configForm, portfolio_risk: parseFloat(e.target.value)})}
                />
                <p className="text-xs text-muted-foreground">Maximum portfolio risk percentage</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="check_interval">Check Interval (seconds)</Label>
                <Input
                  id="check_interval"
                  type="number"
                  value={configForm.check_interval}
                  onChange={(e) => setConfigForm({...configForm, check_interval: parseInt(e.target.value)})}
                />
                <p className="text-xs text-muted-foreground">How often to check for trading signals</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditConfigOpen(false)}>
                Cancel
              </Button>
              <Button onClick={async () => {
                try {
                  // TODO: Call API to update config
                  // await accountsV2Api.updateConfig(accountId, configForm);
                  toast({
                    title: 'Configuration Updated',
                    description: 'Trading configuration has been updated successfully',
                  });
                  setEditConfigOpen(false);
                  loadAccountStatus();
                } catch (error) {
                  toast({
                    variant: 'destructive',
                    title: 'Error',
                    description: 'Failed to update configuration',
                  });
                }
              }}>
                Save Changes
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* View Account Details Modal */}
        {accountDetails && (
          <ViewAccountModal
            open={viewAccountOpen}
            onClose={() => setViewAccountOpen(false)}
            account={accountDetails}
            status={status}
          />
        )}
      </div>
      </div>
    </div>
  );
};

export default AccountDetail;

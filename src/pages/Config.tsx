import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Header } from "@/components/dashboard/Header";
import { useState } from "react";
import { useAccounts } from "@/contexts/AccountsContext";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";

interface RiskSettings {
  risk_percent: number;
  max_positions: number;
  max_concurrent_trades: number;
  portfolio_risk_percent: number;
  stop_loss_pips: number;
  take_profit_pips: number;
}

interface AccountSettings {
  [accountId: string]: RiskSettings;
}

const defaultRiskSettings: RiskSettings = {
  risk_percent: 1,
  max_positions: 5,
  max_concurrent_trades: 15,
  portfolio_risk_percent: 10,
  stop_loss_pips: 50,
  take_profit_pips: 100,
};

const Config = () => {
  const { accounts, selectedAccountId } = useAccounts();
  const { toast } = useToast();
  const [settingsPerAccount, setSettingsPerAccount] = useState<AccountSettings>({
    "1": { ...defaultRiskSettings },
    "2": { ...defaultRiskSettings, risk_percent: 2, max_positions: 3 },
    "3": { ...defaultRiskSettings, risk_percent: 0.5, max_positions: 10 },
  });

  const [generalConfig, setGeneralConfig] = useState({
    apiUrl: "http://localhost:8000",
    refreshInterval: 60,
    autoTrade: false,
    notifications: true,
    soundAlerts: false,
  });

  const currentAccountId = selectedAccountId === "all" ? "1" : selectedAccountId;
  const currentSettings = settingsPerAccount[currentAccountId] || defaultRiskSettings;

  const updateRiskSetting = (key: keyof RiskSettings, value: number) => {
    setSettingsPerAccount((prev) => ({
      ...prev,
      [currentAccountId]: {
        ...prev[currentAccountId],
        [key]: value,
      },
    }));
  };

  const handleSave = () => {
    toast({
      title: "Settings Saved",
      description: "Your settings have been saved successfully.",
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
            <h2 className="text-2xl font-bold">Settings</h2>
            {selectedAccount && (
              <p className="text-sm text-muted-foreground">
                Configuring: {selectedAccount.name}
              </p>
            )}
          </div>
          <Button onClick={handleSave}>Save Changes</Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Risk Settings */}
          <Card className="card-glow lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>⚠️</span> Risk Management
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <Label htmlFor="risk_percent">Risk Per Trade (%)</Label>
                  <Input
                    id="risk_percent"
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="10"
                    value={currentSettings.risk_percent}
                    onChange={(e) => updateRiskSetting("risk_percent", Number(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Percentage of account balance to risk per trade
                  </p>
                </div>

                <div>
                  <Label htmlFor="max_positions">Max Positions</Label>
                  <Input
                    id="max_positions"
                    type="number"
                    min="1"
                    max="50"
                    value={currentSettings.max_positions}
                    onChange={(e) => updateRiskSetting("max_positions", Number(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Maximum open positions per symbol
                  </p>
                </div>

                <div>
                  <Label htmlFor="max_concurrent_trades">Max Concurrent Trades</Label>
                  <Input
                    id="max_concurrent_trades"
                    type="number"
                    min="1"
                    max="100"
                    value={currentSettings.max_concurrent_trades}
                    onChange={(e) => updateRiskSetting("max_concurrent_trades", Number(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Maximum trades across all symbols
                  </p>
                </div>

                <div>
                  <Label htmlFor="portfolio_risk_percent">Portfolio Risk (%)</Label>
                  <Input
                    id="portfolio_risk_percent"
                    type="number"
                    step="0.5"
                    min="1"
                    max="50"
                    value={currentSettings.portfolio_risk_percent}
                    onChange={(e) => updateRiskSetting("portfolio_risk_percent", Number(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Maximum total portfolio risk exposure
                  </p>
                </div>

                <div>
                  <Label htmlFor="stop_loss_pips">Default Stop Loss (pips)</Label>
                  <Input
                    id="stop_loss_pips"
                    type="number"
                    min="5"
                    max="500"
                    value={currentSettings.stop_loss_pips}
                    onChange={(e) => updateRiskSetting("stop_loss_pips", Number(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Default stop loss distance in pips
                  </p>
                </div>

                <div>
                  <Label htmlFor="take_profit_pips">Default Take Profit (pips)</Label>
                  <Input
                    id="take_profit_pips"
                    type="number"
                    min="5"
                    max="1000"
                    value={currentSettings.take_profit_pips}
                    onChange={(e) => updateRiskSetting("take_profit_pips", Number(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Default take profit distance in pips
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* API Configuration */}
          <Card className="card-glow">
            <CardHeader>
              <CardTitle>API Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="apiUrl">API URL</Label>
                <Input
                  id="apiUrl"
                  value={generalConfig.apiUrl}
                  onChange={(e) => setGeneralConfig({ ...generalConfig, apiUrl: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="refreshInterval">Refresh Interval (seconds)</Label>
                <Input
                  id="refreshInterval"
                  type="number"
                  value={generalConfig.refreshInterval}
                  onChange={(e) => setGeneralConfig({ ...generalConfig, refreshInterval: Number(e.target.value) })}
                />
              </div>
            </CardContent>
          </Card>

          {/* Trading & Notifications */}
          <Card className="card-glow">
            <CardHeader>
              <CardTitle>Trading & Notifications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="autoTrade">Auto Trading</Label>
                  <p className="text-xs text-muted-foreground">Enable automated trade execution</p>
                </div>
                <Switch
                  id="autoTrade"
                  checked={generalConfig.autoTrade}
                  onCheckedChange={(checked) => setGeneralConfig({ ...generalConfig, autoTrade: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="notifications">Push Notifications</Label>
                  <p className="text-xs text-muted-foreground">Receive trade alerts</p>
                </div>
                <Switch
                  id="notifications"
                  checked={generalConfig.notifications}
                  onCheckedChange={(checked) => setGeneralConfig({ ...generalConfig, notifications: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="soundAlerts">Sound Alerts</Label>
                  <p className="text-xs text-muted-foreground">Play sound on trade events</p>
                </div>
                <Switch
                  id="soundAlerts"
                  checked={generalConfig.soundAlerts}
                  onCheckedChange={(checked) => setGeneralConfig({ ...generalConfig, soundAlerts: checked })}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Config;

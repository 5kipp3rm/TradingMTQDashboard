import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Header } from "@/components/dashboard/Header";
import { Bell, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const mockAlerts = [
  { id: "1", symbol: "EURUSD", condition: "above", price: 1.0900, triggered: false, createdAt: "2024-12-15T10:00:00Z" },
  { id: "2", symbol: "GBPUSD", condition: "below", price: 1.2600, triggered: true, createdAt: "2024-12-14T15:30:00Z", triggeredAt: "2024-12-16T09:15:00Z" },
  { id: "3", symbol: "XAUUSD", condition: "above", price: 2100, triggered: false, createdAt: "2024-12-10T08:00:00Z" },
];

const Alerts = () => {
  const [alerts] = useState(mockAlerts);

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
          <h2 className="text-2xl font-bold">Price Alerts</h2>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Alert
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-6">
          <Card className="card-glow">
            <CardHeader>
              <CardTitle className="text-lg">Create Alert</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm text-muted-foreground">Symbol</label>
                <Input placeholder="EURUSD" />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Condition</label>
                <select className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm">
                  <option value="above">Price Above</option>
                  <option value="below">Price Below</option>
                  <option value="cross">Price Crosses</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Price</label>
                <Input type="number" step="0.00001" placeholder="1.0850" />
              </div>
              <Button className="w-full">
                <Bell className="h-4 w-4 mr-2" />
                Create Alert
              </Button>
            </CardContent>
          </Card>

          <Card className="card-glow lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-lg">Active Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={cn(
                      "flex items-center justify-between p-4 rounded-lg",
                      alert.triggered ? "bg-success/10" : "bg-muted/30"
                    )}
                  >
                    <div className="flex items-center gap-4">
                      <Bell className={cn("h-5 w-5", alert.triggered ? "text-success" : "text-muted-foreground")} />
                      <div>
                        <p className="font-semibold">
                          {alert.symbol} {alert.condition} ${alert.price}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Created: {new Date(alert.createdAt).toLocaleDateString()}
                          {alert.triggered && alert.triggeredAt && (
                            <span className="text-success ml-2">
                              • Triggered: {new Date(alert.triggeredAt).toLocaleDateString()}
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="text-destructive">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Alerts;

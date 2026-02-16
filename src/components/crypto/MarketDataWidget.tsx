import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { useMarketTicker } from "@/hooks/useCryptoAPI";
import { TrendingUp, TrendingDown, Activity, Search } from "lucide-react";
import { cn } from "@/lib/utils";

export function MarketDataWidget() {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [searchSymbol, setSearchSymbol] = useState('BTCUSDT');
  const { data: ticker, isLoading } = useMarketTicker(searchSymbol, 'BINANCE');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (symbol) {
      setSearchSymbol(symbol.toUpperCase());
    }
  };

  const formatPrice = (value: number) => {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 8,
    });
  };

  const formatVolume = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(2)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}K`;
    }
    return value.toFixed(2);
  };

  const priceChangePositive = ticker && ticker.price_change_24h >= 0;

  return (
    <Card className="card-glow">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Market Data
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Symbol Search */}
        <form onSubmit={handleSearch} className="flex gap-2 mb-4">
          <Input
            placeholder="Enter symbol (e.g., BTCUSDT)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="font-mono"
          />
          <button
            type="submit"
            className="px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            <Search className="h-4 w-4" />
          </button>
        </form>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Activity className="h-6 w-6 animate-pulse text-muted-foreground" />
          </div>
        ) : ticker ? (
          <div className="space-y-4">
            {/* Symbol and Price */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold font-mono">{ticker.symbol}</h3>
                <Badge
                  variant="outline"
                  className={cn(
                    priceChangePositive ? 'bg-success/20 text-success' : 'bg-destructive/20 text-destructive'
                  )}
                >
                  {priceChangePositive ? (
                    <TrendingUp className="h-3 w-3 mr-1" />
                  ) : (
                    <TrendingDown className="h-3 w-3 mr-1" />
                  )}
                  {ticker.price_change_percent_24h.toFixed(2)}%
                </Badge>
              </div>
              <p className="text-3xl font-bold font-mono">${formatPrice(ticker.last_price)}</p>
              <p
                className={cn(
                  "text-sm font-mono mt-1",
                  priceChangePositive ? 'text-success' : 'text-destructive'
                )}
              >
                {priceChangePositive ? '+' : ''}${formatPrice(ticker.price_change_24h)} (24h)
              </p>
            </div>

            {/* Price Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-muted rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">24h High</p>
                <p className="text-sm font-semibold font-mono">${formatPrice(ticker.high_24h)}</p>
              </div>
              <div className="bg-muted rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">24h Low</p>
                <p className="text-sm font-semibold font-mono">${formatPrice(ticker.low_24h)}</p>
              </div>
            </div>

            {/* Bid/Ask */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-success/10 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Bid</p>
                <p className="text-sm font-semibold font-mono text-success">
                  ${formatPrice(ticker.bid_price)}
                </p>
              </div>
              <div className="bg-destructive/10 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Ask</p>
                <p className="text-sm font-semibold font-mono text-destructive">
                  ${formatPrice(ticker.ask_price)}
                </p>
              </div>
            </div>

            {/* Volume */}
            <div className="bg-muted rounded-lg p-3">
              <p className="text-xs text-muted-foreground mb-1">24h Volume</p>
              <p className="text-sm font-semibold font-mono">{formatVolume(ticker.volume_24h)}</p>
            </div>

            {/* Last Update */}
            <p className="text-xs text-muted-foreground text-center">
              Updated: {new Date(ticker.timestamp).toLocaleTimeString()}
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mb-3 opacity-50" />
            <p className="text-sm">Enter a symbol to view market data</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState } from "react";
import { usePlaceOrder, useSymbols } from "@/hooks/useCryptoAPI";
import { useToast } from "@/hooks/use-toast";
import { ShoppingCart, TrendingUp, TrendingDown } from "lucide-react";
import type { PlaceOrderRequest } from "@/types/crypto";

interface OrderFormProps {
  accountId: number;
}

export function OrderForm({ accountId }: OrderFormProps) {
  const { data: symbolsData } = useSymbols('BINANCE', 'USDT');
  const placeOrder = usePlaceOrder(accountId);
  const { toast } = useToast();

  const [symbol, setSymbol] = useState('');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [quantity, setQuantity] = useState('');
  const [limitPrice, setLimitPrice] = useState('');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');

  const symbols = symbolsData?.symbols || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!symbol || !quantity) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    if (orderType === 'LIMIT' && !limitPrice) {
      toast({
        title: "Validation Error",
        description: "Limit price is required for limit orders",
        variant: "destructive",
      });
      return;
    }

    const orderData: PlaceOrderRequest = {
      symbol,
      side,
      order_type: orderType,
      quantity: parseFloat(quantity),
      price: orderType === 'LIMIT' ? parseFloat(limitPrice) : undefined,
    };

    try {
      await placeOrder.mutateAsync(orderData);
      toast({
        title: "Order Placed",
        description: `${side} ${quantity} ${symbol} at ${orderType === 'MARKET' ? 'market price' : `$${limitPrice}`}`,
      });
      // Reset form
      setQuantity('');
      setLimitPrice('');
    } catch (error: any) {
      toast({
        title: "Order Failed",
        description: error.message || "Failed to place order",
        variant: "destructive",
      });
    }
  };

  return (
    <Card className="card-glow">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShoppingCart className="h-5 w-5" />
          Place Order
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Symbol Selection */}
          <div>
            <Label htmlFor="symbol">Trading Pair</Label>
            <Select value={symbol} onValueChange={setSymbol}>
              <SelectTrigger>
                <SelectValue placeholder="Select symbol" />
              </SelectTrigger>
              <SelectContent className="max-h-[200px]">
                {symbols.slice(0, 50).map((sym) => (
                  <SelectItem key={sym.symbol} value={sym.symbol}>
                    {sym.symbol}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Order Type Tabs */}
          <Tabs value={orderType} onValueChange={(v) => setOrderType(v as 'MARKET' | 'LIMIT')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="MARKET">Market</TabsTrigger>
              <TabsTrigger value="LIMIT">Limit</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Buy/Sell Side */}
          <div>
            <Label>Side</Label>
            <div className="grid grid-cols-2 gap-2 mt-2">
              <Button
                type="button"
                variant={side === 'BUY' ? 'default' : 'outline'}
                className={side === 'BUY' ? 'bg-success hover:bg-success/90' : ''}
                onClick={() => setSide('BUY')}
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                Buy
              </Button>
              <Button
                type="button"
                variant={side === 'SELL' ? 'destructive' : 'outline'}
                onClick={() => setSide('SELL')}
              >
                <TrendingDown className="h-4 w-4 mr-2" />
                Sell
              </Button>
            </div>
          </div>

          {/* Quantity */}
          <div>
            <Label htmlFor="quantity">Quantity</Label>
            <Input
              id="quantity"
              type="number"
              step="0.00000001"
              min="0"
              placeholder="0.0"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="font-mono"
              required
            />
          </div>

          {/* Limit Price (only for limit orders) */}
          {orderType === 'LIMIT' && (
            <div>
              <Label htmlFor="limitPrice">Limit Price (USDT)</Label>
              <Input
                id="limitPrice"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={limitPrice}
                onChange={(e) => setLimitPrice(e.target.value)}
                className="font-mono"
                required
              />
            </div>
          )}

          {/* Order Summary */}
          {quantity && symbol && (
            <div className="bg-muted rounded-lg p-3 space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Order Type</span>
                <span className="font-semibold">{orderType}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Side</span>
                <span
                  className={side === 'BUY' ? 'text-success font-semibold' : 'text-destructive font-semibold'}
                >
                  {side}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Symbol</span>
                <span className="font-mono">{symbol}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Quantity</span>
                <span className="font-mono">{quantity}</span>
              </div>
              {orderType === 'LIMIT' && limitPrice && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Price</span>
                  <span className="font-mono">${limitPrice}</span>
                </div>
              )}
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={placeOrder.isPending || !symbol || !quantity}
          >
            {placeOrder.isPending
              ? 'Placing Order...'
              : `${side === 'BUY' ? 'Buy' : 'Sell'} ${symbol || 'Asset'}`}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

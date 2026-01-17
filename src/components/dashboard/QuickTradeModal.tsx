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
import { TrendingUp, TrendingDown } from "lucide-react";
import type { CurrencyPair, QuickTradeParams } from "@/types/trading";
import { useAccounts } from "@/contexts/AccountsContext";
import { positionsApi } from "@/lib/api";

interface QuickTradeModalProps {
  open: boolean;
  onClose: () => void;
  currencies: CurrencyPair[];
  onTrade: (params: QuickTradeParams) => void;
}

export function QuickTradeModal({ open, onClose, currencies, onTrade }: QuickTradeModalProps) {
  const [symbol, setSymbol] = useState("");
  const [volume, setVolume] = useState("0.10");
  const [sl, setSl] = useState("");
  const [tp, setTp] = useState("");
  const [comment, setComment] = useState("");
  const [currentPrice, setCurrentPrice] = useState(0);
  const [loadingPrice, setLoadingPrice] = useState(false);
  const { selectedAccountId } = useAccounts();

  const selectedPair = currencies.find((c) => c.symbol === symbol);

  useEffect(() => {
    if (open && currencies.length > 0 && !symbol) {
      setSymbol(currencies[0].symbol);
    }
  }, [open, currencies, symbol]);

  // Fetch current price when symbol changes
  useEffect(() => {
    if (!open || !symbol || !selectedAccountId) {
      setCurrentPrice(0);
      return;
    }

    const fetchCurrentPrice = async () => {
      setLoadingPrice(true);
      try {
        const accountId = selectedAccountId === "all" ? undefined : parseInt(selectedAccountId, 10);
        if (!accountId) return;

        // Use preview endpoint to get current price
        const response = await positionsApi.preview({
          account_id: accountId,
          symbol: symbol,
          order_type: "BUY",
          volume: 0.01, // Dummy volume just to get prices
        });

        if (response.data) {
          setCurrentPrice(response.data.entry_price);
        }
      } catch (error) {
        console.error("Failed to fetch current price:", error);
      } finally {
        setLoadingPrice(false);
      }
    };

    fetchCurrentPrice();
  }, [open, symbol, selectedAccountId]);

  const resetForm = () => {
    setVolume("0.10");
    setSl("");
    setTp("");
    setComment("");
  };

  const calculateRisk = () => {
    if (!selectedPair || !sl || currentPrice === 0) return 0;
    const slPrice = parseFloat(sl);
    const point = selectedPair.point || 0.0001;
    const pips = Math.abs(currentPrice - slPrice) / point;
    return pips * parseFloat(volume) * 10;
  };

  const calculateReward = () => {
    if (!selectedPair || !tp || currentPrice === 0) return 0;
    const tpPrice = parseFloat(tp);
    const point = selectedPair.point || 0.0001;
    const pips = Math.abs(tpPrice - currentPrice) / point;
    return pips * parseFloat(volume) * 10;
  };

  const setSlFromPips = (pips: number, type: "buy" | "sell") => {
    if (!selectedPair || currentPrice === 0) return;
    const slPrice = type === "buy" 
      ? currentPrice - (pips * (selectedPair.point || 0.0001)) // For BUY, SL is below price
      : currentPrice + (pips * (selectedPair.point || 0.0001)); // For SELL, SL is above price
    setSl(slPrice.toFixed(5));
  };

  const setTpFromPips = (pips: number, type: "buy" | "sell") => {
    if (!selectedPair || currentPrice === 0) return;
    const tpPrice = type === "buy"
      ? currentPrice + (pips * (selectedPair.point || 0.0001)) // For BUY, TP is above price
      : currentPrice - (pips * (selectedPair.point || 0.0001)); // For SELL, TP is below price
    setTp(tpPrice.toFixed(5));
  };

  const validateSlTp = (type: "buy" | "sell"): string | null => {
    if (!selectedPair || currentPrice === 0) return null;
    
    if (sl) {
      const slPrice = parseFloat(sl);
      if (type === "buy" && slPrice >= currentPrice) {
        return `SL ${slPrice} must be BELOW current price ${currentPrice.toFixed(5)} for BUY`;
      }
      if (type === "sell" && slPrice <= currentPrice) {
        return `SL ${slPrice} must be ABOVE current price ${currentPrice.toFixed(5)} for SELL`;
      }
    }
    
    if (tp) {
      const tpPrice = parseFloat(tp);
      if (type === "buy" && tpPrice <= currentPrice) {
        return `TP ${tpPrice} must be ABOVE current price ${currentPrice.toFixed(5)} for BUY`;
      }
      if (type === "sell" && tpPrice >= currentPrice) {
        return `TP ${tpPrice} must be BELOW current price ${currentPrice.toFixed(5)} for SELL`;
      }
    }
    
    return null;
  };

  const handleTrade = (type: "buy" | "sell") => {
    const error = validateSlTp(type);
    if (error) {
      alert(error);
      return;
    }
    
    onTrade({
      symbol,
      volume: parseFloat(volume),
      type,
      sl: sl ? parseFloat(sl) : undefined,
      tp: tp ? parseFloat(tp) : undefined,
      comment: comment || undefined,
    });
    onClose();
    resetForm();
  };

  const risk = calculateRisk();
  const reward = calculateReward();
  const rrRatio = risk > 0 ? (reward / risk).toFixed(2) : "-";

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>⚡</span> Quick Trade
          </DialogTitle>
          <DialogDescription>
            Execute a manual trade with custom parameters
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label htmlFor="symbol">Currency Pair</Label>
            <Select value={symbol} onValueChange={setSymbol}>
              <SelectTrigger>
                <SelectValue placeholder="Select currency..." />
              </SelectTrigger>
              <SelectContent>
                {currencies.map((pair) => (
                  <SelectItem key={pair.symbol} value={pair.symbol}>
                    {pair.symbol} - {pair.description}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="volume">Lots</Label>
              <Input
                id="volume"
                type="number"
                step="0.01"
                min="0.01"
                value={volume}
                onChange={(e) => setVolume(e.target.value)}
              />
            </div>
            <div>
              <Label>Current Price</Label>
              <div className="flex gap-2 mt-2 text-sm">
                <span className="text-muted-foreground">
                  Price: <strong className="text-foreground font-mono">
                    {loadingPrice ? "Loading..." : currentPrice > 0 ? currentPrice.toFixed(5) : "-"}
                  </strong>
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="sl">Stop Loss (SL)</Label>
              <Input
                id="sl"
                type="number"
                step="0.00001"
                placeholder="Optional"
                value={sl}
                onChange={(e) => setSl(e.target.value)}
              />
              <div className="flex gap-1 mt-1">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="text-xs h-6 px-2"
                  onClick={() => setSlFromPips(20, "buy")}
                >
                  -20 pips
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="text-xs h-6 px-2"
                  onClick={() => setSlFromPips(50, "buy")}
                >
                  -50 pips
                </Button>
              </div>
            </div>
            <div>
              <Label htmlFor="tp">Take Profit (TP)</Label>
              <Input
                id="tp"
                type="number"
                step="0.00001"
                placeholder="Optional"
                value={tp}
                onChange={(e) => setTp(e.target.value)}
              />
              <div className="flex gap-1 mt-1">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="text-xs h-6 px-2"
                  onClick={() => setTpFromPips(50, "buy")}
                >
                  +50 pips
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="text-xs h-6 px-2"
                  onClick={() => setTpFromPips(100, "buy")}
                >
                  +100 pips
                </Button>
              </div>
            </div>
          </div>

          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <h4 className="font-semibold flex items-center gap-2">
              <span>📊</span> Profit Calculator
            </h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">Position Value:</span>
              <span className="font-mono text-right">${(parseFloat(volume) * 100000).toLocaleString()}</span>
              <span className="text-muted-foreground">Risk (if SL hit):</span>
              <span className="font-mono text-right text-loss">${risk.toFixed(2)}</span>
              <span className="text-muted-foreground">Reward (if TP hit):</span>
              <span className="font-mono text-right text-profit">${reward.toFixed(2)}</span>
              <span className="text-muted-foreground">Risk/Reward Ratio:</span>
              <span className="font-mono text-right">{rrRatio}</span>
            </div>
          </div>

          <div>
            <Label htmlFor="comment">Comment</Label>
            <Input
              id="comment"
              placeholder="Optional trade comment"
              maxLength={30}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </div>

          <div className="flex gap-3">
            <Button
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              size="lg"
              onClick={() => handleTrade("buy")}
              disabled={!symbol}
            >
              <TrendingUp className="h-5 w-5 mr-2" />
              BUY
            </Button>
            <Button
              className="flex-1 bg-red-600 hover:bg-red-700"
              size="lg"
              onClick={() => handleTrade("sell")}
              disabled={!symbol}
            >
              <TrendingDown className="h-5 w-5 mr-2" />
              SELL
            </Button>
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

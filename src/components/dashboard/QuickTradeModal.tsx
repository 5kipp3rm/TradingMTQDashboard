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

  /**
   * Calculate P&L in USD
   * Formula: Pips × Pip Value × Lot Size
   * 
   * Pip value depends on symbol:
   * - EURUSD (4 decimals): 1 pip = $10 per lot
   * - XAUUSD (2 decimals): 1 pip = $1 per lot
   * - USDJPY (2 decimals): 1 pip = $10 per lot (different calculation)
   */
  const calculateProfitLoss = (targetPrice: number, isLoss: boolean): number => {
    if (!selectedPair || !targetPrice || currentPrice === 0) return 0;
    
    const point = selectedPair.point || 0.0001;
    const volume_lots = parseFloat(volume);
    
    // Calculate pips difference
    const pips = Math.abs(targetPrice - currentPrice) / point;
    
    // Get pip value based on symbol
    // For forex pairs (EURUSD, GBPUSD, etc): pip value = 10 * lot_size
    // For metals (XAUUSD): pip value = 1 * lot_size  
    // For JPY pairs (USDJPY): pip value = 10 * lot_size
    let pip_value = 10; // Default for most forex pairs
    
    if (selectedPair.symbol?.includes('XAU')) {
      pip_value = 1; // Gold: 1 pip = $1 per lot
    } else if (selectedPair.symbol?.includes('JPY')) {
      pip_value = 10; // JPY pairs: 1 pip = $10 per lot
    }
    
    const profitLoss = pips * pip_value * volume_lots;
    
    // Return as loss (negative) or profit (positive)
    return isLoss ? -profitLoss : profitLoss;
  };

  const calculateRisk = () => {
    if (!selectedPair || !sl || currentPrice === 0) return 0;
    const slPrice = parseFloat(sl);
    return Math.abs(calculateProfitLoss(slPrice, true));
  };

  const calculateReward = () => {
    if (!selectedPair || !tp || currentPrice === 0) return 0;
    const tpPrice = parseFloat(tp);
    return calculateProfitLoss(tpPrice, false);
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

          <div className="bg-muted/50 rounded-lg p-4 space-y-3">
            <h4 className="font-semibold flex items-center gap-2">
              <span>📊</span> Trade Analysis
            </h4>
            
            {/* Entry Info */}
            <div className="grid grid-cols-2 gap-2 text-sm border-b pb-3">
              <span className="text-muted-foreground">Entry Price:</span>
              <span className="font-mono text-right">{currentPrice > 0 ? currentPrice.toFixed(5) : "-"}</span>
              <span className="text-muted-foreground">Position Size:</span>
              <span className="font-mono text-right">{volume} lots</span>
              <span className="text-muted-foreground">Position Value:</span>
              <span className="font-mono text-right">${(parseFloat(volume) * 100000).toLocaleString()}</span>
            </div>
            
            {/* Stop Loss Exit */}
            {sl && (
              <div className="grid grid-cols-2 gap-2 text-sm border-b pb-3">
                <span className="text-muted-foreground font-semibold flex items-center gap-1">
                  <span>🛑</span> Stop Loss Exit:
                </span>
                <span></span>
                <span className="text-muted-foreground ml-4">SL Price:</span>
                <span className="font-mono text-right">{parseFloat(sl).toFixed(5)}</span>
                <span className="text-muted-foreground ml-4">Max Loss:</span>
                <span className={`font-mono text-right font-semibold ${calculateRisk() > 0 ? 'text-red-600' : ''}`}>
                  -${calculateRisk().toFixed(2)}
                </span>
              </div>
            )}
            
            {/* Take Profit Exit */}
            {tp && (
              <div className="grid grid-cols-2 gap-2 text-sm border-b pb-3">
                <span className="text-muted-foreground font-semibold flex items-center gap-1">
                  <span>🎯</span> Take Profit Exit:
                </span>
                <span></span>
                <span className="text-muted-foreground ml-4">TP Price:</span>
                <span className="font-mono text-right">{parseFloat(tp).toFixed(5)}</span>
                <span className="text-muted-foreground ml-4">Potential Profit:</span>
                <span className={`font-mono text-right font-semibold ${calculateReward() > 0 ? 'text-green-600' : ''}`}>
                  +${calculateReward().toFixed(2)}
                </span>
              </div>
            )}
            
            {/* Risk/Reward Summary */}
            {sl && tp && (
              <div className="grid grid-cols-2 gap-2 text-sm pt-3">
                <span className="text-muted-foreground font-semibold">Risk/Reward Ratio:</span>
                <span className="font-mono text-right font-semibold">1:{(calculateReward() / calculateRisk()).toFixed(2)}</span>
              </div>
            )}
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

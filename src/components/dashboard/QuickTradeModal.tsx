import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
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

  const selectedPair = currencies.find((c) => c.symbol === symbol);

  useEffect(() => {
    if (open && currencies.length > 0 && !symbol) {
      setSymbol(currencies[0].symbol);
    }
  }, [open, currencies, symbol]);

  const handleTrade = (type: "buy" | "sell") => {
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

  const resetForm = () => {
    setVolume("0.10");
    setSl("");
    setTp("");
    setComment("");
  };

  const calculateRisk = () => {
    if (!selectedPair || !sl) return 0;
    const price = selectedPair.bid;
    const slPrice = parseFloat(sl);
    const pips = Math.abs(price - slPrice) * 10000;
    return pips * parseFloat(volume) * 10;
  };

  const calculateReward = () => {
    if (!selectedPair || !tp) return 0;
    const price = selectedPair.ask;
    const tpPrice = parseFloat(tp);
    const pips = Math.abs(tpPrice - price) * 10000;
    return pips * parseFloat(volume) * 10;
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
                  Bid: <strong className="text-foreground font-mono">{selectedPair?.bid.toFixed(5) || "-"}</strong>
                </span>
                <span className="text-muted-foreground">
                  Ask: <strong className="text-foreground font-mono">{selectedPair?.ask.toFixed(5) || "-"}</strong>
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

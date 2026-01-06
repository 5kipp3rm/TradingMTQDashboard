import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, Edit, Trash2, Check, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { currenciesV2Api } from "@/lib/api-v2";
import { CurrencyConfigModal } from "./CurrencyConfigModal";
import type { CurrencyConfig } from "@/lib/api-v2";

interface CurrenciesCardProps {
  accountId: number;
  currencies: CurrencyConfig[];
  onRefresh: () => void;
}

export const CurrenciesCard = ({ accountId, currencies, onRefresh }: CurrenciesCardProps) => {
  const { toast } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCurrency, setSelectedCurrency] = useState<CurrencyConfig | null>(null);

  const handleAddCurrency = () => {
    setSelectedCurrency(null);
    setModalOpen(true);
  };

  const handleEditCurrency = (currency: CurrencyConfig) => {
    setSelectedCurrency(currency);
    setModalOpen(true);
  };

  const handleDeleteCurrency = async (symbol: string) => {
    if (!confirm(`Are you sure you want to remove ${symbol}?`)) {
      return;
    }

    const response = await currenciesV2Api.delete(accountId, symbol);

    if (response.data?.success) {
      toast({
        title: "Success",
        description: `${symbol} removed successfully`,
      });
      onRefresh();
    } else {
      toast({
        title: "Error",
        description: response.error || "Failed to remove currency",
        variant: "destructive",
      });
    }
  };

  const handleToggleEnabled = async (currency: CurrencyConfig) => {
    const response = await currenciesV2Api.update(accountId, currency.symbol, {
      enabled: !currency.enabled,
    });

    if (response.data?.success) {
      toast({
        title: "Success",
        description: `${currency.symbol} ${!currency.enabled ? "enabled" : "disabled"}`,
      });
      onRefresh();
    } else {
      toast({
        title: "Error",
        description: response.error || "Failed to update currency",
        variant: "destructive",
      });
    }
  };

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Currencies</CardTitle>
          <Button size="sm" onClick={handleAddCurrency}>
            <Plus className="h-4 w-4 mr-2" />
            Add Currency
          </Button>
        </CardHeader>
        <CardContent>
          {currencies.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No currencies configured</p>
              <p className="text-sm mt-2">Click "Add Currency" to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {currencies.map((currency) => (
                <div
                  key={currency.symbol}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {currency.enabled ? (
                        <Check className="h-4 w-4 text-success" />
                      ) : (
                        <X className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className="font-semibold">{currency.symbol}</span>
                    </div>

                    <Badge variant="outline">{currency.strategy_type}</Badge>

                    <div className="text-sm text-muted-foreground">
                      Risk: {currency.risk_percent}% | SL: {currency.sl_pips}p | TP:{" "}
                      {currency.tp_pips}p
                    </div>

                    <div className="text-sm text-muted-foreground">{currency.timeframe}</div>
                  </div>

                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleEnabled(currency)}
                      title={currency.enabled ? "Disable" : "Enable"}
                    >
                      {currency.enabled ? (
                        <X className="h-4 w-4" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditCurrency(currency)}
                      title="Edit"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleDeleteCurrency(currency.symbol)}
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <CurrencyConfigModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedCurrency(null);
        }}
        accountId={accountId}
        currency={selectedCurrency}
        onSuccess={onRefresh}
      />
    </>
  );
};

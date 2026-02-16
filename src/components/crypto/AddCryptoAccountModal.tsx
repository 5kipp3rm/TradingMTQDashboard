import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
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
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Eye, EyeOff, AlertCircle } from "lucide-react";
import type { CreateAccountRequest } from "@/types/crypto";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface AddCryptoAccountModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (account: CreateAccountRequest) => void;
}

const exchanges = [
  { value: "BINANCE", label: "Binance" },
  { value: "KRAKEN", label: "Kraken (Coming Soon)", disabled: true },
  { value: "COINBASE", label: "Coinbase (Coming Soon)", disabled: true },
];

export function AddCryptoAccountModal({ open, onClose, onAdd }: AddCryptoAccountModalProps) {
  const [accountName, setAccountName] = useState("");
  const [exchange, setExchange] = useState("BINANCE");
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [testnet, setTestnet] = useState(false);
  const [isActive, setIsActive] = useState(true);
  const [autoConnect, setAutoConnect] = useState(true);
  const [description, setDescription] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [showApiSecret, setShowApiSecret] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd({
      account_name: accountName,
      exchange,
      api_key: apiKey,
      api_secret: apiSecret,
      testnet,
      is_active: isActive,
      auto_connect: autoConnect,
      description: description || undefined,
    });
    resetForm();
  };

  const resetForm = () => {
    setAccountName("");
    setExchange("BINANCE");
    setApiKey("");
    setApiSecret("");
    setTestnet(false);
    setIsActive(true);
    setAutoConnect(true);
    setDescription("");
    setShowApiKey(false);
    setShowApiSecret(false);
  };

  const isValid = accountName && exchange && apiKey && apiSecret;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[550px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Add Crypto Trading Account
          </DialogTitle>
          <DialogDescription>
            Connect your cryptocurrency exchange account to start trading.
            Your API credentials are encrypted and stored securely.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Alert about API permissions */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Ensure your API key has trading permissions enabled on the exchange.
              For testnet accounts, use testnet API credentials.
            </AlertDescription>
          </Alert>

          {/* Account Name */}
          <div>
            <Label htmlFor="accountName">Account Name</Label>
            <Input
              id="accountName"
              placeholder="e.g., My Binance Account"
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
              required
            />
          </div>

          {/* Exchange Selection */}
          <div>
            <Label htmlFor="exchange">Exchange</Label>
            <Select value={exchange} onValueChange={setExchange}>
              <SelectTrigger>
                <SelectValue placeholder="Select exchange" />
              </SelectTrigger>
              <SelectContent>
                {exchanges.map((ex) => (
                  <SelectItem key={ex.value} value={ex.value} disabled={ex.disabled}>
                    {ex.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* API Key */}
          <div>
            <Label htmlFor="apiKey">API Key</Label>
            <div className="relative">
              <Input
                id="apiKey"
                type={showApiKey ? "text" : "password"}
                placeholder="Enter your API key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="pr-10 font-mono text-sm"
                required
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>
          </div>

          {/* API Secret */}
          <div>
            <Label htmlFor="apiSecret">API Secret</Label>
            <div className="relative">
              <Input
                id="apiSecret"
                type={showApiSecret ? "text" : "password"}
                placeholder="Enter your API secret"
                value={apiSecret}
                onChange={(e) => setApiSecret(e.target.value)}
                className="pr-10 font-mono text-sm"
                required
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={() => setShowApiSecret(!showApiSecret)}
              >
                {showApiSecret ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>
          </div>

          {/* Description */}
          <div>
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              placeholder="Add notes about this account..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>

          {/* Checkboxes */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="testnet"
                checked={testnet}
                onCheckedChange={(checked) => setTestnet(checked as boolean)}
              />
              <Label htmlFor="testnet" className="text-sm font-normal cursor-pointer">
                Testnet account (sandbox mode)
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="isActive"
                checked={isActive}
                onCheckedChange={(checked) => setIsActive(checked as boolean)}
              />
              <Label htmlFor="isActive" className="text-sm font-normal cursor-pointer">
                Active (enable trading)
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="autoConnect"
                checked={autoConnect}
                onCheckedChange={(checked) => setAutoConnect(checked as boolean)}
              />
              <Label htmlFor="autoConnect" className="text-sm font-normal cursor-pointer">
                Auto-connect on startup
              </Label>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid}>
              Add Account
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

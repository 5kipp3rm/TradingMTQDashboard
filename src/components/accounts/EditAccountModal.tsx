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
import { Checkbox } from "@/components/ui/checkbox";
import { Edit } from "lucide-react";
import type { Account } from "@/types/trading";

interface EditAccountModalProps {
  open: boolean;
  onClose: () => void;
  account: Account | null;
  onSave: (id: string, updates: {
    account_name?: string;
    broker?: string;
    server?: string;
    is_demo?: boolean;
    is_active?: boolean;
    is_default?: boolean;
    initial_balance?: number;
    description?: string;
  }) => void;
}

const platforms = ["MT4", "MT5"];

export function EditAccountModal({ open, onClose, account, onSave }: EditAccountModalProps) {
  const [name, setName] = useState("");
  const [broker, setBroker] = useState("");
  const [server, setServer] = useState("");
  const [initialBalance, setInitialBalance] = useState("");
  const [description, setDescription] = useState("");
  const [isDemo, setIsDemo] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [isDefault, setIsDefault] = useState(false);

  useEffect(() => {
    if (account) {
      setName(account.account_name || "");
      setBroker(account.broker || "");
      setServer(account.server || "");
      setInitialBalance(account.initial_balance?.toString() || "");
      setDescription(account.description || "");
      setIsDemo(account.is_demo || false);
      setIsActive(account.is_active || false);
      setIsDefault(account.is_default || false);
    }
  }, [account]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!account) return;

    const updates: any = {};
    if (name !== account.account_name) updates.account_name = name;
    if (broker !== account.broker) updates.broker = broker;
    if (server !== account.server) updates.server = server;
    if (initialBalance && parseFloat(initialBalance) !== account.initial_balance) {
      updates.initial_balance = parseFloat(initialBalance);
    }
    if (description !== account.description) updates.description = description;
    if (isDemo !== account.is_demo) updates.is_demo = isDemo;
    if (isActive !== account.is_active) updates.is_active = isActive;
    if (isDefault !== account.is_default) updates.is_default = isDefault;

    onSave(account.id, updates);
    onClose();
  };

  const isValid = name && broker && server;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit className="h-5 w-5" />
            Edit Account
          </DialogTitle>
          <DialogDescription>
            Update account settings and configuration
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Account Name</Label>
            <Input
              id="name"
              placeholder="e.g., My Main Account"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="broker">Broker</Label>
              <Input
                id="broker"
                placeholder="e.g., ICMarkets"
                value={broker}
                onChange={(e) => setBroker(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="server">Server</Label>
              <Input
                id="server"
                placeholder="e.g., Demo"
                value={server}
                onChange={(e) => setServer(e.target.value)}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="initialBalance">Initial Balance</Label>
            <Input
              id="initialBalance"
              type="number"
              step="0.01"
              placeholder="e.g., 10000.00"
              value={initialBalance}
              onChange={(e) => setInitialBalance(e.target.value)}
            />
          </div>

          <div>
            <Label htmlFor="description">Description (Optional)</Label>
            <Input
              id="description"
              placeholder="Account notes"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="isDemo"
                checked={isDemo}
                onCheckedChange={(checked) => setIsDemo(checked as boolean)}
              />
              <Label htmlFor="isDemo" className="text-sm font-normal cursor-pointer">
                Demo account
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="isActive"
                checked={isActive}
                onCheckedChange={(checked) => setIsActive(checked as boolean)}
              />
              <Label htmlFor="isActive" className="text-sm font-normal cursor-pointer">
                Active
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="isDefault"
                checked={isDefault}
                onCheckedChange={(checked) => setIsDefault(checked as boolean)}
              />
              <Label htmlFor="isDefault" className="text-sm font-normal cursor-pointer">
                Set as default account
              </Label>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid}>
              Save Changes
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Eye, Check, X } from "lucide-react";
import type { Account } from "@/types/trading";

interface ViewAccountModalProps {
  open: boolean;
  onClose: () => void;
  account: Account | null;
}

export function ViewAccountModal({ open, onClose, account }: ViewAccountModalProps) {
  if (!account) return null;

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleString();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Account Details
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b">
            <h3 className="text-lg font-semibold">{account.account_name}</h3>
            <div className="flex gap-2">
              {account.is_active && (
                <Badge variant="default" className="bg-success">
                  <Check className="h-3 w-3 mr-1" />
                  Active
                </Badge>
              )}
              {account.is_default && (
                <Badge variant="secondary">Default</Badge>
              )}
              {account.is_demo && (
                <Badge variant="outline">Demo</Badge>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Account Number</p>
              <p className="font-mono font-semibold">{account.account_number}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Login</p>
              <p className="font-mono font-semibold">{account.login}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Broker</p>
              <p className="font-semibold">{account.broker}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Server</p>
              <p className="font-semibold">{account.server}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Platform</p>
              <p className="font-semibold">{account.platform_type}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Currency</p>
              <p className="font-semibold">{account.currency}</p>
            </div>
          </div>

          <div>
            <p className="text-sm text-muted-foreground">Initial Balance</p>
            <p className="font-mono text-lg font-semibold">
              ${account.initial_balance ? Number(account.initial_balance).toLocaleString() : '0.00'}
            </p>
          </div>

          {account.description && (
            <div>
              <p className="text-sm text-muted-foreground">Description</p>
              <p className="text-sm">{account.description}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 pt-3 border-t">
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="text-xs">{formatDate(account.created_at)}</p>
            </div>
            {account.updated_at && (
              <div>
                <p className="text-sm text-muted-foreground">Updated</p>
                <p className="text-xs">{formatDate(account.updated_at)}</p>
              </div>
            )}
          </div>

          {account.last_connected && (
            <div>
              <p className="text-sm text-muted-foreground">Last Connected</p>
              <p className="text-xs">{formatDate(account.last_connected)}</p>
            </div>
          )}

          <div className="flex justify-end pt-4">
            <Button onClick={onClose}>Close</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

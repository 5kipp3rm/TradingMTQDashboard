import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Header } from "@/components/dashboard/Header";
import { AddCryptoAccountModal } from "@/components/crypto/AddCryptoAccountModal";
import { Plus, Edit, Trash2, Check, Link as LinkIcon, AlertCircle, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import {
  useCryptoAccounts,
  useCreateCryptoAccount,
  useDeleteCryptoAccount,
} from "@/hooks/useCryptoAPI";
import type { CreateAccountRequest } from "@/types/crypto";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const CryptoAccounts = () => {
  const { data: accounts, isLoading, refetch } = useCryptoAccounts();
  const createAccount = useCreateCryptoAccount();
  const deleteAccount = useDeleteCryptoAccount();
  const [addAccountOpen, setAddAccountOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const { toast } = useToast();

  const handleAddAccount = async (accountData: CreateAccountRequest) => {
    try {
      await createAccount.mutateAsync(accountData);
      toast({
        title: "Account Created",
        description: `${accountData.account_name} has been added successfully.`,
      });
      setAddAccountOpen(false);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to create account",
        variant: "destructive",
      });
    }
  };

  const handleDeleteClick = (accountId: number) => {
    setSelectedAccountId(accountId);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (selectedAccountId === null) return;

    try {
      await deleteAccount.mutateAsync(selectedAccountId);
      toast({
        title: "Account Deleted",
        description: "The crypto account has been removed.",
      });
      setDeleteConfirmOpen(false);
      setSelectedAccountId(null);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to delete account",
        variant: "destructive",
      });
    }
  };

  const getConnectionStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'connected':
        return 'bg-success';
      case 'connecting':
        return 'bg-warning';
      case 'disconnected':
      case 'error':
        return 'bg-destructive';
      default:
        return 'bg-muted';
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={30}
          onPeriodChange={() => {}}
          onRefresh={() => refetch()}
          onQuickTrade={() => {}}
        />

        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Crypto Trading Accounts</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Manage your cryptocurrency exchange accounts
            </p>
          </div>
          <Button onClick={() => setAddAccountOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Account
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : accounts && accounts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {accounts.map((account) => (
              <Card
                key={account.account_id}
                className={`card-glow ${account.is_active ? "ring-2 ring-primary" : ""}`}
              >
                <CardHeader className="flex flex-row items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{account.account_name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {account.exchange}
                      {account.testnet && (
                        <Badge variant="outline" className="ml-2">
                          Testnet
                        </Badge>
                      )}
                    </p>
                  </div>
                  {account.is_active && (
                    <Badge variant="default" className="bg-success">
                      <Check className="h-3 w-3 mr-1" />
                      Active
                    </Badge>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Connection Status */}
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Status</span>
                      <Badge
                        variant="outline"
                        className={getConnectionStatusColor(account.connection_status)}
                      >
                        {account.connection_status}
                      </Badge>
                    </div>

                    {/* Balance Summary */}
                    {account.balance_summary && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Total Assets</span>
                          <span className="font-mono font-semibold">
                            ${account.balance_summary.total_assets.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Balances</span>
                          <span className="text-sm">
                            {account.balance_summary.balances.length} assets
                          </span>
                        </div>
                      </>
                    )}

                    {/* Auto Connect */}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Auto Connect</span>
                      <Badge variant="outline">
                        {account.auto_connect ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>

                    {/* Description */}
                    {account.description && (
                      <div className="pt-2 border-t border-border">
                        <p className="text-xs text-muted-foreground">{account.description}</p>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => refetch()}
                        title="Refresh"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled
                        title="Edit (Coming Soon)"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleDeleteClick(account.account_id)}
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="card-glow">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Crypto Accounts</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Get started by adding your first cryptocurrency exchange account
              </p>
              <Button onClick={() => setAddAccountOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Account
              </Button>
            </CardContent>
          </Card>
        )}

        <AddCryptoAccountModal
          open={addAccountOpen}
          onClose={() => setAddAccountOpen(false)}
          onAdd={handleAddAccount}
        />

        <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Crypto Account?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the account
                and remove all associated data.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeleteConfirm}
                className="bg-destructive hover:bg-destructive/90"
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
};

export default CryptoAccounts;

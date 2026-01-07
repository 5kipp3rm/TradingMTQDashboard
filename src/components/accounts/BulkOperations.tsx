import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/hooks/use-toast';
import { accountsV2Api } from '@/lib/api-v2';
import { Spinner } from '@/components/ui/spinner';
import { Play, Square, Wifi, WifiOff } from 'lucide-react';

interface BulkOperationsProps {
  selectedCount: number;
  onSuccess?: () => void;
}

export function BulkOperations({ selectedCount, onSuccess }: BulkOperationsProps) {
  const [confirmAction, setConfirmAction] = useState<{ open: boolean; action: string; title: string; description: string; fn: () => Promise<void> }>({
    open: false,
    action: '',
    title: '',
    description: '',
    fn: async () => {},
  });
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleBulkAction = async (
    action: string,
    title: string,
    description: string,
    apiFn: () => Promise<any>
  ) => {
    setConfirmAction({
      open: true,
      action,
      title,
      description,
      fn: async () => {
        setIsLoading(true);
        try {
          const response = await apiFn();
          if (response.data) {
            const result = response.data as any;
            toast({
              title: `${title} Complete`,
              description: `Successfully ${action} ${result.success_count || 0} accounts${result.failed_count ? `, ${result.failed_count} failed` : ''}.`,
            });
            onSuccess?.();
          } else if (response.error) {
            toast({
              variant: 'destructive',
              title: 'Error',
              description: response.error,
            });
          }
        } catch (error) {
          console.error(`Failed to ${action}:`, error);
          toast({
            variant: 'destructive',
            title: 'Error',
            description: `Failed to ${action} accounts`,
          });
        } finally {
          setIsLoading(false);
          setConfirmAction({ ...confirmAction, open: false });
        }
      },
    });
  };

  return (
    <>
      <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg border">
        <Badge variant="secondary" className="text-sm">
          {selectedCount} All Accounts
        </Badge>
        
        <div className="flex gap-2 ml-auto">
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              handleBulkAction(
                'connect',
                'Connect All',
                'This will connect all accounts to their MT5 servers.',
                accountsV2Api.connectAll
              )
            }
            disabled={isLoading}
          >
            <Wifi className="h-4 w-4 mr-1" />
            Connect All
          </Button>
          
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              handleBulkAction(
                'disconnect',
                'Disconnect All',
                'This will disconnect all accounts from their MT5 servers.',
                accountsV2Api.disconnectAll
              )
            }
            disabled={isLoading}
          >
            <WifiOff className="h-4 w-4 mr-1" />
            Disconnect All
          </Button>
          
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              handleBulkAction(
                'start trading',
                'Start All Trading',
                'This will start trading on all connected accounts.',
                accountsV2Api.startAllTrading
              )
            }
            disabled={isLoading}
          >
            <Play className="h-4 w-4 mr-1" />
            Start All
          </Button>
          
          <Button
            size="sm"
            variant="destructive"
            onClick={() =>
              handleBulkAction(
                'stop trading',
                'Stop All Trading',
                'This will stop trading on all accounts immediately.',
                accountsV2Api.stopAllTrading
              )
            }
            disabled={isLoading}
          >
            <Square className="h-4 w-4 mr-1" />
            Stop All
          </Button>
        </div>
      </div>

      <AlertDialog open={confirmAction.open} onOpenChange={(open) => setConfirmAction({ ...confirmAction, open })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmAction.title}</AlertDialogTitle>
            <AlertDialogDescription>{confirmAction.description}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isLoading}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => confirmAction.fn()}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Processing...
                </>
              ) : (
                'Confirm'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

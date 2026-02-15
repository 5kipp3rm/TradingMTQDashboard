/**
 * StrategyCard Component
 * Displays individual strategy with AI configuration status
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Brain,
  MessageSquare,
  BarChart3,
  Settings,
  Play,
  Pause,
  Trash2,
  TrendingUp,
  TrendingDown,
  Activity,
} from 'lucide-react';
import { strategiesApi, Strategy } from '@/lib/strategies-api';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
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
import AIConfigPanel from './AIConfigPanel';

interface StrategyCardProps {
  strategy: Strategy;
  accountId: number;
}

export default function StrategyCard({ strategy, accountId }: StrategyCardProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [showAIConfig, setShowAIConfig] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Toggle enabled mutation
  const toggleEnabledMutation = useMutation({
    mutationFn: () => 
      strategy.enabled 
        ? strategiesApi.disable(accountId, strategy.symbol)
        : strategiesApi.enable(accountId, strategy.symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies', accountId] });
      toast({
        title: strategy.enabled ? 'Strategy Disabled' : 'Strategy Enabled',
        description: `${strategy.symbol} strategy ${strategy.enabled ? 'paused' : 'activated'}`,
      });
    },
    onError: (error: Error) => {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message,
      });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => strategiesApi.delete(accountId, strategy.symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies', accountId] });
      toast({
        title: 'Strategy Deleted',
        description: `${strategy.symbol} strategy removed`,
      });
    },
    onError: (error: Error) => {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message,
      });
    },
  });

  const handleToggleEnabled = () => {
    toggleEnabledMutation.mutate();
  };

  const handleDelete = () => {
    deleteMutation.mutate();
    setShowDeleteDialog(false);
  };

  // AI features count
  const aiFeatures = [
    strategy.use_ml_enhancement && 'ML Enhancement',
    strategy.use_llm_sentiment && 'LLM Sentiment',
    strategy.use_llm_analyst && 'LLM Analyst',
  ].filter(Boolean);

  return (
    <>
      <Card className={`${!strategy.enabled ? 'opacity-60' : ''} hover:shadow-lg transition-shadow`}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {strategy.symbol}
                {strategy.enabled ? (
                  <Badge variant="default" className="bg-green-500">
                    <Activity className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                ) : (
                  <Badge variant="secondary">
                    <Pause className="h-3 w-3 mr-1" />
                    Paused
                  </Badge>
                )}
              </CardTitle>
              <CardDescription className="mt-1">
                {strategy.strategy_type} • {strategy.execution_mode}
              </CardDescription>
            </div>
            <Switch
              checked={strategy.enabled}
              onCheckedChange={handleToggleEnabled}
              disabled={toggleEnabledMutation.isPending}
            />
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* AI Features */}
          {aiFeatures.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {strategy.use_ml_enhancement && (
                <Badge variant="outline" className="border-blue-500 text-blue-600">
                  <Brain className="h-3 w-3 mr-1" />
                  ML: {strategy.ml_model_type?.toUpperCase()}
                </Badge>
              )}
              {strategy.use_llm_sentiment && (
                <Badge variant="outline" className="border-purple-500 text-purple-600">
                  <MessageSquare className="h-3 w-3 mr-1" />
                  Sentiment
                </Badge>
              )}
              {strategy.use_llm_analyst && (
                <Badge variant="outline" className="border-purple-500 text-purple-600">
                  <BarChart3 className="h-3 w-3 mr-1" />
                  Analyst
                </Badge>
              )}
            </div>
          )}

          {/* Strategy Parameters */}
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Execution:</span>
              <span className="font-medium capitalize">{strategy.execution_mode}</span>
            </div>
            {strategy.strategy_params && Object.keys(strategy.strategy_params).length > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500">Parameters:</span>
                <span className="font-medium">{Object.keys(strategy.strategy_params).length} configured</span>
              </div>
            )}
          </div>

          {/* No AI Warning */}
          {aiFeatures.length === 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm">
              <p className="text-yellow-800">
                💡 No AI features enabled. Configure ML or LLM to enhance this strategy.
              </p>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => setShowAIConfig(true)}
          >
            <Settings className="h-4 w-4 mr-1" />
            Configure AI
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDeleteDialog(true)}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </CardFooter>
      </Card>

      {/* AI Config Dialog */}
      {showAIConfig && (
        <AIConfigPanel
          strategy={strategy}
          accountId={accountId}
          open={showAIConfig}
          onOpenChange={setShowAIConfig}
        />
      )}

      {/* Delete Confirmation */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Strategy?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove the <strong>{strategy.symbol}</strong> strategy configuration.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

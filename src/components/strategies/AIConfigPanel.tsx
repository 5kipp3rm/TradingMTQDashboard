/**
 * AIConfigPanel Component - Phase 5
 * Per-symbol ML/LLM configuration interface
 */

import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Brain, MessageSquare, BarChart3, Save, Info } from 'lucide-react';
import { strategiesApi, Strategy, ML_MODEL_TYPES, LLM_PROVIDERS } from '@/lib/strategies-api';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Separator } from '@/components/ui/separator';

interface AIConfigPanelProps {
  strategy: Strategy;
  accountId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function AIConfigPanel({ strategy, accountId, open, onOpenChange }: AIConfigPanelProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Local state for configuration
  const [mlEnabled, setMlEnabled] = useState(strategy.use_ml_enhancement || false);
  const [mlModelType, setMlModelType] = useState<'lstm' | 'random_forest'>(
    strategy.ml_model_type || 'lstm'
  );

  const [sentimentEnabled, setSentimentEnabled] = useState(strategy.use_llm_sentiment || false);
  const [sentimentProvider, setSentimentProvider] = useState<'openai' | 'anthropic'>(
    strategy.llm_sentiment_provider || 'openai'
  );
  const [sentimentModel, setSentimentModel] = useState(
    strategy.llm_sentiment_model || 'gpt-4'
  );

  const [analystEnabled, setAnalystEnabled] = useState(strategy.use_llm_analyst || false);
  const [analystProvider, setAnalystProvider] = useState<'openai' | 'anthropic'>(
    strategy.llm_analyst_provider || 'openai'
  );
  const [analystModel, setAnalystModel] = useState(
    strategy.llm_analyst_model || 'gpt-4'
  );

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: () => 
      strategiesApi.update(accountId, strategy.symbol, {
        use_ml_enhancement: mlEnabled,
        ml_model_type: mlEnabled ? mlModelType : null,
        
        use_llm_sentiment: sentimentEnabled,
        llm_sentiment_provider: sentimentEnabled ? sentimentProvider : null,
        llm_sentiment_model: sentimentEnabled ? sentimentModel : null,
        
        use_llm_analyst: analystEnabled,
        llm_analyst_provider: analystEnabled ? analystProvider : null,
        llm_analyst_model: analystEnabled ? analystModel : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies', accountId] });
      toast({
        title: 'AI Configuration Updated',
        description: `${strategy.symbol} AI settings saved successfully`,
      });
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message,
      });
    },
  });

  const handleSave = () => {
    updateMutation.mutate();
  };

  const handleCancel = () => {
    // Reset to original values
    setMlEnabled(strategy.use_ml_enhancement || false);
    setMlModelType(strategy.ml_model_type || 'lstm');
    setSentimentEnabled(strategy.use_llm_sentiment || false);
    setSentimentProvider(strategy.llm_sentiment_provider || 'openai');
    setSentimentModel(strategy.llm_sentiment_model || 'gpt-4');
    setAnalystEnabled(strategy.use_llm_analyst || false);
    setAnalystProvider(strategy.llm_analyst_provider || 'openai');
    setAnalystModel(strategy.llm_analyst_model || 'gpt-4');
    onOpenChange(false);
  };

  // Get available models for selected provider
  const getSentimentModels = () => {
    const provider = LLM_PROVIDERS.find(p => p.value === sentimentProvider);
    return provider?.models || [];
  };

  const getAnalystModels = () => {
    const provider = LLM_PROVIDERS.find(p => p.value === analystProvider);
    return provider?.models || [];
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>AI Configuration - {strategy.symbol}</DialogTitle>
          <DialogDescription>
            Configure ML enhancement and LLM features for this strategy
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* ML Enhancement Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-blue-600" />
                <div>
                  <h3 className="font-semibold">ML Enhancement</h3>
                  <p className="text-sm text-gray-500">Machine learning signal enhancement</p>
                </div>
              </div>
              <Switch
                checked={mlEnabled}
                onCheckedChange={setMlEnabled}
              />
            </div>

            {mlEnabled && (
              <div className="ml-7 space-y-3 border-l-2 border-blue-200 pl-4">
                <div className="space-y-2">
                  <Label htmlFor="ml-model">Model Type</Label>
                  <Select value={mlModelType} onValueChange={(v) => setMlModelType(v as any)}>
                    <SelectTrigger id="ml-model">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ML_MODEL_TYPES.map((model) => (
                        <SelectItem key={model.value} value={model.value}>
                          <div>
                            <div className="font-medium">{model.label}</div>
                            <div className="text-xs text-gray-500">{model.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                  <div className="flex gap-2">
                    <Info className="h-4 w-4 text-blue-600 mt-0.5" />
                    <div className="text-blue-800">
                      <strong>ML Enhancement:</strong> Processes raw strategy signals through a trained model
                      to improve signal quality and timing. Model weights are loaded automatically.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <Separator />

          {/* LLM Sentiment Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-purple-600" />
                <div>
                  <h3 className="font-semibold">LLM Sentiment Analysis</h3>
                  <p className="text-sm text-gray-500">Market sentiment from news & social media</p>
                </div>
              </div>
              <Switch
                checked={sentimentEnabled}
                onCheckedChange={setSentimentEnabled}
              />
            </div>

            {sentimentEnabled && (
              <div className="ml-7 space-y-3 border-l-2 border-purple-200 pl-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="sentiment-provider">Provider</Label>
                    <Select value={sentimentProvider} onValueChange={(v) => setSentimentProvider(v as any)}>
                      <SelectTrigger id="sentiment-provider">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {LLM_PROVIDERS.map((provider) => (
                          <SelectItem key={provider.value} value={provider.value}>
                            {provider.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="sentiment-model">Model</Label>
                    <Select value={sentimentModel} onValueChange={setSentimentModel}>
                      <SelectTrigger id="sentiment-model">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {getSentimentModels().map((model) => (
                          <SelectItem key={model} value={model}>
                            {model}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded p-3 text-sm">
                  <div className="flex gap-2">
                    <Info className="h-4 w-4 text-purple-600 mt-0.5" />
                    <div className="text-purple-800">
                      <strong>Sentiment Analysis:</strong> Analyzes recent news and social media
                      to gauge market sentiment, adding context to technical signals.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <Separator />

          {/* LLM Analyst Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-purple-600" />
                <div>
                  <h3 className="font-semibold">LLM Market Analyst</h3>
                  <p className="text-sm text-gray-500">Deep market analysis and reasoning</p>
                </div>
              </div>
              <Switch
                checked={analystEnabled}
                onCheckedChange={setAnalystEnabled}
              />
            </div>

            {analystEnabled && (
              <div className="ml-7 space-y-3 border-l-2 border-purple-200 pl-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="analyst-provider">Provider</Label>
                    <Select value={analystProvider} onValueChange={(v) => setAnalystProvider(v as any)}>
                      <SelectTrigger id="analyst-provider">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {LLM_PROVIDERS.map((provider) => (
                          <SelectItem key={provider.value} value={provider.value}>
                            {provider.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="analyst-model">Model</Label>
                    <Select value={analystModel} onValueChange={setAnalystModel}>
                      <SelectTrigger id="analyst-model">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {getAnalystModels().map((model) => (
                          <SelectItem key={model} value={model}>
                            {model}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded p-3 text-sm">
                  <div className="flex gap-2">
                    <Info className="h-4 w-4 text-purple-600 mt-0.5" />
                    <div className="text-purple-800">
                      <strong>Market Analyst:</strong> Performs comprehensive market analysis,
                      combining technical indicators with fundamental data for enhanced decision-making.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Summary */}
          <div className="bg-gray-50 border rounded p-4">
            <h4 className="font-semibold mb-2">Configuration Summary</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">ML Enhancement:</span>
                <span className={mlEnabled ? 'text-green-600 font-medium' : 'text-gray-400'}>
                  {mlEnabled ? `Enabled (${mlModelType.toUpperCase()})` : 'Disabled'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">LLM Sentiment:</span>
                <span className={sentimentEnabled ? 'text-purple-600 font-medium' : 'text-gray-400'}>
                  {sentimentEnabled ? `Enabled (${sentimentProvider}/${sentimentModel})` : 'Disabled'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">LLM Analyst:</span>
                <span className={analystEnabled ? 'text-purple-600 font-medium' : 'text-gray-400'}>
                  {analystEnabled ? `Enabled (${analystProvider}/${analystModel})` : 'Disabled'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            <Save className="h-4 w-4 mr-2" />
            {updateMutation.isPending ? 'Saving...' : 'Save Configuration'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

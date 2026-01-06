import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { aiConfigV2Api } from "@/lib/api-v2";
import type { AIConfig } from "@/lib/api-v2";
import { Bot, Brain, MessageSquare, TrendingUp, AlertCircle } from "lucide-react";

interface AIConfigModalProps {
  open: boolean;
  onClose: () => void;
  accountId: number;
  currentConfig?: AIConfig | null;
  onSuccess?: () => void;
}

const ML_MODEL_TYPES = [
  { value: "RandomForest", label: "Random Forest" },
  { value: "LSTM", label: "LSTM Neural Network" },
  { value: "XGBoost", label: "XGBoost" },
  { value: "GradientBoosting", label: "Gradient Boosting" },
];

const LLM_PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "cohere", label: "Cohere" },
];

const OPENAI_MODELS = [
  { value: "gpt-4", label: "GPT-4" },
  { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
  { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
];

const ANTHROPIC_MODELS = [
  { value: "claude-3-opus-20240229", label: "Claude 3 Opus" },
  { value: "claude-3-sonnet-20240229", label: "Claude 3 Sonnet" },
  { value: "claude-3-haiku-20240307", label: "Claude 3 Haiku" },
];

export const AIConfigModal = ({
  open,
  onClose,
  accountId,
  currentConfig,
  onSuccess,
}: AIConfigModalProps) => {
  const { toast } = useToast();

  // ML Enhancement State
  const [useML, setUseML] = useState(false);
  const [mlModelType, setMlModelType] = useState("RandomForest");

  // LLM Sentiment State
  const [useLLMSentiment, setUseLLMSentiment] = useState(false);
  const [sentimentProvider, setSentimentProvider] = useState("openai");
  const [sentimentModel, setSentimentModel] = useState("gpt-4");
  const [sentimentApiKey, setSentimentApiKey] = useState("");

  // LLM Analyst State
  const [useLLMAnalyst, setUseLLMAnalyst] = useState(false);
  const [analystProvider, setAnalystProvider] = useState("anthropic");
  const [analystModel, setAnalystModel] = useState("claude-3-sonnet-20240229");
  const [analystApiKey, setAnalystApiKey] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form when currentConfig changes
  useEffect(() => {
    if (currentConfig) {
      setUseML(currentConfig.use_ml_enhancement);
      setMlModelType(currentConfig.ml_model_type || "RandomForest");

      setUseLLMSentiment(currentConfig.use_llm_sentiment);
      setSentimentProvider(currentConfig.llm_sentiment_provider || "openai");
      setSentimentModel(currentConfig.llm_sentiment_model || "gpt-4");
      setSentimentApiKey(""); // Don't populate API keys for security

      setUseLLMAnalyst(currentConfig.use_llm_analyst);
      setAnalystProvider(currentConfig.llm_analyst_provider || "anthropic");
      setAnalystModel(currentConfig.llm_analyst_model || "claude-3-sonnet-20240229");
      setAnalystApiKey(""); // Don't populate API keys for security
    }
  }, [currentConfig, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const updateData: any = {
        use_ml_enhancement: useML,
        use_llm_sentiment: useLLMSentiment,
        use_llm_analyst: useLLMAnalyst,
      };

      if (useML) {
        updateData.ml_model_type = mlModelType;
      }

      if (useLLMSentiment) {
        updateData.llm_sentiment_provider = sentimentProvider;
        updateData.llm_sentiment_model = sentimentModel;
        if (sentimentApiKey) {
          updateData.llm_sentiment_api_key = sentimentApiKey;
        }
      }

      if (useLLMAnalyst) {
        updateData.llm_analyst_provider = analystProvider;
        updateData.llm_analyst_model = analystModel;
        if (analystApiKey) {
          updateData.llm_analyst_api_key = analystApiKey;
        }
      }

      const response = await aiConfigV2Api.update(accountId, updateData);

      if (response.data?.success) {
        toast({
          title: "Success",
          description: "AI configuration updated successfully",
        });
        onSuccess?.();
        onClose();
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to update AI configuration",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSentimentModels = () => {
    return sentimentProvider === "openai" ? OPENAI_MODELS : ANTHROPIC_MODELS;
  };

  const getAnalystModels = () => {
    return analystProvider === "openai" ? OPENAI_MODELS : ANTHROPIC_MODELS;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            AI Enhancement Configuration
          </DialogTitle>
          <DialogDescription>
            Configure machine learning models and LLM features for signal enhancement
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              AI enhancements can improve trading signals but may incur additional costs (especially
              LLM services). Test with demo accounts first.
            </AlertDescription>
          </Alert>

          <Tabs defaultValue="ml" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="ml">
                <Brain className="h-4 w-4 mr-2" />
                ML Enhancement
              </TabsTrigger>
              <TabsTrigger value="sentiment">
                <MessageSquare className="h-4 w-4 mr-2" />
                LLM Sentiment
              </TabsTrigger>
              <TabsTrigger value="analyst">
                <TrendingUp className="h-4 w-4 mr-2" />
                LLM Analyst
              </TabsTrigger>
            </TabsList>

            {/* ML Enhancement Tab */}
            <TabsContent value="ml" className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch id="use-ml" checked={useML} onCheckedChange={setUseML} />
                <Label htmlFor="use-ml" className="font-semibold">
                  Enable ML Signal Enhancement
                </Label>
              </div>

              {useML && (
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="space-y-2">
                    <Label htmlFor="ml-model-type">ML Model Type</Label>
                    <Select value={mlModelType} onValueChange={setMlModelType}>
                      <SelectTrigger id="ml-model-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ML_MODEL_TYPES.map((model) => (
                          <SelectItem key={model.value} value={model.value}>
                            {model.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Machine learning model to enhance signal confidence
                    </p>
                  </div>

                  <Alert>
                    <AlertDescription className="text-sm">
                      ML models analyze historical patterns and adjust signal confidence. No API key
                      required - models run locally.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </TabsContent>

            {/* LLM Sentiment Tab */}
            <TabsContent value="sentiment" className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="use-sentiment"
                  checked={useLLMSentiment}
                  onCheckedChange={setUseLLMSentiment}
                />
                <Label htmlFor="use-sentiment" className="font-semibold">
                  Enable LLM Sentiment Analysis
                </Label>
              </div>

              {useLLMSentiment && (
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="space-y-2">
                    <Label htmlFor="sentiment-provider">LLM Provider</Label>
                    <Select value={sentimentProvider} onValueChange={setSentimentProvider}>
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
                          <SelectItem key={model.value} value={model.value}>
                            {model.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="sentiment-api-key">API Key</Label>
                    <Input
                      id="sentiment-api-key"
                      type="password"
                      value={sentimentApiKey}
                      onChange={(e) => setSentimentApiKey(e.target.value)}
                      placeholder="Enter API key (leave blank to keep existing)"
                    />
                    <p className="text-xs text-muted-foreground">
                      API key will be encrypted before storage
                    </p>
                  </div>

                  <Alert>
                    <AlertDescription className="text-sm">
                      LLM sentiment analysis uses news and market data to filter signals. Costs vary
                      by provider (~$0.01-0.10 per signal).
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </TabsContent>

            {/* LLM Analyst Tab */}
            <TabsContent value="analyst" className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="use-analyst"
                  checked={useLLMAnalyst}
                  onCheckedChange={setUseLLMAnalyst}
                />
                <Label htmlFor="use-analyst" className="font-semibold">
                  Enable LLM Market Analyst
                </Label>
              </div>

              {useLLMAnalyst && (
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="space-y-2">
                    <Label htmlFor="analyst-provider">LLM Provider</Label>
                    <Select value={analystProvider} onValueChange={setAnalystProvider}>
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
                          <SelectItem key={model.value} value={model.value}>
                            {model.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="analyst-api-key">API Key</Label>
                    <Input
                      id="analyst-api-key"
                      type="password"
                      value={analystApiKey}
                      onChange={(e) => setAnalystApiKey(e.target.value)}
                      placeholder="Enter API key (leave blank to keep existing)"
                    />
                    <p className="text-xs text-muted-foreground">
                      API key will be encrypted before storage
                    </p>
                  </div>

                  <Alert>
                    <AlertDescription className="text-sm">
                      Market analyst provides comprehensive market analysis and risk assessment. Higher
                      cost (~$0.10-0.50 per signal) but more thorough.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </TabsContent>
          </Tabs>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Configuration"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

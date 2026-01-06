import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bot, Brain, MessageSquare, TrendingUp, Settings } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { aiConfigV2Api } from "@/lib/api-v2";
import { AIConfigModal } from "./AIConfigModal";
import type { AIConfig } from "@/lib/api-v2";

interface AIConfigCardProps {
  accountId: number;
  onRefresh: () => void;
}

export const AIConfigCard = ({ accountId, onRefresh }: AIConfigCardProps) => {
  const { toast } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadConfig();
  }, [accountId]);

  const loadConfig = async () => {
    setIsLoading(true);
    const response = await aiConfigV2Api.get(accountId);
    if (response.data) {
      setConfig(response.data);
    } else {
      toast({
        title: "Error",
        description: response.error || "Failed to load AI configuration",
        variant: "destructive",
      });
    }
    setIsLoading(false);
  };

  const handleQuickToggle = async (feature: "ml" | "sentiment" | "analyst") => {
    if (!config) return;

    let response;
    const isEnabled =
      feature === "ml"
        ? config.use_ml_enhancement
        : feature === "sentiment"
        ? config.use_llm_sentiment
        : config.use_llm_analyst;

    if (isEnabled) {
      // Disable
      if (feature === "ml") {
        response = await aiConfigV2Api.disableML(accountId);
      } else if (feature === "sentiment") {
        response = await aiConfigV2Api.disableLLMSentiment(accountId);
      } else {
        response = await aiConfigV2Api.disableLLMAnalyst(accountId);
      }
    } else {
      // Can't enable without configuration - open modal
      setModalOpen(true);
      return;
    }

    if (response.data?.success) {
      toast({
        title: "Success",
        description: `${
          feature === "ml" ? "ML Enhancement" : feature === "sentiment" ? "LLM Sentiment" : "LLM Analyst"
        } ${isEnabled ? "disabled" : "enabled"}`,
      });
      loadConfig();
      onRefresh();
    } else {
      toast({
        title: "Error",
        description: response.error || "Failed to update configuration",
        variant: "destructive",
      });
    }
  };

  const handleModalSuccess = () => {
    loadConfig();
    onRefresh();
  };

  const hasAnyAI = config
    ? config.use_ml_enhancement || config.use_llm_sentiment || config.use_llm_analyst
    : false;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            AI Enhancement
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </CardContent>
      </Card>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5" />
                AI Enhancement
              </CardTitle>
              <CardDescription>Machine learning and LLM-powered trading signals</CardDescription>
            </div>
            <Button size="sm" onClick={() => setModalOpen(true)}>
              <Settings className="h-4 w-4 mr-2" />
              Configure
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {!hasAnyAI ? (
            <div className="text-center py-8">
              <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
              <p className="text-muted-foreground mb-2">No AI enhancements enabled</p>
              <p className="text-sm text-muted-foreground mb-4">
                Enable ML or LLM features to improve trading signals
              </p>
              <Button onClick={() => setModalOpen(true)}>Enable AI Features</Button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* ML Enhancement */}
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Brain className="h-5 w-5 text-blue-500" />
                  <div>
                    <p className="font-medium">ML Signal Enhancement</p>
                    {config.use_ml_enhancement && config.ml_model_type && (
                      <p className="text-sm text-muted-foreground">Model: {config.ml_model_type}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {config.use_ml_enhancement ? (
                    <Badge variant="default" className="bg-green-500">
                      Enabled
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Disabled</Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleQuickToggle("ml")}
                    disabled={!config.use_ml_enhancement}
                  >
                    {config.use_ml_enhancement ? "Disable" : "Enable"}
                  </Button>
                </div>
              </div>

              {/* LLM Sentiment */}
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-5 w-5 text-purple-500" />
                  <div>
                    <p className="font-medium">LLM Sentiment Analysis</p>
                    {config.use_llm_sentiment &&
                      config.llm_sentiment_provider &&
                      config.llm_sentiment_model && (
                        <p className="text-sm text-muted-foreground">
                          {config.llm_sentiment_provider} - {config.llm_sentiment_model}
                        </p>
                      )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {config.use_llm_sentiment ? (
                    <Badge variant="default" className="bg-green-500">
                      Enabled
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Disabled</Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleQuickToggle("sentiment")}
                    disabled={!config.use_llm_sentiment}
                  >
                    {config.use_llm_sentiment ? "Disable" : "Enable"}
                  </Button>
                </div>
              </div>

              {/* LLM Market Analyst */}
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <TrendingUp className="h-5 w-5 text-orange-500" />
                  <div>
                    <p className="font-medium">LLM Market Analyst</p>
                    {config.use_llm_analyst &&
                      config.llm_analyst_provider &&
                      config.llm_analyst_model && (
                        <p className="text-sm text-muted-foreground">
                          {config.llm_analyst_provider} - {config.llm_analyst_model}
                        </p>
                      )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {config.use_llm_analyst ? (
                    <Badge variant="default" className="bg-green-500">
                      Enabled
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Disabled</Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleQuickToggle("analyst")}
                    disabled={!config.use_llm_analyst}
                  >
                    {config.use_llm_analyst ? "Disable" : "Enable"}
                  </Button>
                </div>
              </div>

              {/* Summary */}
              <div className="pt-4 border-t">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">Active AI Features:</span>
                  <span className="font-semibold">
                    {[
                      config.use_ml_enhancement,
                      config.use_llm_sentiment,
                      config.use_llm_analyst,
                    ].filter(Boolean).length}{" "}
                    / 3
                  </span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <AIConfigModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        accountId={accountId}
        currentConfig={config}
        onSuccess={handleModalSuccess}
      />
    </>
  );
};

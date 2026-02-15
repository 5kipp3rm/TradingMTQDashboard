import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { IchimokuResponse } from "@/hooks/useIchimoku";

interface IchimokuPanelProps {
  data: IchimokuResponse | null;
  isLoading?: boolean;
}

export function IchimokuPanel({ data, isLoading }: IchimokuPanelProps) {
  if (isLoading) {
    return (
      <Card className="card-glow">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Ichimoku Signal</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[220px] bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className="card-glow">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Ichimoku Signal</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[220px] flex items-center justify-center text-muted-foreground text-sm">
            No data — select account & symbol
          </div>
        </CardContent>
      </Card>
    );
  }

  const { current, signal, cloud, parameters } = data;

  return (
    <Card className="card-glow">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Ichimoku Signal</CardTitle>
          <SignalBadge type={signal.type} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Signal Summary */}
        <div className="flex items-center justify-between gap-4 text-sm">
          <div className="space-y-1">
            <p className="text-muted-foreground">Trend</p>
            <p className="font-semibold">{formatSignalLabel(signal.type)}</p>
          </div>
          <div className="space-y-1 text-center">
            <p className="text-muted-foreground">Strength</p>
            <StrengthMeter strength={signal.strength} />
          </div>
          <div className="space-y-1 text-right">
            <p className="text-muted-foreground">Crossover</p>
            <p className="font-medium text-xs">
              {signal.crossover === "NONE" ? "—" : formatCrossover(signal.crossover)}
            </p>
          </div>
        </div>

        {/* Current Values */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
          <ValueRow label="Price" value={current.price} />
          <ValueRow label="Tenkan" value={current.tenkan} color="#2196F3" />
          <ValueRow label="Kijun" value={current.kijun} color="#F44336" />
          <ValueRow label="Chikou" value={current.chikou} color="#9C27B0" />
          <ValueRow label="Span A" value={current.senkou_a} color="#4CAF50" />
          <ValueRow label="Span B" value={current.senkou_b} color="#FF9800" />
        </div>

        {/* Cloud Status */}
        <div className="rounded-md border p-2.5 text-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Cloud</span>
            <span className="font-medium">
              {cloud.is_bullish_cloud ? (
                <span className="text-green-500">▲ Bullish</span>
              ) : cloud.is_bullish_cloud === false ? (
                <span className="text-red-500">▼ Bearish</span>
              ) : (
                "—"
              )}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Price vs Cloud</span>
            <span className="font-medium">{cloud.price_position ?? "—"}</span>
          </div>
          {cloud.thickness !== null && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Cloud Thickness</span>
              <span className="font-mono">{cloud.thickness.toFixed(getDecimals(cloud.thickness))}</span>
            </div>
          )}
        </div>

        {/* Period config */}
        <div className="flex gap-2 flex-wrap text-[10px] text-muted-foreground">
          <span>T={parameters.tenkan_period}</span>
          <span>K={parameters.kijun_period}</span>
          <span>S={parameters.senkou_b_period}</span>
          <span>D={parameters.displacement}</span>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SignalBadge({ type }: { type: string }) {
  const variant = type.includes("BULLISH")
    ? "default"
    : type.includes("BEARISH")
    ? "destructive"
    : "secondary";

  return (
    <Badge variant={variant} className="text-xs">
      {formatSignalLabel(type)}
    </Badge>
  );
}

function StrengthMeter({ strength }: { strength: string }) {
  const bars = strength === "strong" ? 3 : strength === "moderate" ? 2 : strength === "weak" ? 1 : 0;
  return (
    <div className="flex items-center gap-0.5" title={strength}>
      {[1, 2, 3].map((n) => (
        <div
          key={n}
          className="w-2 rounded-sm"
          style={{
            height: 6 + n * 3,
            backgroundColor:
              n <= bars
                ? bars === 3
                  ? "#4CAF50"
                  : bars === 2
                  ? "#FF9800"
                  : "#F44336"
                : "hsl(var(--muted))",
          }}
        />
      ))}
    </div>
  );
}

function ValueRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number | null;
  color?: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="flex items-center gap-1.5 text-muted-foreground">
        {color && (
          <span
            className="inline-block h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: color }}
          />
        )}
        {label}
      </span>
      <span className="font-mono">
        {value !== null && value !== undefined ? value.toFixed(getDecimals(value)) : "—"}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatSignalLabel(type: string): string {
  return type
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatCrossover(crossover: string): string {
  const map: Record<string, string> = {
    TENKAN_KIJUN_BULLISH: "TK Cross ▲",
    TENKAN_KIJUN_BEARISH: "TK Cross ▼",
    PRICE_CLOUD_BULLISH: "Cloud Break ▲",
    PRICE_CLOUD_BEARISH: "Cloud Break ▼",
    CLOUD_FLIP_BULLISH: "Cloud Flip ▲",
    CLOUD_FLIP_BEARISH: "Cloud Flip ▼",
  };
  return map[crossover] ?? crossover;
}

function getDecimals(v: number): number {
  if (v === 0) return 2;
  const abs = Math.abs(v);
  if (abs >= 100) return 2;
  if (abs >= 1) return 4;
  return 6;
}

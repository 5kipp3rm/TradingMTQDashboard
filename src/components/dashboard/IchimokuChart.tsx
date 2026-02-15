import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { IchimokuDataPoint, IchimokuResponse } from "@/hooks/useIchimoku";

// ---------------------------------------------------------------------------
// Colours – matches classic Ichimoku charting convention
// ---------------------------------------------------------------------------
const COLORS = {
  tenkan: "#2196F3",     // Blue – Conversion Line
  kijun: "#F44336",      // Red – Base Line
  senkouA: "#4CAF50",    // Green – Leading Span A
  senkouB: "#FF9800",    // Orange – Leading Span B
  chikou: "#9C27B0",     // Purple – Lagging Span
  close: "#E0E0E0",      // Light grey – Price
  cloudBullish: "rgba(76, 175, 80, 0.12)",   // Green fill
  cloudBearish: "rgba(244, 67, 54, 0.12)",   // Red fill
};

interface IchimokuChartProps {
  data: IchimokuDataPoint[];
  response: IchimokuResponse | null;
  isLoading?: boolean;
}

export function IchimokuChart({ data, response, isLoading }: IchimokuChartProps) {
  // Compute Y-axis domain with some padding
  const [yMin, yMax] = useMemo(() => {
    if (data.length === 0) return [0, 1];

    let min = Infinity;
    let max = -Infinity;

    for (const pt of data) {
      const values = [pt.tenkan, pt.kijun, pt.senkou_a, pt.senkou_b, pt.chikou, pt.close ?? null];
      for (const v of values) {
        if (v !== null && v !== undefined) {
          if (v < min) min = v;
          if (v > max) max = v;
        }
      }
    }

    const padding = (max - min) * 0.05;
    return [min - padding, max + padding];
  }, [data]);

  // Build cloud fill data – two areas stacked to simulate cloud
  const chartData = useMemo(() => {
    return data.map((pt) => ({
      ...pt,
      // For cloud shading we use the gap between spans
      cloudFill:
        pt.senkou_a !== null && pt.senkou_b !== null
          ? Math.abs(pt.senkou_a - pt.senkou_b)
          : null,
      isBullishCloud: pt.senkou_a !== null && pt.senkou_b !== null && pt.senkou_a >= pt.senkou_b,
    }));
  }, [data]);

  // Only render the most recent portion for readability (last 120 candles)
  const visibleData = useMemo(() => {
    const maxVisible = 120;
    return chartData.length > maxVisible
      ? chartData.slice(chartData.length - maxVisible)
      : chartData;
  }, [chartData]);

  return (
    <Card className="card-glow col-span-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            Ichimoku Kinko Hyo
            {response && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                {response.symbol} · {response.timeframe} · {response.candle_count} candles
              </span>
            )}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[420px] bg-muted animate-pulse rounded" />
        ) : data.length === 0 ? (
          <div className="h-[420px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">No Ichimoku data available</p>
              <p className="text-sm">Select a connected account and symbol to view</p>
            </div>
          </div>
        ) : (
          <div className="h-[420px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={visibleData}
                margin={{ top: 10, right: 30, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="label"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={11}
                  tickLine={false}
                  interval="preserveStartEnd"
                  minTickGap={40}
                />
                <YAxis
                  domain={[yMin, yMax]}
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v: number) => v.toFixed(getDecimals(v))}
                  width={75}
                />
                <Tooltip content={<IchimokuTooltip />} />
                <Legend
                  verticalAlign="top"
                  height={28}
                  iconType="line"
                  wrapperStyle={{ fontSize: 11 }}
                />

                {/* ---- Cloud shading (area between Span A and Span B) ---- */}
                <Area
                  type="monotone"
                  dataKey="cloudTop"
                  stroke="none"
                  fill="transparent"
                  name="Cloud Top"
                  legendType="none"
                  isAnimationActive={false}
                />
                <Area
                  type="monotone"
                  dataKey="cloudBottom"
                  stroke="none"
                  fillOpacity={1}
                  fill="url(#cloudGradient)"
                  name="Cloud"
                  legendType="none"
                  isAnimationActive={false}
                />

                {/* ---- Price line (if OHLC included) ---- */}
                {visibleData[0]?.close !== undefined && (
                  <Line
                    type="monotone"
                    dataKey="close"
                    stroke={COLORS.close}
                    strokeWidth={1.5}
                    dot={false}
                    name="Price"
                    isAnimationActive={false}
                  />
                )}

                {/* ---- Senkou Span A ---- */}
                <Line
                  type="monotone"
                  dataKey="senkou_a"
                  stroke={COLORS.senkouA}
                  strokeWidth={1}
                  strokeDasharray="4 2"
                  dot={false}
                  name="Span A"
                  connectNulls={false}
                  isAnimationActive={false}
                />
                {/* ---- Senkou Span B ---- */}
                <Line
                  type="monotone"
                  dataKey="senkou_b"
                  stroke={COLORS.senkouB}
                  strokeWidth={1}
                  strokeDasharray="4 2"
                  dot={false}
                  name="Span B"
                  connectNulls={false}
                  isAnimationActive={false}
                />

                {/* ---- Tenkan-sen ---- */}
                <Line
                  type="monotone"
                  dataKey="tenkan"
                  stroke={COLORS.tenkan}
                  strokeWidth={1.5}
                  dot={false}
                  name="Tenkan"
                  connectNulls={false}
                  isAnimationActive={false}
                />
                {/* ---- Kijun-sen ---- */}
                <Line
                  type="monotone"
                  dataKey="kijun"
                  stroke={COLORS.kijun}
                  strokeWidth={1.5}
                  dot={false}
                  name="Kijun"
                  connectNulls={false}
                  isAnimationActive={false}
                />

                {/* ---- Chikou Span ---- */}
                <Line
                  type="monotone"
                  dataKey="chikou"
                  stroke={COLORS.chikou}
                  strokeWidth={1}
                  strokeDasharray="2 2"
                  dot={false}
                  name="Chikou"
                  connectNulls={false}
                  isAnimationActive={false}
                />

                {/* Gradient definition for cloud */}
                <defs>
                  <linearGradient id="cloudGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={COLORS.senkouA} stopOpacity={0.15} />
                    <stop offset="100%" stopColor={COLORS.senkouB} stopOpacity={0.08} />
                  </linearGradient>
                </defs>
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Custom Tooltip
// ---------------------------------------------------------------------------

function IchimokuTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;

  const fmt = (v: number | null | undefined) =>
    v !== null && v !== undefined ? v.toFixed(getDecimals(v)) : "—";

  // Extract values from payload
  const values: Record<string, number | null> = {};
  for (const entry of payload) {
    values[entry.dataKey] = entry.value;
  }

  return (
    <div
      className="rounded-lg border bg-card p-3 shadow-md text-sm"
      style={{ minWidth: 180 }}
    >
      <p className="font-medium text-foreground mb-1.5">{label}</p>
      <div className="space-y-0.5 text-xs">
        {values.close !== undefined && (
          <Row label="Price" value={fmt(values.close)} color={COLORS.close} />
        )}
        <Row label="Tenkan" value={fmt(values.tenkan)} color={COLORS.tenkan} />
        <Row label="Kijun" value={fmt(values.kijun)} color={COLORS.kijun} />
        <Row label="Span A" value={fmt(values.senkou_a)} color={COLORS.senkouA} />
        <Row label="Span B" value={fmt(values.senkou_b)} color={COLORS.senkouB} />
        <Row label="Chikou" value={fmt(values.chikou)} color={COLORS.chikou} />
      </div>
    </div>
  );
}

function Row({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="flex items-center gap-1.5">
        <span
          className="inline-block h-2 w-2 rounded-full"
          style={{ backgroundColor: color }}
        />
        {label}
      </span>
      <span className="font-mono">{value}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getDecimals(v: number): number {
  if (v === 0) return 2;
  const abs = Math.abs(v);
  if (abs >= 100) return 2; // e.g. XAUUSD 2040.55
  if (abs >= 1) return 4;   // e.g. EURUSD 1.1025
  return 6;                 // very small prices
}

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface IchimokuParams {
  accountId: string;
  symbol: string;
  timeframe?: string;
  count?: number;
  tenkanPeriod?: number;
  kijunPeriod?: number;
  senkouBPeriod?: number;
  displacement?: number;
  includeRaw?: boolean;
}

export interface IchimokuCurrent {
  price: number;
  tenkan: number | null;
  kijun: number | null;
  senkou_a: number | null;
  senkou_b: number | null;
  chikou: number | null;
}

export interface IchimokuSignal {
  type: string;
  crossover: string;
  is_bullish: boolean;
  is_bearish: boolean;
  strength: string;
}

export interface IchimokuCloud {
  top: number | null;
  bottom: number | null;
  thickness: number | null;
  price_position: "ABOVE" | "BELOW" | "INSIDE" | null;
  is_bullish_cloud: boolean | null;
}

export interface IchimokuSeries {
  timestamps: string[];
  tenkan: (number | null)[];
  kijun: (number | null)[];
  senkou_a: (number | null)[];
  senkou_b: (number | null)[];
  chikou: (number | null)[];
}

export interface IchimokuOHLC {
  timestamps: string[];
  open: number[];
  high: number[];
  low: number[];
  close: number[];
}

export interface IchimokuResponse {
  symbol: string;
  timeframe: string;
  account_id: number;
  candle_count: number;
  timestamp: string;
  parameters: {
    tenkan_period: number;
    kijun_period: number;
    senkou_b_period: number;
    displacement: number;
  };
  current: IchimokuCurrent;
  signal: IchimokuSignal;
  cloud: IchimokuCloud;
  series: IchimokuSeries;
  ohlc?: IchimokuOHLC;
}

/** Merged per-candle data point for Recharts */
export interface IchimokuDataPoint {
  timestamp: string;
  /** Short label for X-axis */
  label: string;
  tenkan: number | null;
  kijun: number | null;
  senkou_a: number | null;
  senkou_b: number | null;
  chikou: number | null;
  close?: number;
  /** Cloud fill helper: higher of senkou_a / senkou_b */
  cloudTop: number | null;
  /** Cloud fill helper: lower of senkou_a / senkou_b */
  cloudBottom: number | null;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useIchimoku(params: IchimokuParams | null) {
  const [data, setData] = useState<IchimokuResponse | null>(null);
  const [chartData, setChartData] = useState<IchimokuDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchIchimoku = useCallback(async () => {
    if (!params || !params.accountId || params.accountId === "all" || !params.symbol) {
      setData(null);
      setChartData([]);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const queryParts: string[] = [];
      if (params.timeframe) queryParts.push(`timeframe=${params.timeframe}`);
      if (params.count) queryParts.push(`count=${params.count}`);
      if (params.tenkanPeriod) queryParts.push(`tenkan_period=${params.tenkanPeriod}`);
      if (params.kijunPeriod) queryParts.push(`kijun_period=${params.kijunPeriod}`);
      if (params.senkouBPeriod) queryParts.push(`senkou_b_period=${params.senkouBPeriod}`);
      if (params.displacement) queryParts.push(`displacement=${params.displacement}`);
      if (params.includeRaw) queryParts.push("include_raw=true");

      const qs = queryParts.length > 0 ? `?${queryParts.join("&")}` : "";
      const endpoint = `/indicators/ichimoku/${params.accountId}/${params.symbol}${qs}`;

      const resp = await apiClient.get<IchimokuResponse>(endpoint);

      if (resp.error) {
        setError(resp.error);
        setData(null);
        setChartData([]);
      } else if (resp.data) {
        setData(resp.data);
        setChartData(transformToChartData(resp.data));
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(msg);
      setData(null);
      setChartData([]);
    } finally {
      setIsLoading(false);
    }
  }, [
    params?.accountId,
    params?.symbol,
    params?.timeframe,
    params?.count,
    params?.tenkanPeriod,
    params?.kijunPeriod,
    params?.senkouBPeriod,
    params?.displacement,
    params?.includeRaw,
  ]);

  useEffect(() => {
    fetchIchimoku();
  }, [fetchIchimoku]);

  return { data, chartData, isLoading, error, refresh: fetchIchimoku };
}

// ---------------------------------------------------------------------------
// Transform API response → per-candle Recharts data
// ---------------------------------------------------------------------------

function transformToChartData(resp: IchimokuResponse): IchimokuDataPoint[] {
  const { series, ohlc } = resp;
  const len = series.timestamps.length;
  const points: IchimokuDataPoint[] = [];

  for (let i = 0; i < len; i++) {
    const ts = series.timestamps[i];
    const a = series.senkou_a[i];
    const b = series.senkou_b[i];

    points.push({
      timestamp: ts,
      label: formatTimestamp(ts, resp.timeframe),
      tenkan: series.tenkan[i],
      kijun: series.kijun[i],
      senkou_a: a,
      senkou_b: b,
      chikou: series.chikou[i],
      close: ohlc ? ohlc.close[i] : undefined,
      cloudTop: a !== null && b !== null ? Math.max(a, b) : null,
      cloudBottom: a !== null && b !== null ? Math.min(a, b) : null,
    });
  }

  return points;
}

function formatTimestamp(iso: string, timeframe: string): string {
  try {
    const d = new Date(iso);
    if (timeframe.startsWith("D") || timeframe.startsWith("W") || timeframe === "MN1") {
      return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    }
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso.slice(11, 16) || iso.slice(0, 10);
  }
}

/**
 * Position Calculator
 *
 * Calculates TP/SL distances, potential profit/loss, risk-reward ratio,
 * and progress percentage for open positions.
 */

import type { Position } from "@/types/trading";

/** Pip size lookup by symbol suffix / known pairs */
function getPointSize(symbol: string): number {
  const s = symbol.toUpperCase();
  // JPY pairs: 0.01 per pip
  if (s.includes("JPY")) return 0.01;
  // Gold
  if (s === "XAUUSD" || s === "GOLD") return 0.1;
  // Silver
  if (s === "XAGUSD" || s === "SILVER") return 0.01;
  // Indices
  if (["US30", "US500", "NAS100", "US100", "USTEC", "DJ30"].some(i => s.includes(i))) return 1;
  // Oil
  if (s.includes("OIL") || s === "USOIL" || s === "UKOIL") return 0.01;
  // Crypto (BTC/ETH)
  if (s.includes("BTC")) return 1;
  if (s.includes("ETH")) return 0.1;
  // Standard forex: 0.0001
  return 0.0001;
}

export interface PositionMetrics {
  /** The raw position */
  position: Position;

  // ---- TP metrics ----
  /** Distance from current price to TP in price units (null if no TP) */
  tpDistance: number | null;
  /** Distance to TP in pips */
  tpPips: number | null;
  /** Estimated profit at TP (based on current P/L ratio) */
  tpPotentialProfit: number | null;

  // ---- SL metrics ----
  /** Distance from current price to SL in price units (null if no SL) */
  slDistance: number | null;
  /** Distance to SL in pips */
  slPips: number | null;
  /** Estimated loss at SL (negative value) */
  slPotentialLoss: number | null;

  // ---- Ratio / progress ----
  /** Risk-Reward ratio (TP distance / SL distance). null if either missing */
  riskReward: number | null;
  /**
   * Progress towards TP expressed as 0-100%.
   * 0 % = at open price, 100 % = at TP.
   * Can exceed 100 % or go negative when price overshoots.
   * null if no TP.
   */
  tpProgress: number | null;
  /**
   * Progress towards SL expressed as 0-100%.
   * 0 % = at open price, 100 % = at SL (hit stop).
   * null if no SL.
   */
  slProgress: number | null;
}

/**
 * Calculate metrics for a single position.
 */
export function calculatePositionMetrics(pos: Position): PositionMetrics {
  const point = getPointSize(pos.symbol);
  const isBuy = pos.type === "buy";

  // ----- Distance calculations -----
  let tpDistance: number | null = null;
  let tpPips: number | null = null;
  let slDistance: number | null = null;
  let slPips: number | null = null;

  if (pos.tp != null && pos.tp > 0) {
    // For BUY: profit when price goes UP   → tp > openPrice
    // For SELL: profit when price goes DOWN → tp < openPrice
    tpDistance = isBuy
      ? pos.tp - pos.currentPrice
      : pos.currentPrice - pos.tp;
    tpPips = Math.round(Math.abs(pos.tp - pos.currentPrice) / point);
  }

  if (pos.sl != null && pos.sl > 0) {
    slDistance = isBuy
      ? pos.currentPrice - pos.sl
      : pos.sl - pos.currentPrice;
    slPips = Math.round(Math.abs(pos.currentPrice - pos.sl) / point);
  }

  // ----- Profit / Loss estimation -----
  // Use the relationship: profit / priceMove = constant (for the same volume & symbol)
  // profitPerPoint = current profit / (currentPrice - openPrice) for buy
  const priceMove = isBuy
    ? pos.currentPrice - pos.openPrice
    : pos.openPrice - pos.currentPrice;

  // Avoid division by zero
  const profitPerPoint =
    Math.abs(priceMove) > point * 0.1 ? pos.profit / priceMove : null;

  let tpPotentialProfit: number | null = null;
  let slPotentialLoss: number | null = null;

  if (pos.tp != null && pos.tp > 0) {
    const tpMove = isBuy
      ? pos.tp - pos.openPrice
      : pos.openPrice - pos.tp;
    if (profitPerPoint != null) {
      tpPotentialProfit = parseFloat((profitPerPoint * tpMove).toFixed(2));
    }
  }

  if (pos.sl != null && pos.sl > 0) {
    const slMove = isBuy
      ? pos.sl - pos.openPrice
      : pos.openPrice - pos.sl;
    if (profitPerPoint != null) {
      slPotentialLoss = parseFloat((profitPerPoint * slMove).toFixed(2));
    }
  }

  // ----- Risk / Reward -----
  let riskReward: number | null = null;
  if (
    pos.tp != null &&
    pos.tp > 0 &&
    pos.sl != null &&
    pos.sl > 0
  ) {
    const tpDist = Math.abs(pos.tp - pos.openPrice);
    const slDist = Math.abs(pos.sl - pos.openPrice);
    if (slDist > 0) {
      riskReward = parseFloat((tpDist / slDist).toFixed(2));
    }
  }

  // ----- Progress -----
  let tpProgress: number | null = null;
  let slProgress: number | null = null;

  if (pos.tp != null && pos.tp > 0) {
    const totalToTp = isBuy
      ? pos.tp - pos.openPrice
      : pos.openPrice - pos.tp;
    if (Math.abs(totalToTp) > 0) {
      tpProgress = parseFloat(((priceMove / totalToTp) * 100).toFixed(1));
    }
  }

  if (pos.sl != null && pos.sl > 0) {
    const totalToSl = isBuy
      ? pos.openPrice - pos.sl
      : pos.sl - pos.openPrice;
    if (Math.abs(totalToSl) > 0) {
      // progress toward SL: how much of the distance has been "consumed"
      // negative priceMove → moving toward SL for buy
      const moveTowardSl = -priceMove; // positive means moving toward SL
      slProgress = parseFloat(((moveTowardSl / totalToSl) * 100).toFixed(1));
    }
  }

  return {
    position: pos,
    tpDistance,
    tpPips,
    tpPotentialProfit,
    slDistance,
    slPips,
    slPotentialLoss,
    riskReward,
    tpProgress,
    slProgress,
  };
}

/**
 * Calculate metrics for multiple positions.
 */
export function calculateAllPositionMetrics(
  positions: Position[]
): PositionMetrics[] {
  return positions.map(calculatePositionMetrics);
}

import type { EtfProxy } from "../../api/client";
import { ymd } from "./watchlist-format";

/**
 * Purpose: pure display helpers of the 国家队 ETF panel (plan 15 phase 7b, D-126). Flows and positions are
 * computed in Python (EtfProxyBuilder); this only formats them.
 * Contract: money is 亿元 as written by Python; null / undefined → "—".
 */

/** Purpose: 亿元 with thousands separators and no decimals. Contract: 9162.2 → "9,162 亿"; null → "—". */
export const yi = (v: number | null | undefined): string =>
  v == null ? "—" : Math.round(v).toLocaleString("en-US") + " 亿";

/** Purpose: a signed flow. Contract: 4268.4 → "+4,268 亿"; −9471.7 → "−9,472 亿"; 0 → "0 亿"; null → "—". */
export const signedYi = (v: number | null | undefined): string => {
  if (v == null) return "—";
  const r = Math.round(v);
  return (r > 0 ? "+" : r < 0 ? "−" : "") + Math.abs(r).toLocaleString("en-US") + " 亿";
};

/** Purpose: "in" / "out" / "flat" class of a flow for colouring. Contract: |v| < 0.5 or null → "flat". */
export const flowClass = (v: number | null | undefined): "in" | "out" | "flat" =>
  v == null || Math.abs(v) < 0.5 ? "flat" : v > 0 ? "in" : "out";

/**
 * Purpose: the one-sentence headline of the panel.
 * Contract: no core totals → "" ; otherwise position now, peak and trough since the peak, recent flow, as-of date.
 */
export function proxyHeadline(doc: EtfProxy, recentDays: number): string {
  const c = doc.totals.core;
  if (!c) return "";
  const share = c.peak.position ? Math.round(((c.position ?? 0) / c.peak.position) * 100) : null;
  return `核心 ETF 仓位（按现价）${yi(c.position)}${share != null ? `，是峰值的 ${share}%` : ""}。` +
    `峰值 ${yi(c.peak.position)}（${ymd(c.peak.date)}），之后最低 ${yi(c.trough_since_peak.position)}（${ymd(c.trough_since_peak.date)}）。` +
    `最近 ${recentDays} 个交易日净申购 ${signedYi(c.flow_recent)}，今年以来 ${signedYi(c.flow_ytd)}。份额截至 ${ymd(doc.as_of)}。`;
}

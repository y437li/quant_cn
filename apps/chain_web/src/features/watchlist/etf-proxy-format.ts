import type { EtfProxy, ProxyIndex, ProxyMark, ProxyWindow } from "../../api/client";
import { ymd } from "./watchlist-format";

/**
 * Purpose: pure display helpers of the 国家队 ETF panel (plan 15 phase 7b, D-126). Flows and positions are
 * computed in Python (EtfProxyBuilder); this only formats them.
 * Contract: money is 亿元 as written by Python; null / undefined → "—".
 */

/** Purpose: 亿元 with thousands separators and no decimals. Contract: 9162.2 → "9,162 亿"; null → "—". */
export const yi = (v: number | null | undefined): string =>
  v == null ? "—" : Math.round(v).toLocaleString("en-US") + " 亿";

/** Purpose: a signed whole number. Contract: 4268.4 → "+4,268"; −9471.7 → "−9,472"; 0.3 → "0"; null → "—". */
export const signedNum = (v: number | null | undefined): string => {
  if (v == null) return "—";
  const r = Math.round(v);
  return (r > 0 ? "+" : r < 0 ? "−" : "") + Math.abs(r).toLocaleString("en-US");
};

/** Purpose: a signed flow. Contract: 4268.4 → "+4,268 亿"; −9471.7 → "−9,472 亿"; 0 → "0 亿"; null → "—". */
export const signedYi = (v: number | null | undefined): string => (v == null ? "—" : signedNum(v) + " 亿");

/** Purpose: "in" / "out" / "flat" class of a flow for colouring. Contract: |v| < 0.5 or null → "flat". */
export const flowClass = (v: number | null | undefined): "in" | "out" | "flat" =>
  v == null || Math.abs(v) < 0.5 ? "flat" : v > 0 ? "in" : "out";

/** Purpose: a position with its month. Contract: {20250425, 11376} → "11,376 亿（2025-04）"; no mark / no date → "—". */
export const markYi = (m: ProxyMark | null | undefined): string =>
  !m?.date ? "—" : `${yi(m.position)}（${ymd(m.date).slice(0, 7)}）`;

/** Purpose: a drawdown in %. Contract: −21.43 → "−21.4%"; 0 → "0.0%"; null → "—". */
export const pctDown = (v: number | null | undefined): string =>
  v == null ? "—" : (v < 0 ? "−" : "") + Math.abs(v).toFixed(1) + "%";

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

/** Purpose: a 近3月 percentile. Contract: 96.8 → "97%"; 100 → "100%"; no window / null → "—". */
export const pctRank = (w: ProxyWindow | null | undefined): string =>
  w?.pct == null ? "—" : `${Math.round(w.pct)}%`;

/** Purpose: a 近3月 range. Contract: {low 4169.4, high 8977.2} → "4,169–8,977 亿"; a missing bound → "—". */
export const windowRange = (w: ProxyWindow | null | undefined): string =>
  w?.low == null || w.high == null ? "—" : `${Math.round(w.low).toLocaleString("en-US")}–${yi(w.high)}`;

/**
 * Purpose: the 近3月 line under the headline.
 * Contract: no core window → ""; otherwise core and (when present) other percentile and range, the sessions used,
 * and the core flow of the last rhythm weeks; a window shorter than the setting says how many sessions it covers.
 */
export function windowLine(doc: EtfProxy): string {
  const c = doc.totals.core, o = doc.totals.other;
  if (!c?.window || c.window.pct == null) return "";
  const days = doc.pct_window_days ?? c.window.days;
  const span = c.window.days < days ? `（只有 ${c.window.days} 个交易日）` : "";
  const other = o?.window?.pct != null ? `；其他 ETF ${pctRank(o.window)}（区间 ${windowRange(o.window)}）` : "";
  const weeks = c.flow_weeks != null ? `。核心近 ${doc.rhythm_weeks ?? 5} 周净申购 ${signedYi(c.flow_weeks)}` : "";
  return `近3月分位${span}：核心 ETF 仓位 ${pctRank(c.window)}（区间 ${windowRange(c.window)}）${other}${weeks}。`;
}

/** One row of the weekly flow matrix: the week's last day and one flow per index (null = no data that week). */
export interface MatrixRow { date: string; flows: (number | null)[] }

/**
 * Purpose: the per-index weekly net-flow matrix, newest week first.
 * Contract: weeks = the union of the indices' weekly dates (each index's week ends on the same session),
 * the last `weeks` of them; a week an index lacks → null; weeks ≤ 0 or no indices → [].
 */
export function flowMatrix(indices: ProxyIndex[], weeks: number): MatrixRow[] {
  if (weeks <= 0 || !indices.length) return [];
  const byIndex = indices.map((x) => new Map(x.weekly.map((w) => [w.date, w.flow])));
  const dates = [...new Set(indices.flatMap((x) => x.weekly.map((w) => w.date)))].sort().slice(-weeks).reverse();
  return dates.map((date) => ({ date, flows: byIndex.map((m) => m.get(date) ?? null) }));
}

/**
 * Purpose: heat strength of a matrix cell, 0–100, on a square-root scale so small outflows stay visible next to big inflows.
 * Contract: √(|v| / max(|all|)) × 100, rounded; null, 0 or max 0 → 0.
 */
export function heat(v: number | null, rows: MatrixRow[]): number {
  const max = Math.max(0, ...rows.flatMap((r) => r.flows.map((f) => Math.abs(f ?? 0))));
  return v == null || max === 0 ? 0 : Math.round(Math.sqrt(Math.abs(v) / max) * 100);
}

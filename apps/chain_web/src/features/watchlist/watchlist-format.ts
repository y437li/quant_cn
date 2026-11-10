import type { WatchlistEntry, WatchStatus } from "../../api/client";

/**
 * Purpose: pure display helpers of the watchlist page (labels, number formats, which entry to headline,
 * badge count, chart scales and label placement). No business numbers are derived here: gap, status,
 * PE and yield at the buy price come from Python (APP_STANDARD §1).
 * Contract: every formatter returns "—" for null / undefined; fractions are shown as percentages.
 */

/** Purpose: Chinese label of a status. Contract: in → 区间内, near → 接近, far → 较远. */
export const STATUS_ZH: Record<WatchStatus, string> = { in: "区间内", near: "接近", far: "较远" };
export const statusLabel = (s: WatchStatus): string => STATUS_ZH[s] ?? s;

/** Purpose: price with two decimals. Contract: number | null → "11.84" | "—". */
export const px = (v: number | null | undefined): string => (v == null ? "—" : v.toFixed(2));
/** Purpose: a fraction as a percentage with one decimal. Contract: 0.042 → "4.2%"; null → "—". */
export const pctOf = (v: number | null | undefined): string => (v == null ? "—" : (v * 100).toFixed(1) + "%");
/** Purpose: a multiple with one decimal. Contract: 9.07 → "9.1 倍"; null → "—". */
export const times = (v: number | null | undefined): string => (v == null ? "—" : v.toFixed(1) + " 倍");
/** Purpose: YYYYMMDD → YYYY-MM-DD. Contract: other strings pass through; "" → "—". */
export const ymd = (d: string | null | undefined): string => (!d ? "—" : /^\d{8}$/.test(d) ? `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6)}` : d);

/** Purpose: the distance to the buy zone in words. Contract: gap 0 → "已到买入区间"; −0.1554 → "还需下跌 15.5%". */
export const gapText = (gap: number): string => (gap >= 0 ? "已到买入区间" : "还需下跌 " + pctOf(-gap));
/** Purpose: the gap as a bare percentage for tables. Contract: 0 → "0%"; −0.3941 → "39.4%". */
export const gapPct = (gap: number): string => (gap >= 0 ? "0%" : pctOf(-gap));
/** Purpose: buy price as a range or a single price. Contract: 9/10 → "9.00–10.00"; 25/25 → "25.00". */
export const buyText = (e: Pick<WatchlistEntry, "buy_low" | "buy_high">): string =>
  e.buy_low === e.buy_high ? px(e.buy_high) : `${px(e.buy_low)}–${px(e.buy_high)}`;
/** Purpose: broker target range. Contract: both null → "—"; one null → the other; else "low–high". */
export const targetText = (e: Pick<WatchlistEntry, "target_low" | "target_high">): string => {
  if (e.target_low == null && e.target_high == null) return "—";
  if (e.target_low == null || e.target_high == null || e.target_low === e.target_high) return px(e.target_low ?? e.target_high);
  return `${px(e.target_low)}–${px(e.target_high)}`;
};

/**
 * Purpose: the entry closest to its buy price (largest gap_to_buy, which is ≤ 0).
 * Contract: [] → null; ties keep the first in file order.
 */
export function nearestEntry<T extends Pick<WatchlistEntry, "gap_to_buy">>(entries: T[]): T | null {
  let best: T | null = null;
  for (const e of entries) if (!best || e.gap_to_buy > best.gap_to_buy) best = e;
  return best;
}

/** Purpose: header-chip badge. Contract: number of entries whose status is in or near (0 hides the badge). */
export const badgeCount = (entries: Pick<WatchlistEntry, "status">[] | null | undefined): number =>
  (entries || []).filter((e) => e.status === "in" || e.status === "near").length;

/** Purpose: the forecast year for the table header. Contract: first non-null eps_year, else "" (header shows "预测"). */
export const epsYearOf = (entries: Pick<WatchlistEntry, "eps_year">[]): string => entries.find((e) => e.eps_year)?.eps_year || "";

/** Purpose: approximate rendered width of a label. Contract: CJK characters count as one em, others 0.6 em. */
export const textWidth = (t: string, size = 11): number => [...t].reduce((w, ch) => w + (ch.charCodeAt(0) > 0x2e80 ? size : size * 0.6), 0);

export interface Label { x: number; text: string; anchor: "start" | "middle" | "end" }
/**
 * Purpose: keep labels inside [0, width] and drop any that would overlap one already placed.
 * Contract: input in priority order; output keeps that order with x shifted to fit; the gap is the minimum
 * spacing between two labels.
 */
export function placeLabels(labels: Label[], width: number, size = 11, gap = 6): Label[] {
  const placed: [number, number][] = [];
  const out: Label[] = [];
  for (const l of labels) {
    const w = textWidth(l.text, size);
    let left = l.anchor === "start" ? l.x : l.anchor === "middle" ? l.x - w / 2 : l.x - w;
    left = Math.min(Math.max(0, left), Math.max(0, width - w));
    if (placed.some(([a, b]) => left < b + gap && left + w > a - gap)) continue;
    placed.push([left, left + w]);
    out.push({ ...l, x: l.anchor === "start" ? left : l.anchor === "middle" ? left + w / 2 : left + w });
  }
  return out;
}

/** Purpose: a linear scale. Contract: maps d0..d1 onto r0..r1; a zero-width domain maps to the middle. */
export const linear = (d0: number, d1: number, r0: number, r1: number) => (v: number): number =>
  d1 === d0 ? (r0 + r1) / 2 : r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

/** Purpose: round axis ticks. Contract: about n ticks at a 1/2/5×10^k step, all within [lo, hi]. */
export function niceTicks(lo: number, hi: number, n = 4): number[] {
  if (!(hi > lo)) return [lo];
  const raw = (hi - lo) / n;
  const p = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * p).find((s) => s >= raw) as number;
  const out: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}

/** Purpose: YYYYMMDD → epoch ms (UTC) for the time axis. Contract: "20261106" → Date.UTC(2026, 10, 6). */
export const dayMs = (d: string): number => Date.UTC(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8));

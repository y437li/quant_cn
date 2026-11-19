import type { FuturesFamily, FuturesSpread } from "../../api/client";

export const EXTREME_LO = 0.05;
export const EXTREME_HI = 0.95;
export const SHAPE_ZH: Record<string, string> = { backwardation: "近高远低", contango: "近低远高", flat: "平坦", none: "—" };

/** Purpose: families by group in first-seen order. Contract: order inside a group kept. */
export function groupFamilies(rows: FuturesFamily[]): [string, FuturesFamily[]][] {
  const groups = [...new Set(rows.map((r) => r.group))];
  return groups.map((g) => [g, rows.filter((r) => r.group === g)]);
}

/** Purpose: signed percent of a fraction. Contract: 0.038 → "+3.8%"; null → "—". */
export function signedPct(v: number | null, digits = 1): string {
  if (v == null) return "—";
  return (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v * 100).toFixed(digits) + "%";
}

/** Purpose: percentile as "87%". Contract: null → "—". */
export const pctText = (p: number | null): string => (p == null ? "—" : `${Math.round(p * 100)}%`);

/** Purpose: true at or beyond the 5% / 95% flag bounds. Contract: null → false. */
export const isExtreme = (p: number | null): boolean => p != null && (p <= EXTREME_LO || p >= EXTREME_HI);

/** Purpose: a price with separators and decimals that fit its size. Contract: ≥ 1000 no decimals, ≥ 10 one, else two. */
export function priceText(v: number | null): string {
  if (v == null) return "—";
  const d = Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 10 ? 1 : 2;
  return v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
}

/** Purpose: colour class of a signed number (red up, green down as on Chinese screens). */
export const moveClass = (v: number | null): string => (v == null || v === 0 ? "" : v > 0 ? "up" : "down");

/** Purpose: "202612" → "26-12"; "20261113" → "2026-11-13". */
export const shortMonth = (m: string): string => `${m.slice(2, 4)}-${m.slice(4, 6)}`;
export const ymdText = (d: string): string => (d.length === 8 ? `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6)}` : d);

/** Purpose: a spread value: ratios with two decimals, 元 amounts as whole numbers with separators. Contract: signed adds "+". */
export function spreadText(s: Pick<FuturesSpread, "kind">, v: number, signed = false): string {
  const sign = v < 0 ? "−" : signed && v > 0 ? "+" : "";
  const a = Math.abs(v);
  return sign + (s.kind === "ratio" ? a.toFixed(2) : Math.round(a).toLocaleString("en-US"));
}

export const REGIME_ZH: Record<string, string> = { new_longs: "多头增仓", new_shorts: "空头增仓", long_liquidation: "多头减仓", short_covering: "空头回补" };

/** Purpose: signed lots with separators. Contract: -25695 → "−25,695"; null → "—". */
export function lotsText(v: number | null, signed = true): string {
  if (v == null) return "—";
  return (v < 0 ? "−" : signed && v > 0 ? "+" : "") + Math.round(Math.abs(v)).toLocaleString("en-US");
}

import type { MacroSeries } from "../../api/client";

export const GROUPS = ["价格", "景气", "货币", "社融"] as const;
export const EXTREME = 0.1; // percentile at or beyond which a line is marked (bottom / top 10% of 5 years)

/** Purpose: lines by group in GROUPS order. Contract: groups without lines are left out; order inside a group kept. */
export function groupSeries(series: MacroSeries[]): [string, MacroSeries[]][] {
  const known: string[] = [...GROUPS];
  const names = [...known, ...series.map((s) => s.group).filter((g) => !known.includes(g))];
  return [...new Set(names)].map((g) => [g, series.filter((s) => s.group === g)] as [string, MacroSeries[]]).filter(([, rows]) => rows.length > 0);
}

/** Purpose: display a value in the line's unit. Contract: 亿元 with separators, else one decimal (two for 社融存量同比); signed adds "+". */
export function formatValue(s: Pick<MacroSeries, "key" | "unit">, v: number | null, signed = false): string {
  if (v == null) return "—";
  const sign = v < 0 ? "−" : signed && v > 0 ? "+" : "";
  if (s.unit === "亿元") return sign + Math.round(Math.abs(v)).toLocaleString("en-US");
  return sign + Math.abs(v).toFixed(s.key === "sf_stock_yoy" ? 2 : 1) + (s.unit === "%" ? "%" : "");
}

/** Purpose: true when the 5-year percentile is in the bottom or top 10%. Contract: null → false. */
export const isExtreme = (pct: number | null): boolean => pct != null && (pct <= EXTREME || pct >= 1 - EXTREME);

/** Purpose: "202610" → "2026-10". Contract: empty → "—". */
export const monthLabel = (m: string): string => (m ? `${m.slice(0, 4)}-${m.slice(4, 6)}` : "—");

/** Purpose: the chart's reference line: 50 for PMI lines (expansion / contraction), else 0. */
export const refLine = (key: string): number => (key.startsWith("pmi") ? 50 : 0);

/** Purpose: the page headline. Contract: latest month, count of new prints, and the extremes by name. */
export function macroHeadline(series: MacroSeries[], newPrints: string[]): string {
  const latest = series.reduce((m, s) => (s.month > m ? s.month : m), "");
  const ext = series.filter((s) => isExtreme(s.pct_5y)).map((s) => s.name);
  return `最新数据 ${monthLabel(latest)}；${newPrints.length} 项新发布。` + (ext.length ? `处于 5 年极端分位：${ext.join("、")}。` : "");
}

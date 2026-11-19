import type { RatesFxFlag, RatesFxRow, RatesFxUnit } from "../../api/client";

const sign = (v: number) => (v < 0 ? "−" : v > 0 ? "+" : "");

/** Purpose: a row's level by unit: yield "1.6055%" (中债 quotes 4 decimals), bp "43.5bp", rate 4 significant decimals (6.6661, 159.23), gap "−0.71%". Contract: null → "—". */
export function formatLevel(v: number | null, unit: RatesFxUnit): string {
  if (v == null) return "—";
  if (unit === "yield") return `${v.toFixed(4)}%`;
  if (unit === "bp") return `${sign(v)}${Math.abs(v).toFixed(1)}bp`;
  if (unit === "gap") return `${sign(v)}${Math.abs(v * 100).toFixed(2)}%`;
  return v >= 100 ? v.toFixed(2) : v.toFixed(4);
}

/** Purpose: a change by unit: yield / bp in bp ("−4bp"), rate in % ("+1.26%"), gap in percentage points ("+0.04pp"). Contract: null → "—"; zero has no sign. */
export function formatChange(v: number | null, unit: RatesFxUnit): string {
  if (v == null) return "—";
  if (unit === "yield" || unit === "bp") return `${sign(Math.round(v))}${Math.abs(Math.round(v))}bp`;
  if (unit === "gap") return `${sign(v)}${Math.abs(v * 100).toFixed(2)}pp`;
  return `${sign(v)}${Math.abs(v * 100).toFixed(2)}%`;
}

/** Purpose: the CSS class of a change: up / down, or "" for zero / none. Contract: pure. */
export const changeClass = (v: number | null) => (v == null || v === 0 ? "" : v > 0 ? "up" : "down");

/** Purpose: the rows of one group in document order. Contract: rows of other groups are dropped. */
export const groupRows = (rows: RatesFxRow[], group: string) => rows.filter((r) => r.group === group);

/** Purpose: the page headline for a group: 10Y and USDCNH lines first, then that group's alerts; "没有提醒" when none. Contract: rows missing from the document are skipped. */
export function ratesHeadline(rows: RatesFxRow[], flags: RatesFxFlag[], group: string): string {
  const by = new Map(rows.map((r) => [r.key, r]));
  const lead = group === "债市" ? ["cn_10y", "cn_30y"] : ["usdcnh", "cn_us_10y"];
  const parts = lead.map((k) => by.get(k)).filter((r): r is RatesFxRow => !!r)
    .map((r) => `${r.name} ${formatLevel(r.value, r.unit)}（一周 ${formatChange(r.chg["1w"], r.unit)}，5年分位 ${r.pct == null ? "—" : `${Math.round(r.pct * 100)}%`}）`);
  const keys = new Set(rows.filter((r) => r.group === group).map((r) => r.key));
  const alerts = flags.filter((f) => keys.has(f.key.split(":")[0])).map((f) => f.message);
  return `${parts.join("；")}。${alerts.length ? `提醒：${alerts.join("；")}。` : "没有提醒。"}`;
}

/** Purpose: rows drawn as charts in a group, in this order. Contract: keys missing from the document are skipped. */
export const CHART_KEYS: Record<string, string[]> = {
  债市: ["cn_10y", "cn_30y", "term_10_1", "credit_bank", "erp", "anchor"],
  汇率: ["usdcnh", "fix_gap", "eurcnh", "cnhjpy", "dxy", "cn_us_10y"],
};

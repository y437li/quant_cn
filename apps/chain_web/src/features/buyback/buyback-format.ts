import type { BuybackRow, BuybackSection } from "../../api/client";

export const LOAN = "专项贷款";
export const KIND_LABEL: Record<string, string> = { buyback: "回购", increase: "增持" };
export const EVENT_LABEL: Record<string, string> = { new: "新公告", completed: "达下限", stopped: "终止", expired: "到期", ended: "期满" };

/** Purpose: an amount in 亿元 as text: ≥ 100 亿 whole with separators ("1,308亿"), ≥ 1 亿 with 2 decimals ("12.30亿"), below in 万 ("8,000万"). Contract: null → "—"; 0 → "0". */
export function formatYi(v: number | null): string {
  if (v == null) return "—";
  if (v === 0) return "0";
  if (Math.abs(v) >= 100) return `${Math.round(v).toLocaleString("en-US")}亿`;
  if (Math.abs(v) >= 1) return `${v.toFixed(2)}亿`;
  return `${Math.round(v * 1e4).toLocaleString("en-US")}万`;
}

/** Purpose: a planned range "1.00亿–2.00亿", or the one side known ("≥0.50亿", "≤2.00亿"). Contract: both null → "—". */
export function formatRange(low: number | null, high: number | null): string {
  if (low != null && high != null) return low === high ? formatYi(low) : `${formatYi(low)}–${formatYi(high)}`;
  if (low != null) return `≥${formatYi(low)}`;
  if (high != null) return `≤${formatYi(high)}`;
  return "—";
}

/** Purpose: a fraction as a whole percent ("27%"), signed when asked ("−58%"). Contract: null → "—". */
export function formatPct(v: number | null, signed = false): string {
  if (v == null) return "—";
  const p = Math.round(v * 100);
  return signed && p > 0 ? `+${p}%` : p < 0 ? `−${Math.abs(p)}%` : `${p}%`;
}

export interface BuybackFilter { tag: string; loan: boolean; minYi: number }

/** Purpose: rows passing the page filters: tag ("" = all), 专项贷款 only, planned high ≥ minYi (亿). Contract: pure; order kept. */
export function filterRows(rows: BuybackRow[], f: BuybackFilter): BuybackRow[] {
  return rows.filter((r) => (!f.tag || r.tags.includes(f.tag)) && (!f.loan || r.funding.includes(LOAN))
    && (f.minYi <= 0 || (r.high_yi ?? r.low_yi ?? 0) >= f.minYi));
}

/** Purpose: the headline of one kind: live count, planned range, executed, loans, the window's new count. Contract: pure. */
export function buybackHeadline(s: BuybackSection, kind: string, days: number): string {
  const t = s.totals.all;
  const fresh = s.events.filter((e) => e.event === "new").length;
  const name = KIND_LABEL[kind] ?? kind;
  return `在执行的${name} ${t.count} 个，计划 ${formatRange(t.low_yi, t.high_yi)}，已执行 ${formatYi(t.executed_yi)}；`
    + `用${LOAN}的 ${s.totals.loan.count} 个（贷款 ${formatYi(s.totals.loan.loan_yi)}）。近 ${days} 天新公告 ${fresh} 个。`;
}

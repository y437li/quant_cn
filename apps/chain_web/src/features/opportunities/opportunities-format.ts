import type { Opportunities, OpportunityRow } from "../../api/client";

/** Rule names of OpportunitySettings in plain words. */
export const RULE_LABEL: Record<string, string> = {
  retail_leaving: "散户离场",
  inflow: "大单流入",
  earnings: "利润拐点",
  valuation: "估值低于中位",
  fit: "不加重持仓风格",
};

/** Purpose: a share as a signed percent ("+56%"); null → "—". Contract: pure; whole percent. */
export function formatSignedPct(v: number | null): string {
  return v == null ? "—" : `${v >= 0 ? "+" : ""}${Math.round(v * 100)}%`;
}

/** Purpose: the group a row belongs to on the page. Contract: listed + new → "new", listed → "stay", near → "near". */
export function rowGroup(r: OpportunityRow): "new" | "stay" | "near" {
  if (r.status === "near") return "near";
  return r.is_new ? "new" : "stay";
}

/** Purpose: "PB 1.68，5 年中位 2.43" style valuation text. Contract: missing value or median → "—". */
export function formatValuation(r: OpportunityRow, field: string): string {
  if (r.val_value == null || r.val_median == null) return "—";
  return `${field.toUpperCase()} ${r.val_value.toFixed(2)} / ${r.val_median.toFixed(2)}`;
}

/** Purpose: the page headline. Contract: "11-18：入选 2 只（新 1），差一条 5 只；移出 1 只" ; empty list says so. */
export function opportunityHeadline(doc: Opportunities): string {
  const listed = doc.rows.filter((r) => r.status === "listed");
  const fresh = listed.filter((r) => r.is_new).length;
  const near = doc.rows.length - listed.length;
  const day = `${doc.as_of.slice(4, 6)}-${doc.as_of.slice(6)}`;
  const out = doc.dropped.length ? `；移出 ${doc.dropped.length} 只` : "";
  if (!doc.rows.length) return `${day}：今天没有股票满足条件${out}。`;
  return `${day}：入选 ${listed.length} 只（新 ${fresh}），差一条 ${near} 只${out}。`;
}

import type { ConditionResult, ConditionStatus, PositionReview } from "../../api/client";

/**
 * Purpose: pure display helpers for structured conditions and the position chip row (plan 15 ph7f). Every value is
 * computed in Python (ConditionEvaluator, PositionReviewer); this only formats them.
 * Contract: numbers in, strings out; null → "—"; unknown is shown as unknown, never as met.
 */

const OPS: Record<string, string> = { "<=": "≤", ">=": "≥", "<": "<", ">": ">", "==": "=" };

/** Purpose: a metric value in its unit. Contract: fractions as %, 亿 flows signed, counts plain; null → "—". */
export function metricText(metric: string, v: number | null): string {
  if (v == null) return "—";
  if (/^(gm_q|dedt_yoy_q|holders_chg_q|margin_chg_60d|shareholder_yield|buyback_yield|buyback_done_pct|rz_chg_20d)$/.test(metric)) return (v * 100).toFixed(1) + "%";
  if (/_pp$/.test(metric)) return (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(2) + "pp";
  if (/_pct$|^winner_rate$/.test(metric)) return v.toFixed(1) + "%";
  if (/_net_/.test(metric)) return (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(2) + "亿";
  if (/^(retail_gauge|ocf_to_np|bank_etf_z)$/.test(metric)) return v.toFixed(2);
  return Number.isInteger(v) ? String(v) : v.toFixed(2);
}

/** Purpose: tooltip of one chip. Contract: "大单… · 现值 1 · 要求 ≥ 3"; required ones start with "【必须】". */
export const conditionTitle = (c: ConditionResult): string =>
  `${c.required ? "【必须】" : ""}${c.label} · 现值 ${metricText(c.metric, c.actual)} · 要求 ${OPS[c.op] ?? c.op} ${metricText(c.metric, c.value)}`;

/** Purpose: a chip's mark. Contract: met → "✓", unmet → "✗", unknown → "?". */
export const stateMark = (c: ConditionResult): string => (c.state === "met" ? "✓" : c.state === "unmet" ? "✗" : "?");

/** Purpose: count line. Contract: 2 met of 3, needed 2 → "已满足 2 / 3（需要 2）"; needed null → "（需要全部）". */
export function conditionCount(cs: ConditionResult[], needed: number | null): string {
  const met = cs.filter((c) => c.state === "met").length;
  return `已满足 ${met} / ${cs.length}` + (needed == null ? "（需要全部）" : `（需要 ${needed}）`);
}

/** Purpose: label of the combined status. Contract: buy → "可以买", near → "价到，条件未齐", wait → "等待". */
export const conditionStatusLabel = (s: ConditionStatus): string => (s === "buy" ? "可以买" : s === "near" ? "价到，条件未齐" : "等待");

/** RetailGauge bands (percentile of predicted holder growth): class, label. ≥ 0.8 is the e-mail's retail-inflow alert. */
export const GAUGE_BANDS: [number, string, string][] = [
  [0.8, "rg-hot", "散户在进（≥ 0.8）"], [0.6, "rg-warm", "散户偏多（0.6–0.8）"], [0.4, "rg-mid", "中性（0.4–0.6）"],
  [0.2, "rg-cool", "散户偏少（0.2–0.4）"], [-Infinity, "rg-cold", "散户在走、筹码集中（< 0.2）"],
];

/** Purpose: colour band of a RetailGauge value. Contract: null → ["", "无数据"]; bands from GAUGE_BANDS, lower bound inclusive. */
export function gaugeBand(v: number | null): [string, string] {
  if (v == null) return ["", "无数据"];
  const band = GAUGE_BANDS.find(([lo]) => v >= lo) as [number, string, string];
  return [band[1], band[2]];
}

/** Purpose: the 散户过热 badge of a reading (D-155 / D-167). Contract: gauge_avoid_strong 1 → strong badge; gauge_avoid 1 → badge; else null. */
export function gaugeBadge(chips: Record<string, number | null | undefined>): { cls: string; label: string } | null {
  if (chips.gauge_avoid_strong === 1) return { cls: "rg-avoid-strong", label: "散户过热·连续" };
  if (chips.gauge_avoid === 1) return { cls: "rg-avoid", label: "散户过热" };
  return null;
}

/**
 * Purpose: the D-167 streak as text, e.g. "≤0.3 连续 2/3" or "≥0.9 连续 3/3".
 * Contract: low side when retail_gauge ≤ 0.3 and gauge_lo_streak ≥ 1, high side when ≥ 0.9 and gauge_hi_streak ≥ 1; else "".
 */
export function gaugeStreak(chips: Record<string, number | null | undefined>, need = 3): string {
  const v = chips.retail_gauge;
  if (v == null) return "";
  const lo = chips.gauge_lo_streak ?? 0, hi = chips.gauge_hi_streak ?? 0;
  if (v <= 0.3 && lo >= 1) return `≤0.3 连续 ${Math.min(lo, need)}/${need}`;
  if (v >= 0.9 && hi >= 1) return `≥0.9 连续 ${Math.min(hi, need)}/${need}`;
  return "";
}

/** Chip-row columns of the 持仓 page: key, header. */
export const CHIP_COLUMNS: [string, string][] = [
  ["holders_chg_q", "户数季变"], ["retail_gauge", "散户温度计"], ["winner_rate", "获利盘"], ["lg_net_4w", "大单4周"],
  ["lg_weeks_pos_4w", "大单流入周"], ["margin_chg_60d", "融资60日"], ["north_chg_pp", "北向上期变化"], ["gm_q", "单季毛利率"],
  ["dedt_yoy_q", "单季扣非同比"], ["unlock_6m_pct", "半年解禁"], ["shareholder_yield", "股东回报率"], ["buyback_plan_pct", "回购计划"],
];

/** Purpose: positions with any flag, flag messages joined. Contract: none → []; order of the input. */
export function listAlerts(reviews: Record<string, PositionReview>, names: Record<string, string>): string[] {
  return Object.entries(reviews).filter(([, r]) => r.flags.length > 0)
    .map(([code, r]) => `${names[code] ?? code}：${r.flags.map((f) => f.message).join("；")}`);
}

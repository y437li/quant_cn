import type { MarginPanel } from "../../api/client";

/** Purpose: the one-line reading of a stock's margin state. Contract: missing numbers print "—". */
export function marginHeadline(m: MarginPanel): string {
  const n = (v: number | null, d = 2) => (v == null ? "—" : v.toFixed(d));
  const chg = m.rz_chg_20d == null ? "—" : `${m.rz_chg_20d > 0 ? "+" : ""}${(m.rz_chg_20d * 100).toFixed(1)}%`;
  return `融资余额 ${n(m.rz_yi)} 亿（占流通市值 ${n(m.rz_pct_float, 1)}%），20 日 ${chg}；融券 ${n(m.rq_wan, 0)} 万元`;
}

/** Purpose: flag the margin signals the research found contrarian. Contract: list of short warnings, [] when none. */
export function marginWarnings(m: MarginPanel): string[] {
  const out: string[] = [];
  if (m.rz_chg_20d != null && m.rz_chg_20d >= 0.15) out.push("融资 20 日增加 ≥ 15%：杠杆资金在追（历史上之后偏弱）");
  if (m.rq_max_wan && m.rq_wan != null && m.rq_wan >= 0.9 * m.rq_max_wan && m.rq_wan > 0) out.push("融券接近一年最高：有人在加空");
  return out;
}

/** Purpose: the price at which the first forced liquidations start, both margin assumptions. */
export const firstLiquidation = (m: MarginPanel): string =>
  m.ladder.first_liq == null ? "无融资仓位" : `首批平仓约 ${m.ladder.first_liq.toFixed(2)}（保证金 100%）/ ${m.ladder.first_liq_low_margin?.toFixed(2)}（80%）`;

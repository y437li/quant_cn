import { describe, expect, it } from "vitest";
import type { MarginPanel } from "../../api/client";
import { firstLiquidation, marginHeadline, marginWarnings } from "./margin-format";

const m: MarginPanel = {
  code: "301358.SZ", as_of: "20261112", float_mv_yi: 401.2, rz_yi: 17.18, rz_pct_float: 4.28, rz_chg_20d: -0.016, rz_net_20d_yi: -0.3,
  rq_wan: 773.1, rq_pct_float: 0.02, rq_max_wan: 2995.3, rq_sell_20d_wan: 12.3,
  ladder: { debt_yi: 17.76, first_liq: 34.01, first_liq_low_margin: 37.79, forced: [] }, daily: [],
};

describe("margin-format", () => {
  it("TC-MGF-001 headline and first liquidation", () => {
    expect(marginHeadline(m)).toBe("融资余额 17.18 亿（占流通市值 4.3%），20 日 -1.6%；融券 773 万元");
    expect(firstLiquidation(m)).toBe("首批平仓约 34.01（保证金 100%）/ 37.79（80%）");
  });
  it("TC-MGF-002 warnings only on chasing financing or near-max shorts", () => {
    expect(marginWarnings(m)).toEqual([]);
    expect(marginWarnings({ ...m, rz_chg_20d: 0.2, rq_wan: 2900 }).length).toBe(2);
  });
});

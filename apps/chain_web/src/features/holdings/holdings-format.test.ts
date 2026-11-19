import { describe, expect, it } from "vitest";
import type { HoldingsRisk } from "../../api/client";
import { expo, holdingsHeadline, listIndustries, listStyles, pnlClass, pnlPct, share, yuan } from "./holdings-format";
import sample from "./holdings-risk.fixture.json";

const doc = sample as unknown as HoldingsRisk;

describe("holdings formatting", () => {
  it("TC-HRW-001 numbers", () => {
    expect([yuan(1234567), yuan(-98765.43), yuan(null), share(0.2664), share(undefined), expo(-0.689), expo(0.3), expo(0.001), expo(null)])
      .toEqual(["1,234,567", "−98,765", "—", "26.6%", "—", "−0.69", "+0.30", "0.00", "—"]);
    expect([pnlClass(1), pnlClass(-1), pnlClass(null)]).toEqual(["up", "down", "flat"]);
    expect([pnlPct({ cost: 8, pnl_pct: 0.25 }), pnlPct({ cost: -2.46, pnl_pct: null }), pnlPct({ cost: 0, pnl_pct: null }), pnlPct({ cost: 5, pnl_pct: null })])
      .toEqual(["+25.0%", "已回本", "已回本", "—"]);
  });
  it("TC-HRW-002 grouping", () => {
    expect(listStyles(doc.factors).map((f) => f.factor)).toEqual(["momentum"]);
    expect(listIndustries(doc.factors).map((f) => f.label)).toEqual(["农林牧渔"]);
  });
  it("TC-HRW-003 headline", () => {
    expect(holdingsHeadline(doc)).toBe(
      "2026-11-11 收盘：总资产 1,000,000 元（股票 950,000，现金 50,000），浮动盈亏 −50,000 元。组合年化波动 19.6%，相对 000300.SH 跟踪误差 15.1%；大盘贡献 60.2% 的风险；最大的风格偏离是 动量 −0.68。");
    expect(holdingsHeadline({ ...doc, as_of: "" })).toBe("");
  });
});

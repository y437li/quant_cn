import { describe, expect, it } from "vitest";
import type { HoldingsRisk } from "../../api/client";
import { expo, holdingsHeadline, listIndustries, listStyles, pnlClass, share, yuan } from "./holdings-format";
import sample from "./holdings-risk.fixture.json";

const doc = sample as unknown as HoldingsRisk;

describe("holdings formatting", () => {
  it("TC-HRW-001 numbers", () => {
    expect([yuan(1144171), yuan(-191804.93), yuan(null), share(0.2664), share(undefined), expo(-0.689), expo(0.3), expo(0.001), expo(null)])
      .toEqual(["1,144,171", "−191,805", "—", "26.6%", "—", "−0.69", "+0.30", "0.00", "—"]);
    expect([pnlClass(1), pnlClass(-1), pnlClass(null)]).toEqual(["up", "down", "flat"]);
  });
  it("TC-HRW-002 grouping", () => {
    expect(listStyles(doc.factors).map((f) => f.factor)).toEqual(["momentum"]);
    expect(listIndustries(doc.factors).map((f) => f.label)).toEqual(["农林牧渔"]);
  });
  it("TC-HRW-003 headline", () => {
    expect(holdingsHeadline(doc)).toBe(
      "2026-11-11 收盘：总资产 1,144,171 元（股票 1,122,156，现金 22,015），浮动盈亏 −191,805 元。组合年化波动 19.6%，相对 000300.SH 跟踪误差 15.1%；大盘贡献 60.2% 的风险；最大的风格偏离是 动量 −0.68。");
    expect(holdingsHeadline({ ...doc, as_of: "" })).toBe("");
  });
});

import { describe, expect, it } from "vitest";
import type { FuturesFamily } from "../../api/client";
import fixture from "./futures-monitor.fixture.json";
import { REGIME_ZH, groupFamilies, isExtreme, lotsText, moveClass, pctText, priceText, shortMonth, signedPct, spreadText } from "./futures-format";

const fams = fixture.families as unknown as FuturesFamily[];

describe("futures-format", () => {
  it("TC-FUF-001 groups in first-seen order", () => {
    expect(groupFamilies(fams).map(([g, r]) => [g, r.length])).toEqual([["有色", 1], ["农产品", 1]]);
  });
  it("TC-FUF-002 number formats", () => {
    expect([signedPct(0.038), signedPct(-0.02), signedPct(null)]).toEqual(["+3.8%", "−2.0%", "—"]);
    expect([priceText(86500), priceText(12.34), priceText(5.4)]).toEqual(["86,500", "12.3", "5.40"]);
    expect([pctText(0.99), shortMonth("202612"), moveClass(-1)]).toEqual(["99%", "26-12", "down"]);
    expect([spreadText({ kind: "sum" }, -9.8, true), spreadText({ kind: "sum" }, 1124.5), spreadText({ kind: "ratio" }, 0.29, true)]).toEqual(["−10", "1,125", "+0.29"]);
  });
  it("TC-FUF-003 extremes at the 5% / 95% bounds", () => {
    expect([isExtreme(0.95), isExtreme(0.94), isExtreme(0.05), isExtreme(null)]).toEqual([true, false, true, false]);
  });
  it("TC-FUF-004 lots and regimes", () => {
    expect([lotsText(-25695), lotsText(3462), lotsText(null), lotsText(5, false)]).toEqual(["−25,695", "+3,462", "—", "5"]);
    expect(REGIME_ZH.long_liquidation).toBe("多头减仓");
  });
});

import { describe, expect, it } from "vitest";
import type { RatesFxRow } from "../../api/client";
import { changeClass, formatChange, formatLevel, groupRows, ratesHeadline } from "./rates-fx-format";

const row = (key: string, group: string, unit: RatesFxRow["unit"], value: number, w: number | null): RatesFxRow => ({
  key, name: key, group, unit, date: "20261117", value, chg: { "1w": w, "1m": null, "3m": null, "1y": null },
  pct: 0.01, low_1y: null, high_1y: null, stale: false, alerts: [], history: [],
});

describe("rates-fx format", () => {
  it("TC-RFF-001 levels and changes by unit", () => {
    expect(formatLevel(1.6055, "yield")).toBe("1.6055%");
    expect(formatLevel(-22.96, "bp")).toBe("−23.0bp");
    expect(formatLevel(6.6661, "rate")).toBe("6.6661");
    expect(formatLevel(159.2305, "rate")).toBe("159.23");
    expect(formatLevel(-0.0071, "gap")).toBe("−0.71%");
    expect(formatLevel(null, "rate")).toBe("—");
    expect(formatChange(-4.4, "yield")).toBe("−4bp");
    expect(formatChange(0.0126, "rate")).toBe("+1.26%");
    expect(formatChange(0.0004, "gap")).toBe("+0.04pp");
    expect(formatChange(0, "bp")).toBe("0bp");
    expect(changeClass(-1)).toBe("down");
    expect(changeClass(null)).toBe("");
  });

  it("TC-RFF-002 headline: lead rows, then the group's alerts; groupRows keeps one group", () => {
    const rows = [row("cn_10y", "债市", "yield", 1.6055, 0.9), row("usdcnh", "汇率", "rate", 6.6661, -0.0011)];
    const flags = [{ key: "cn_10y:extreme", kind: "extreme", name: "x", message: "10年新低" }];
    expect(ratesHeadline(rows, flags, "债市")).toBe("cn_10y 1.6055%（一周 +1bp，5年分位 1%）。提醒：10年新低。");
    expect(ratesHeadline(rows, flags, "汇率")).toBe("usdcnh 6.6661（一周 −0.11%，5年分位 1%）。没有提醒。");
    expect(groupRows(rows, "汇率").map((r) => r.key)).toEqual(["usdcnh"]);
  });
});

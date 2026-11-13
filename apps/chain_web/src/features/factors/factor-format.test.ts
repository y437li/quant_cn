import { describe, expect, it } from "vitest";
import type { FactorMonitor } from "../../api/client";
import { factorName, isAlert, monitorHeadline, moveClass, sigma, signedPct, splitFactors, toPoints, volPct } from "./factor-format";
import doc from "./factor-monitor.fixture.json";

const monitor = doc as unknown as FactorMonitor;

describe("factor monitor formatting", () => {
  it("TC-FMW-001 numbers", () => {
    expect([signedPct(0.0123), signedPct(-0.004), signedPct(0), signedPct(null), volPct(0.182), volPct(undefined)])
      .toEqual(["+1.23%", "−0.40%", "0.00%", "—", "18.2%", "—"]);
    expect([sigma(-1.234), sigma(0.04), sigma(2), sigma(null)]).toEqual(["−1.2σ", "0.0σ", "+2.0σ", "—"]);
    expect([moveClass(0.1), moveClass(-0.1), moveClass(0), moveClass(null)]).toEqual(["up", "down", "flat", "flat"]);
  });
  it("TC-FMW-002 alerts, split and points", () => {
    expect([isAlert({ sigma_move: -2.1, vol_ratio: 1 }), isAlert({ sigma_move: 0.5, vol_ratio: 1.6 }), isAlert({ sigma_move: null, vol_ratio: null })])
      .toEqual([true, true, false]);
    const { styles, industries } = splitFactors(monitor.factors);
    expect(styles.map((f) => f.factor)).toEqual(["country", "momentum"]);
    expect(industries.map((f) => f.label)).toEqual(["农林牧渔"]);
    expect([factorName(styles[0]), factorName(styles[1]), factorName(industries[0]), factorName({ factor: "x", label: "x", kind: "style" })])
      .toEqual(["市场", "动量", "农林牧渔", "x"]);
    expect(factorName({ factor: "dividend_yield", label: "dividend_yield", kind: "style" })).toBe("股息率");
    expect(toPoints(["a", "b", "c"], [1, null, 3])).toEqual([{ d: "a", v: 1 }, { d: "c", v: 3 }]);
  });
  it("TC-FMW-003 headline", () => {
    expect(monitorHeadline(monitor)).toBe("2026-11-11 收盘：市场因子 +0.42%；风格里动得最多的是 动量 −0.31%（−1.2σ）。");
    expect(monitorHeadline({ ...monitor, factors: [] })).toBe("");
  });
});

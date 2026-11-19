import { describe, expect, it } from "vitest";
import type { SmallCapWatch, VolatilityMonitor } from "../../api/client";
import fixture from "./volatility-monitor.fixture.json";
import { SHARE_BOTTOM_REFS, STATE_LABEL, formatScTrigger, formatScValue, levelRefs, marginChartPoints, marginDepthRefs, marginPoints, marginShareChartPoints, marginSharePoints, orderRows, smallCapHeadline, smallPoints } from "./smallcap-format";

const w = (fixture as VolatilityMonitor).smallcap as SmallCapWatch;

describe("smallcap-format", () => {
  it("TC-SCF-001 triggered rows first, nothing lost", () => {
    const keys = orderRows(w.rows).map((r) => r.key);
    expect(keys).toEqual(["gap", "limit_downs", "level_6075", "etf_flow_1d"]);
    expect(STATE_LABEL.on).toBe("已触发");
  });
  it("TC-SCF-002 values and triggers by unit", () => {
    expect(w.rows.map(formatScValue)).toEqual(["84只", "6,092", "21.9%", "—"]);
    expect(formatScValue({ value: 0.3633, unit: "占比" })).toBe("36%");
    expect(formatScValue({ value: -136.17, unit: "亿" })).toBe("−136.2亿");
    expect(w.rows.map(formatScTrigger)).toEqual(["≥ 500只", "≤ 6,075", "≥ 90% 分位", ""]);
    expect(formatScTrigger({ trigger: 0.7, unit: "占比" })).toBe("≥ 70%");
  });
  it("TC-SCF-003 chart points, level lines and headline", () => {
    expect(smallPoints([...w.history, { date: "x", small: null, limit_downs: null, low_share: null, gap: null, gap_pct: null }])).toHaveLength(3);
    expect(levelRefs([...w.rows, { ...w.rows[1], key: "l2", trigger: 5500 }])).toEqual([5500, 6075]);
    expect(smallCapHeadline(w.rows, [])).toBe("已触发 中证1000 - 沪深300 波动差；接近：中证1000 跌到 6,075 6,092。");
    expect(smallCapHeadline(w.rows, ["gap"])).toContain("波动差（新）");
    expect(smallCapHeadline(w.rows.map((r) => ({ ...r, state: "off" as const })), [])).toBe("没有触发。");
  });
  it("TC-SCF-004 margin rows and chart points (plan 30 ph4)", () => {
    expect(formatScValue({ value: 22083.4, unit: "亿元" })).toBe("22,083亿元");
    expect(formatScValue({ value: 2.514, unit: "%" })).toBe("2.5%");
    expect(formatScTrigger({ trigger: 0, unit: "占比" })).toBe("≥ 0%");
    const h = [
      { date: "20261117", small: 6100, limit_downs: 1, low_share: 0.3, gap: 20, gap_pct: 0.9, rz: 22171, rz_ma: 22950, rz_circ: 0.0251 },
      { date: "20261118", small: 6053, limit_downs: 2, low_share: 0.4, gap: 21, gap_pct: 0.9 },
    ];
    expect(marginPoints(h)).toEqual([{ date: "20261117", value: 22171 }]);
    expect(marginSharePoints(h)[0].value).toBeCloseTo(2.51);
  });
  it("TC-SCF-006 long share chart points (plan 30 ph6)", () => {
    const history = [{ date: "20261117", small: 6100, limit_downs: 1, low_share: 0.3, gap: 20, gap_pct: 0.9, rz_circ: 0.0251 }, { date: "20261118", small: 6053, limit_downs: 2, low_share: 0.4, gap: 21, gap_pct: 0.9, rz_circ: 0.0253 }];
    const long = [{ date: "20190104", share: 2.078, small: 4498 }, { date: "20261113", share: 2.518, small: null }];
    expect(marginShareChartPoints({ history, margin_share_long: long })).toEqual([{ date: "20190104", value: 2.078 }, { date: "20261113", value: 2.518 }]);
    expect(marginShareChartPoints({ history })[1].value).toBeCloseTo(2.53);
    expect(marginShareChartPoints({ history, margin_share_long: long.slice(0, 1) })).toHaveLength(2);
    expect(SHARE_BOTTOM_REFS).toEqual([1.94, 2.54]);
  });
  it("TC-SCF-005 涨跌 rows and 建仓档 rows (plan 30 ph5)", () => {
    expect(formatScValue({ value: -0.0188, unit: "涨跌" })).toBe("−1.9%");
    expect(formatScTrigger({ trigger: -0.03, unit: "涨跌" })).toBe("≤ −3%");
    expect(formatScValue({ value: null, unit: "" })).toBe("—");
    expect(formatScTrigger({ trigger: null, unit: "" })).toBe("");
  });
  it("TC-SCF-007 balance chart points and depth lines (plan 30 ph7)", () => {
    const history = [{ date: "20261117", small: 6100, limit_downs: 1, low_share: 0.3, gap: 20, gap_pct: 0.9, rz: 22171 }, { date: "20261118", small: 6053, limit_downs: 2, low_share: 0.4, gap: 21, gap_pct: 0.9, rz: 22083 }];
    const long = [{ date: "20190104", share: 2.078, small: 4498, rz: 9000 }, { date: "20260626", share: 2.8, small: 7000, rz: 30000 }, { date: "20261113", share: 2.518, small: null, rz: 22000 }];
    const margin_episodes = [{ name: "2015", depth: -0.6, months: 12 }, { name: "2024", depth: -0.13, months: 9 }];
    expect(marginChartPoints({ history, margin_share_long: long }).map((p) => p.value)).toEqual([9000, 30000, 22000]);
    expect(marginChartPoints({ history, margin_share_long: long.map(({ rz: _, ...p }) => p) })).toHaveLength(2);
    const refs = marginDepthRefs({ history, margin_share_long: long, margin_episodes });
    expect(refs[0]).toBeCloseTo(12000);
    expect(refs[1]).toBeCloseTo(26100);
    expect(marginDepthRefs({ history, margin_episodes })).toEqual([]);
  });
});

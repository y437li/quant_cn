import { describe, expect, it } from "vitest";
import type { ConditionResult } from "../../api/client";
import { conditionCount, conditionStatusLabel, conditionTitle, gaugeBadge, gaugeBand, gaugeStreak, listAlerts, metricText, stateMark } from "./condition-format";

const c = (state: ConditionResult["state"], actual: number | null): ConditionResult =>
  ({ label: "大单近 4 周至少 3 周净流入", kind: "flow", metric: "lg_weeks_pos_4w", op: ">=", value: 3, actual, state });

describe("condition-format (plan 15 ph7f)", () => {
  it("TC-CF-001 metric units and unknown values", () => {
    expect(metricText("gm_q", 0.2214)).toBe("22.1%");
    expect(metricText("lg_net_4w", -2.5)).toBe("−2.50亿");
    expect(metricText("north_chg_pp", 0.4)).toBe("+0.40pp");
    expect(metricText("winner_rate", 9.5)).toBe("9.5%");
    expect(metricText("lg_weeks_pos_4w", 3)).toBe("3");
    expect(metricText("retail_gauge", null)).toBe("—");
  });
  it("TC-CF-002 chips, counts and status labels", () => {
    expect(stateMark(c("met", 3))).toBe("✓");
    expect(stateMark(c("unknown", null))).toBe("?");
    expect(conditionTitle(c("unmet", 1))).toBe("大单近 4 周至少 3 周净流入 · 现值 1 · 要求 ≥ 3");
    expect(conditionCount([c("met", 3), c("unknown", null)], 2)).toBe("已满足 1 / 2（需要 2）");
    expect(conditionCount([c("met", 3)], null)).toBe("已满足 1 / 1（需要全部）");
    expect(conditionStatusLabel("near")).toBe("价到，条件未齐");
  });
  it("TC-CF-003 alerts list only flagged positions", () => {
    const reviews = {
      A: { note: null, flags: [{ kind: "note" as const, message: "缺少持仓笔记" }], chips: {}, period: null, conditions: [] },
      B: { note: null, flags: [], chips: {}, period: null, conditions: [] },
    };
    expect(listAlerts(reviews, { A: "甲" })).toEqual(["甲：缺少持仓笔记"]);
  });
  it("TC-CF-004 RetailGauge colour bands", () => {
    expect([0.85, 0.8, 0.7, 0.5, 0.3, 0.1].map((v) => gaugeBand(v)[0])).toEqual(["rg-hot", "rg-hot", "rg-warm", "rg-mid", "rg-cool", "rg-cold"]);
    expect(gaugeBand(null)).toEqual(["", "无数据"]);
  });

  it("TC-CF-006 散户过热 badge and streak", () => {
    expect(gaugeBadge({ gauge_avoid: 1, gauge_avoid_strong: 1 })?.cls).toBe("rg-avoid-strong");
    expect(gaugeBadge({ gauge_avoid: 1, gauge_avoid_strong: 0 })?.label).toBe("散户过热");
    expect(gaugeBadge({ gauge_avoid: 0 })).toBeNull();
    expect(gaugeStreak({ retail_gauge: 0.2, gauge_lo_streak: 2 })).toBe("≤0.3 连续 2/3");
    expect(gaugeStreak({ retail_gauge: 0.95, gauge_hi_streak: 5 })).toBe("≥0.9 连续 3/3");
    expect(gaugeStreak({ retail_gauge: 0.5, gauge_lo_streak: 2 })).toBe("");
    expect(gaugeStreak({ retail_gauge: null })).toBe("");
  });
});

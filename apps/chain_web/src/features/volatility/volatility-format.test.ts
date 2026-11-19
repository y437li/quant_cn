import { describe, expect, it } from "vitest";
import type { VolatilityMonitor } from "../../api/client";
import fixture from "./volatility-monitor.fixture.json";
import { alertText, dayLabel, formatVol, groupLines, refLevel, volHeadline } from "./volatility-format";

const doc = fixture as VolatilityMonitor;

describe("volatility-format", () => {
  it("TC-VOF-001 groups in fixed order and formats values", () => {
    expect(groupLines(doc.lines).map(([g]) => g)).toEqual(["美国", "A股"]);
    expect([formatVol(-0.24, true), formatVol(1.21, true), formatVol(null)]).toEqual(["−0.2", "+1.2", "—"]);
    expect(dayLabel("20261113")).toBe("2026-11-13");
  });
  it("TC-VOF-002 reference level and alert rules", () => {
    expect([refLevel(doc.lines[0]), refLevel(doc.lines[1])]).toEqual([25, 18.9]);
    expect(alertText(doc.lines[0])).toBe("≥ 25，单日涨 ≥ 30%");
    expect(alertText(doc.lines[1])).toBe("≥ 1年 90% 分位");
  });
  it("TC-VOF-003 headline lists values, percentiles and alerts", () => {
    expect(volHeadline(doc.lines, doc.flags)).toBe("美国 VIX 18.7（70%），300ETF VIX 17.6。提醒：美国 VIX 28.2 ≥ 25。");
    expect(volHeadline(doc.lines, [])).toBe("美国 VIX 18.7（70%），300ETF VIX 17.6。没有提醒。");
  });
});

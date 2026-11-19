import { describe, expect, it } from "vitest";
import type { MacroSeries } from "../../api/client";
import fixture from "./macro-monitor.fixture.json";
import { formatValue, groupSeries, isExtreme, macroHeadline, monthLabel, refLine } from "./macro-format";

const doc = fixture as { series: MacroSeries[]; new_prints: string[] };

describe("macro-format", () => {
  it("TC-MCF-001 groups in fixed order and formats by unit", () => {
    expect(groupSeries(doc.series).map(([g]) => g)).toEqual(["价格", "景气"]);
    expect(formatValue({ key: "cpi", unit: "%" }, -0.2, true)).toBe("−0.2%");
    expect(formatValue({ key: "sf_inc", unit: "亿元" }, 18895, true)).toBe("+18,895");
    expect(formatValue({ key: "sf_stock_yoy", unit: "%" }, 7.11)).toBe("7.11%");
    expect(formatValue({ key: "pmi_mfg", unit: "" }, null)).toBe("—");
  });
  it("TC-MCF-002 extremes, reference lines and labels", () => {
    expect([isExtreme(0.1), isExtreme(0.5), isExtreme(0.95), isExtreme(null)]).toEqual([true, false, true, false]);
    expect([refLine("pmi_mfg"), refLine("cpi")]).toEqual([50, 0]);
    expect(monthLabel("202610")).toBe("2026-10");
  });
  it("TC-MCF-003 headline names the latest month and the extremes", () => {
    expect(macroHeadline(doc.series, doc.new_prints)).toBe("最新数据 2026-10；1 项新发布。处于 5 年极端分位：制造业 PMI。");
  });
});

import { describe, expect, it } from "vitest";
import type { SectorDoc } from "../../api/client";
import { formatPct, formatValue, listColumns, listPeriods, marketName, periodLabel, rankChange } from "./sector-monitor-format";

describe("sector monitor format", () => {
  it("formats values by unit and percentiles", () => {
    expect(formatValue(1532.784, "亿元")).toBe("1,532.8");
    expect(formatValue(0.051, "元")).toBe("0.051");
    expect(formatValue(183, "款")).toBe("183");
    expect(formatValue(null, "%")).toBe("—");
    expect(formatPct(0.857)).toBe("86%");
    expect(formatValue(33, "名")).toBe("33");
  });
  it("describes rank moves and markets", () => {
    expect(rankChange(33, 40)).toBe("↑7");
    expect(rankChange(40, 33)).toBe("↓7");
    expect(rankChange(5, 5)).toBe("–");
    expect(rankChange(5, null)).toBe("新");
    expect(rankChange(null, 5)).toBe("");
    expect(marketName("jp")).toBe("日本");
    expect(marketName("zz")).toBe("ZZ");
    expect(marketName(null)).toBe("");
  });
  it("labels periods", () => {
    expect(periodLabel("2026-10")).toBe("26年10月");
    expect(periodLabel("20260930")).toBe("26Q3");
    expect(periodLabel("20261117")).toBe("11-17");
    expect(periodLabel("2025")).toBe("2025");
  });
  it("lists periods and table columns", () => {
    const doc: SectorDoc = {
      key: "games", name: "游戏", as_of: "20261117", index: { code: "801764.SI", name: "申万游戏Ⅱ" },
      charts: [
        { key: "game_approvals", title: "每月版号数", unit: "款", lines: [{ label: "全部", points: [["2026-10", 183], ["2026-09", 206]] }] },
        { key: "revenue_q", title: "单季营收", unit: "亿元", lines: [{ label: "巨人网络", points: [["20260930", 19.96]] }] },
        { key: "realized_vol", title: "20 日实际波动率(年化)", unit: "%", lines: [] },
        { key: "valuation", title: "PE(TTM) 5 年分位", unit: "%", in_table: true, extra: { key: "valuation_level", label: "PE(TTM)", unit: "" }, lines: [] },
        { key: "surveys", title: "机构调研(天 / 月)", unit: "次", in_table: false, extra: { key: "surveys_recent", label: "近 90 天调研", unit: "次" }, lines: [] },
      ],
      table: [{ code: "002558.SZ", name: "巨人网络", kind: "company", revenue_q: 19.96, valuation: 20, valuation_level: 11.2, surveys: 1, surveys_recent: 3, vol_20: 62, vol_20_pct: 0.86, vol_60: 44, retail_gauge: 0.87 }],
    };
    expect(listPeriods(doc.charts[0])).toEqual(["2026-09", "2026-10"]);
    expect(listColumns(doc).map((c) => c.key)).toEqual(["revenue_q", "valuation", "valuation_level", "surveys_recent", "vol_20", "vol_20_pct", "vol_60", "vol_60_pct", "retail_gauge"]);
    expect(formatValue(58, "城")).toBe("58");
  });
});

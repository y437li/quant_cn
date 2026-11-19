import { describe, expect, it } from "vitest";
import type { EtfProxy, ProxyIndex } from "../../api/client";
import { flowClass, flowMatrix, heat, markYi, pctDown, pctRank, proxyHeadline, signedNum, signedYi, windowLine, windowRange, yi } from "./etf-proxy-format";

const doc = {
  as_of: "20261106", price_as_of: "20261111", start: "20220101", n_members: 161,
  totals: {
    core: { aum: 8993.6, position: 9162.2, flow_recent: 4268.4, flow_ytd: -9471.7,
      peak: { date: "20241011", position: 19250.4 }, trough_since_peak: { date: "20260706", position: 3236.1 } },
  },
  recent: [], weekly: [], yearly: [], indices: [],
} as unknown as EtfProxy;

describe("etf proxy formatting (2026-11-06 lake)", () => {
  it("TC-EPW-001 money and signed flows", () => {
    expect([yi(9162.2), yi(null), signedYi(4268.4), signedYi(-9471.7), signedYi(0.2), signedYi(undefined)])
      .toEqual(["9,162 亿", "—", "+4,268 亿", "−9,472 亿", "0 亿", "—"]);
  });
  it("TC-EPW-002 flow classes", () => {
    expect([flowClass(10), flowClass(-10), flowClass(0.3), flowClass(null)]).toEqual(["in", "out", "flat", "flat"]);
  });
  it("TC-EPW-003 headline", () => {
    expect(proxyHeadline(doc, 20)).toBe(
      "核心 ETF 仓位（按现价）9,162 亿，是峰值的 48%。峰值 19,250 亿（2024-10-11），之后最低 3,236 亿（2026-07-06）。最近 20 个交易日净申购 +4,268 亿，今年以来 −9,472 亿。份额截至 2026-11-06。");
    expect(proxyHeadline({ ...doc, totals: {} }, 20)).toBe("");
  });
  it("TC-EPW-004 index rhythm cells", () => {
    expect([markYi({ date: "20250425", position: 11376 }), markYi({ date: "", position: null }), markYi(undefined)])
      .toEqual(["11,376 亿（2025-04）", "—", "—"]);
    expect([pctDown(-21.43), pctDown(0), pctDown(null)]).toEqual(["−21.4%", "0.0%", "—"]);
  });
  it("TC-EPW-005 近3月 percentile, range and line", () => {
    const w = { pct: 96.8, low: 4169.4, high: 8977.2, days: 63 };
    expect([pctRank(w), pctRank({ ...w, pct: null }), pctRank(undefined), windowRange(w), windowRange({ ...w, low: null })])
      .toEqual(["97%", "—", "—", "4,169–8,977 亿", "—"]);
    expect([signedNum(1615), signedNum(-296.6), signedNum(0.4), signedNum(null)]).toEqual(["+1,615", "−297", "0", "—"]);
    const core = { ...doc.totals.core!, flow_weeks: 2474.6, window: { pct: 100, low: 4169.4, high: 8977.2, days: 63 } };
    const other = { ...core, window: { pct: 92.9, low: 3031.3, high: 3990.8, days: 63 } };
    const full = { ...doc, rhythm_weeks: 4, pct_window_days: 63, totals: { core, other } } as EtfProxy;
    expect(windowLine(full)).toBe(
      "近3月分位：核心 ETF 仓位 100%（区间 4,169–8,977 亿）；其他 ETF 93%（区间 3,031–3,991 亿）。核心近 4 周净申购 +2,475 亿。");
    const short = { ...full, totals: { core: { ...core, flow_weeks: null, window: { ...core.window, days: 40 } } } } as EtfProxy;
    expect(windowLine(short)).toBe("近3月分位（只有 40 个交易日）：核心 ETF 仓位 100%（区间 4,169–8,977 亿）。");
    expect(windowLine(doc)).toBe("");
  });
  it("TC-EPW-006 weekly flow matrix and heat", () => {
    const ix = (name: string, flows: [string, number][]) =>
      ({ name, weekly: flows.map(([date, flow]) => ({ date, position: null, flow })) }) as unknown as ProxyIndex;
    const rows = flowMatrix([ix("沪深300", [["20261106", 689], ["20261113", -89], ["20261118", 331]]),
      ix("中证1000", [["20261113", -101], ["20261118", -12]])], 2);
    expect(rows).toEqual([{ date: "20261118", flows: [331, -12] }, { date: "20261113", flows: [-89, -101] }]);
    expect(flowMatrix([ix("a", [["20261106", 689]])], 5)).toEqual([{ date: "20261106", flows: [689] }]);
    expect([flowMatrix([], 3), flowMatrix([ix("a", [["20261106", 1]])], 0)]).toEqual([[], []]);
    const sparse = flowMatrix([ix("a", [["20261106", 1]]), ix("b", [["20261113", 2]])], 2);
    expect(sparse[1].flows).toEqual([1, null]);
    expect([heat(331, rows), heat(-101, rows), heat(null, rows), heat(0, [{ date: "x", flows: [0] }])]).toEqual([100, 55, 0, 0]);
  });
});

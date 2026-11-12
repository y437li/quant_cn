import { describe, expect, it } from "vitest";
import type { EtfProxy } from "../../api/client";
import { flowClass, proxyHeadline, signedYi, yi } from "./etf-proxy-format";

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
});

import { describe, expect, it } from "vitest";
import type { ProxyStyle } from "../../api/client";
import { styleHeadline, stylePoints } from "./etf-style-format";

const bank: ProxyStyle = {
  key: "bank", name: "银行", metric: "bank_etf_z", as_of: "20261111", n_etf: 16, aum: 255, flow_1d: 3, flow_window: 42,
  flow_pct: 0.165, z: 1.99, status: "hot", hot_since: "20261030",
  history: [{ d: "20261030", z: 1.6, flow_pct: 0.12 }, { d: "20261106", z: null, flow_pct: null }, { d: "20261111", z: 1.99, flow_pct: 0.165 }],
};

describe("etf-style-format", () => {
  it("TC-ESF-001 headline names status, z and flow share", () => {
    expect(styleHeadline(bank)).toBe("过热 · z +2.0 · 20 日净流入 +42 亿（占规模 +16.5%）");
    expect(styleHeadline({ ...bank, status: "normal", z: null, flow_pct: null, flow_window: null })).toBe("正常 · z — · 20 日净流入 —（占规模 —）");
  });
  it("TC-ESF-002 chart points skip missing z", () => {
    expect(stylePoints(bank).map((p) => p.x)).toEqual(["20261030", "20261111"]);
  });
});

import { describe, expect, it } from "vitest";
import type { BuybackRow, BuybackSection } from "../../api/client";
import { buybackHeadline, filterRows, formatPct, formatRange, formatYi } from "./buyback-format";

const row = (code: string, tags: string[], funding: string[], high: number | null, event?: string): BuybackRow => ({
  code, name: code, date: "20261117", end: "20271117", state: "open", tags, holders: [], funding, loan_bank: null,
  loan_yi: null, low_yi: null, high_yi: high, executed_yi: 0, done_pct: 0, price_cap: null, close: null, cap_gap: null,
  mv_pct: null, labelled: true, event,
});

describe("buyback format", () => {
  it("TC-BBF-001 amounts, ranges and percents", () => {
    expect(formatYi(12.3)).toBe("12.30亿");
    expect(formatYi(1307.58)).toBe("1,308亿");
    expect(formatYi(0.8)).toBe("8,000万");
    expect(formatYi(0)).toBe("0");
    expect(formatYi(null)).toBe("—");
    expect(formatRange(1, 2)).toBe("1.00亿–2.00亿");
    expect(formatRange(null, 2)).toBe("≤2.00亿");
    expect(formatRange(0.5, null)).toBe("≥5,000万");
    expect(formatRange(null, null)).toBe("—");
    expect(formatPct(0.2735)).toBe("27%");
    expect(formatPct(-0.5838, true)).toBe("−58%");
    expect(formatPct(0.07, true)).toBe("+7%");
    expect(formatPct(null)).toBe("—");
  });

  it("TC-BBF-002 filters and headline", () => {
    const rows = [row("A", ["注销"], ["自有", "专项贷款"], 3), row("B", ["维护价值"], ["自有"], 0.5), row("C", ["注销"], ["自有"], null)];
    expect(filterRows(rows, { tag: "注销", loan: false, minYi: 0 }).map((r) => r.code)).toEqual(["A", "C"]);
    expect(filterRows(rows, { tag: "", loan: true, minYi: 0 }).map((r) => r.code)).toEqual(["A"]);
    expect(filterRows(rows, { tag: "", loan: false, minYi: 1 }).map((r) => r.code)).toEqual(["A"]);
    const s: BuybackSection = {
      live: rows, events: [row("A", [], [], 3, "new"), row("B", [], [], 1, "completed")],
      totals: { all: { count: 3, low_yi: 2, high_yi: 3.5, executed_yi: 1.25 }, by_tag: [], by_funding: [], loan: { count: 1, loan_yi: 0.9 } },
      months: [],
    };
    expect(buybackHeadline(s, "buyback", 7)).toBe("在执行的回购 3 个，计划 2.00亿–3.50亿，已执行 1.25亿；用专项贷款的 1 个（贷款 9,000万）。近 7 天新公告 1 个。");
  });
});

import { describe, expect, it } from "vitest";
import type { Opportunities, OpportunityRow } from "../../api/client";
import { formatSignedPct, formatValuation, opportunityHeadline, rowGroup } from "./opportunities-format";

const row = (over: Partial<OpportunityRow>): OpportunityRow => ({
  code: "605365.SH", name: "立达信", rank: 1, status: "listed", is_new: true, rules_hit: [], missing: [],
  pct: 0.01, exp_change: -0.05, lo_streak: 3, circ_mv: 64, lg_weeks_pos_4w: 3, lg_net_4w: 0.12, sm_weeks_neg_4w: 2,
  sm_net_4w: -0.1, margin_chg_60d: 0.02, winner_rate: 3.1, cost_lo_gap: -0.03, cost_hi_gap: -0.2, period: "20260930",
  np_yoy: 0.56, np_qoq: 0.81, val_value: 1.68, val_median: 2.43, fit_styles: "size", fit_delta: -0.2, ...over,
});

describe("opportunities format", () => {
  it("TC-OPF-001 groups, numbers and valuation", () => {
    expect(rowGroup(row({}))).toBe("new");
    expect(rowGroup(row({ is_new: false }))).toBe("stay");
    expect(rowGroup(row({ status: "near" }))).toBe("near");
    expect(formatSignedPct(0.56)).toBe("+56%");
    expect(formatSignedPct(-0.126)).toBe("-13%");
    expect(formatSignedPct(null)).toBe("—");
    expect(formatValuation(row({}), "pb")).toBe("PB 1.68 / 2.43");
    expect(formatValuation(row({ val_median: null }), "pb")).toBe("—");
  });

  it("TC-OPF-002 headline", () => {
    const doc: Opportunities = {
      as_of: "20261118", previous_as_of: "20261113",
      rules: { min_circ_mv: 50, inflow_weeks: 3, np_yoy_min: 0.2, np_qoq_min: 0, valuation_field: "pb", valuation_years: 5, fit_weight: 0.05, fit_styles: 2, top_n: 10, near_n: 5 },
      rows: [row({}), row({ is_new: false }), row({ status: "near" })],
      dropped: [{ code: "x", name: "x", status: "listed" }],
    };
    expect(opportunityHeadline(doc)).toBe("11-18：入选 2 只（新 1），差一条 1 只；移出 1 只。");
    expect(opportunityHeadline({ ...doc, rows: [], dropped: [] })).toBe("11-18：今天没有股票满足条件。");
  });
});

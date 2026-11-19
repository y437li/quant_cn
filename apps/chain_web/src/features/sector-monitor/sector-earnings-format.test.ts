import { describe, expect, it } from "vitest";
import type { SectorEarningsRow } from "../../api/client";
import { pickRows, seasonLabel, signedPct, statusLabel } from "./sector-earnings-format";

const row = (code: string, status: SectorEarningsRow["status"], pre: number | null): SectorEarningsRow => ({
  code, name: code, end_date: "20260930", status, n: 10, expected: 10, share: 1, n_top: 5, pre, react: 0,
  sig_date: null, back: null, hchg: null, rally: false,
});

describe("sector earnings format", () => {
  it("labels seasons, signs and statuses", () => {
    expect(seasonLabel("20260930")).toBe("2026Q3");
    expect(seasonLabel("20251231")).toBe("2025Q4");
    expect(seasonLabel(null)).toBe("—");
    expect(signedPct(43.83)).toBe("+43.8%");
    expect(signedPct(-0.24)).toBe("−0.2%");
    expect(signedPct(null)).toBe("—");
    expect(statusLabel("firing")).toBe("触发");
    expect(statusLabel("none")).toBe("");
  });
  it("shows firing and provisional sectors, then the closest others", () => {
    const rows = [row("a", "none", 5), row("b", "firing", 20), row("c", "none", 12), row("d", "provisional", 16), row("e", "none", null)];
    expect(pickRows(rows, 1).map((r) => r.code)).toEqual(["b", "d", "c"]);
    expect(pickRows(rows, 5).map((r) => r.code)).toEqual(["b", "d", "c", "a"]);
  });
});

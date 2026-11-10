import { describe, expect, it } from "vitest";
import type { Watchlist, WatchlistEntry } from "../../api/client";
import sample from "./watchlist.fixture.json";
import {
  badgeCount, buyText, epsYearOf, gapPct, gapText, linear, nearestEntry, niceTicks, pctOf, placeLabels, px, statusLabel, targetText, textWidth, times, ymd,
} from "./watchlist-format";

const doc = sample as unknown as Watchlist;
const [fuling, yanjin] = doc.entries;
const withStatus = (status: WatchlistEntry["status"], gap = -0.2) => ({ ...fuling, status, gap_to_buy: gap });

describe("watchlist formatting (2026-11-06 sample)", () => {
  it("TC-WL-001 status labels", () => {
    expect([statusLabel("in"), statusLabel("near"), statusLabel("far")]).toEqual(["区间内", "接近", "较远"]);
  });
  it("TC-WL-002 numbers on the 涪陵榨菜 and 盐津铺子 cards", () => {
    expect([px(fuling.price), gapText(fuling.gap_to_buy), times(fuling.pe_at_buy), pctOf(fuling.yield_at_buy)]).toEqual(["11.84", "还需下跌 15.5%", "15.5 倍", "4.2%"]);
    expect([px(yanjin.price), gapPct(yanjin.gap_to_buy), times(yanjin.pe_at_buy), pctOf(yanjin.yield_at_buy)]).toEqual(["41.26", "39.4%", "9.1 倍", "5.6%"]);
    expect([buyText(fuling), buyText(yanjin), targetText(yanjin)]).toEqual(["9.00–10.00", "25.00", "44.16–57.50"]);
  });
  it("TC-WL-003 inside the zone and nulls", () => {
    expect([gapText(0), gapPct(0)]).toEqual(["已到买入区间", "0%"]);
    expect([px(null), pctOf(null), times(undefined), ymd(""), ymd("20261106")]).toEqual(["—", "—", "—", "—", "2026-11-06"]);
    expect(targetText({ target_low: null, target_high: null })).toBe("—");
    expect(targetText({ target_low: null, target_high: 12 })).toBe("12.00");
  });
  it("TC-WL-004 nearest entry is the largest gap; empty list gives null", () => {
    expect(nearestEntry(doc.entries)?.name).toBe("涪陵榨菜");
    expect(nearestEntry([])).toBeNull();
    expect(nearestEntry([withStatus("far", -0.3), withStatus("in", 0)])?.gap_to_buy).toBe(0);
  });
  it("TC-WL-005 badge counts near and in only", () => {
    expect(badgeCount(doc.entries)).toBe(0);
    expect(badgeCount([withStatus("in"), withStatus("near"), withStatus("far")])).toBe(2);
    expect(badgeCount(null)).toBe(0);
  });
  it("TC-WL-006 forecast year header", () => {
    expect(epsYearOf(doc.entries)).toBe("2026");
    expect(epsYearOf([{ eps_year: null }])).toBe("");
  });
});

describe("watchlist chart helpers", () => {
  it("TC-WL-007 labels stay inside the box and never overlap", () => {
    const out = placeLabels([
      { x: 100, text: "现价 11.84", anchor: "middle" },
      { x: 104, text: "买 9.00–10.00", anchor: "start" },
      { x: 300, text: "52周高 13.70", anchor: "end" },
      { x: -50, text: "52周低 10.80", anchor: "start" },
    ], 300);
    expect(out.map((l) => l.text)).toEqual(["现价 11.84", "52周高 13.70"]);
    expect(out[1].x).toBe(300);
    const w = textWidth("52周低 10.80");
    expect(placeLabels([{ x: -50, text: "52周低 10.80", anchor: "start" }], 300)[0].x).toBe(0);
    expect(placeLabels([{ x: 299, text: "52周低 10.80", anchor: "start" }], 300)[0].x).toBeCloseTo(300 - w);
  });
  it("TC-WL-008 scales and ticks", () => {
    expect(linear(0, 10, 0, 100)(5)).toBe(50);
    expect(linear(3, 3, 0, 100)(3)).toBe(50);
    expect(niceTicks(9.1, 14.2, 4)).toEqual([10, 12, 14]);
    expect(niceTicks(5, 5)).toEqual([5]);
  });
});

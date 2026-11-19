import { describe, expect, it } from "vitest";
import { NAV, readRoute, routeHash, type Page } from "./app-route";

describe("app routes", () => {
  it("TC-AR-001 every simple page maps to its hash and back", () => {
    for (const p of ["macro", "futures", "volatility", "sector-monitor", "etf", "factors", "holdings", "watchlist", "opportunities"] as Page[]) expect(readRoute(routeHash(p)).page).toBe(p);
    expect(readRoute(routeHash("dupont", ["002714.SZ", "000001.SZ"]))).toEqual({ page: "dupont", codes: ["002714.SZ", "000001.SZ"] });
  });
  it("TC-AR-002 selections, empty and unknown hashes show the chain page", () => {
    for (const h of ["", "#co=002714.SZ", "#node=MAT_X", "#sector=801010", "#nope"]) expect(readRoute(h).page).toBe("chain");
  });
  it("TC-AR-003 every nav page appears once", () => {
    const pages = NAV.flatMap((g) => g.items.map((i) => i.page));
    expect(new Set(pages).size).toBe(pages.length);
  });
});

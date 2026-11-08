import { describe, expect, it } from "vitest";
import type { Bootstrap, Company } from "../api/client";
import { buildCompanyElements, buildNetworkElements, buildNodeElements, buildSectorElements } from "./elements";
import { buildIndex } from "./taxonomy";

const boot = {
  nodes: [
    { id: "SEG_B", t: "segment", n: "电池", al: [], sec: "630000" },
    { id: "MAT_LI", t: "material", n: "碳酸锂", al: [] },
    { id: "PROD_A", t: "product", n: "动力电池", al: [], s: "SEG_B", sec: "630000" },
    { id: "MKT_EV", t: "end_market", n: "新能源汽车", al: [] },
  ],
  edges: [["PROD_A", "uses_material", "MAT_LI"], ["PROD_A", "used_in", "MKT_EV"]],
  sectors: { "630000": "电力设备" }, quick: [], n_companies: 1, kpis: {}, archetypes: {}, clock_l3: {}, clock_prod: {}, broker_prod: {}, broker_ind: {},
} as unknown as Bootstrap;
const tx = buildIndex(boot);
const opts = { depth: 2, dir: "both" as const, showCp: true };
const company = {
  code: "300750.SZ", name: "宁德时代", l1: "630000", l3: "锂电池", sw: [], links: [],
  revenue: [{ item: "动力电池系统", pct: 70, gm: 23, pids: ["PROD_A"], how: "contains" }],
  customers: { total_pct: 30, total: 1, consistent: true, rows: [{ rank: 1, name: "比亚迪股份有限公司", amount: 1, pct: 9.5, anon: false, code: "002594.SZ" }, { rank: 2, name: "客户二", amount: 1, pct: 5, anon: true }] },
  suppliers: { total_pct: null, total: null, consistent: false, rows: [] },
  named: [{ name: "Tesla", detail: "定点", page: 12, code: null }],
  apps: { 动力电池系统: [{ node_id: "MKT_EV", name: "新能源汽车", weight: "主要", evidence: { quote: "q", page: 3 } }] },
} as unknown as Company;
const ids = (els: { data: Record<string, any> }[]) => new Set(els.map((e) => e.data.id));

describe("element builders", () => {
  // TC-EL-001: company lanes: own product in lane 2, material upstream, market in lane 4, counterparties linked
  it("TC-EL-001 company swim lanes", () => {
    const els = buildCompanyElements(tx, company, { "002594.SZ": { code: "002594.SZ", name: "比亚迪", n_links: 1, first_pid: null } }, opts);
    const by = Object.fromEntries(els.filter((e) => !e.data.source).map((e) => [e.data.id, e.data]));
    expect(by["PROD_A"].col).toBe(2);
    expect(by["MAT_LI"].col).toBe(1);
    expect(by["MKT_EV"].col).toBe(4);
    expect(by["CO:002594.SZ"].type).toBe("company");
    expect(by["CU:2"].type).toBe("counterparty");
    expect(by["EXT:Tesla"].type).toBe("foreign");
    expect(els.some((e) => e.data.kind === "app" && e.data.target === "MKT_EV")).toBe(true);
  });
  // TC-EL-002: every edge joins existing nodes; ids unique
  it("TC-EL-002 edges are valid and ids unique", () => {
    const els = buildCompanyElements(tx, company, {}, opts);
    const nodeIds = ids(els.filter((e) => !e.data.source));
    els.filter((e) => e.data.source).forEach((e) => { expect(nodeIds.has(e.data.source)).toBe(true); expect(nodeIds.has(e.data.target)).toBe(true); });
    expect(ids(els).size).toBe(els.length);
  });
  // TC-EL-003: node and segment views include makers and products
  it("TC-EL-003 node and segment", () => {
    const node = buildNodeElements(tx, "PROD_A", [{ code: "300750.SZ", name: "宁德时代", pct: 70 }], opts);
    expect(ids(node).has("CO:300750.SZ")).toBe(true);
    expect(ids(buildNodeElements(tx, "SEG_B", [], opts)).has("PROD_A")).toBe(true);
  });
  // TC-EL-004: sector segments and company network
  it("TC-EL-004 sector and network", () => {
    expect(ids(buildSectorElements(tx, "630000", boot.sectors, opts)).has("SEG_B")).toBe(true);
    const net = buildNetworkElements({ nodes: [{ code: "A", name: "a", in_sector: true }, { code: "B", name: "b", in_sector: false }], edges: [{ from: "A", to: "B", kind: "sells", label: "9%" }, { from: "A", to: "X", kind: "sells", label: "" }] });
    expect(net.filter((e) => e.data.source).length).toBe(1);
  });
});

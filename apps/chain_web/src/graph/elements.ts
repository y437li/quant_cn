import type { Company, CompanyBrief, Network } from "../api/client";
import { pct, REL_ZH } from "../lib/format";
import { type Taxonomy, typeOf, walk } from "./taxonomy";

/**
 * Purpose: turn API data into Cytoscape elements for each view (company swim lanes, node neighbourhood,
 * segment, sector segments, sector company network). Layout only; no business numbers are computed.
 * Contract: every builder returns unique-id elements; edges only between existing nodes.
 * Test cases: TC-EL-001..004 in elements.test.ts.
 */
export interface El { data: Record<string, any> }
export interface Opts { depth: number; dir: "up" | "down" | "both"; showCp: boolean }

class Builder {
  els: El[] = [];
  ids = new Set<string>();
  add(el: El) { if (!this.ids.has(el.data.id)) { this.ids.add(el.data.id); this.els.push(el); } }
  edge(s: string, t: string, kind: string, label = "") {
    if (this.ids.has(s) && this.ids.has(t) && s !== t) this.add({ data: { id: `${s}>${t}>${kind}`, source: s, target: t, kind, label } });
  }
}
const chainNode = (tx: Taxonomy, id: string, focus = false): El => ({ data: { id, label: tx.N[id].n, type: typeOf(tx.N[id]), imp: tx.N[id].imp || "", focus: focus ? 1 : 0 } });

export function buildCompanyElements(tx: Taxonomy, c: Company, related: Record<string, CompanyBrief>, o: Opts): El[] {
  const b = new Builder(), cid = "CO:" + c.code;
  const put = (el: El, col: number, rank = 0) => { el.data.col = col; el.data.rank = rank; b.add(el); };
  const own: string[] = [];
  [...c.revenue].sort((x, y) => y.pct - x.pct).forEach((r) => r.pids.forEach((p, i) => {
    if (tx.N[p] && !own.includes(p)) { own.push(p); put(chainNode(tx, p, true), 2, r.pct - i); }
  }));
  put({ data: { id: cid, label: c.name, type: "company", focus: 1 } }, 2, 1e9);
  c.revenue.forEach((r) => r.pids.forEach((p, i) => b.edge(cid, p, "produces", i === 0 ? pct(r.pct) : "")));
  for (const side of ["up", "down"] as const) {
    if (o.dir === (side === "up" ? "down" : "up")) continue;
    const w = walk(tx, own, side === "up" ? Math.max(1, o.depth - 1) : o.depth, side, 6);
    w.nodes.forEach((d, id) => { if (d !== 0 && !own.includes(id)) put(chainNode(tx, id), side === "up" ? 1 : tx.N[id].t === "end_market" ? 4 : 3, -Math.abs(d)); });
    w.edges.forEach(([s, t]) => b.edge(s, t, "prior"));
  }
  if (o.showCp) addCounterparties(b, put, tx, c, related, cid);
  addApplications(b, put, tx, c, cid);
  const titles = ["", "上游：原料 / 部件 + 供应商", "本公司及其产品", "下游：产品 + 客户", "终端市场"];
  titles.forEach((t, i) => { if (t && b.els.some((e) => e.data.col === i && !e.data.source)) b.add({ data: { id: "LANE:" + i, label: t, type: "lane", col: i, rank: 2e9 } }); });
  return b.els;
}

function addCounterparties(b: Builder, put: (el: El, col: number, rank?: number) => void, tx: Taxonomy, c: Company, related: Record<string, CompanyBrief>, cid: string) {
  const place = (r: { rank: number; name: string; pct: number; anon: boolean; code?: string | null; group?: boolean }, side: "u" | "d") => {
    const other = r.code && r.code !== c.code ? related[r.code] : undefined;
    const word = side === "u" ? "供应商" : "客户";
    const id = other ? "CO:" + other.code : `${side === "u" ? "SU" : "CU"}:${r.rank}`;
    const label = other ? `${other.name}\n${word}${r.rank} · ${pct(r.pct)}${r.group ? " · 子公司" : ""}` : `${r.anon ? word + r.rank : r.name}\n${pct(r.pct)}`;
    put({ data: { id, label, type: other ? "company" : "counterparty", focus: 0 } }, side === "u" ? 1 : 3, (other ? 500 : -500) + r.pct);
    if (side === "u") b.edge(id, cid, "buys"); else b.edge(cid, id, "sells");
    if (other?.first_pid && tx.N[other.first_pid]) {
      if (!b.ids.has(other.first_pid)) put(chainNode(tx, other.first_pid), side === "u" ? 1 : 3, 499 + r.pct);
      b.edge(id, other.first_pid, "produces");
    }
  };
  (c.suppliers?.rows || []).forEach((r) => place(r, "u"));
  (c.customers?.rows || []).forEach((r) => place(r, "d"));
  (c.named || []).slice(0, 12).forEach((r) => {
    const listed = r.code && r.code !== c.code ? related[r.code] : undefined;
    const id = listed ? "CO:" + listed.code : "EXT:" + r.name;
    put({ data: { id, label: `${listed ? listed.name : r.name}\n点名客户${r.detail ? " · " + r.detail.slice(0, 6) : ""}`, type: listed ? "company" : "foreign" } }, 3, 400);
    b.edge(cid, id, "named");
  });
}

function addApplications(b: Builder, put: (el: El, col: number, rank?: number) => void, tx: Taxonomy, c: Company, cid: string) {
  c.revenue.forEach((rv) => ((c.apps && c.apps[rv.item]) || []).filter((a) => a.node_id && tx.N[a.node_id]).slice(0, 4).forEach((a) => {
    const id = a.node_id as string;
    put(chainNode(tx, id), tx.N[id].t === "end_market" ? 4 : 3, a.weight === "主要" ? 50 : 10);
    b.edge(rv.pids[0] && b.ids.has(rv.pids[0]) ? rv.pids[0] : cid, id, "app", a.weight);
  }));
}

export function buildNodeElements(tx: Taxonomy, id: string, makers: { code: string; name: string; pct: number }[], o: Opts): El[] {
  const b = new Builder();
  if (tx.N[id].t === "segment") {
    const ps = (tx.SEGP[id] || []).slice(0, 60);
    ps.forEach((p) => b.add(chainNode(tx, p, true)));
    const w = walk(tx, ps, 1, o.dir, 6);
    w.nodes.forEach((_, n) => b.add(chainNode(tx, n, ps.includes(n))));
    w.edges.forEach(([s, t]) => b.edge(s, t, "prior"));
  } else {
    const w = walk(tx, [id], o.depth, o.dir, 12);
    w.nodes.forEach((_, n) => b.add(chainNode(tx, n, n === id)));
    w.edges.forEach(([s, t, r]) => b.edge(s, t, "prior", REL_ZH[r] || ""));
  }
  makers.slice(0, 40).forEach((m) => {
    const target = b.ids.has(id) ? id : null;
    b.add({ data: { id: "CO:" + m.code, label: m.name, type: "company", focus: 0 } });
    if (target) b.edge("CO:" + m.code, target, "produces", pct(m.pct));
  });
  return b.els;
}

export function buildSectorElements(tx: Taxonomy, l1: string, sectors: Record<string, string>, o: Opts): El[] {
  const b = new Builder();
  const segs = Object.values(tx.N).filter((n) => n.t === "segment" && n.sec === l1).map((n) => n.id);
  const group = (id: string): El => ({ data: { id, label: tx.N[id].t === "segment" && tx.N[id].sec && sectors[tx.N[id].sec as string] ? `${tx.N[id].n}\n${sectors[tx.N[id].sec as string]}` : tx.N[id].n, type: typeOf(tx.N[id]), focus: 0 } });
  segs.forEach((id) => b.add({ data: { id, label: `${tx.N[id].n}\n${(tx.SEGP[id] || []).length} 项`, type: "segment", focus: 1 } }));
  const top = (m: Record<string, Record<string, number>>, id: string) => Object.entries(m[id] || {}).sort((x, y) => y[1] - x[1]).slice(0, o.depth + 2);
  segs.forEach((id) => {
    if (o.dir !== "down") top(tx.GIN, id).forEach(([g, k]) => { b.add(group(g)); b.edge(g, id, "prior", String(k)); });
    if (o.dir !== "up") top(tx.GOUT, id).forEach(([g, k]) => { b.add(group(g)); b.edge(id, g, "prior", String(k)); });
  });
  return b.els;
}

export function buildNetworkElements(net: Network): El[] {
  const b = new Builder();
  net.nodes.forEach((n) => b.add({ data: { id: "CO:" + n.code, label: n.name, type: n.in_sector ? "company" : "counterparty", focus: 0 } }));
  net.edges.forEach((e) => b.edge("CO:" + e.from, "CO:" + e.to, e.kind, e.label));
  return b.els;
}

import type { Bootstrap, TaxNode } from "../api/client";

/**
 * Purpose: index the taxonomy once for walking the chain (upstream → downstream) and grouping by segment.
 * Contract: buildIndex(boot) → Taxonomy; walk(seeds, depth, dir, cap) → nodes with signed hop distance (−up / +down) and edges.
 */
export interface Flow { other: string; rel: string }
export interface Taxonomy {
  N: Record<string, TaxNode>; OUT: Record<string, Flow[]>; IN: Record<string, Flow[]>; SEGP: Record<string, string[]>;
  GOUT: Record<string, Record<string, number>>; GIN: Record<string, Record<string, number>>;
}
export const typeOf = (n: TaxNode) => (n.t === "product" && n.k === "service" ? "service" : n.t);

export function buildIndex(boot: Bootstrap): Taxonomy {
  const t: Taxonomy = { N: {}, OUT: {}, IN: {}, SEGP: {}, GOUT: {}, GIN: {} };
  boot.nodes.forEach((n) => (t.N[n.id] = n));
  const add = (from: string, to: string, rel: string) => {
    (t.OUT[from] ||= []).push({ other: to, rel });
    (t.IN[to] ||= []).push({ other: from, rel });
  };
  for (const [s, r, o] of boot.edges) {
    if (r === "uses_material") add(o, s, r);
    else if (r !== "part_of" && r !== "substitute_for") add(s, o, r);
  }
  boot.nodes.forEach((n) => { if (n.t === "product" && n.s) (t.SEGP[n.s] ||= []).push(n.id); });
  const group = (id: string) => { const n = t.N[id]; return !n ? null : n.t === "product" ? n.s || id : id; };
  const bump = (m: Record<string, Record<string, number>>, a: string, b: string) => { (m[a] ||= {})[b] = (m[a][b] || 0) + 1; };
  for (const from in t.OUT) for (const e of t.OUT[from]) {
    const a = group(from), b = group(e.other);
    if (a && b && a !== b) { bump(t.GOUT, a, b); bump(t.GIN, b, a); }
  }
  return t;
}

export function walk(t: Taxonomy, seeds: string[], depth: number, dir: "up" | "down" | "both", cap = 14) {
  const seen = new Map<string, number>(seeds.map((s) => [s, 0]));
  const edges: [string, string, string][] = [];
  let up = [...seeds], down = [...seeds];
  for (let d = 1; d <= depth; d++) {
    if (dir !== "down") {
      const next: string[] = [];
      for (const id of up) for (const e of (t.IN[id] || []).slice(0, cap)) {
        edges.push([e.other, id, e.rel]);
        if (!seen.has(e.other)) { seen.set(e.other, -d); next.push(e.other); }
      }
      up = next;
    }
    if (dir !== "up") {
      const next: string[] = [];
      for (const id of down) for (const e of (t.OUT[id] || []).slice(0, cap)) {
        edges.push([id, e.other, e.rel]);
        if (!seen.has(e.other)) { seen.set(e.other, d); next.push(e.other); }
      }
      down = next;
    }
  }
  return { nodes: seen, edges };
}

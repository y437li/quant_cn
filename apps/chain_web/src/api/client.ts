/**
 * Typed client for apps/chain_api/openapi.yaml (plan 15, D-116).
 * Purpose: the only place the front end talks to the server.
 * Contract: every function resolves to the documented JSON or rejects with an Error carrying the server message.
 */
export interface TaxNode { id: string; t: string; n: string; en?: string | null; p?: string | null; s?: string | null; k?: string | null; imp?: string | null; al: string[]; sec?: string | null }
export interface RevenueLine { item: string; pct: number; gm: number | null; pids: string[]; how: string; sales?: number }
export interface Evidence { quote: string; page: number }
export interface CompanyBrief { code: string; name: string; l1?: string; l3?: string | null; n_links: number; first_pid: string | null }
export interface CpRow { rank: number; name: string; amount: number; pct: number; anon: boolean; code?: string | null; group?: boolean }
export interface CpTable { total_pct: number | null; total: number | null; consistent: boolean; rows: CpRow[] }
export interface ViewPoint { point: string; sources: string[]; metric?: string; unit?: string }
export interface BrokerView { summary: string; method_consensus: string; multiple_range: Record<string, unknown> | null; points: Record<string, ViewPoint[]>; refs: Record<string, string>; n_reports: number; n_sent: number }
export interface BrokerStat { n: number; methods: [string, number][]; pe_by_year?: Record<string, [number, number]>; pe_target: number | null; pe_target_n: number; pb?: number | null; pb_n?: number; loss_share?: number; bare_share?: number; metrics: [string, number][] }
export interface Clock { n: number; demand: number; margin_pp: number; capex: number | null; phase: string }
export interface Party { name: string; role: string; detail: string; evidence: Evidence; src?: string; code?: string | null }
export interface Company {
  code: string; name: string; l1: string; l3: string | null; sw: string[]; revenue: RevenueLine[]; links: [string, string, number | null][];
  source?: string; pages?: number; sections?: Record<string, [number, number]>; md_share?: number;
  customers?: CpTable; suppliers?: CpTable; named?: { name: string; detail: string; page: number; code?: string | null; src?: string }[];
  llm?: { counterparties: Party[]; types: Record<string, string[]> } | null; apps?: Record<string, { node_id: string | null; name: string; weight: string; evidence: Evidence; weak?: boolean }[]>;
  valuations?: { org: string; date: string; title: string; valuation: Record<string, any> }[]; quarterly?: { kind: string; summary: string; value?: string | null; unit?: string | null; counterparty?: string | null; evidence: Evidence; period: string }[];
  regions?: { item: string; pct: number }[]; eliminations?: { item: string; sales: number; pct: number }[]; internal?: string[];
  business?: Record<string, any>; broker_view?: BrokerView | null; peers?: { code: string; score: number; shared: string[] }[];
}
export interface Bootstrap {
  nodes: TaxNode[]; edges: [string, string, string][]; sectors: Record<string, string>; quick: CompanyBrief[]; n_companies: number;
  kpis: Record<string, { kpis: Kpi[]; groups: { name: string; sw: string[]; kpis: Kpi[] }[] }>; archetypes: Record<string, any>;
  clock_l3: Record<string, Clock>; clock_prod: Record<string, Clock>; broker_prod: Record<string, BrokerStat>; broker_ind: Record<string, BrokerStat>;
}
export interface Kpi { id: string; name: string; unit?: string; freq?: string; definition?: string }
export interface SearchHit { kind: "company" | "node"; id: string; label: string; sub: string }
export interface Maker { code: string; name: string; item: string; pct: number; how: string }
export interface Network { nodes: { code: string; name: string; in_sector: boolean }[]; edges: { from: string; to: string; kind: string; label: string }[] }

async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) {
    let msg = `HTTP ${r.status}`;
    try { msg = (await r.json()).error || msg; } catch { /* body is not JSON */ }
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

const enc = encodeURIComponent;
export const api = {
  getBootstrap: () => getJSON<Bootstrap>("/api/bootstrap"),
  findHits: (q: string) => getJSON<SearchHit[]>(`/api/search?q=${enc(q)}&limit=30`),
  getCompany: (code: string) => getJSON<{ company: Company; related: Record<string, CompanyBrief> }>(`/api/companies/${enc(code)}`),
  listMakers: (id: string) => getJSON<Maker[]>(`/api/nodes/${enc(id)}/makers`),
  listSectorCompanies: (l1: string) => getJSON<CompanyBrief[]>(`/api/sectors/${enc(l1)}/companies`),
  getSectorNetwork: (l1: string, outside: boolean) => getJSON<Network>(`/api/sectors/${enc(l1)}/network?outside=${outside}`),
  getView: (scope: "product" | "industry", id: string) => getJSON<BrokerView>(`/api/views/${scope}/${enc(id)}`).catch(() => null),
};

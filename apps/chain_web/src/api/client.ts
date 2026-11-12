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
/** Watchlist (观察账本, plan 15 phase 7): every number is computed in Python; fractions for gap, yields. */
export type WatchStatus = "in" | "near" | "far";
export interface WeeklyClose { date: string; close: number }
export interface WatchlistEntry {
  code: string; name: string; buy_low: number; buy_high: number; added: string; thesis: string; watch: string;
  price: number; price_date: string; pe_ttm: number | null; pb: number | null; div_yield: number | null; dps_ttm: number | null;
  eps_year: string | null; eps_fy: number | null; eps_brokers: number | null; target_low: number | null; target_high: number | null;
  low_52w: number | null; high_52w: number | null; gap_to_buy: number; pe_at_buy: number | null; yield_at_buy: number | null;
  status: WatchStatus; weekly: WeeklyClose[];
}
export interface Watchlist { as_of: string; near_pct: number; entries: WatchlistEntry[]; missing: string[] }
/** National-team ETF proxy (国家队 ETF, plan 15 phase 7b, D-126): 亿元, computed in Python. */
export interface ProxyMark { date: string; position: number | null }
export interface ProxyTotals { aum: number | null; position: number | null; flow_recent: number | null; flow_ytd: number | null; peak: ProxyMark; trough_since_peak: ProxyMark }
export interface ProxyWeek { date: string; core_flow?: number | null; other_flow?: number | null; core_position?: number | null; other_position?: number | null }
export interface ProxyIndex {
  name: string; reference: string; n_etf: number; aum: number | null; position: number | null; core_position: number | null;
  flow_recent: number | null; flow_ytd: number | null; weekly: { date: string; position: number | null; flow: number | null }[];
}
export interface EtfProxy {
  as_of: string; price_as_of: string; start: string; n_members: number; totals: { core?: ProxyTotals; other?: ProxyTotals };
  recent: { date: string; core?: number | null; other?: number | null }[]; weekly: ProxyWeek[];
  yearly: { year: string; core?: number | null; other?: number | null }[]; indices: ProxyIndex[];
}
/** Factor monitor (因子监控, plan 15 phase 7c, D-132): fractions, computed in Python. */
export interface FactorReturns { d1: number | null; w1: number | null; m1: number | null; m3: number | null; ytd: number | null; y1: number | null }
export interface MonitoredFactor {
  factor: string; label: string; kind: "country" | "style" | "industry"; ret: FactorReturns;
  forecast_vol: number | null; realized_vol_21: number | null; realized_vol_63: number | null; vol_ratio: number | null; sigma_move: number | null;
  cum: (number | null)[]; forecast: (number | null)[]; realized: (number | null)[];
}
export interface FactorMonitor { as_of: string; model: string; n_sessions: number; dates: string[]; factors: MonitoredFactor[] }
/** Holdings risk (持仓, plan 15 phase 7d, D-132): CNY values, fractions for weights / vols / shares of risk. */
export interface HoldingPosition {
  code: string; name: string; shares: number | null; cost: number | null; close: number | null; value: number | null; weight: number | null;
  pnl: number | null; pnl_pct: number | null; vol: number | null; contrib: number | null;
}
export interface HoldingFactor { factor: string; label: string; kind: "country" | "style" | "industry"; exposure: number | null; active: number | null; contrib: number | null }
export interface HoldingsRisk {
  as_of: string; model: string; benchmark: string; cash: number; value: number; stock_value: number; pnl: number;
  risk: Record<string, number | null>; positions: HoldingPosition[]; factors: HoldingFactor[];
  correlation: { codes: string[]; matrix: number[][] };
  stock_exposures: { styles: string[]; rows: { code: string; industry: string; values: (number | null)[] }[] }; missing: string[];
}

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
  getWatchlist: () => getJSON<Watchlist>("/api/watchlist"),
  getEtfProxy: () => getJSON<EtfProxy>("/api/etf-proxy"),
  getFactorMonitor: () => getJSON<FactorMonitor>("/api/factor-monitor"),
  getHoldingsRisk: () => getJSON<HoldingsRisk>("/api/holdings-risk"),
  getView: (scope: "product" | "industry", id: string) => getJSON<BrokerView>(`/api/views/${scope}/${enc(id)}`).catch(() => null),
};

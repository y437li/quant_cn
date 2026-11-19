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
/** Structured condition evaluated in Python (plan 15 ph7f): actual null = unknown, never treated as met. */
export type ConditionState = "met" | "unmet" | "unknown";
export interface ConditionResult { label: string; kind: string; metric: string; op: string; value: number; actual: number | null; state: ConditionState; required?: boolean }
export type ConditionStatus = "buy" | "near" | "wait";
/** Watchlist (观察账本, plan 15 phase 7): every number is computed in Python; fractions for gap, yields. */
export type WatchStatus = "in" | "near" | "far";
export interface WeeklyClose { date: string; close: number }
export interface WatchlistEntry {
  /** "etf" rows (ph7p) are priced from fund_daily and carry no valuation fields. */
  kind?: "stock" | "etf";
  code: string; name: string; buy_low: number; buy_high: number; added: string; thesis: string; watch: string;
  price: number; price_date: string; pe_ttm: number | null; pb: number | null; div_yield: number | null; dps_ttm: number | null;
  eps_year: string | null; eps_fy: number | null; eps_brokers: number | null; target_low: number | null; target_high: number | null;
  low_52w: number | null; high_52w: number | null; gap_to_buy: number; pe_at_buy: number | null; yield_at_buy: number | null;
  shareholder_yield?: number | null; buyback_plan_pct?: number | null;
  /** latest 散户温度计 reading (plan 21 ph5): retail_gauge, gauge_exp_change, gauge_avoid / gauge_avoid_strong / gauge_leaving (1 / 0), gauge_lo_streak / gauge_hi_streak */
  retail?: Record<string, number | null>;
  status: WatchStatus; weekly: WeeklyClose[];
  conditions: ConditionResult[]; conditions_needed: number | null; condition_status: ConditionStatus;
}
export interface Watchlist { as_of: string; near_pct: number; entries: WatchlistEntry[]; missing: string[] }
/** National-team ETF proxy (国家队 ETF, plan 15 phase 7b, D-126): 亿元, computed in Python. */
export interface ProxyMark { date: string; position: number | null }
/** 近3月 window (ph7o): today's position ranked among the last `days` daily positions, pct 0–100, low / high in 亿元. */
export interface ProxyWindow { pct: number | null; low: number | null; high: number | null; days: number }
export interface ProxyTotals {
  aum: number | null; position: number | null; flow_recent: number | null; flow_ytd: number | null; peak: ProxyMark; trough_since_peak: ProxyMark;
  flow_weeks?: number | null; window?: ProxyWindow;
}
export interface ProxyWeek { date: string; core_flow?: number | null; other_flow?: number | null; core_position?: number | null; other_position?: number | null }
export interface ProxyIndex {
  name: string; reference: string; n_etf: number; aum: number | null; position: number | null; core_position: number | null;
  flow_recent: number | null; flow_ytd: number | null; weekly: { date: string; position: number | null; flow: number | null }[];
  /** rhythm: peak and the trough after it, added since the trough, last weeks / this week / last day flows, reference drawdown % */
  peak?: ProxyMark; trough_since_peak?: ProxyMark; since_trough?: number | null; flow_weeks?: number | null; flow_week?: number | null;
  flow_day?: number | null; drawdown?: number | null; window?: ProxyWindow;
}
export interface EtfProxy {
  as_of: string; price_as_of: string; start: string; n_members: number;
  /** settings echoed by Python (ph7o): weeks in 近N周, sessions in 近3月, weeks in the flow matrix; absent in older files */
  rhythm_weeks?: number; pct_window_days?: number; matrix_weeks?: number; totals: { core?: ProxyTotals; other?: ProxyTotals };
  recent: { date: string; core?: number | null; other?: number | null }[]; weekly: ProxyWeek[];
  yearly: { year: string; core?: number | null; other?: number | null }[]; indices: ProxyIndex[]; styles: ProxyStyle[];
}
/** Style ETF crowding (银行 / 红利, plan 15 ph7g): money in 亿元, flow_pct a fraction of AUM. */
export interface ProxyStyle {
  key: string; name: string; metric: string; as_of: string; n_etf: number; aum: number | null; flow_1d: number | null;
  flow_window: number | null; flow_pct: number | null; z: number | null; status: "hot" | "cooled" | "normal"; hot_since: string;
  history: { d: string; z: number | null; flow_pct: number | null }[];
}
/** 融资融券 of one stock (plan 15 ph7m): money in 亿 (rz, buy, repay), short balance in 万元, short sales in shares. */
export interface MarginDay { d: string; close: number | null; rz: number | null; buy: number | null; repay: number | null; rq: number | null; rq_sell: number | null }
export interface MarginLadderStep { fall_pct: number; price: number; debt_yi: number | null; share: number }
export interface MarginPanel {
  code: string; as_of: string; float_mv_yi: number | null; rz_yi: number | null; rz_pct_float: number | null; rz_chg_20d: number | null;
  rz_net_20d_yi: number | null; rq_wan: number | null; rq_pct_float: number | null; rq_max_wan: number | null; rq_sell_20d_wan: number | null;
  ladder: { debt_yi: number | null; first_liq: number | null; first_liq_low_margin: number | null; forced: MarginLadderStep[] }; daily: MarginDay[];
}
/** Futures monitor (期货监测, plan 15 ph7i, D-145): changes and curve spreads as fractions, prices as quoted. */
export interface FuturesPoint { d: string; v: number }
export interface FuturesFamily {
  family: string; name: string; group: string; as_of: string; contract: string; price: number | null;
  pct_1y: number | null; pct_5y: number | null; chg_1w: number | null; chg_3m: number | null;
  front_vs_4th: number | null; front_vs_4th_pct: number | null; front_vs_12m: number | null; front_vs_12m_pct: number | null;
  shape: string; oi: number | null; oi_chg_5d: number | null; oi_z: number | null;
  curve: { month: string; price: number; oi: number }[]; price_history: FuturesPoint[]; curve_history: FuturesPoint[];
  broker: FuturesBroker | null; chg_1y: number | null;
}
export interface FuturesBroker { as_of: string; net: number | null; gross: number | null; net_share: number | null; net_share_chg_5d: number | null; net_share_pct_5y: number | null }
export interface IndexFuture {
  product: string; name: string; index: string; as_of: string; main_contract: string; price: number | null; spot: number | null;
  basis_pct: number | null; basis_annualised: number | null; basis_pct_5y: number | null; net: number | null; net_chg_5d: number | null;
  net_pct_5y: number | null; oi: number | null; oi_chg_5d: number | null; regime: string; history: { d: string; basis: number | null; net: number | null }[];
}
export interface FuturesSpread { key: string; name: string; unit: string; kind: string; as_of: string; value: number | null; chg_1w: number | null; pct_5y: number | null; history: FuturesPoint[] }
export interface FuturesFlag { key: string; kind: string; name: string; message: string }
export interface FuturesMonitor { as_of: string; families: FuturesFamily[]; spreads: FuturesSpread[]; index_futures: IndexFuture[]; flags: FuturesFlag[]; new_flags: string[]; missing: string[] }

/** Macro monitor (宏观监测, plan 15 ph7h, D-143): values as printed (%, pp, index or 亿元), computed in Python. */
export interface MacroPoint { month: string; value: number }
export interface MacroSeries {
  key: string; name: string; group: string; unit: string; month: string; value: number | null;
  prev_month: string; prev: number | null; change: number | null; pct_5y: number | null; new_print: boolean; history: MacroPoint[];
}
export interface MacroMonitor { as_of: string; missing: string[]; new_prints: string[]; series: MacroSeries[] }

/** Volatility monitor (波动率监测, plan 03 ph6, D-152): VIX points; pct and chg_pct are fractions, computed in Python. */
export interface VolPoint { date: string; value: number }
export interface VolAlerts { level: number | null; jump: number | null; pct: number | null }
export interface VolLine {
  key: string; name: string; group: string; kind: string; code: string; date: string; value: number; chg: number | null; chg_pct: number | null;
  pct: number | null; median: number; low: number; high: number; n_obs: number; quality_flag: string; alerts: VolAlerts; history: VolPoint[];
}
export interface VolFlag { key: string; kind: string; name: string; message: string }
/** 小盘观察 (plan 30): small-cap bottom signals with their trigger state; pct only on percentile rows. */
export type SmallCapState = "on" | "near" | "off" | "info";
export interface SmallCapRow {
  key: string; group: string; name: string; value: number | null; unit: string; trigger: number | null; state: SmallCapState; note: string; date: string;
  pct?: number | null;
}
export interface SmallCapPoint {
  date: string; small: number | null; limit_downs: number | null; low_share: number | null; gap: number | null; gap_pct: number | null;
  /** 杠杆 (plan 30 ph4): financing balance and its mean in 亿, share of float market cap as a fraction; absent in older files */
  rz?: number | null; rz_ma?: number | null; rz_circ?: number | null;
}
export interface SmallCapWatch { as_of: string; rows: SmallCapRow[]; history: SmallCapPoint[]; triggered: string[]; new_triggered: string[]; missing: string[] }
export interface VolatilityMonitor { as_of: string; window: number; lines: VolLine[]; flags: VolFlag[]; new_flags: string[]; missing: string[]; smallcap: SmallCapWatch | null }

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
  reviews: Record<string, PositionReview>;
}
/** Position note, flags, 筹码结构 row and conditions (plan 15 ph7f, PositionReviewer). */
export interface PositionNote { thesis: string; falsifier: string; stop: number | null; target: number | null; action: string; watch: string; reviewed: string }
export type FlagKind = "stop" | "target" | "weight" | "review" | "note";
export interface ReviewFlag { kind: FlagKind; message: string }
export interface PositionReview {
  note: PositionNote | null; flags: ReviewFlag[]; chips: Record<string, number | null>; period: string | null; conditions: ConditionResult[];
}

/** 行业监控 (plan 31): one chart line, a chart, a sector and the whole document of GET /api/sector-monitor. */
export interface SectorLine { label: string; points: [string, number][] }
export interface SectorExtra { key: string; label: string; unit: string }
export interface SectorChart {
  key: string; title: string; unit: string; invert?: boolean; in_table?: boolean; extra?: SectorExtra; lines: SectorLine[];
}
export interface SectorApp {
  app_id: string; name: string; company: string | null; code: string | null; rank: number | null; prev: number | null;
  free: number | null; overseas_best: number | null; overseas_market: string | null; overseas_markets: number;
}
export interface SectorTopApp { rank: number; name: string; company: string | null; code: string | null; prev: number | null }
export interface SectorNewApp extends SectorApp { release_date: string }
export interface SectorRankings {
  as_of: string | null; prev: string | null; country: string; apps: SectorApp[]; top: SectorTopApp[]; new?: SectorNewApp[];
}
export interface SectorDoc {
  key: string; name: string; as_of: string | null; index: { code: string; name: string };
  charts: SectorChart[]; table: Record<string, string | number | null>[]; rankings?: SectorRankings;
}
export interface SectorMonitor { as_of: string | null; sectors: SectorDoc[] }

/** 财报季信号 (plan 35): one Shenwan L2 sector and fiscal quarter, and the whole document of GET /api/sector-earnings. */
export type SectorEarningsStatus = "firing" | "provisional" | "none";
export interface SectorEarningsRow {
  code: string; name: string; end_date: string; status: SectorEarningsStatus; n: number; expected: number; share: number;
  n_top: number; pre: number | null; react: number | null; sig_date: string | null; back: number | null; hchg: number | null;
  rally: boolean; fwd60?: number | null; fwd120?: number | null;
}
export interface SectorEarningsRecord { n: number; fwd60?: number | null; fwd120?: number | null }
export interface SectorEarningsSignal {
  as_of: string; season: string | null; rows: SectorEarningsRow[]; history: SectorEarningsRow[]; firings: SectorEarningsRow[];
  record: { rally?: SectorEarningsRecord; all?: SectorEarningsRecord }; new_flags: string[];
  thresholds: { pre_min: number; react_max: number; rally_min: number; report_share: number; top_decile: number; min_events: number };
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
/** One 利率汇率 row (plan 34): level and changes in its unit (yield / bp: bp changes; rate: fractions; gap: fraction points). */
export type RatesFxUnit = "yield" | "bp" | "rate" | "gap";
export interface RatesFxRow {
  key: string; name: string; group: string; unit: RatesFxUnit; date: string; value: number;
  chg: { "1w": number | null; "1m": number | null; "3m": number | null; "1y": number | null };
  pct: number | null; low_1y: number | null; high_1y: number | null; stale: boolean; alerts: string[];
  history: VolPoint[];
}
export interface RatesFxFlag { key: string; kind: string; name: string; message: string }
/** rates_fx_monitor.json (plan 34, D-171). */
export interface RatesFxMonitor {
  as_of: string; groups: string[]; rows: RatesFxRow[]; flags: RatesFxFlag[]; new_flags: string[];
  missing: string[]; stale: string[];
  curve: { tenors: string[]; points: { label: string; date: string; values: (number | null)[] }[] };
}

/** One programme of the buyback monitor (plan 32): amounts in 亿元, done_pct = executed ÷ low (else high), cap_gap = close ÷ price cap − 1, mv_pct = high ÷ market cap. */
export interface BuybackRow {
  code: string; name: string | null; date: string; end: string; state: string; tags: string[]; holders: string[];
  funding: string[]; loan_bank: string | null; loan_yi: number | null; low_yi: number | null; high_yi: number | null;
  executed_yi: number | null; done_pct: number | null; price_cap: number | null; close: number | null;
  cap_gap: number | null; mv_pct: number | null; labelled: boolean; event?: string;
}
export interface BuybackTotal { count: number; low_yi: number; high_yi: number; executed_yi: number }
export interface BuybackSection {
  live: BuybackRow[]; events: BuybackRow[];
  totals: { all: BuybackTotal; by_tag: (BuybackTotal & { label: string })[]; by_funding: (BuybackTotal & { label: string })[]; loan: { count: number; loan_yi: number } };
  months: { month: string; count: number; high_yi: number; loan_count: number; loan_yi: number }[];
}
/** buyback_monitor.json (plan 32, D-169): 回购 and 增持 kept apart. */
export interface TaskRunStep { task: string; status: TaskState; duration_s: number; exit_code: number | null; as_of: string | null; note: string }
export type TaskState = "ok" | "failed" | "skipped";
export interface TaskStep { task: string; status: TaskState | null; last_ok_at: string | null; as_of: string | null; history: { run_id: string; status: TaskState; duration_s: number }[] }
/** 机会清单 (plan 21 ph4-5): one row of GET /api/opportunities; numbers null when unknown. */
export interface OpportunityRow {
  code: string; name: string | null; rank: number; status: "listed" | "near"; is_new: boolean;
  rules_hit: string[]; missing: string[];
  pct: number | null; exp_change: number | null; lo_streak: number | null; circ_mv: number | null;
  lg_weeks_pos_4w: number | null; lg_net_4w: number | null; sm_weeks_neg_4w: number | null; sm_net_4w: number | null;
  margin_chg_60d: number | null; winner_rate: number | null; cost_lo_gap: number | null; cost_hi_gap: number | null;
  period: string | null; np_yoy: number | null; np_qoq: number | null; val_value: number | null; val_median: number | null;
  fit_styles: string | null; fit_delta: number | null;
}

/** The whole opportunities.json document (OpportunityDocument). */
export interface Opportunities {
  as_of: string; previous_as_of: string | null;
  rules: { min_circ_mv: number; inflow_weeks: number; np_yoy_min: number; np_qoq_min: number; valuation_field: string; valuation_years: number; fit_weight: number; fit_styles: number; top_n: number; near_n: number };
  rows: OpportunityRow[];
  dropped: { code: string; name: string | null; status: string }[];
}

export interface TaskStatus {
  last_run: { run_id: string; trigger: string; started_at: string; finished_at: string; counts: Record<TaskState, number>; steps: TaskRunStep[] } | null;
  steps: TaskStep[];
}
export interface BuybackMonitor { as_of: string; days: number; start: string; buyback: BuybackSection; increase: BuybackSection }

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
  getMacro: () => getJSON<MacroMonitor>("/api/macro"),
  getFutures: () => getJSON<FuturesMonitor>("/api/futures"),
  getMargin: (code: string) => getJSON<MarginPanel>(`/api/margin/${enc(code)}`),
  getVolatility: () => getJSON<VolatilityMonitor>("/api/volatility"),
  getHoldingsRisk: () => getJSON<HoldingsRisk>("/api/holdings-risk"),
  getSectorMonitor: () => getJSON<SectorMonitor>("/api/sector-monitor"),
  getSectorEarnings: () => getJSON<SectorEarningsSignal>("/api/sector-earnings"),
  getRatesFx: () => getJSON<RatesFxMonitor>("/api/rates-fx"),
  getBuyback: () => getJSON<BuybackMonitor>("/api/buyback"),
  getTasks: () => getJSON<TaskStatus>("/api/tasks"),
  getOpportunities: () => getJSON<Opportunities>("/api/opportunities"),
  getView: (scope: "product" | "industry", id: string) => getJSON<BrokerView>(`/api/views/${scope}/${enc(id)}`).catch(() => null),
};

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, type Bootstrap, type Company, type CompanyBrief, type Maker, type Network, type Watchlist } from "./api/client";
import { ChainGraph, type GraphControl } from "./components/chain-graph";
import { readRoute, routeHash, type Page } from "./components/app-route";
import { Ctx, type Selection } from "./components/context";
import { SideNav } from "./components/side-nav";
import { Splitter } from "./components/splitter";
import { CompanyDossier } from "./features/company/company-dossier";
import { NodeDossier } from "./features/node/node-dossier";
import { SearchBox } from "./features/search/search-box";
import { SectorDossier } from "./features/sector/sector-dossier";
import { DupontPage } from "./features/dupont/dupont-page";
import { WatchlistPage } from "./features/watchlist/watchlist-page";
import { FactorsPage } from "./features/factors/factors-page";
import { HoldingsPage } from "./features/holdings/holdings-page";
import { MacroPage } from "./features/macro/macro-page";
import { VolatilityPage } from "./features/volatility/volatility-page";
import { SectorMonitorPage } from "./features/sector-monitor/sector-monitor-page";
import { RatesFxPage } from "./features/rates-fx/rates-fx-page";
import { BuybackPage } from "./features/buyback/buyback-page";
import { TasksPage } from "./features/tasks/tasks-page";
import { OpportunitiesPage } from "./features/opportunities/opportunities-page";
import { FuturesPage } from "./features/futures/futures-page";
import { EtfPage } from "./features/etf/etf-page";
import { badgeCount } from "./features/watchlist/watchlist-format";
import { buildCompanyElements, buildNetworkElements, buildNodeElements, buildSectorElements, type El } from "./graph/elements";
import { buildIndex } from "./graph/taxonomy";

/** Purpose: the app shell (plan 15 ph7j): left sidebar (市场 / 监测 / 我的), top bar with search, then the current page; the chain page has its own toolbar (sector, quick list), graph stage and resizable dossier. The URL hash holds the page or the chain selection. */
type Loaded =
  | { kind: "company"; c: Company; related: Record<string, CompanyBrief> }
  | { kind: "node"; id: string; makers: Maker[] }
  | { kind: "sector"; l1: string; companies: CompanyBrief[]; net: Network | null };

const parseHash = (): Selection | null => {
  const m = location.hash.match(/^#(co|node|sector)=(.+)$/);
  return m ? { kind: m[1] === "co" ? "company" : (m[1] as "node" | "sector"), id: decodeURIComponent(m[2]) } : null;
};
const toHash = (s: Selection) => `#${s.kind === "company" ? "co" : s.kind}=${encodeURIComponent(s.id)}`;

export function App() {
  const [boot, setBoot] = useState<Bootstrap | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sel, setSel] = useState<Selection>(parseHash() || { kind: "company", id: "002714.SZ" });
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [opts, setOpts] = useState({ depth: 2, dir: "both" as "up" | "down" | "both", showCp: true, net: true });
  const [wide, setWide] = useState(false);
  const ctl = useRef<GraphControl | null>(null);
  const stage = useRef<HTMLElement>(null);
  const tx = useMemo(() => (boot ? buildIndex(boot) : null), [boot]);
  const [route, setRoute] = useState(readRoute(location.hash));
  const page = route.page;
  const [wl, setWl] = useState<{ doc: Watchlist | null; error: string | null }>({ doc: null, error: null });
  useEffect(() => { const f = () => setRoute(readRoute(location.hash)); addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []);
  useEffect(() => { api.getWatchlist().then((doc) => setWl({ doc, error: null })).catch((e) => setWl({ doc: null, error: e.message })); }, [page === "watchlist"]);
  const openDupont = (codes: string[]) => { location.hash = routeHash("dupont", codes); setRoute({ page: "dupont", codes }); };
  const nBadge = badgeCount(wl.doc?.entries);

  useEffect(() => { api.getBootstrap().then(setBoot).catch((e) => setError(e.message)); }, []);
  useEffect(() => { const f = () => { const s = parseHash(); if (s) setSel(s); }; addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []);
  const select = useCallback((s: Selection) => { if (location.hash !== toHash(s)) location.hash = toHash(s); setRoute({ page: "chain", codes: [] }); setSel(s); }, []);
  const open = (p: Page) => (p === "chain" ? select(sel) : p === "dupont" ? openDupont(route.codes.length ? route.codes : sel.kind === "company" ? [sel.id] : []) : ((location.hash = routeHash(p)), setRoute({ page: p, codes: [] })));

  useEffect(() => {
    if (!tx) return;
    let live = true;
    setError(null);
    const done = (l: Loaded) => { if (live) setLoaded(l); };
    const fail = (e: Error) => { if (live) setError(e.message); };
    if (sel.kind === "company") api.getCompany(sel.id).then((r) => done({ kind: "company", c: r.company, related: r.related })).catch(fail);
    else if (sel.kind === "node") { if (!tx.N[sel.id]) { fail(new Error("未知节点 " + sel.id)); return; } api.listMakers(sel.id).then((m) => done({ kind: "node", id: sel.id, makers: m })).catch(fail); }
    else Promise.all([api.listSectorCompanies(sel.id), opts.net ? api.getSectorNetwork(sel.id, opts.showCp) : Promise.resolve(null)])
      .then(([companies, net]) => done({ kind: "sector", l1: sel.id, companies, net })).catch(fail);
    return () => { live = false; };
  }, [sel, tx, opts.net, opts.showCp]);

  const graph = useMemo<{ els: El[]; layout: "lanes" | "cose" | "dagre" }>(() => {
    if (!tx || !boot || !loaded) return { els: [], layout: "dagre" };
    if (loaded.kind === "company") return { els: buildCompanyElements(tx, loaded.c, loaded.related, opts), layout: "lanes" };
    if (loaded.kind === "node") return { els: buildNodeElements(tx, loaded.id, loaded.makers, opts), layout: "dagre" };
    if (loaded.net) return { els: buildNetworkElements(loaded.net), layout: "cose" };
    return { els: buildSectorElements(tx, loaded.l1, boot.sectors, opts), layout: "dagre" };
  }, [tx, boot, loaded, opts]);

  const onPick = useCallback((id: string) => {
    if (id.startsWith("CO:")) select({ kind: "company", id: id.slice(3) });
    else if (tx?.N[id]) select({ kind: "node", id });
  }, [tx, select]);
  useEffect(() => { const f = () => setTimeout(() => ctl.current?.resize(), 80); document.addEventListener("fullscreenchange", f); return () => document.removeEventListener("fullscreenchange", f); }, []);
  useEffect(() => { setTimeout(() => ctl.current?.resize(), 60); }, [wide]);

  if (!boot || !tx) return <div className="boot">{error ? `数据没有加载出来：${error}` : "正在加载产业链数据…"}</div>;
  return (
    <Ctx.Provider value={{ boot, tx, select }}>
      <div className="app shell">
        <SideNav page={page} open={open} badges={{ watchlist: nBadge }} subtitle={`全市场 · ${boot.n_companies} 家`} />
        <div className="shell-main">
        <header className="topbar">
          <SearchBox />
        </header>
        {page === "macro" ? <MacroPage /> : page === "futures" ? <FuturesPage /> : page === "volatility" ? <VolatilityPage /> : page === "rates" ? <RatesFxPage /> : page === "buyback" ? <BuybackPage /> : page === "tasks" ? <TasksPage /> : page === "opportunities" ? <OpportunitiesPage /> : page === "sector-monitor" ? <SectorMonitorPage /> : page === "etf" ? <EtfPage /> : page === "holdings" ? <HoldingsPage /> : page === "factors" ? <FactorsPage /> : page === "watchlist" ? <WatchlistPage doc={wl.doc} error={wl.error} /> : page === "dupont" ? <DupontPage codes={route.codes} setCodes={openDupont} /> : (
        <>
        <div className="chain-bar">
          <label className="sector">按行业看
            <select value={sel.kind === "sector" ? sel.id : ""} onChange={(e) => e.target.value && select({ kind: "sector", id: e.target.value })}>
              <option value="">申万一级行业…</option>
              {Object.entries(boot.sectors).sort().map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <div className="quick">{boot.quick.map((q) => <button type="button" key={q.code} className={`chip ${sel.kind === "company" && sel.id === q.code ? "on" : ""}`} onClick={() => select({ kind: "company", id: q.code })}>{q.name}</button>)}</div>
        </div>
        <main className={wide ? "wide" : ""}>
          <section className="stage" ref={stage} aria-label="产业链网络">
            <div className="controls">
              <label>层数 <select value={opts.depth} onChange={(e) => setOpts({ ...opts, depth: +e.target.value })}>{[1, 2, 3].map((d) => <option key={d}>{d}</option>)}</select></label>
              <label>方向 <select value={opts.dir} onChange={(e) => setOpts({ ...opts, dir: e.target.value as "up" | "down" | "both" })}><option value="both">上下游</option><option value="up">只看上游</option><option value="down">只看下游</option></select></label>
              <label><input type="checkbox" checked={opts.showCp} onChange={(e) => setOpts({ ...opts, showCp: e.target.checked })} /> 客户/供应商</label>
              <label><input type="checkbox" checked={opts.net} onChange={(e) => setOpts({ ...opts, net: e.target.checked })} /> 行业看公司网络</label>
              <span className="zoom">
                <button type="button" title="放大" onClick={() => ctl.current?.zoomBy(1.25)}>＋</button>
                <button type="button" title="缩小" onClick={() => ctl.current?.zoomBy(0.8)}>－</button>
                <button type="button" onClick={() => ctl.current?.fit()}>适配</button>
                <button type="button" onClick={() => setWide(!wide)}>{wide ? "展开详情" : "收起详情"}</button>
                <button type="button" onClick={() => (document.fullscreenElement ? document.exitFullscreen() : stage.current?.requestFullscreen())}>全屏</button>
              </span>
            </div>
            <ChainGraph elements={graph.els} layout={graph.layout} onPick={onPick} control={ctl} />
          </section>
          {!wide && <Splitter onResize={() => ctl.current?.resize()} />}
          {!wide && (
            <section className="dossier" aria-label="详情" data-sel={error ? "error:" + sel.id : loaded ? (loaded.kind === "company" ? loaded.c.code : loaded.kind === "node" ? loaded.id : loaded.l1) : ""}>
              {error ? <p className="empty">出错了：{error}</p>
                : !loaded ? <p className="empty">正在加载…</p>
                : loaded.kind === "company" ? <CompanyDossier key={loaded.c.code} c={loaded.c} related={loaded.related} />
                : loaded.kind === "node" ? <NodeDossier key={loaded.id} id={loaded.id} makers={loaded.makers} />
                : <SectorDossier key={loaded.l1} l1={loaded.l1} companies={loaded.companies} />}
            </section>
          )}
        </main>
        </>)}
        </div>
      </div>
    </Ctx.Provider>
  );
}

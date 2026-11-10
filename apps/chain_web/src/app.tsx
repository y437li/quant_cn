import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, type Bootstrap, type Company, type CompanyBrief, type Maker, type Network, type Watchlist } from "./api/client";
import { ChainGraph, type GraphControl } from "./components/chain-graph";
import { Ctx, type Selection } from "./components/context";
import { Splitter } from "./components/splitter";
import { CompanyDossier } from "./features/company/company-dossier";
import { NodeDossier } from "./features/node/node-dossier";
import { SearchBox } from "./features/search/search-box";
import { SectorDossier } from "./features/sector/sector-dossier";
import { DupontPage } from "./features/dupont/dupont-page";
import { WatchlistPage } from "./features/watchlist/watchlist-page";
import { badgeCount } from "./features/watchlist/watchlist-format";
import { buildCompanyElements, buildNetworkElements, buildNodeElements, buildSectorElements, type El } from "./graph/elements";
import { buildIndex } from "./graph/taxonomy";

/** Purpose: the app shell: header (search, sector, page chips, quick list), graph stage with controls, resizable dossier; the DuPont (#dupont=) and watchlist (#watchlist) pages replace the stage. URL hash keeps the selection. */
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
  const readDupont = () => { const m = location.hash.match(/^#dupont=?(.*)$/); return m ? m[1].split(",").filter(Boolean).map(decodeURIComponent) : null; };
  const [dupont, setDupont] = useState<string[] | null>(readDupont());
  const readWatch = () => location.hash === "#watchlist";
  const [watch, setWatch] = useState(readWatch());
  const [wl, setWl] = useState<{ doc: Watchlist | null; error: string | null }>({ doc: null, error: null });
  useEffect(() => { const f = () => { setDupont(readDupont()); setWatch(readWatch()); }; addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []);
  useEffect(() => { api.getWatchlist().then((doc) => setWl({ doc, error: null })).catch((e) => setWl({ doc: null, error: e.message })); }, [watch]);
  const openDupont = (codes: string[]) => { location.hash = "#dupont=" + codes.map(encodeURIComponent).join(","); setWatch(false); setDupont(codes); };
  const openWatch = () => { location.hash = "#watchlist"; setDupont(null); setWatch(true); };
  const nBadge = badgeCount(wl.doc?.entries);

  useEffect(() => { api.getBootstrap().then(setBoot).catch((e) => setError(e.message)); }, []);
  useEffect(() => { const f = () => { const s = parseHash(); if (s) setSel(s); }; addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []);
  const select = useCallback((s: Selection) => { if (location.hash !== toHash(s)) location.hash = toHash(s); setDupont(null); setWatch(false); setSel(s); }, []);

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
      <div className="app">
        <header>
          <h1>A股产业链图谱<small>全市场 · {boot.n_companies} 家 · 本地 demo</small></h1>
          <SearchBox />
          <label className="sector">按行业看
            <select value={sel.kind === "sector" ? sel.id : ""} onChange={(e) => e.target.value && select({ kind: "sector", id: e.target.value })}>
              <option value="">申万一级行业…</option>
              {Object.entries(boot.sectors).sort().map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <nav className="pages">
            <button type="button" className={`chip ${dupont || watch ? "" : "on"}`} onClick={() => select(sel)}>产业链图谱</button>
            <button type="button" className={`chip ${dupont ? "on" : ""}`} onClick={() => openDupont(dupont || (sel.kind === "company" ? [sel.id] : []))}>杜邦坐标</button>
            <button type="button" className={`chip ${watch ? "on" : ""}`} onClick={openWatch} data-page="watchlist">观察账本{nBadge > 0 && <span className="badge" title="接近或已到买入区间的股票数">{nBadge}</span>}</button>
          </nav>
          <div className="quick">{boot.quick.map((q) => <button type="button" key={q.code} className={`chip ${sel.kind === "company" && sel.id === q.code ? "on" : ""}`} onClick={() => select({ kind: "company", id: q.code })}>{q.name}</button>)}</div>
        </header>
        {watch ? <WatchlistPage doc={wl.doc} error={wl.error} /> : dupont ? <DupontPage codes={dupont} setCodes={openDupont} /> : (
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
        </main>)}
      </div>
    </Ctx.Provider>
  );
}

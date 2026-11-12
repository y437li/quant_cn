import { useEffect, useRef, useState, type PointerEvent, type RefObject } from "react";
import { api, type EtfProxy, type ProxyWeek } from "../../api/client";
import { flowClass, proxyHeadline, signedYi, yi } from "./etf-proxy-format";
import { dayMs, linear, niceTicks, ymd } from "./watchlist-format";

const RECENT_SHOWN = 5;

/** Purpose: the pixel width of a box, kept current with a ResizeObserver. Contract: at least min. */
function useWidth(min = 280): [RefObject<HTMLDivElement>, number] {
  const ref = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(min);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setW(Math.max(min, Math.floor(el.clientWidth))));
    ro.observe(el);
    return () => ro.disconnect();
  }, [min]);
  return [ref, w];
}

/**
 * Purpose: the 国家队 ETF panel at the top of 观察账本 (plan 15 phase 7b, D-126): headline, weekly position of
 * the core (national-team) ETFs and of the other ETFs at today's price, weekly core net flow, per-index table,
 * last days' flows. Loads GET /api/etf-proxy itself; every number is from the Python EtfProxyBuilder.
 * Contract: renders nothing until loaded; an error or an empty document shows a one-line note.
 */
export function EtfProxyPanel() {
  const [state, setState] = useState<{ doc: EtfProxy | null; error: string | null }>({ doc: null, error: null });
  useEffect(() => { api.getEtfProxy().then((doc) => setState({ doc, error: null })).catch((e) => setState({ doc: null, error: e.message })); }, []);
  const { doc, error } = state;
  if (error) return <section className="wl-section ep"><p className="note">国家队 ETF 数据没有加载出来：{error}</p></section>;
  if (!doc) return null;
  if (!doc.as_of) return <section className="wl-section ep" data-ep="0"><p className="note">还没有国家队 ETF 数据：运行 <code>make etf-proxy</code>。</p></section>;
  const recent = doc.recent.slice(-RECENT_SHOWN);
  return (
    <section className="wl-section ep" data-ep={doc.indices.length}>
      <h3>国家队 ETF 代理</h3>
      <p className="ep-head">{proxyHeadline(doc, doc.recent.length)}</p>
      <PositionChart weeks={doc.weekly} />
      <FlowBars weeks={doc.weekly} />
      <div className="ep-recent">
        <span className="wl-k">最近 {recent.length} 个交易日（核心 / 其他）</span>
        {recent.map((d) => (
          <span key={d.date} className="ep-day"><span className="wl-k">{ymd(d.date).slice(5)}</span>
            <span className={`num ep-${flowClass(d.core)}`}>{signedYi(d.core)}</span> / <span className={`num ep-${flowClass(d.other)}`}>{signedYi(d.other)}</span></span>
        ))}
      </div>
      <div className="scrollx">
        <table className="wl-table">
          <thead><tr>{["指数", "ETF 数", "规模", "仓位（按现价）", "其中核心", `近 ${doc.recent.length} 日净申赎`, "今年净申赎"].map((h, i) => <th key={h} className={i ? "num" : ""}>{h}</th>)}</tr></thead>
          <tbody>{doc.indices.map((x) => (
            <tr key={x.name}>
              <td>{x.name}</td><td className="num">{x.n_etf}</td><td className="num">{yi(x.aum)}</td><td className="num">{yi(x.position)}</td>
              <td className="num">{yi(x.core_position)}</td>
              <td className={`num ep-${flowClass(x.flow_recent)}`}>{signedYi(x.flow_recent)}</td><td className={`num ep-${flowClass(x.flow_ytd)}`}>{signedYi(x.flow_ytd)}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      <details className="wl-notes">
        <summary>口径</summary>
        <dl>
          <dt>范围</dt><dd>{doc.n_members} 只完全跟踪 7 个宽基指数的场内 ETF（不含联接、增强），自 {ymd(doc.start)} 起。核心 = 国家队重仓的 11 只大 ETF；其他 = 同指数的其余 ETF。ETF 份额包含所有持有人，季报前十大持有人可以核对。</dd>
          <dt>净申赎</dt><dd>规模变化减去价格涨跌带来的部分（AUM_t − AUM_t−1 × 当日收益），份额拆分和缺数日不影响。</dd>
          <dt>仓位（按现价）</dt><dd>规模按每个指数最大 ETF 的价格折回今天的价格水平，所以涨跌不会显示成买卖。</dd>
          <dt>更新</dt><dd>交易日 18:30 自动运行 make etf-proxy。份额数据比价格晚 1–3 天：份额截至 {ymd(doc.as_of)}，价格截至 {ymd(doc.price_as_of)}。</dd>
        </dl>
      </details>
    </section>
  );
}

/** Purpose: weekly core and other positions (亿元, today's price) on one axis, legend, end labels, hover tooltip. */
function PositionChart({ weeks }: { weeks: ProxyWeek[] }) {
  const [ref, W] = useWidth();
  const [hover, setHover] = useState<number | null>(null);
  const pts = weeks.filter((w) => w.core_position != null).map((w) => ({ t: dayMs(w.date), d: w.date, c: w.core_position ?? 0, o: w.other_position ?? null }));
  if (pts.length < 2) return <div className="wl-chart note" ref={ref}>没有周数据</div>;
  const H = 190, m = { l: 52, r: 64, t: 10, b: 20 };
  const vmax = Math.max(...pts.map((p) => Math.max(p.c, p.o ?? 0))) * 1.06;
  const ticks = niceTicks(0, vmax, 4);
  const x = linear(pts[0].t, pts[pts.length - 1].t, m.l, W - m.r), y = linear(0, vmax, H - m.b, m.t);
  const line = (k: "c" | "o") => pts.filter((p) => p[k] != null).map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p[k] as number).toFixed(1)}`).join("");
  const years = [...new Set(pts.map((p) => p.d.slice(0, 4)))];
  const last = pts[pts.length - 1];
  const move = (ev: PointerEvent<SVGRectElement>) => {
    const px0 = ev.clientX - ev.currentTarget.getBoundingClientRect().left + m.l;
    let best = 0;
    pts.forEach((p, i) => { if (Math.abs(x(p.t) - px0) < Math.abs(x(pts[best].t) - px0)) best = i; });
    setHover(best);
  };
  const h = hover != null ? pts[hover] : null;
  const flow = h ? weeks.find((w) => w.date === h.d) : null;
  return (
    <div className="wl-chart" ref={ref}>
      <div className="ep-legend"><span className="ep-key core" />核心 11 只（国家队代理）<span className="ep-key other" />其他同指数 ETF</div>
      <svg width={W} height={H} role="img" aria-label="国家队 ETF 周仓位（按现价，亿元）">
        {ticks.map((t) => <g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} className="wl-grid" /><text x={m.l - 6} y={y(t) + 4} textAnchor="end" className="wl-ax">{Math.round(t).toLocaleString("en-US")}</text></g>)}
        {years.map((yr) => { const p = pts.find((q) => q.d.startsWith(yr)); return p && <text key={yr} x={x(p.t)} y={H - 5} className="wl-ax">{yr}</text>; })}
        <path d={line("o")} className="ep-line other" />
        <path d={line("c")} className="ep-line core" />
        <text x={x(last.t) + 6} y={y(last.c) + 4} className="wl-lbl">{yi(last.c)}</text>
        {last.o != null && <text x={x(last.t) + 6} y={y(last.o) + 4} className="wl-lbl">{yi(last.o)}</text>}
        {h && <line x1={x(h.t)} x2={x(h.t)} y1={m.t} y2={H - m.b} className="wl-grid" />}
        {h && <circle cx={x(h.t)} cy={y(h.c)} r={4} className="wl-dot" />}
        <rect x={m.l} y={m.t} width={W - m.l - m.r} height={H - m.t - m.b} fill="transparent" onPointerMove={move} onPointerLeave={() => setHover(null)} />
      </svg>
      {h && (
        <div className="wl-tip" style={{ left: x(h.t) + 190 > W ? x(h.t) - 180 : x(h.t) + 10, top: 24 }}>
          <span>周 {ymd(h.d)}</span>核心 {yi(h.c)} · 其他 {yi(h.o)}<span>当周核心净申赎 {signedYi(flow?.core_flow)}</span>
        </div>
      )}
    </div>
  );
}

/** Purpose: weekly net flow of the core ETFs as bars around zero (blue = in, orange = out). */
function FlowBars({ weeks }: { weeks: ProxyWeek[] }) {
  const [ref, W] = useWidth();
  const pts = weeks.filter((w) => w.core_flow != null);
  if (pts.length < 2) return null;
  const H = 90, m = { l: 52, r: 64, t: 6, b: 6 };
  const amax = Math.max(...pts.map((p) => Math.abs(p.core_flow as number))) || 1;
  const step = (W - m.l - m.r) / pts.length;
  const y = linear(-amax, amax, H - m.b, m.t), bw = Math.max(0.6, step - (step > 3 ? 1 : 0));
  return (
    <div className="wl-chart" ref={ref}>
      <span className="wl-k">核心 ETF 每周净申赎（亿元）</span>
      <svg width={W} height={H} role="img" aria-label="核心 ETF 每周净申赎">
        <line x1={m.l} x2={W - m.r} y1={y(0)} y2={y(0)} className="wl-grid" />
        <text x={m.l - 6} y={y(amax) + 8} textAnchor="end" className="wl-ax">+{Math.round(amax).toLocaleString("en-US")}</text>
        <text x={m.l - 6} y={y(-amax)} textAnchor="end" className="wl-ax">−{Math.round(amax).toLocaleString("en-US")}</text>
        {pts.map((p, i) => {
          const v = p.core_flow as number, x0 = m.l + i * step;
          return <rect key={p.date} x={x0} width={bw} y={Math.min(y(v), y(0))} height={Math.max(1, Math.abs(y(v) - y(0)))} className={`ep-bar ep-${flowClass(v)}`}><title>{`${ymd(p.date)} ${signedYi(v)}`}</title></rect>;
        })}
      </svg>
    </div>
  );
}

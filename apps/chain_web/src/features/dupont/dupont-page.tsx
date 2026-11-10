import { useEffect, useMemo, useState } from "react";
import { api, type SearchHit } from "../../api/client";
import { useApp } from "../../components/context";
import { DRIVER_ZH, DupontPlane, type MarketPt as PlanePt, type Path } from "../../components/dupont-plane";
import { Note, Tag } from "../../components/ui";

/**
 * Purpose: a dedicated DuPont page: pick any companies (each its own colour and path), highlight a sector,
 * play the whole market year by year. Positions come from bootstrap.dupont_all (Python, FY2019–FY2025).
 * Contract: selection lives in the URL hash (#dupont=code,code); no server calls besides search.
 */
type MarketPt = [number, number, string, string, string | null];
export const PALETTE = ["var(--c5)", "var(--c1)", "var(--c3)", "var(--c4)", "var(--c2)", "var(--c6)"];

export function DupontPage({ codes, setCodes }: { codes: string[]; setCodes: (c: string[]) => void }) {
  const { boot, select } = useApp();
  const byYear = useMemo(() => (boot as unknown as { dupont_all?: Record<string, MarketPt[]> }).dupont_all || {}, [boot]);
  const years = useMemo(() => Object.keys(byYear).sort(), [byYear]);
  const index = useMemo(() => {
    const m: Record<string, Record<string, MarketPt>> = {};
    for (const y of years) for (const pt of byYear[y]) (m[pt[2]] ||= {})[y] = pt;
    return m;
  }, [byYear, years]);
  const [yi, setYi] = useState(years.length - 1);
  const [playing, setPlaying] = useState(false);
  const [sector, setSector] = useState("");
  const [driver, setDriver] = useState("");
  const [hideFlagged, setHideFlagged] = useState(false);
  const visible = (m: PlanePt) => (!driver || m[5] === driver) && (!hideFlagged || !m[6]);
  const names = (boot as unknown as { names?: Record<string, string> }).names || {};
  const [labels, setLabels] = useState<Record<string, string>>(() => ({ ...names }));
  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => setYi((i) => { if (i >= years.length - 1) { setPlaying(false); return i; } return i + 1; }), 1000);
    return () => clearInterval(t);
  }, [playing, years.length]);
  useEffect(() => { // names for codes that came in through the URL
    codes.filter((c) => !labels[c]).forEach((c) => api.getCompany(c).then((r) => setLabels((l) => ({ ...l, [c]: r.company.name }))).catch(() => undefined));
  }, [codes]); // eslint-disable-line react-hooks/exhaustive-deps
  const year = years[yi] || "2025";
  const paths: Path[] = codes.map((code, i) => ({
    label: labels[code] || code, color: PALETTE[i % PALETTE.length],
    pts: years.slice(0, yi + 1).filter((y) => index[code]?.[y]).map((y) => ({ p: y.includes("Q") ? y + "年化" : y, at: index[code][y][0], roe: index[code][y][1] })),
  }));
  const add = (h: SearchHit) => { setLabels((l) => ({ ...l, [h.id]: h.label })); if (!codes.includes(h.id)) setCodes([...codes, h.id]); };
  const play = () => { if (yi >= years.length - 1) setYi(0); setPlaying(!playing); };
  return (
    <div className="dupont-page">
      <section className="dp-chart">
        <div className="player">
          <button type="button" className="chip on" onClick={play}>{playing ? "❚❚ 暂停" : "▶ 播放"}</button>
          <input type="range" min={0} max={years.length - 1} value={yi} onChange={(e) => { setPlaying(false); setYi(+e.target.value); }} aria-label="年份" />
          <b className="num">{year}</b>
          <label className="sector">高亮行业
            <select value={sector} onChange={(e) => setSector(e.target.value)}>
              <option value="">不高亮</option>
              {Object.entries(boot.sectors).sort().map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
        </div>
        <div className="player">
          <label className="sector">驱动类型
            <select value={driver} onChange={(e) => setDriver(e.target.value)}>
              <option value="">全部</option>
              {Object.entries(DRIVER_ZH).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <label className="sector"><input type="checkbox" checked={hideFlagged} onChange={(e) => setHideFlagged(e.target.checked)} /> 隐藏 ROE 失真的点</label>
          <span className="note">利润率驱动：净利率 ≥15% 且周转 &lt;1；周转驱动：周转 ≥1.2 且权益乘数 &lt;3；杠杆驱动：权益乘数 ≥3</span>
        </div>
        <DupontPlane big visible={visible} year={year} paths={paths} highlight={sector ? (m) => m[3] === sector && visible(m) : undefined}
          pickHint="点击加入 / 移出对比" onPick={(code) => (codes.includes(code) ? setCodes(codes.filter((x) => x !== code)) : add({ kind: "company", id: code, label: names[code] || labels[code] || code, sub: "" }))}
          caption={`${codes.length ? `彩色轨迹 = 所选公司 ${years[0]}→${year}；` : ""}${sector ? `蓝点 = ${boot.sectors[sector]}（点击加入对比）；` : ""}`} />
      </section>
      <aside className="dp-side">
        <div className="dp-head">
          <h3>选公司</h3>
          <button type="button" className="chip" disabled={!codes.length && !sector && !driver && !hideFlagged}
            title="清除所有已选公司，并恢复高亮行业和筛选" onClick={() => { setCodes([]); setSector(""); setDriver(""); setHideFlagged(false); setPlaying(false); setYi(years.length - 1); }}>全部清除</button>
        </div>
        <CompanyPicker onPick={add} />
        <div className="dp-chips">{codes.map((c, i) => (
          <span key={c} className="dp-chip" style={{ borderColor: PALETTE[i % PALETTE.length] }}>
            <i style={{ background: PALETTE[i % PALETTE.length] }} />
            <button type="button" className="link" onClick={() => select({ kind: "company", id: c })}>{labels[c] || c}</button>
            <button type="button" className="x" aria-label="移除" onClick={() => setCodes(codes.filter((x) => x !== c))}>×</button>
          </span>
        ))}</div>
        {!codes.length && <Note>用上面的搜索框添加公司；或先选“高亮行业”，再点图上的蓝点。</Note>}
        {codes.length > 0 && (
          <table className="fin"><thead><tr><th>{year}</th><th className="num">ROE</th><th className="num">周转</th></tr></thead>
            <tbody>{codes.map((c, i) => { const m = index[c]?.[year]; return (
              <tr key={c}><td><Tag><span style={{ color: PALETTE[i % PALETTE.length] }}>●</span> {labels[c] || c}</Tag></td><td className="num">{m ? m[1] + "%" : "—"}</td><td className="num">{m ? m[0] : "—"}</td></tr>
            ); })}</tbody></table>
        )}
        <Note>坐标固定：资产周转率 0–2 次，ROE −20%–40%。灰点 = 全部 A 股当年年报；播放时所有点一起按年切换。ROE = 净利率 × 资产周转率 × 权益乘数。</Note>
      </aside>
    </div>
  );
}

function CompanyPicker({ onPick }: { onPick: (h: SearchHit) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  useEffect(() => {
    const s = q.trim();
    if (!s) { setHits([]); return; }
    const t = setTimeout(() => api.findHits(s).then((h) => setHits(h.filter((x) => x.kind === "company"))).catch(() => setHits([])), 150);
    return () => clearTimeout(t);
  }, [q]);
  return (
    <div className="search dp-search">
      <input type="search" placeholder="公司名或代码，回车添加" value={q} onChange={(e) => setQ(e.target.value)} aria-label="添加公司"
        onKeyDown={(e) => { if (e.key === "Enter" && hits[0]) { onPick(hits[0]); setQ(""); } }} />
      {q.trim() && hits.length > 0 && (
        <div className="results">{hits.slice(0, 10).map((h) => <button type="button" key={h.id} onClick={() => { onPick(h); setQ(""); }}><span>{h.label}</span><span className="kind">{h.id}</span></button>)}</div>
      )}
    </div>
  );
}

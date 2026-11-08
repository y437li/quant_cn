import { useState } from "react";
import { useApp } from "./context";

/**
 * Purpose: one fixed DuPont plane for every view (x = asset turnover 0–2, y = ROE −20%–40%), so positions compare
 * across companies. Layers: the whole market (FY2025, faint), a highlighted group, and optional paths.
 * Contract: points outside the frame are drawn on the edge with an open marker; numbers come from Python.
 */
export const X_MAX = 2, Y_MIN = -20, Y_MAX = 40;
export type Path = { label: string; color?: string; pts: { p: string; at: number; roe: number }[] };
export type MarketPt = [number, number, string, string, string | null, string?, string?]; // turnover, ROE, code, L1, L3, driver, flag
export const DRIVER_ZH: Record<string, string> = { margin: "利润率驱动", turnover: "周转驱动", leverage: "杠杆驱动", mixed: "混合" };
export const FLAG_ZH: Record<string, string> = { thin: "⚠ 净资产过小，ROE 失真", gap: "⚠ 三项乘积与 ROE 不符（年内净资产变化大）" };

export function DupontPlane(p: { big?: boolean; pickHint?: string; year?: string; visible?: (pt: MarketPt) => boolean; highlight?: (pt: MarketPt) => boolean; paths?: Path[]; caption?: string; onPick?: (code: string) => void }) {
  const { boot } = useApp();
  const byYear = ((boot as unknown as { dupont_all?: Record<string, MarketPt[]> }).dupont_all || {});
  const names = (boot as unknown as { names?: Record<string, string> }).names || {};
  const [hover, setHover] = useState<{ m: MarketPt; x: number; y: number } | null>(null);
  const hoverOn = (m: MarketPt) => (e: React.MouseEvent) => {
    const box = (e.currentTarget as SVGElement).ownerSVGElement!.parentElement!.getBoundingClientRect();
    setHover({ m, x: e.clientX - box.left, y: e.clientY - box.top });
  };
  const pick = (code: string) => p.onPick && p.onPick(code);
  const year = p.year && byYear[p.year] ? p.year : Object.keys(byYear).sort().slice(-1)[0] || "2025";
  const all = (byYear[year] || []).filter((m) => !p.visible || p.visible(m));
  const W = p.big ? 1200 : 400, H = p.big ? 760 : 270, L = p.big ? 52 : 34, B = p.big ? 40 : 26, T = 8, R = 8;
  const clampX = (v: number) => Math.min(Math.max(v, 0), X_MAX), clampY = (v: number) => Math.min(Math.max(v, Y_MIN), Y_MAX);
  const sx = (v: number) => L + (clampX(v) / X_MAX) * (W - L - R);
  const sy = (v: number) => T + ((Y_MAX - clampY(v)) / (Y_MAX - Y_MIN)) * (H - T - B);
  const out = (at: number, roe: number) => at > X_MAX || at < 0 || roe > Y_MAX || roe < Y_MIN;
  const hi = p.highlight ? all.filter(p.highlight) : [];
  const medAt = 0.6, medRoe = 8; // quadrant guides: typical A-share turnover and ROE
  return (
    <figure className="dupont-fig" style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${H}`} className={p.big ? "dupont big" : "dupont"} role="img" aria-label="杜邦坐标：资产周转率与 ROE">
        <defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--c5)" /></marker></defs>
        <rect x={sx(medAt)} y={T} width={sx(X_MAX) - sx(medAt)} height={sy(medRoe) - T} fill="var(--c2)" opacity={0.06} />
        {[-20, -10, 0, 10, 20, 30, 40].map((t) => <g key={"y" + t}><line x1={L} x2={W - R} y1={sy(t)} y2={sy(t)} stroke={t === 0 ? "var(--muted)" : "var(--soft)"} strokeDasharray={t === 0 ? "3 3" : undefined} /><text x={L - 6} y={sy(t) + 4} textAnchor="end" className="ax">{t}%</text></g>)}
        {[0, 0.5, 1, 1.5, 2].map((t) => <g key={"x" + t}><line x1={sx(t)} x2={sx(t)} y1={T} y2={H - B} stroke="var(--soft)" /><text x={sx(t)} y={H - B + (p.big ? 20 : 12)} textAnchor="middle" className="ax">{t}</text></g>)}
        <line x1={sx(medAt)} x2={sx(medAt)} y1={T} y2={H - B} stroke="var(--line)" strokeDasharray="2 4" />
        <line x1={L} x2={W - R} y1={sy(medRoe)} y2={sy(medRoe)} stroke="var(--line)" strokeDasharray="2 4" />
        <text x={W - R - 2} y={T + 10} textAnchor="end" className="q">高周转 · 高回报</text>
        <text x={L + 4} y={T + 10} className="q">高利润率</text>
        <text x={W - R - 2} y={H - B - 4} textAnchor="end" className="q">薄利多销</text>
        {all.map((m) => <circle key={m[2]} cx={sx(m[0])} cy={sy(m[1])} r={p.big ? 2.2 : 1.4} fill={m[6] ? "none" : "var(--muted)"} fillOpacity={0.22} stroke={m[6] ? "var(--muted)" : "transparent"} strokeOpacity={m[6] ? 0.5 : 1} strokeWidth={m[6] ? 0.8 : p.big ? 6 : 4} pointerEvents="all"
          style={{ cursor: p.onPick ? "pointer" : "default" }} onMouseMove={hoverOn(m)} onMouseLeave={() => setHover(null)} onClick={() => pick(m[2])} />)}
        {hi.map((m) => <circle key={"h" + m[2]} cx={sx(m[0])} cy={sy(m[1])} r={p.big ? 4.5 : 2.8} fill={out(m[0], m[1]) || m[6] ? "none" : "var(--c1)"} stroke="var(--c1)" opacity={0.75} strokeWidth={p.big ? 6 : 4} strokeOpacity={0.3} style={{ cursor: p.onPick ? "pointer" : undefined }} onMouseMove={hoverOn(m)} onMouseLeave={() => setHover(null)} onClick={() => pick(m[2])} />)}
        {(p.paths || []).map((path) => (
          <g key={path.label}>
            <polyline points={path.pts.map((x) => `${sx(x.at)},${sy(x.roe)}`).join(" ")} fill="none" stroke={path.color || "var(--c5)"} strokeWidth={p.big ? 3.5 : 1.8} />
            {path.pts.map((x, i) => <g key={x.p}><circle cx={sx(x.at)} cy={sy(x.roe)} r={(i === path.pts.length - 1 ? 4 : 2.6) * (p.big ? 1.7 : 1)} fill={out(x.at, x.roe) ? "var(--panel)" : path.color || "var(--c5)"} stroke={path.color || "var(--c5)"}><title>{`${x.p} ROE ${x.roe}% 周转 ${x.at}`}</title></circle>
              {(i === 0 || i === path.pts.length - 1) && <text x={sx(x.at) + 5} y={sy(x.roe) - 5} className="lbl">{p.big && i === path.pts.length - 1 ? path.label : x.p.replace("年化", "")}</text>}</g>)}
          </g>
        ))}
        <text x={W - R} y={H - 2} textAnchor="end" className="ax">资产周转率（次/年）</text>
        <text x={L + 2} y={H - B - 4} className="ax">ROE</text>
        <text x={(W + L) / 2} y={H / 2} textAnchor="middle" className="yr">{year}</text>
        {hover && <circle cx={sx(hover.m[0])} cy={sy(hover.m[1])} r={p.big ? 9 : 6} fill="none" stroke="var(--c5)" strokeWidth={2} pointerEvents="none" />}
      </svg>
      {hover && (
        <div className="dp-tip" style={{ left: hover.x + 14, top: hover.y + 10 }}>
          <b>{names[hover.m[2]] || hover.m[2]}</b> <span className="note">{hover.m[2]}</span>
          <div className="note">{boot.sectors[hover.m[3]] || ""}{hover.m[4] ? " · " + hover.m[4] : ""}</div>
          <div className="num">{year} · ROE {hover.m[1]}% · 周转 {hover.m[0]}</div>
          {hover.m[5] && <div>{DRIVER_ZH[hover.m[5]]}</div>}
          {hover.m[6] && <div style={{ color: "var(--c5)" }}>{FLAG_ZH[hover.m[6]]}</div>}
          {p.onPick && <div className="note">{p.pickHint || "点击打开"}</div>}
        </div>
      )}
      <figcaption className="note">{p.caption} 坐标固定（周转 0–2 次，ROE −20%–40%），超出范围的点贴边画为空心；ROE 失真的点（净资产过小、或三项乘积与 ROE 不符）也画为空心。灰点 = 全部 A 股 {year.includes("Q") ? year + "（年化，已披露季报的公司）" : year + " 年"}；虚线为周转 0.6 次、ROE 8% 参考线。</figcaption>
    </figure>
  );
}

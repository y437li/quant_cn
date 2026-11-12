import { useEffect, useRef, useState, type PointerEvent, type RefObject } from "react";
import { dayMs, linear, niceTicks, ymd } from "../watchlist/watchlist-format";

/** Purpose: the pixel width of a box, kept current with a ResizeObserver. Contract: returns at least min. */
function useBoxWidth(min = 240): [RefObject<HTMLDivElement>, number] {
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

export interface Series { name: string; cls: string; points: { d: string; v: number }[] }

/**
 * Purpose: daily line chart of one or two series in percent (cumulative return, or forecast vs realized vol),
 * gridlines, date axis, a zero line when the range crosses 0, and a hover readout of every series.
 * Contract: series share the date axis; fewer than two points in total draws a note instead.
 */
export function LineChart({ series, label }: { series: Series[]; label: string }) {
  const [ref, W] = useBoxWidth();
  const [hover, setHover] = useState<string | null>(null);
  const all = series.flatMap((s) => s.points);
  if (all.length < 2) return <div className="fm-chart note" ref={ref}>没有数据</div>;
  const H = 170;
  const ts = [...new Set(all.map((p) => p.d))].sort();
  const vs = all.map((p) => p.v * 100);
  const pad = (Math.max(...vs) - Math.min(...vs)) * 0.06 || 1;
  const ticks = niceTicks(Math.min(...vs) - pad, Math.max(...vs) + pad, 4);
  const lo = Math.min(ticks[0], Math.min(...vs)), hi = Math.max(ticks[ticks.length - 1], Math.max(...vs));
  const m = { l: 44, r: 8, t: 8, b: 20 };
  const x = linear(dayMs(ts[0]), dayMs(ts[ts.length - 1]), m.l, W - m.r);
  const y = linear(lo, hi, H - m.b, m.t);
  const nx = Math.max(2, Math.floor(W / 110));
  const xTicks = Array.from({ length: nx }, (_, i) => ts[Math.round((i * (ts.length - 1)) / (nx - 1))]);
  const path = (s: Series) => s.points.map((p, i) => `${i ? "L" : "M"}${x(dayMs(p.d)).toFixed(1)},${y(p.v * 100).toFixed(1)}`).join("");
  const move = (ev: PointerEvent<SVGRectElement>) => {
    const t = ev.clientX - ev.currentTarget.getBoundingClientRect().left + m.l;
    let best = ts[0];
    for (const d of ts) if (Math.abs(x(dayMs(d)) - t) < Math.abs(x(dayMs(best)) - t)) best = d;
    setHover(best);
  };
  const hx = hover ? x(dayMs(hover)) : 0;
  return (
    <div className="fm-chart" ref={ref}>
      <svg width={W} height={H} role="img" aria-label={label}>
        {ticks.map((t) => <g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} className={t === 0 ? "fm-zero" : "wl-grid"} /><text x={m.l - 6} y={y(t) + 4} textAnchor="end" className="wl-ax">{t}%</text></g>)}
        {xTicks.map((d, i) => <text key={d + i} x={x(dayMs(d))} y={H - 5} textAnchor={i === 0 ? "start" : i === nx - 1 ? "end" : "middle"} className="wl-ax">{ymd(d).slice(0, 7)}</text>)}
        {series.map((s) => <path key={s.name} d={path(s)} className={`fm-line ${s.cls}`} />)}
        {hover && <line x1={hx} x2={hx} y1={m.t} y2={H - m.b} className="fm-cursor" />}
        <rect x={m.l} y={m.t} width={W - m.l - m.r} height={H - m.t - m.b} fill="transparent" onPointerMove={move} onPointerLeave={() => setHover(null)} />
      </svg>
      <div className="fm-legend">{series.map((s) => <span key={s.name} className={s.cls}>{s.name}</span>)}</div>
      {hover && (
        <div className="wl-tip" style={{ left: hx + 170 > W ? hx - 160 : hx + 10, top: 6 }}>
          <span>{ymd(hover)}</span>
          {series.map((s) => { const p = s.points.find((q) => q.d === hover); return <div key={s.name}>{s.name} {p ? (p.v * 100).toFixed(2) + "%" : "—"}</div>; })}
        </div>
      )}
    </div>
  );
}

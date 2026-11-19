import { useEffect, useRef, useState, type PointerEvent, type RefObject } from "react";
import type { MacroSeries } from "../../api/client";
import { linear, niceTicks } from "../watchlist/watchlist-format";
import { formatValue, monthLabel, refLine } from "./macro-format";

/** Purpose: the pixel width of a box, kept current with a ResizeObserver. Contract: returns at least min. */
function useBoxWidth(min = 220): [RefObject<HTMLDivElement>, number] {
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
 * Purpose: one macro line over its last 60 monthly prints: gridlines, a reference line (50 for PMI, else 0) when in range,
 * the latest print as a dot, year ticks, and a hover readout.
 * Contract: fewer than two prints draws a note instead.
 */
export function MacroChart({ s, height = 150 }: { s: MacroSeries; height?: number }) {
  const [ref, W] = useBoxWidth();
  const [hover, setHover] = useState<number | null>(null);
  const pts = s.history;
  if (pts.length < 2) return <div className="mc-chart note" ref={ref}>没有足够数据</div>;
  const vs = pts.map((p) => p.value);
  const pad = (Math.max(...vs) - Math.min(...vs)) * 0.08 || 1;
  const ticks = niceTicks(Math.min(...vs) - pad, Math.max(...vs) + pad, 3);
  const lo = Math.min(ticks[0], ...vs), hi = Math.max(ticks[ticks.length - 1], ...vs);
  const m = { l: s.unit === "亿元" ? 54 : 38, r: 10, t: 8, b: 18 };
  const x = linear(0, pts.length - 1, m.l, W - m.r);
  const y = linear(lo, hi, height - m.b, m.t);
  const ref0 = refLine(s.key);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join("");
  const years = pts.map((p, i) => [p.month, i] as const).filter(([mo], i) => mo.endsWith("01") && i > 0);
  const move = (ev: PointerEvent<SVGRectElement>) => {
    const t = (ev.clientX - ev.currentTarget.getBoundingClientRect().left) / (W - m.l - m.r);
    setHover(Math.max(0, Math.min(pts.length - 1, Math.round(t * (pts.length - 1)))));
  };
  const last = pts.length - 1;
  const fmtTick = (t: number) => (s.unit === "亿元" ? `${(t / 10000).toFixed(1)}万` : String(t));
  return (
    <div className="mc-chart" ref={ref}>
      <svg width={W} height={height} role="img" aria-label={`${s.name} 近 ${pts.length} 个月`}>
        {ticks.map((t) => <g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} className="wl-grid" /><text x={m.l - 5} y={y(t) + 4} textAnchor="end" className="wl-ax">{fmtTick(t)}</text></g>)}
        {ref0 >= lo && ref0 <= hi && <line x1={m.l} x2={W - m.r} y1={y(ref0)} y2={y(ref0)} className="mc-ref" />}
        {years.map(([mo, i]) => <text key={mo} x={x(i)} y={height - 4} textAnchor="middle" className="wl-ax">{mo.slice(0, 4)}</text>)}
        <path d={d} className="mc-line" />
        <circle cx={x(last)} cy={y(pts[last].value)} r={3.5} className="mc-dot" />
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={m.t} y2={height - m.b} className="fm-cursor" />}
        <rect x={m.l} y={m.t} width={W - m.l - m.r} height={height - m.t - m.b} fill="transparent" onPointerMove={move} onPointerLeave={() => setHover(null)} />
      </svg>
      {hover != null && (
        <div className="wl-tip" style={{ left: x(hover) + 120 > W ? x(hover) - 110 : x(hover) + 8, top: 4 }}>
          {monthLabel(pts[hover].month)} <b>{formatValue(s, pts[hover].value)}</b>
        </div>
      )}
    </div>
  );
}

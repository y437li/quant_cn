import { useEffect, useRef, useState, type PointerEvent, type RefObject } from "react";
import { linear, niceTicks } from "../watchlist/watchlist-format";

/** Purpose: the pixel width of a box, kept current with a ResizeObserver. Contract: returns at least min. */
function useBoxWidth(min = 260): [RefObject<HTMLDivElement>, number] {
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

export interface ChartPoint { x: string; v: number }

/**
 * Purpose: a line over evenly spaced points (dates or contract months) with gridlines, a zero line when in range,
 * sparse x labels, the last point as a dot and a hover readout.
 * Contract: fewer than two points draws a note; fmt formats axis ticks and the readout; xfmt formats x labels.
 */
export function FuturesChart({ points, label, fmt, xfmt, height = 170, dots = false }: {
  points: ChartPoint[]; label: string; fmt: (v: number) => string; xfmt: (x: string) => string; height?: number; dots?: boolean;
}) {
  const [ref, W] = useBoxWidth();
  const [hover, setHover] = useState<number | null>(null);
  if (points.length < 2) return <div className="mc-chart note" ref={ref}>没有足够数据</div>;
  const vs = points.map((p) => p.v);
  const pad = (Math.max(...vs) - Math.min(...vs)) * 0.08 || Math.abs(vs[0]) * 0.02 || 1;
  const ticks = niceTicks(Math.min(...vs) - pad, Math.max(...vs) + pad, 3);
  const lo = Math.min(ticks[0], ...vs), hi = Math.max(ticks[ticks.length - 1], ...vs);
  const m = { l: 58, r: 12, t: 8, b: 20 };
  const x = linear(0, points.length - 1, m.l, W - m.r);
  const y = linear(lo, hi, height - m.b, m.t);
  const d = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
  const nx = Math.min(points.length, Math.max(2, Math.floor(W / 90)));
  const xt = Array.from({ length: nx }, (_, i) => Math.round((i * (points.length - 1)) / (nx - 1)));
  const last = points.length - 1;
  const move = (ev: PointerEvent<SVGRectElement>) => {
    const t = (ev.clientX - ev.currentTarget.getBoundingClientRect().left) / (W - m.l - m.r);
    setHover(Math.max(0, Math.min(last, Math.round(t * last))));
  };
  return (
    <div className="mc-chart" ref={ref}>
      <svg width={W} height={height} role="img" aria-label={label}>
        {ticks.map((t) => <g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} className="wl-grid" /><text x={m.l - 5} y={y(t) + 4} textAnchor="end" className="wl-ax">{fmt(t)}</text></g>)}
        {lo < 0 && hi > 0 && <line x1={m.l} x2={W - m.r} y1={y(0)} y2={y(0)} className="mc-ref" />}
        {xt.map((i, k) => <text key={i} x={x(i)} y={height - 5} textAnchor={k === 0 ? "start" : k === nx - 1 ? "end" : "middle"} className="wl-ax">{xfmt(points[i].x)}</text>)}
        <path d={d} className="mc-line" />
        {dots && points.map((p, i) => <circle key={p.x} cx={x(i)} cy={y(p.v)} r={2.5} className="mc-dot" />)}
        <circle cx={x(last)} cy={y(points[last].v)} r={3.5} className="mc-dot" />
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={m.t} y2={height - m.b} className="fm-cursor" />}
        <rect x={m.l} y={m.t} width={W - m.l - m.r} height={height - m.t - m.b} fill="transparent" onPointerMove={move} onPointerLeave={() => setHover(null)} />
      </svg>
      {hover != null && (
        <div className="wl-tip" style={{ left: x(hover) + 130 > W ? x(hover) - 120 : x(hover) + 8, top: 4 }}>
          {xfmt(points[hover].x)} <b>{fmt(points[hover].v)}</b>
        </div>
      )}
    </div>
  );
}

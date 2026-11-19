import { useEffect, useRef, useState, type PointerEvent, type RefObject } from "react";
import type { VolPoint } from "../../api/client";
import { linear, niceTicks } from "../watchlist/watchlist-format";
import { dayLabel, formatVol } from "./volatility-format";

const last0 = (pts: VolPoint[]) => pts.length - 1;

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
 * Purpose: one daily series over the window: gridlines, dashed reference lines (a volatility index's alert level or
 * median; the 中证1000 watch levels), the latest value as a dot, month ticks (year ticks when the series spans two calendar
 * years or more), and a hover readout.
 * Contract: fewer than two points draws a note instead; every ref is kept inside the y range; `format` formats the hover
 * value (default formatVol, one decimal).
 */
export function VolatilityChart({ name, points, refs, height = 150, format = formatVol }: { name: string; points: VolPoint[]; refs: number[]; height?: number; format?: (v: number) => string }) {
  const [ref, W] = useBoxWidth();
  const [hover, setHover] = useState<number | null>(null);
  const pts = points;
  if (pts.length < 2) return <div className="mc-chart note" ref={ref}>没有足够数据</div>;
  const vs = pts.map((p) => p.value);
  const pad = (Math.max(...vs, ...refs) - Math.min(...vs, ...refs)) * 0.08 || 1;
  const ticks = niceTicks(Math.min(...vs, ...refs) - pad, Math.max(...vs, ...refs) + pad, 3);
  const lo = Math.min(ticks[0], ...vs, ...refs), hi = Math.max(ticks[ticks.length - 1], ...vs, ...refs);
  const m = { l: 32, r: 10, t: 8, b: 18 };
  const x = linear(0, pts.length - 1, m.l, W - m.r);
  const y = linear(lo, hi, height - m.b, m.t);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join("");
  const years = Number(pts[last0(pts)].date.slice(0, 4)) - Number(pts[0].date.slice(0, 4)) >= 2;  // long series: year ticks
  const cut = years ? 4 : 6;
  const months = pts.map((p, i) => [p.date, i] as const).filter(([dt, i]) => i > 0 && dt.slice(0, cut) !== pts[i - 1].date.slice(0, cut));
  const step = Math.max(1, Math.ceil(months.length / 6));
  const move = (ev: PointerEvent<SVGRectElement>) => {
    const t = (ev.clientX - ev.currentTarget.getBoundingClientRect().left) / (W - m.l - m.r);
    setHover(Math.max(0, Math.min(pts.length - 1, Math.round(t * (pts.length - 1)))));
  };
  const last = pts.length - 1;
  return (
    <div className="mc-chart" ref={ref}>
      <svg width={W} height={height} role="img" aria-label={`${name} 近 ${pts.length} 个交易日`}>
        {ticks.map((t) => <g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} className="wl-grid" /><text x={m.l - 5} y={y(t) + 4} textAnchor="end" className="wl-ax">{t}</text></g>)}
        {refs.map((r) => <line key={r} x1={m.l} x2={W - m.r} y1={y(r)} y2={y(r)} className="mc-ref" />)}
        {months.filter((_, k) => k % step === 0).map(([dt, i]) => <text key={dt} x={x(i)} y={height - 4} textAnchor="middle" className="wl-ax">{years || dt.slice(4, 6) === "01" ? dt.slice(0, 4) : `${Number(dt.slice(4, 6))}月`}</text>)}
        <path d={d} className="mc-line" />
        <circle cx={x(last)} cy={y(pts[last].value)} r={3.5} className="mc-dot" />
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={m.t} y2={height - m.b} className="fm-cursor" />}
        <rect x={m.l} y={m.t} width={W - m.l - m.r} height={height - m.t - m.b} fill="transparent" onPointerMove={move} onPointerLeave={() => setHover(null)} />
      </svg>
      {hover != null && (
        <div className="wl-tip" style={{ left: x(hover) + 130 > W ? x(hover) - 120 : x(hover) + 8, top: 4 }}>
          {dayLabel(pts[hover].date)} <b>{format(pts[hover].value)}</b>
        </div>
      )}
    </div>
  );
}

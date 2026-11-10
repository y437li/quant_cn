import { useEffect, useRef, useState, type PointerEvent, type RefObject } from "react";
import type { WatchlistEntry } from "../../api/client";
import { dayMs, linear, niceTicks, placeLabels, px, ymd, type Label } from "./watchlist-format";

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

const nums = (xs: (number | null)[]) => xs.filter((v): v is number => v != null);

/**
 * Purpose: one-line price map of a stock: 52-week low–high line, green buy zone, dashed broker target box,
 * dot at the current price, non-overlapping labels (buy, price, 52-week high).
 * Contract: draws only what is present (null 52-week or target values are skipped).
 */
export function RangeBar({ e }: { e: WatchlistEntry }) {
  const [ref, W] = useBoxWidth();
  const H = 52, y = 18;
  const lo = Math.min(...nums([e.low_52w, e.buy_low, e.price, e.target_low])) * 0.94;
  const hi = Math.max(...nums([e.high_52w, e.target_high, e.price, e.buy_high])) * 1.03;
  const x = linear(lo, hi, 6, W - 6);
  const single = e.buy_low === e.buy_high;
  const labels: Label[] = [
    { x: x(e.price), text: `现价 ${px(e.price)}`, anchor: "middle" },
    { x: x(single ? e.buy_high : e.buy_low), text: single ? `买 ${px(e.buy_high)}` : `买 ${px(e.buy_low)}–${px(e.buy_high)}`, anchor: single ? "middle" : "start" },
    ...(e.high_52w != null ? [{ x: x(e.high_52w), text: `52周高 ${px(e.high_52w)}`, anchor: "end" as const }] : []),
    ...(e.low_52w != null ? [{ x: x(e.low_52w), text: `52周低 ${px(e.low_52w)}`, anchor: "start" as const }] : []),
  ];
  const tl = e.target_low ?? e.target_high, th = e.target_high ?? e.target_low;
  return (
    <div className="wl-range" ref={ref}>
      <svg width={W} height={H} role="img" aria-label={`${e.name} 价格区间`}>
        {e.low_52w != null && e.high_52w != null && <line x1={x(e.low_52w)} x2={x(e.high_52w)} y1={y} y2={y} className="wl-52w" />}
        <rect x={x(e.buy_low) - (single ? 2 : 0)} y={y - 9} width={Math.max(4, x(e.buy_high) - x(e.buy_low))} height={18} rx={3} className="wl-zone" />
        {tl != null && th != null && <rect x={x(tl)} y={y - 9} width={Math.max(2, x(th) - x(tl))} height={18} rx={3} className="wl-target" />}
        <circle cx={x(e.price)} cy={y} r={6} className="wl-dot" />
        {placeLabels(labels, W).map((l) => <text key={l.text} x={l.x} y={44} textAnchor={l.anchor} className="wl-lbl">{l.text}</text>)}
      </svg>
    </div>
  );
}

/**
 * Purpose: weekly closes over the last year with the buy zone as a green band and a hover tooltip.
 * Contract: weekly sorted by date; fewer than two points draws a note instead of a chart.
 */
export function WeeklyChart({ e }: { e: WatchlistEntry }) {
  const [ref, W] = useBoxWidth();
  const [hover, setHover] = useState<number | null>(null);
  const pts = e.weekly.map((p) => ({ t: dayMs(p.date), v: p.close, d: p.date }));
  if (pts.length < 2) return <div className="wl-chart note" ref={ref}>没有周线数据</div>;
  const H = 150;
  const yMin = Math.min(...pts.map((p) => p.v), e.buy_low) * 0.95, yMax = Math.max(...pts.map((p) => p.v), e.buy_high) * 1.04;
  const ticks = niceTicks(yMin, yMax, 4);
  const m = { l: Math.max(...ticks.map((t) => String(Math.round(t)).length)) * 7 + 10, r: 8, t: 8, b: 20 };
  const x = linear(pts[0].t, pts[pts.length - 1].t, m.l, W - m.r);
  const y = linear(yMin, yMax, H - m.b, m.t);
  const nx = Math.max(2, Math.floor(W / 110));
  const xTicks = Array.from({ length: nx }, (_, i) => pts[Math.round((i * (pts.length - 1)) / (nx - 1))]);
  const path = pts.map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
  const band = [y(e.buy_high), y(e.buy_low)];
  const move = (ev: PointerEvent<SVGRectElement>) => {
    const px0 = ev.clientX - ev.currentTarget.getBoundingClientRect().left + m.l;
    let best = 0;
    pts.forEach((p, i) => { if (Math.abs(x(p.t) - px0) < Math.abs(x(pts[best].t) - px0)) best = i; });
    setHover(best);
  };
  const h = hover != null ? pts[hover] : null;
  const last = pts[pts.length - 1];
  return (
    <div className="wl-chart" ref={ref}>
      <svg width={W} height={H} role="img" aria-label={`${e.name} 近一年周收盘价`}>
        {ticks.map((t) => <g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} className="wl-grid" /><text x={m.l - 6} y={y(t) + 4} textAnchor="end" className="wl-ax">{Math.round(t)}</text></g>)}
        {xTicks.map((p, i) => <text key={p.d} x={x(p.t)} y={H - 5} textAnchor={i === 0 ? "start" : i === nx - 1 ? "end" : "middle"} className="wl-ax">{ymd(p.d).slice(0, 7)}</text>)}
        <rect x={m.l} width={W - m.l - m.r} y={band[0] - (e.buy_low === e.buy_high ? 1 : 0)} height={Math.max(2, band[1] - band[0])} className="wl-band" />
        <line x1={m.l} x2={W - m.r} y1={band[0]} y2={band[0]} className="wl-band-top" />
        <path d={path} className="wl-line" />
        <circle cx={x(last.t)} cy={y(last.v)} r={3.5} className="wl-dot" />
        {h && <circle cx={x(h.t)} cy={y(h.v)} r={4} className="wl-dot" />}
        <rect x={m.l} y={m.t} width={W - m.l - m.r} height={H - m.t - m.b} fill="transparent" onPointerMove={move} onPointerLeave={() => setHover(null)} />
      </svg>
      {h && (
        <div className="wl-tip" style={{ left: x(h.t) + 150 > W ? x(h.t) - 140 : x(h.t) + 10, top: Math.max(0, y(h.v) - 44) }}>
          <span>周收盘 {ymd(h.d)}</span>{px(h.v)} 元
        </div>
      )}
    </div>
  );
}

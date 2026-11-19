import { useEffect, useRef, useState, type PointerEvent, type RefObject } from "react";
import type { SectorChart } from "../../api/client";
import { linear, niceTicks } from "../watchlist/watchlist-format";
import { formatValue, listPeriods, periodLabel } from "./sector-monitor-format";

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

/**
 * Purpose: one 行业监控 chart: every line on a shared period axis (company lines in the palette, the sector index or
 * 全部 dashed), a zero line when the range crosses 0, a legend, and a hover readout of every line at that period.
 * Contract: a chart without points draws a note; a line missing a period leaves a gap; at most 7 lines are coloured
 * (c1..c6, then ink); clicking a legend entry highlights that line and fades the others (click again to clear);
 * chart.invert draws the y axis upside down (ranks: 1 at the top).
 */
export function SectorChartCard({ chart, index }: { chart: SectorChart; index: string }) {
  const [ref, W] = useBoxWidth();
  const [hover, setHover] = useState<number | null>(null);
  const [focus, setFocus] = useState<string | null>(null);
  const periods = listPeriods(chart);
  const vs = chart.lines.flatMap((l) => l.points.map((p) => p[1]));
  const head = <header><span className="mc-name">{chart.title}</span><span className="mc-month">{chart.unit}</span></header>;
  if (periods.length < 2 || !vs.length) return <article className="mc-card sm-card" data-chart={chart.key}>{head}<div className="mc-chart note" ref={ref}>暂无数据</div></article>;
  const H = 170, m = { l: 40, r: 10, t: 8, b: 18 };
  const lo0 = Math.min(...vs), hi0 = Math.max(...vs), pad = (hi0 - lo0) * 0.08 || 1;
  const ticks = niceTicks(lo0 - pad, hi0 + pad, 3);
  const lo = Math.min(ticks[0], lo0), hi = Math.max(ticks[ticks.length - 1], hi0);
  const at = new Map(periods.map((p, i) => [p, i]));
  const x = linear(0, periods.length - 1, m.l, W - m.r);
  const y = chart.invert ? linear(lo, hi, m.t, H - m.b) : linear(lo, hi, H - m.b, m.t);
  const dashed = (label: string) => label === index || label === "全部";
  const colour = (k: number, label: string) => (dashed(label) ? "var(--ink)" : `var(--c${(k % 6) + 1})`);
  const path = (pts: [string, number][]) => {
    let out = "", prev = -2;
    for (const [p, v] of pts) {
      const i = at.get(p) ?? 0;
      out += `${i === prev + 1 ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
      prev = i;
    }
    return out;
  };
  const step = Math.max(1, Math.ceil(periods.length / 6));
  const move = (ev: PointerEvent<SVGRectElement>) => {
    const t = (ev.clientX - ev.currentTarget.getBoundingClientRect().left) / (W - m.l - m.r);
    setHover(Math.max(0, Math.min(periods.length - 1, Math.round(t * (periods.length - 1)))));
  };
  const hp = hover == null ? null : periods[hover];
  return (
    <article className="mc-card sm-card" data-chart={chart.key}>
      {head}
      <div className="mc-chart" ref={ref}>
        <svg width={W} height={H} role="img" aria-label={chart.title}>
          {ticks.map((t) => <g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} className="wl-grid" /><text x={m.l - 5} y={y(t) + 4} textAnchor="end" className="wl-ax">{t}</text></g>)}
          {lo < 0 && hi > 0 && <line x1={m.l} x2={W - m.r} y1={y(0)} y2={y(0)} className="mc-ref" />}
          {periods.map((p, i) => (i % step === 0 ? <text key={p} x={x(i)} y={H - 4} textAnchor="middle" className="wl-ax">{periodLabel(p)}</text> : null))}
          {chart.lines.map((l, k) => <path key={l.label} d={path(l.points)} className={`sm-line ${focus && focus !== l.label ? "faded" : ""} ${focus === l.label ? "focus" : ""}`} style={{ stroke: colour(k, l.label) }} strokeDasharray={dashed(l.label) ? "4 3" : undefined} />)}
          {hover != null && <line x1={x(hover)} x2={x(hover)} y1={m.t} y2={H - m.b} className="fm-cursor" />}
          <rect x={m.l} y={m.t} width={W - m.l - m.r} height={H - m.t - m.b} fill="transparent" onPointerMove={move} onPointerLeave={() => setHover(null)} />
        </svg>
        {hp != null && (
          <div className="wl-tip sm-tip" style={{ left: x(hover ?? 0) + 170 > W ? x(hover ?? 0) - 160 : x(hover ?? 0) + 8, top: 4 }}>
            <div>{periodLabel(hp)}</div>
            {chart.lines.map((l) => { const v = l.points.find((p) => p[0] === hp); return v ? <div key={l.label}>{l.label} <b>{formatValue(v[1], chart.unit)}</b></div> : null; })}
          </div>
        )}
      </div>
      <div className="sm-legend">{chart.lines.map((l, k) => (
        <button type="button" key={l.label} className={focus === l.label ? "on" : ""} aria-pressed={focus === l.label} onClick={() => setFocus(focus === l.label ? null : l.label)}>
          <i style={{ background: colour(k, l.label) }} />{l.label}
        </button>
      ))}</div>
    </article>
  );
}

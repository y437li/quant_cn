import type { RatesFxMonitor } from "../../api/client";
import { linear, niceTicks } from "../watchlist/watchlist-format";

const W = 520, H = 190, M = { l: 44, r: 14, t: 10, b: 22 };
const CLS = ["rf-now", "rf-m1", "rf-y1"];

/**
 * Purpose: the government yield curve today, a month and a year earlier: one line per snapshot over evenly spaced
 * tenors, with a legend of the snapshot dates under the chart.
 * Contract: no tenors or no snapshots draws a note; null points break the line; every point is inside the y range.
 */
export function CurveChart({ curve }: { curve: RatesFxMonitor["curve"] }) {
  const { tenors, points } = curve;
  if (!tenors.length || !points.length) return <div className="mc-chart note">没有曲线数据</div>;
  const vs = points.flatMap((p) => p.values.filter((v): v is number => v != null));
  const ticks = niceTicks(Math.min(...vs) - 0.05, Math.max(...vs) + 0.05, 5);
  const lo = Math.min(ticks[0], ...vs), hi = Math.max(ticks[ticks.length - 1], ...vs);
  const x = linear(0, tenors.length - 1, M.l, W - M.r);
  const y = linear(lo, hi, H - M.b, M.t);
  return (
    <div className="mc-chart rf-curve">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="国债收益率曲线">
        {ticks.filter((t) => t >= lo && t <= hi).map((t) => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} className="wl-grid" /><text x={M.l - 5} y={y(t) + 4} textAnchor="end" className="wl-ax">{t.toFixed(2)}%</text></g>)}
        {tenors.map((t, i) => <text key={t} x={x(i)} y={H - 6} textAnchor="middle" className="wl-ax">{t}</text>)}
        {points.map((p, k) => {
          const d = p.values.map((v, i) => (v == null ? "" : `${i && p.values[i - 1] != null ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`)).join("");
          return (
            <g key={p.label} className={CLS[k] ?? "rf-m1"}>
              <path d={d} className="rf-line" />
            </g>
          );
        })}
      </svg>
      <div className="rf-legend">{points.map((p, k) => <span key={p.label} className={CLS[k] ?? "rf-m1"}><i />{p.label} {p.date.slice(0, 4)}-{p.date.slice(4, 6)}-{p.date.slice(6)}</span>)}</div>
    </div>
  );
}

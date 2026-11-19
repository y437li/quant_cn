import type { BuybackSection } from "../../api/client";
import { linear, niceTicks } from "../watchlist/watchlist-format";

const W = 640, H = 170, M = { l: 44, r: 10, t: 10, b: 22 };

/**
 * Purpose: new programmes per announcement month: one bar per month (planned high, 亿元), the 专项贷款 part darker;
 * a hover title gives count, amount and loans.
 * Contract: no months draws a note; year labels under each January and under the first month.
 */
export function MonthChart({ months }: { months: BuybackSection["months"] }) {
  if (!months.length) return <div className="mc-chart note">没有按月数据</div>;
  const top = Math.max(...months.map((m) => m.high_yi), 1);
  const ticks = niceTicks(0, top, 4);
  const hi = Math.max(ticks[ticks.length - 1], top);
  const step = (W - M.l - M.r) / months.length;
  const y = linear(0, hi, H - M.b, M.t);
  return (
    <div className="mc-chart bb-months">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="每月新公告金额">
        {ticks.map((t) => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} className="wl-grid" /><text x={M.l - 5} y={y(t) + 4} textAnchor="end" className="wl-ax">{t}</text></g>)}
        {months.map((m, i) => {
          const x = M.l + i * step + step * 0.15, w = step * 0.7;
          const loan = Math.min(m.loan_yi, m.high_yi);
          return (
            <g key={m.month}>
              <title>{`${m.month.slice(0, 4)}-${m.month.slice(4)}：${m.count} 个，计划上限 ${m.high_yi.toFixed(1)} 亿；专项贷款 ${m.loan_count} 个 ${m.loan_yi.toFixed(1)} 亿`}</title>
              <rect x={x} width={w} y={y(m.high_yi)} height={y(0) - y(m.high_yi)} className="bb-bar" />
              {loan > 0 && <rect x={x} width={w} y={y(loan)} height={y(0) - y(loan)} className="bb-bar loan" />}
              {(i === 0 || m.month.endsWith("01")) && <text x={x} y={H - 6} className="wl-ax">{m.month.slice(0, 4)}</text>}
            </g>
          );
        })}
      </svg>
      <div className="rf-legend"><span><i className="bb-key" />计划上限（亿元）</span><span><i className="bb-key loan" />其中专项贷款</span></div>
    </div>
  );
}

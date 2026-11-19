import { useEffect, useState } from "react";
import { api, type Opportunities, type OpportunityRow } from "../../api/client";
import { RULE_LABEL, formatSignedPct, formatValuation, opportunityHeadline, rowGroup } from "./opportunities-format";

const GROUP_LABEL = { new: "新入选", stay: "留在清单", near: "差一条" } as const;

/**
 * Purpose: the 机会清单 page at #opportunities (plan 21 ph5): the daily list — new names first, then the ones that stayed,
 * then near-misses with the missing rule — each with the 散户温度计 reading, profit growth, valuation against its own
 * median, order-flow streaks, chip cost band and the style-fit check; the names that dropped off; the rule legend.
 * Contract: read-only display of GET /api/opportunities; no document → empty state with the command to run.
 */
export function OpportunitiesPage() {
  const [doc, setDoc] = useState<Opportunities | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.getOpportunities().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page" data-empty="opportunities"><p className="wl-empty">机会清单没有加载出来：{error}。先运行 <code>make opportunity-list</code>。</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  const r = doc.rules;
  return (
    <div className="wl-page mc-page" data-page="opportunities">
      <div className="wl-head"><h2>机会清单</h2><p>{opportunityHeadline(doc)}</p></div>
      <section className="wl-section">
        <div className="fm-scroll">
          <table className="fm-table op-table">
            <thead><tr><th>分组</th><th>股票</th><th>温度计</th><th>利润同比 / 环比</th><th>估值 / {r.valuation_years} 年中位</th><th>大单周数</th><th>获利盘</th><th>流通市值</th><th>缺</th></tr></thead>
            <tbody>
              {doc.rows.map((x) => <OpportunityLine key={x.code} r={x} field={r.valuation_field} />)}
            </tbody>
          </table>
        </div>
        {!doc.rows.length && <p className="wl-empty">今天没有股票满足全部条件，也没有只差一条的。</p>}
      </section>
      {doc.dropped.length > 0 && <p className="wl-note">今天移出：{doc.dropped.map((d) => d.name ?? d.code).join("、")}</p>}
      <p className="wl-note">
        条件：流通市值 ≥ {r.min_circ_mv} 亿；散户温度计连续 3 次 ≤ 0.3（散户离场，必须满足）；近 4 周至少 {r.inflow_weeks} 周大单净流入；
        单季利润同比 ≥ {Math.round(r.np_yoy_min * 100)}% 且环比不降；{r.valuation_field.toUpperCase()} 低于自身 {r.valuation_years} 年中位；
        按 {Math.round(r.fit_weight * 100)}% 仓位加入不加重持仓最大的 {r.fit_styles} 个风格敞口。散户过热（≥ 0.9）的股票不会出现；已持有的股票不列。
      </p>
    </div>
  );
}

function OpportunityLine({ r, field }: { r: OpportunityRow; field: string }) {
  const g = rowGroup(r);
  return (
    <tr data-code={r.code} data-group={g} className={`op-${g}`}>
      <td>{GROUP_LABEL[g]}</td>
      <td><a href={`#co=${encodeURIComponent(r.code)}`}>{r.name ?? r.code}</a> <span className="wl-code">{r.code}</span></td>
      <td title={`连续 ${r.lo_streak ?? 0} 次 ≤ 0.3；预计户数变化 ${formatSignedPct(r.exp_change)}`}>{r.pct == null ? "—" : r.pct.toFixed(2)}</td>
      <td>{formatSignedPct(r.np_yoy)} / {formatSignedPct(r.np_qoq)}</td>
      <td>{formatValuation(r, field)}</td>
      <td>{r.lg_weeks_pos_4w == null ? "—" : `${r.lg_weeks_pos_4w}/4`}</td>
      <td title={`现价相对 15% / 85% 成本线 ${formatSignedPct(r.cost_lo_gap)} / ${formatSignedPct(r.cost_hi_gap)}`}>{r.winner_rate == null ? "—" : `${r.winner_rate.toFixed(0)}%`}</td>
      <td>{r.circ_mv == null ? "—" : `${Math.round(r.circ_mv)} 亿`}</td>
      <td>{r.missing.map((m) => RULE_LABEL[m] ?? m).join("、") || "—"}</td>
    </tr>
  );
}

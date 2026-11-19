import type { HoldingPosition, PositionReview } from "../../api/client";
import { ConditionChips } from "../conditions/condition-chips";
import { CHIP_COLUMNS, GAUGE_BANDS, gaugeBadge, gaugeBand, gaugeStreak, metricText } from "../conditions/condition-format";
import { PointList } from "../watchlist/point-list";
import { ymd } from "../watchlist/watchlist-format";

/**
 * Purpose: the 持仓笔记与筹码 section of #holdings (plan 15 ph7f): per position the flags (stop, target, weight, review,
 * missing note), stop / target, the 筹码结构 and statement row, the structured conditions and the note itself.
 * Contract: read-only display of `reviews` from GET /api/holdings-risk; positions without a review are skipped.
 */
export function PositionNotes({ positions, reviews }: { positions: HoldingPosition[]; reviews: Record<string, PositionReview> }) {
  const rows = positions.filter((p) => reviews[p.code]);
  if (rows.length === 0) return null;
  return (
    <section className="wl-section" data-section="notes">
      <h3>持仓笔记与筹码 <small className="wl-code">止损、目标、仓位上限和复盘提醒；筹码与财报为当日湖内数据</small></h3>
      <div className="fm-scroll"><table className="fm-table pn-table">
        <thead><tr><th>股票</th><th>提醒</th><th>止损 / 目标</th>{CHIP_COLUMNS.map(([k, h]) => <th key={k}>{h}</th>)}</tr></thead>
        <tbody>{rows.map((p) => {
          const r = reviews[p.code];
          return (
            <tr key={p.code} data-code={p.code}>
              <td>{p.name}</td>
              <td>{r.flags.length === 0 ? <span className="flat">—</span> : r.flags.map((f) => <span key={f.kind} className={`pn-flag ${f.kind}`}>{f.message}</span>)}</td>
              <td className="num">{r.note?.stop?.toFixed(2) ?? "—"} / {r.note?.target?.toFixed(2) ?? "—"}</td>
              {CHIP_COLUMNS.map(([k]) => {
                const v = r.chips[k] ?? null;
                if (k !== "retail_gauge") return <td key={k} className="num">{metricText(k, v)}</td>;
                const [cls, label] = gaugeBand(v);
                const badge = gaugeBadge(r.chips), streak = gaugeStreak(r.chips);
                return (
                  <td key={k} className={`num rg ${cls}`} title={`散户温度计：${label}${streak ? `；${streak}` : ""}`}>
                    {metricText(k, v)}
                    {badge && <span className={`rg-badge ${badge.cls}`}>{badge.label}</span>}
                    {streak && <small className="rg-streak">{streak}</small>}
                  </td>);
              })}
            </tr>);
        })}</tbody>
      </table></div>
      <p className="rg-legend">散户温度计：{GAUGE_BANDS.map(([, cls, label]) => <span key={cls} className={`rg ${cls}`}>{label}</span>)}；≥ 0.9 标“散户过热”，连续 3 次标“散户过热·连续”（回避）；≤ 0.3 连续 3 次才算散户离场。</p>
      {rows.map((p) => {
        const r = reviews[p.code];
        if (!r.note && r.conditions.length === 0) return null;
        return (
          <details key={p.code} className="pn-note" data-note={p.code}>
            <summary>{p.name}{r.note?.reviewed ? <small className="wl-code"> 复盘于 {ymd(r.note.reviewed)}</small> : null}{r.period ? <small className="wl-code"> · 财报期 {ymd(r.period)}</small> : null}</summary>
            <ConditionChips items={r.conditions} />
            {r.note && (
              <dl>
                {r.note.thesis && <><dt>逻辑</dt><dd><PointList text={r.note.thesis} /></dd></>}
                {r.note.falsifier && <><dt>证伪</dt><dd><PointList text={r.note.falsifier} /></dd></>}
                {r.note.action && <><dt>操作</dt><dd><PointList text={r.note.action} /></dd></>}
                {r.note.watch && <><dt>要盯</dt><dd><PointList text={r.note.watch} /></dd></>}
              </dl>
            )}
          </details>);
      })}
    </section>
  );
}

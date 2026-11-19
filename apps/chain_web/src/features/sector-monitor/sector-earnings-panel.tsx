import { useEffect, useState } from "react";
import { api, type SectorEarningsRow, type SectorEarningsSignal } from "../../api/client";
import { pickRows, seasonLabel, signedPct, statusLabel } from "./sector-earnings-format";

const EXTRA = 10;

/** Purpose: one season row: sector, status, share reported, best-surprise count, pre / reaction excess, prior rally, holders. */
function SeasonRow({ r, isNew }: { r: SectorEarningsRow; isNew: boolean }) {
  return (
    <tr className={r.status === "firing" ? "se-fire" : r.status === "provisional" ? "se-prov" : ""}>
      <td>{r.name}{isNew ? <span className="se-new">新</span> : null}</td>
      <td>{statusLabel(r.status)}</td>
      <td>{`${Math.round(r.share * 100)}%`}</td>
      <td>{r.n_top}</td>
      <td>{signedPct(r.pre)}</td>
      <td>{signedPct(r.react)}</td>
      <td className={r.rally ? "se-rally" : ""}>{signedPct(r.back)}</td>
      <td>{signedPct(r.hchg)}</td>
    </tr>
  );
}

/**
 * Purpose: the 财报季信号 block of #sector-monitor (plan 35, D-172): every Shenwan L2 sector's reading for the current
 * season (firing and provisional first, then the sectors closest to firing; all on request), the past firings with what
 * followed, the record, and notes with the definition and its known misses.
 * Contract: read-only display of GET /api/sector-earnings; no document → a one-line hint with the command to run.
 */
export function SectorEarningsPanel() {
  const [doc, setDoc] = useState<SectorEarningsSignal | null>(null);
  const [missing, setMissing] = useState(false);
  const [all, setAll] = useState(false);
  const [past, setPast] = useState(false);
  useEffect(() => { api.getSectorEarnings().then(setDoc).catch(() => setMissing(true)); }, []);
  if (missing) return <p className="wl-empty" data-empty="sector-earnings">还没有财报季信号。先运行 <code>make sector-earnings-signal</code>。</p>;
  if (!doc) return null;
  const rows = all ? doc.rows : pickRows(doc.rows, EXTRA);
  const fired = doc.rows.filter((r) => r.status === "firing").length;
  const prov = doc.rows.filter((r) => r.status === "provisional").length;
  const rec = doc.record.rally;
  const t = doc.thresholds;
  return (
    <div className="se-panel" data-panel="sector-earnings">
      <p className="se-summary">
        {seasonLabel(doc.season)} 财报季：{fired ? `${fired} 个行业触发` : "没有行业触发"}{prov ? `，${prov} 个临时读数` : ""}。
        {rec && rec.n ? ` 历史上行业大涨后触发 ${rec.n} 次，之后 60 天平均 ${signedPct(rec.fwd60)}、120 天 ${signedPct(rec.fwd120)}。` : ""}
      </p>
      <div className="sm-table-wrap">
        <table className="fm-table se-table">
          <thead><tr><th>行业</th><th>状态</th><th>已披露</th><th>超预期最好</th><th>披露前60天</th><th>披露当天</th><th>此前120天</th><th>股东户数</th></tr></thead>
          <tbody>{rows.map((r) => <SeasonRow key={r.code} r={r} isNew={doc.new_flags.includes(r.code)} />)}</tbody>
        </table>
      </div>
      <div className="se-actions">
        <button onClick={() => setAll(!all)}>{all ? "只看接近触发的" : `显示全部 ${doc.rows.length} 个行业`}</button>
        <button onClick={() => setPast(!past)}>{past ? "收起历史触发" : `历史触发 ${doc.firings.length} 次`}</button>
      </div>
      {past && (
        <div className="sm-table-wrap">
          <table className="fm-table se-table" data-table="se-firings">
            <thead><tr><th>行业</th><th>季度</th><th>信号日</th><th>此前120天</th><th>披露前60天</th><th>披露当天</th><th>之后60天</th><th>之后120天</th></tr></thead>
            <tbody>
              {[...doc.firings].reverse().map((r) => (
                <tr key={`${r.code}-${r.end_date}`}>
                  <td>{r.name}</td><td>{seasonLabel(r.end_date)}</td><td>{r.sig_date ?? "—"}</td>
                  <td className={r.rally ? "se-rally" : ""}>{signedPct(r.back)}</td><td>{signedPct(r.pre)}</td><td>{signedPct(r.react)}</td>
                  <td>{signedPct(r.fwd60)}</td><td>{signedPct(r.fwd120)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="wl-note">
        每个申万二级行业（按季度末的成分）里，取本季业绩超预期最好的公司（全市场 SUE 前 {(10 - t.top_decile) * 10}%，至少 {t.min_events} 家）：
        披露前 60 个交易日已跑赢全市场 ≥ {t.pre_min}%，而披露当天和次日超额 ≤ {t.react_max}%，即“好消息涨不动”。
        行业里 {Math.round(t.report_share * 100)}% 的公司披露后才算触发，之前为临时读数。此前120天为行业指数相对全部二级行业平均的超额，≥ {t.rally_min}% 标为大涨。
        股东户数为成分股季度末户数变化的中位数，只作参考。已知局限：白酒 2021 年那种财报前就杀估值的顶看不到；长牛里会提前触发（通信设备 2025 年 8 月）；历史上只有约 25 次大涨后触发。
      </p>
    </div>
  );
}

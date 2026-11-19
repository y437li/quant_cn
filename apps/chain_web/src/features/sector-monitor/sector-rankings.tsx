import type { SectorRankings } from "../../api/client";
import { marketName, periodLabel, rankChange } from "./sector-monitor-format";

const NEW_SHOWN = 30; // 新品上榜 rows shown
const cls = (change: string) => (change.startsWith("↑") || change === "新" ? "up" : change.startsWith("↓") ? "down" : "");

/**
 * Purpose: the App Store 排行榜 block of a sector (plan 19 ph2): the games of the sector companies and of every A-share
 * company in the publisher map (home grossing rank with the
 * move since the previous capture, home free rank, best overseas grossing rank and market, overseas markets in the
 * top 100), the home top-grossing list with each game's company, and 新品上榜 (games released within the window, any
 * publisher, first NEW_SHOWN rows). Contract: read-only; no capture → a note.
 */
export function SectorRankingsPanel({ rankings }: { rankings: SectorRankings }) {
  const home = marketName(rankings.country);
  if (!rankings.as_of) return <p className="wl-empty">还没有 App Store 榜单数据。</p>;
  const when = `${periodLabel(rankings.as_of)}${rankings.prev ? `，对比 ${periodLabel(rankings.prev)}` : ""}`;
  return (
    <div className="sm-rank" data-block="rankings">
      <div className="sm-rank-col">
        <h4>A 股游戏公司排名 <small>{when}</small></h4>
        <div className="sm-table-wrap">
          <table className="fm-table sm-table">
            <thead><tr><th className="txt">游戏</th><th className="txt">公司</th><th>{home}畅销</th><th>变化</th><th>{home}免费</th><th>海外最佳</th><th>海外上榜</th></tr></thead>
            <tbody>
              {rankings.apps.map((a) => {
                const change = rankChange(a.rank, a.prev);
                return (
                  <tr key={a.app_id}>
                    <td className="txt">{a.name}</td><td className="txt">{a.company ?? ""}</td><td>{a.rank ?? "—"}</td>
                    <td className={cls(change)}>{change}</td><td>{a.free ?? "—"}</td>
                    <td>{a.overseas_best == null ? "—" : `${a.overseas_best}（${marketName(a.overseas_market)}）`}</td>
                    <td>{a.overseas_markets ? `${a.overseas_markets} 国` : "—"}</td>
                  </tr>
                );
              })}
              {!rankings.apps.length && <tr><td colSpan={7}>今天没有 A 股游戏公司的游戏进任何市场前 100。</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
      <div className="sm-rank-col">
        <h4>{home}畅销榜前 {rankings.top.length}</h4>
        <div className="sm-table-wrap">
          <table className="fm-table sm-table">
            <thead><tr><th>#</th><th className="txt">游戏</th><th className="txt">公司</th><th>变化</th></tr></thead>
            <tbody>
              {rankings.top.map((t) => {
                const change = rankChange(t.rank, t.prev);
                return (
                  <tr key={t.rank}>
                    <td>{t.rank}</td><td className="txt">{t.name}</td><td className="txt">{t.company ?? ""}</td><td className={cls(change)}>{change}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
            </div>
      {!!rankings.new?.length && (
        <div className="sm-rank-col sm-rank-wide">
          <h4>新品上榜 <small>近 90 天上线、今天在{home}畅销 / 免费前 100 或海外畅销前 100，共 {rankings.new.length} 款{rankings.new.length > NEW_SHOWN ? `，显示前 ${NEW_SHOWN}` : ""}</small></h4>
          <div className="sm-table-wrap">
            <table className="fm-table sm-table">
              <thead><tr><th className="txt">游戏</th><th className="txt">公司</th><th>上线</th><th>{home}畅销</th><th>{home}免费</th><th>海外最佳</th><th>海外上榜</th></tr></thead>
              <tbody>
                {rankings.new.slice(0, NEW_SHOWN).map((a) => (
                  <tr key={a.app_id}>
                    <td className="txt">{a.name}</td><td className="txt">{a.company ?? ""}</td><td>{periodLabel(a.release_date)}</td>
                    <td>{a.rank ?? "—"}</td><td>{a.free ?? "—"}</td>
                    <td>{a.overseas_best == null ? "—" : `${a.overseas_best}（${marketName(a.overseas_market)}）`}</td>
                    <td>{a.overseas_markets ? `${a.overseas_markets} 国` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

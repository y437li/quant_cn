import type { SmallCapWatch } from "../../api/client";
import { VolatilityChart } from "./volatility-chart";
import { dayLabel } from "./volatility-format";
import { SHARE_BOTTOM_REFS, STATE_LABEL, formatScTrigger, formatScValue, levelRefs, marginChartPoints, marginDepthRefs, marginShareChartPoints, orderRows, smallCapHeadline, smallPoints } from "./smallcap-format";

/**
 * Purpose: the 小盘观察 panel on #volatility (plan 30 ph2): headline, a table of every signal (realised vol, 1000−300 vol
 * gap, panic breadth, 中证1000 levels, ETF flows) with triggered rows first and red, near rows amber, and a 中证1000
 * chart with the watch levels as dashed lines; ph4 adds the 融资余额 (亿) and 融资余额 / 流通市值 (%) charts when present; ph6 draws the share weekly since 2019 with the bottom-day range as dashed lines; ph7 draws the balance weekly since 2019 with the past 去杠杆 depths below its high as dashed lines.
 * Contract: read-only display of the `smallcap` part of GET /api/volatility; null → nothing rendered.
 */
export function SmallCapPanel({ w }: { w: SmallCapWatch | null }) {
  if (!w || !w.rows.length) return null;
  const pts = smallPoints(w.history);
  const rz = marginChartPoints(w), share = marginShareChartPoints(w);
  const long = (w.margin_share_long?.length ?? 0) > 1, rzLong = (w.margin_share_long ?? []).filter((p) => p.rz != null).length > 1;
  const depthRefs = marginDepthRefs(w);
  return (
    <section className="wl-section sc-panel" data-panel="smallcap">
      <h3>小盘观察</h3>
      <p className="sc-head">{smallCapHeadline(w.rows, w.new_triggered)}{w.missing.length > 0 && ` 缺少数据：${w.missing.join("、")}。`}</p>
      <div className="sc-body">
        <div className="sc-table-wrap">
          <table className="fm-table sc-table">
            <thead><tr><th>指标</th><th>最新</th><th>3年分位</th><th>触发线</th><th>状态</th><th>说明</th></tr></thead>
            <tbody>
              {orderRows(w.rows).map((r) => (
                <tr key={r.key} className={`sc-${r.state}`} data-row={r.key}>
                  <td><span className="sc-group">{r.group}</span>{r.name}</td>
                  <td>{formatScValue(r)}</td>
                  <td>{r.pct == null ? "" : `${Math.round(r.pct * 100)}%`}</td>
                  <td>{formatScTrigger(r)}</td>
                  <td className="sc-state">{STATE_LABEL[r.state] ?? r.state}</td>
                  <td className="sc-note">{r.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <article className="mc-card sc-chart">
          <header><span className="mc-name">中证1000</span><span className="mc-month">{dayLabel(w.as_of)}</span></header>
          <VolatilityChart name="中证1000" points={pts} refs={levelRefs(w.rows)} height={190} />
        </article>
        {rz.length > 1 && (
          <article className="mc-card sc-chart" data-chart="margin">
            <header><span className="mc-name">融资余额（亿元{rzLong && "，2019 年起，周"}）</span><span className="mc-month">{dayLabel(rz[rz.length - 1].date)}</span></header>
            <VolatilityChart name="融资余额" points={rz} refs={depthRefs} height={160} format={(v) => `${(v / 1e4).toFixed(1)}万`} />
          </article>
        )}
        {share.length > 1 && (
          <article className="mc-card sc-chart" data-chart="margin-share">
            <header><span className="mc-name">融资余额 / 流通市值{long && "（2019 年起，周）"}</span><span className="mc-month">{dayLabel(share[share.length - 1].date)}</span></header>
            <VolatilityChart name="融资余额占流通市值" points={share} refs={long ? SHARE_BOTTOM_REFS : []} height={160} format={(v) => `${v.toFixed(2)}%`} />
          </article>
        )}
      </div>
      <p className="wl-note">实际波动为 20 日年化，分位按近 3 年计算；波动差 = 中证1000 − 沪深300 实际波动，低于 70% 分位为退出线。图中虚线为你设的中证1000 点位。融资余额：两融数据次日早上公布，比行情晚一天；缺交易所的日子不画。融资余额图的虚线是从 2019 年以来高点按历次去杠杆幅度（2015 −60%、2018 −33%、2022 −17%、2024 −13%）往下画的位置；去杠杆深度一行的节奏看 10 日平滑后的每日变化：在 ±20 亿以内为走平，下降中再看加速度的正负。企稳 = 融资余额距 250 日高点 ≤ −10% 且 5 日变化转正（历史 12 次，60 天平均 +7.4%，今年 8、9 月两次失败）。融资余额 / 流通市值图的两条虚线 1.94% 和 2.54% 是 2019 年以来六次中证1000 见底当天的区间；这个比值的最低点通常在价格见底后 2–6 周才出现，不能用来抄底。</p>
    </section>
  );
}

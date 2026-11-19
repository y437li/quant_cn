import { useEffect, useState } from "react";
import { api, type MarginPanel } from "../../api/client";
import { FuturesChart } from "../futures/futures-chart";
import { ymdText } from "../futures/futures-format";
import { firstLiquidation, marginHeadline, marginWarnings } from "./margin-format";

/**
 * Purpose: 融资融券 tab of the company dossier (plan 15 ph7m): headline, warnings, financing and short balance charts
 * over ~6 months, and the forced-liquidation ladder (debt forced if the price falls by 10–40%).
 * Contract: loads GET /api/margin/{code}; a 404 shows "不是两融标的或没有数据".
 */
export function MarginTab({ code }: { code: string }) {
  const [m, setM] = useState<MarginPanel | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { setM(null); setError(null); api.getMargin(code).then(setM).catch((e) => setError(e.message)); }, [code]);
  if (error) return <p className="empty" data-margin-empty="1">不是两融标的或没有数据。</p>;
  if (!m) return <p className="empty">正在加载…</p>;
  const pts = (k: "rz" | "rq") => m.daily.filter((x) => x[k] != null).map((x) => ({ x: x.d, v: x[k] as number }));
  return (
    <div className="mg-tab" data-margin={m.code}>
      <p className="mg-head">{marginHeadline(m)} <small className="wl-code">数据截至 {ymdText(m.as_of)}</small></p>
      {marginWarnings(m).map((w) => <p key={w} className="mg-warn">{w}</p>)}
      <figure><figcaption>融资余额（亿）</figcaption>
        <FuturesChart label="融资余额" points={pts("rz")} fmt={(v) => v.toFixed(1)} xfmt={(d) => ymdText(d).slice(5)} height={140} /></figure>
      <figure><figcaption>融券余额（万元）· 近 20 日融券卖出 {m.rq_sell_20d_wan ?? "—"} 万股</figcaption>
        <FuturesChart label="融券余额" points={pts("rq")} fmt={(v) => v.toFixed(0)} xfmt={(d) => ymdText(d).slice(5)} height={120} /></figure>
      <h4>强平阶梯 <small className="wl-code">{firstLiquidation(m)}</small></h4>
      <table className="fm-table mg-ladder">
        <thead><tr><th>再跌</th><th>价格</th><th>被强平融资（亿）</th><th>占全部融资</th></tr></thead>
        <tbody>{m.ladder.forced.map((f) => (
          <tr key={f.fall_pct} className={f.share > 0 ? "hit" : ""}><td>{f.fall_pct}%</td><td>{f.price.toFixed(2)}</td><td>{f.debt_yi?.toFixed(2) ?? "—"}</td><td>{Math.round(f.share * 100)}%</td></tr>
        ))}</tbody>
      </table>
      <p className="note">按"先买先还"估算每笔融资的买入价，平仓价 = 买入价 × 1.3 ÷（1 + 保证金比例）。账户之间保证金和担保品不同，只看大致位置。研究显示：融资 20 日快速增加、融券占比高的股票之后偏弱（2024 年后变弱）。</p>
    </div>
  );
}

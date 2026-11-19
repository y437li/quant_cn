import { useEffect, useState } from "react";
import { api, type EtfProxy } from "../../api/client";
import { FuturesChart } from "../futures/futures-chart";
import { ymdText } from "../futures/futures-format";
import { STATUS_ZH, styleHeadline, stylePoints } from "./etf-style-format";

/**
 * Purpose: 风格 ETF 资金强度 (plan 15 ph7g): one card per style (银行, 红利) with status, z, 20-day flow vs AUM and the
 * weekly z history with the 1.5 过热 line implied by the axis.
 * Contract: loads GET /api/etf-proxy; renders nothing without styles.
 */
export function EtfStylePanel() {
  const [doc, setDoc] = useState<EtfProxy | null>(null);
  useEffect(() => { api.getEtfProxy().then(setDoc).catch(() => setDoc(null)); }, []);
  const styles = doc?.styles ?? [];
  if (!styles.length) return null;
  return (
    <section className="wl-section" data-section="styles">
      <h3>风格 ETF 资金强度 <small className="wl-code">截至 {ymdText(styles[0].as_of)}</small></h3>
      <div className="es-grid">
        {styles.map((s) => (
          <article key={s.key} className={`es-card ${s.status}`} data-style={s.key}>
            <header><b>{s.name} ETF</b><span className={`es-status ${s.status}`}>{STATUS_ZH[s.status]}</span></header>
            <p className="es-line">{styleHeadline(s)}</p>
            <p className="note">{s.n_etf} 只 ETF，规模 {s.aum == null ? "—" : `${s.aum.toFixed(0)} 亿`}{s.status === "hot" && s.hot_since && `；${ymdText(s.hot_since)} 起过热`}</p>
            <FuturesChart label={`${s.name} ETF 资金强度 z`} points={stylePoints(s)} fmt={(v) => v.toFixed(1)} xfmt={(d) => ymdText(d).slice(0, 7)} height={150} />
          </article>
        ))}
      </div>
      <p className="wl-note">z = 近 20 个交易日净流入占规模的比例，相对此前 250 个交易日的标准分。z ≥ 1.5 记为过热（2022-08 至 2026-11，银行指数在过热后 60 日平均 −3.0%，其余时间 +2.7%），回落到 z ≤ 0 记为降温。风格 ETF 不计入上面的国家队统计。</p>
    </section>
  );
}

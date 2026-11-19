import { useEffect, useState } from "react";
import { api, type MacroMonitor, type MacroSeries } from "../../api/client";
import { MacroChart } from "./macro-chart";
import { formatValue, groupSeries, isExtreme, macroHeadline, monthLabel } from "./macro-format";

/** Purpose: one card per line: name, latest print and month, change vs previous, 5-year percentile, new marker, chart. */
function MacroCard({ s }: { s: MacroSeries }) {
  const cls = s.change == null || s.change === 0 ? "" : s.change > 0 ? "up" : "down";
  return (
    <article className={`mc-card ${s.new_print ? "new" : ""}`} data-series={s.key}>
      <header>
        <span className="mc-name">{s.name}{s.new_print && <span className="mc-new" title="上次生成后的新数据">新</span>}</span>
        <span className="mc-month">{monthLabel(s.month)}</span>
      </header>
      <div className="mc-figs">
        <b>{formatValue(s, s.value)}</b>
        <span className={cls}>{formatValue(s, s.change, true)}</span>
        <span className={`mc-pct ${isExtreme(s.pct_5y) ? "ext" : ""}`} title="最新值在近 5 年（60 个月）中的分位">5年分位 {s.pct_5y == null ? "—" : `${Math.round(s.pct_5y * 100)}%`}</span>
      </div>
      <MacroChart s={s} />
    </article>
  );
}

/**
 * Purpose: the 宏观监测 page at #macro (plan 15 ph7h, D-143): headline, then per group (价格 / 景气 / 货币 / 社融) a grid of cards
 * with the latest print and a 5-year chart; notes on sources and units.
 * Contract: read-only display of GET /api/macro; empty document → empty state with the command to run.
 */
export function MacroPage() {
  const [doc, setDoc] = useState<MacroMonitor | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.getMacro().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page"><p className="wl-empty">宏观数据没有加载出来：{error}</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  if (!doc.series.length) return <div className="wl-page" data-empty="macro"><p className="wl-empty">还没有宏观数据。先运行 <code>make macro-monitor</code>。</p></div>;
  return (
    <div className="wl-page mc-page" data-page="macro">
      <div className="wl-head">
        <h2>宏观监测</h2>
        <p>{macroHeadline(doc.series, doc.new_prints)}{doc.missing.length > 0 && ` 缺少数据表：${doc.missing.join("、")}。`}</p>
      </div>
      {groupSeries(doc.series).map(([g, rows]) => (
        <section className="wl-section" key={g}>
          <h3>{g}</h3>
          <div className="mc-grid">{rows.map((s) => <MacroCard key={s.key} s={s} />)}</div>
        </section>
      ))}
      <p className="wl-note">数据：Tushare（国家统计局 CPI / PPI / PMI，人民银行 M1 / M2 / 社融），每个工作日 18:30 刷新。社融单位亿元；存量同比和同比多增由存量与去年同月计算。分位为最新值在近 60 个月中的位置，≤10% 或 ≥90% 标橙。PMI 图中虚线为 50 荣枯线，其余为 0 线。</p>
    </div>
  );
}

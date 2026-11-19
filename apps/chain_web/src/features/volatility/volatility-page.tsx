import { useEffect, useState } from "react";
import { api, type VolatilityMonitor, type VolLine } from "../../api/client";
import { SmallCapPanel } from "./smallcap-panel";
import { VolatilityChart } from "./volatility-chart";
import { alertText, dayLabel, formatVol, groupLines, refLevel, volHeadline } from "./volatility-format";

/** Purpose: one card per index: name, latest value and date, one-day change, 1-year percentile and range, alert rules, chart. */
function VolCard({ s, alerting }: { s: VolLine; alerting: boolean }) {
  const cls = s.chg == null || s.chg === 0 ? "" : s.chg > 0 ? "up" : "down";
  const rules = alertText(s);
  return (
    <article className={`mc-card ${alerting ? "new" : ""}`} data-series={s.key}>
      <header>
        <span className="mc-name">{s.name}{alerting && <span className="mc-new" title="触发提醒">警</span>}</span>
        <span className="mc-month">{dayLabel(s.date)}</span>
      </header>
      <div className="mc-figs">
        <b>{formatVol(s.value)}</b>
        <span className={cls}>{formatVol(s.chg, true)}</span>
        <span className={`mc-pct ${s.pct != null && s.pct >= 0.9 ? "ext" : ""}`} title={`最新值在近 ${s.n_obs} 个交易日中的分位`}>1年分位 {s.pct == null ? "—" : `${Math.round(s.pct * 100)}%`}</span>
      </div>
      <div className="mc-month">区间 {formatVol(s.low)}–{formatVol(s.high)}，中位 {formatVol(s.median)}{rules && `；提醒 ${rules}`}{s.quality_flag !== "ok" && `；${s.quality_flag}`}</div>
      <VolatilityChart name={s.name} points={s.history} refs={[refLevel(s)]} />
    </article>
  );
}

/**
 * Purpose: the 波动率监测 page at #volatility (plan 03 ph6, D-152): headline with alerts, then per group (美国 / A股) a grid of
 * cards with the latest value and a one-year chart; the 小盘观察 panel (plan 30 ph2) above them; notes on method and sources.
 * Contract: read-only display of GET /api/volatility; empty document → empty state with the command to run.
 */
export function VolatilityPage() {
  const [doc, setDoc] = useState<VolatilityMonitor | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.getVolatility().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page"><p className="wl-empty">波动率数据没有加载出来：{error}</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  if (!doc.lines.length) return <div className="wl-page" data-empty="volatility"><p className="wl-empty">还没有波动率数据。先运行 <code>make volatility-monitor</code>。</p></div>;
  const alerting = new Set(doc.flags.map((f) => f.key.split(":")[0]));
  return (
    <div className="wl-page mc-page" data-page="volatility">
      <div className="wl-head">
        <h2>波动率监测</h2>
        <p>{volHeadline(doc.lines, doc.flags)}{doc.missing.length > 0 && ` 缺少数据：${doc.missing.join("、")}。`}</p>
      </div>
      <SmallCapPanel w={doc.smallcap ?? null} />
      {groupLines(doc.lines).map(([g, rows]) => (
        <section className="wl-section" key={g}>
          <h3>{g}</h3>
          <div className="mc-grid">{rows.map((s) => <VolCard key={s.key} s={s} alerting={alerting.has(s.key)} />)}</div>
        </section>
      ))}
      <p className="wl-note">美国 VIX：CBOE 官网收盘（美东日期）。A 股：用上交所 / 中金所期权日收盘按 CBOE 方法计算的 30 天隐含波动率（交易日时钟），截至 {dayLabel(doc.as_of)}。分位为最新值在近 {doc.window} 个交易日中的位置，≥90% 标橙；图中虚线为提醒线，没有提醒线时为中位数。</p>
    </div>
  );
}

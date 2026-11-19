import { useEffect, useState } from "react";
import { api, type RatesFxMonitor, type RatesFxRow } from "../../api/client";
import { dayLabel } from "../volatility/volatility-format";
import { VolatilityChart } from "../volatility/volatility-chart";
import { CurveChart } from "./curve-chart";
import { CHART_KEYS, changeClass, formatChange, formatLevel, groupRows, ratesHeadline } from "./rates-fx-format";

const HORIZONS = [["1w", "1周"], ["1m", "1月"], ["3m", "3月"], ["1y", "1年"]] as const;

/** Purpose: the table of one group: level, changes, 5-year percentile, 1-year range, alerts. Contract: alerting rows are marked. */
function RatesTable({ rows }: { rows: RatesFxRow[] }) {
  return (
    <div className="fm-scroll">
      <table className="fm-table rf-table">
        <thead><tr><th>项目</th><th>最新</th>{HORIZONS.map(([, l]) => <th key={l}>{l}</th>)}<th title="最新值在近 5 年中的分位">5年分位</th><th>1年区间</th><th>日期</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} data-row={r.key} className={r.alerts.length ? "rf-alert" : ""} title={r.alerts.join("；")}>
              <td>{r.name}{r.alerts.length > 0 && <span className="mc-new" title={r.alerts.join("；")}>警</span>}</td>
              <td>{formatLevel(r.value, r.unit)}</td>
              {HORIZONS.map(([h]) => <td key={h} className={changeClass(r.chg[h])}>{formatChange(r.chg[h], r.unit)}</td>)}
              <td className={r.pct != null && (r.pct >= 0.9 || r.pct <= 0.1) ? "rf-ext" : ""}>{r.pct == null ? "—" : `${Math.round(r.pct * 100)}%`}</td>
              <td>{formatLevel(r.low_1y, r.unit)} – {formatLevel(r.high_1y, r.unit)}</td>
              <td className={r.stale ? "rf-stale" : ""}>{dayLabel(r.date)}{r.stale && " 旧"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Purpose: one chart card: name, latest level, five-year chart. Contract: the hover value uses the row's unit. */
function RatesCard({ r }: { r: RatesFxRow }) {
  return (
    <article className={`mc-card ${r.alerts.length ? "new" : ""}`} data-series={r.key}>
      <header><span className="mc-name">{r.name}</span><span className="mc-month">{dayLabel(r.date)}</span></header>
      <div className="mc-figs"><b>{formatLevel(r.value, r.unit)}</b><span className={changeClass(r.chg["1w"])}>一周 {formatChange(r.chg["1w"], r.unit)}</span></div>
      <VolatilityChart name={r.name} points={r.history} refs={[]} format={(v) => formatLevel(v, r.unit)} />
    </article>
  );
}

/**
 * Purpose: the 利率汇率 page at #rates (plan 34, D-171): a 债市 / 汇率 switch; per group a headline with alerts, the
 * table, and charts (债市 also the government curve today / 1 month / 1 year ago); notes on sources.
 * Contract: read-only display of GET /api/rates-fx; no document → empty state with the command to run.
 */
export function RatesFxPage() {
  const [doc, setDoc] = useState<RatesFxMonitor | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [group, setGroup] = useState("债市");
  useEffect(() => { api.getRatesFx().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page" data-empty="rates"><p className="wl-empty">利率汇率数据没有加载出来：{error}。先运行 <code>make rates-fx-monitor</code>。</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  const rows = groupRows(doc.rows, group);
  const by = new Map(rows.map((r) => [r.key, r]));
  const charts = (CHART_KEYS[group] ?? []).map((k) => by.get(k)).filter((r): r is RatesFxRow => !!r);
  return (
    <div className="wl-page mc-page" data-page="rates">
      <div className="wl-head">
        <h2>利率汇率</h2>
        <div className="seg">{doc.groups.map((g) => <button key={g} type="button" data-group={g} className={`chip ${g === group ? "on" : ""}`} onClick={() => setGroup(g)}>{g}</button>)}</div>
        <p>{ratesHeadline(doc.rows, doc.flags, group)}{doc.missing.length > 0 && ` 缺少数据：${doc.missing.join("、")}。`}</p>
      </div>
      <section className="wl-section"><RatesTable rows={rows} /></section>
      {group === "债市" && <section className="wl-section"><h3>国债收益率曲线</h3><CurveChart curve={doc.curve} /></section>}
      <section className="wl-section">
        <h3>走势（近 5 年；近 1 年为日数据，更早为周数据）</h3>
        <div className="mc-grid">{charts.map((r) => <RatesCard key={r.key} r={r} />)}</div>
      </section>
      <p className="wl-note">债市：中债收益率曲线（国债、AAA 商业银行普通债、AAA 中短期票据，AkShare），SHIBOR；股债性价比 = 沪深300 成分股盈利收益率（Σ市值 / PE TTM ÷ Σ市值，亏损股只计市值）− 10 年国债。汇率：FXCM 日收盘（纽约 17:00，买卖价中值），外管局人民币中间价，美国国债收益率（东方财富）。分位为最新值在近 5 年中的位置，≥90% 或 ≤10% 标色；变动：收益率与利差为 bp，汇率为 %。截至 {dayLabel(doc.as_of)}。</p>
    </div>
  );
}

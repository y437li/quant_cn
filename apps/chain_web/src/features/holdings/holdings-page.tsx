import { useEffect, useState } from "react";
import { api, type HoldingsRisk } from "../../api/client";
import { factorName, signedPct, volPct } from "../factors/factor-format";
import { listAlerts } from "../conditions/condition-format";
import { expo, holdingsHeadline, listIndustries, listStyles, pnlClass, pnlPct, share, yuan } from "./holdings-format";
import { PositionNotes } from "./position-notes";

/** Purpose: background of an exposure cell, blue for positive and amber for negative, opacity by |v| up to 2. */
const heat = (v: number | null): string | undefined =>
  v == null || Math.abs(v) < 0.25 ? undefined : `color-mix(in srgb, var(${v > 0 ? "--c1" : "--c3"}) ${Math.round(Math.min(Math.abs(v), 2) / 2 * 45)}%, transparent)`;

/** Purpose: a horizontal bar of a signed exposure around 0, scaled to ±2. Contract: null draws nothing. */
function ExpoBar({ v }: { v: number | null }) {
  if (v == null) return <span className="hr-bar" />;
  const w = Math.min(Math.abs(v), 2) / 2 * 50;
  return <span className="hr-bar"><i className={v >= 0 ? "pos" : "neg"} style={{ width: `${w}%`, left: v >= 0 ? "50%" : `${50 - w}%` }} /></span>;
}

/**
 * Purpose: the 持仓 page at #holdings (plan 15 phase 7d, D-132): headline, risk tiles, positions with P&L and share of
 * risk, style exposures vs the benchmark, industry weights, model correlations, notes.
 * Contract: read-only display of GET /api/holdings-risk; empty document → empty state with the file to edit.
 */
export function HoldingsPage() {
  const [doc, setDoc] = useState<HoldingsRisk | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.getHoldingsRisk().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page"><p className="wl-empty">持仓数据没有加载出来：{error}</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  if (!doc.as_of) return <div className="wl-page" data-empty="holdings"><p className="wl-empty">还没有持仓数据。编辑 <code>config/local.positions.yaml</code>，再运行 <code>make holdings-risk</code>。</p></div>;
  const r = doc.risk;
  const names = Object.fromEntries(doc.positions.map((p) => [p.code, p.name]));
  const rows = [...doc.positions].sort((a, b) => (b.contrib ?? -1) - (a.contrib ?? -1));
  const alerts = listAlerts(doc.reviews ?? {}, names);
  return (
    <div className="wl-page hr-page" data-page="holdings">
      <div className="wl-head"><h2>持仓</h2><p>{holdingsHeadline(doc)}</p></div>
      {alerts.length > 0 && <ul className="pn-alerts" data-alerts={alerts.length}>{alerts.map((a) => <li key={a}>{a}</li>)}</ul>}
      <section className="hr-tiles">
        {[["组合波动", r.total], ["因子部分", r.factor], ["个股部分", r.specific], ["跟踪误差", r.active_total]].map(([k, v]) => (
          <div key={k as string} className="wl-card"><span className="wl-k">{k as string}（年化）</span><span className="wl-big">{volPct(v as number | null)}</span></div>
        ))}
      </section>
      <section className="wl-section">
        <h3>持仓明细 <small className="wl-code">按风险贡献排序</small></h3>
        <div className="fm-scroll"><table className="fm-table">
          <thead><tr><th>股票</th><th>股数</th><th>成本</th><th>收盘</th><th>市值</th><th>仓位</th><th>盈亏</th><th>盈亏%</th><th>自身波动</th><th>风险贡献</th></tr></thead>
          <tbody>{rows.map((p) => (
            <tr key={p.code} data-code={p.code}>
              <td>{p.name} <span className="wl-code">{p.code}</span></td><td>{p.shares ?? "—"}</td><td>{p.cost?.toFixed(3) ?? "—"}</td><td>{p.close?.toFixed(2) ?? "—"}</td>
              <td>{yuan(p.value)}</td><td>{share(p.weight)}</td><td className={pnlClass(p.pnl)}>{yuan(p.pnl)}</td><td className={p.cost != null && p.cost <= 0 ? "up" : pnlClass(p.pnl_pct)}>{pnlPct(p)}</td>
              <td>{volPct(p.vol)}</td><td>{share(p.contrib)}</td>
            </tr>))}
          </tbody>
        </table></div>
        {doc.missing.length > 0 && <p className="wl-notes">没有收盘价或模型预测、未计入风险：{doc.missing.join("、")}</p>}
      </section>
      <PositionNotes positions={rows} reviews={doc.reviews ?? {}} />
      <section className="wl-section">
        <h3>风格敞口 <small className="wl-code">相对 {doc.benchmark}，单位：标准差</small></h3>
        <div className="fm-scroll"><table className="fm-table">
          <thead><tr><th>风格</th><th>组合</th><th>相对基准</th><th className="hr-barh">−2 · 0 · +2</th><th>风险占比</th></tr></thead>
          <tbody>{listStyles(doc.factors).map((f) => (
            <tr key={f.factor}><td>{factorName(f)}</td><td>{expo(f.exposure)}</td><td>{expo(f.active)}</td><td><ExpoBar v={f.active ?? f.exposure} /></td><td>{share(f.contrib)}</td></tr>))}
          </tbody>
        </table></div>
      </section>
      {doc.stock_exposures.rows.length > 0 && (
        <section className="wl-section">
          <h3>个股因子敞口 <small className="wl-code">单位：标准差（全市场市值加权均值为 0）；蓝 = 正，橙 = 负</small></h3>
          <div className="fm-scroll"><table className="fm-table hr-expo">
            <thead><tr><th>股票</th><th>行业</th>{doc.stock_exposures.styles.map((f) => <th key={f}>{factorName({ factor: f, label: f, kind: "style" })}</th>)}</tr></thead>
            <tbody>{doc.stock_exposures.rows.map((r) => (
              <tr key={r.code}><td>{names[r.code] ?? r.code}</td><td>{r.industry || "—"}</td>
                {r.values.map((v, j) => <td key={j} style={{ background: heat(v) }}>{expo(v)}</td>)}</tr>))}
            </tbody>
          </table></div>
        </section>
      )}
      <section className="wl-section">
        <h3>行业</h3>
        <div className="fm-scroll"><table className="fm-table">
          <thead><tr><th>申万一级</th><th>权重</th><th>相对基准</th><th>风险占比</th></tr></thead>
          <tbody>{listIndustries(doc.factors).map((f) => (
            <tr key={f.factor}><td>{f.label}</td><td>{share(f.exposure)}</td><td>{f.active == null ? "—" : signedPct(f.active, 1)}</td><td>{share(f.contrib)}</td></tr>))}
          </tbody>
        </table></div>
      </section>
      {doc.correlation.codes.length > 1 && (
        <section className="wl-section">
          <h3>模型相关系数</h3>
          <div className="fm-scroll"><table className="fm-table hr-corr">
            <thead><tr><th />{doc.correlation.codes.map((c) => <th key={c}>{names[c] ?? c}</th>)}</tr></thead>
            <tbody>{doc.correlation.matrix.map((row, i) => (
              <tr key={doc.correlation.codes[i]}><td>{names[doc.correlation.codes[i]] ?? doc.correlation.codes[i]}</td>
                {row.map((v, j) => <td key={j} style={{ background: i === j ? undefined : `color-mix(in srgb, var(--c1) ${Math.round(Math.max(0, v) * 100)}%, transparent)` }}>{v.toFixed(2)}</td>)}</tr>))}
            </tbody>
          </table></div>
        </section>
      )}
      <p className="wl-notes">按 {doc.as_of} 收盘价估值，风险来自 {doc.model} 风险模型。风险贡献按欧拉分解，各股之和为 100%。持仓每天存入湖里 <code>derived.holdings_positions</code> / <code>derived.holdings_risk</code>。</p>
    </div>
  );
}

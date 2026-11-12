import { useEffect, useState } from "react";
import { api, type FactorMonitor, type MonitoredFactor } from "../../api/client";
import { ymd } from "../watchlist/watchlist-format";
import { LineChart } from "./factor-chart";
import { factorName, isAlert, monitorHeadline, moveClass, sigma, signedPct, splitFactors, toPoints, volPct } from "./factor-format";

const WINDOWS: [keyof MonitoredFactor["ret"], string][] = [["d1", "今日"], ["w1", "1周"], ["m1", "1月"], ["m3", "3月"], ["ytd", "今年"], ["y1", "1年"]];

/** Purpose: one table of factors; a click picks the factor shown in the charts. Contract: rows in the given order. */
function FactorTable({ rows, picked, pick, title }: { rows: MonitoredFactor[]; picked: string; pick: (f: string) => void; title: string }) {
  return (
    <section className="wl-section">
      <h3>{title}</h3>
      <div className="fm-scroll">
        <table className="fm-table">
          <thead><tr><th>因子</th>{WINDOWS.map(([, n]) => <th key={n}>{n}</th>)}<th title="今日收益 / 前一日预测的日波动">今日σ</th><th>预测波动</th><th>实际21日</th><th>实际63日</th><th title="实际21日 / 预测">比值</th></tr></thead>
          <tbody>
            {rows.map((f) => (
              <tr key={f.factor} className={`${f.factor === picked ? "on" : ""} ${isAlert(f) ? "alert" : ""}`} onClick={() => pick(f.factor)} data-factor={f.factor}>
                <td>{factorName(f)}</td>
                {WINDOWS.map(([k]) => <td key={k} className={moveClass(f.ret[k])}>{signedPct(f.ret[k])}</td>)}
                <td className={moveClass(f.sigma_move)}>{sigma(f.sigma_move)}</td>
                <td>{volPct(f.forecast_vol)}</td><td>{volPct(f.realized_vol_21)}</td><td>{volPct(f.realized_vol_63)}</td>
                <td>{f.vol_ratio == null ? "—" : f.vol_ratio.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/**
 * Purpose: the 因子监控 page at #factors (plan 15 phase 7c, D-132): headline, charts of the picked factor (cumulative
 * return; forecast vs 21-day realized vol), style and industry tables, data notes.
 * Contract: read-only display of GET /api/factor-monitor; empty document → empty state with the command to run.
 */
export function FactorsPage() {
  const [doc, setDoc] = useState<FactorMonitor | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [picked, setPicked] = useState("country");
  useEffect(() => { api.getFactorMonitor().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page"><p className="wl-empty">因子数据没有加载出来：{error}</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  if (!doc.factors.length) return <div className="wl-page" data-empty="factors"><p className="wl-empty">还没有因子数据。先运行 <code>make risk-model</code>，再运行 <code>make factor-monitor</code>。</p></div>;
  const f = doc.factors.find((x) => x.factor === picked) ?? doc.factors[0];
  const { styles, industries } = splitFactors(doc.factors);
  return (
    <div className="wl-page fm-page" data-page="factors">
      <div className="wl-head">
        <h2>因子监控</h2>
        <p>{monitorHeadline(doc)} 模型 <b>{doc.model}</b>，共 {doc.n_sessions} 个交易日；图表显示最近 {doc.dates.length} 个交易日。</p>
      </div>
      <section className="wl-section">
        <h3>{factorName(f)} <small className="wl-code">{f.factor}</small></h3>
        <div className="fm-charts">
          <LineChart label={`${factorName(f)} 累计收益`} series={[{ name: "累计收益", cls: "c1", points: toPoints(doc.dates, f.cum) }]} />
          <LineChart label={`${factorName(f)} 波动率`} series={[
            { name: "预测波动（年化）", cls: "c2", points: toPoints(doc.dates, f.forecast) },
            { name: "实际21日（年化）", cls: "c3", points: toPoints(doc.dates, f.realized) },
          ]} />
        </div>
      </section>
      <FactorTable title="市场与风格" rows={styles} picked={f.factor} pick={setPicked} />
      <FactorTable title="申万一级行业" rows={industries} picked={f.factor} pick={setPicked} />
      <p className="wl-notes">收益是风险模型回归出的因子日收益按窗口复利；预测波动来自 {ymd(doc.as_of)} 的因子协方差，年化 ×√252；今日σ = 今日收益 ÷ 前一日预测的日波动。|今日σ| ≥ 2 或 比值 ≥ 1.5 的行高亮。</p>
    </div>
  );
}

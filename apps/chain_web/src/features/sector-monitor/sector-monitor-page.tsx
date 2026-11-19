import { useEffect, useState } from "react";
import { api, type SectorDoc, type SectorMonitor } from "../../api/client";
import { SectorChartCard } from "./sector-chart";
import { SectorEarningsPanel } from "./sector-earnings-panel";
import { SectorRankingsPanel } from "./sector-rankings";
import { formatPct, formatValue, listColumns } from "./sector-monitor-format";

/** Purpose: the company table of a sector: the index row first (vol only, other cells blank), then each company's latest values. */
function SectorTable({ doc }: { doc: SectorDoc }) {
  const cols = listColumns(doc);
  const cell = (row: SectorDoc["table"][number], key: string, unit: string, pct?: boolean) => {
    const v = row[key];
    if (typeof v !== "number") return row.kind === "index" ? "" : "—";
    if (pct) return formatPct(v);
    return key === "retail_gauge" ? v.toFixed(2) : formatValue(v, unit);
  };
  return (
    <div className="sm-table-wrap">
      <table className="fm-table sm-table">
        <thead><tr><th>名称</th>{cols.map((c) => <th key={c.key}>{c.label}{c.unit && !c.pct ? `(${c.unit})` : ""}</th>)}</tr></thead>
        <tbody>
          {doc.table.map((r) => (
            <tr key={String(r.code)} className={r.kind === "index" ? "sm-index" : ""}>
              <td>{String(r.name)}</td>
              {cols.map((c) => {
                const v = r[c.key];
                const hot = c.pct && typeof v === "number" && v >= 0.9;
                const gauge = c.key === "retail_gauge" && typeof v === "number" ? (v >= 0.9 ? "hot" : v <= 0.3 ? "cool" : "") : "";
                return <td key={c.key} className={`${hot ? "ext" : ""} ${gauge}`}>{cell(r, c.key, c.unit, c.pct)}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Purpose: the 行业监控 page at #sector-monitor (plan 31 ph5): a switch between the configured sectors (房地产, 游戏),
 * the company table (latest values, realised vol with its 3-year percentile, 散户温度计), the App Store 排行榜 when the
 * sector has one (games), and one chart per metric; above them the 财报季信号 of every Shenwan L2 sector (plan 35).
 * Contract: read-only display of GET /api/sector-monitor; no document → empty state with the command to run.
 */
export function SectorMonitorPage() {
  const [doc, setDoc] = useState<SectorMonitor | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [key, setKey] = useState<string | null>(null);
  useEffect(() => { api.getSectorMonitor().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page" data-empty="sector-monitor"><p className="wl-empty">行业监控数据没有加载出来：{error}。先运行 <code>make sector-monitor</code>。</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  if (!doc.sectors.length) return <div className="wl-page" data-empty="sector-monitor"><p className="wl-empty">还没有行业监控数据。先运行 <code>make sector-monitor</code>。</p></div>;
  const sector = doc.sectors.find((s) => s.key === key) ?? doc.sectors[0];
  return (
    <div className="wl-page mc-page" data-page="sector-monitor">
      <div className="wl-head">
        <h2>行业监控</h2>
        <div className="sm-switch" role="tablist">
          {doc.sectors.map((s) => <button key={s.key} role="tab" aria-selected={s.key === sector.key} className={s.key === sector.key ? "on" : ""} onClick={() => setKey(s.key)}>{s.name}</button>)}
        </div>
      </div>
      <section className="wl-section">
        <h3>财报季信号（全部申万二级行业）</h3>
        <SectorEarningsPanel />
      </section>
      <section className="wl-section">
        <h3>公司一览</h3>
        <SectorTable doc={sector} />
      </section>
      {sector.rankings && (
        <section className="wl-section">
          <h3>App Store 排行榜</h3>
          <SectorRankingsPanel rankings={sector.rankings} />
        </section>
      )}
      <section className="wl-section">
        <h3>指标走势</h3>
        <div className="mc-grid sm-grid">{sector.charts.map((c) => <SectorChartCard key={c.key} chart={c} index={sector.index.name} />)}</div>
      </section>
      <p className="wl-note">
        70 城房价为一线（4 城）与二线、三线城市的简单平均环比（国家统计局每月中旬发布）。签约额与拿地来自开发商月度销售简报（经营数据公告），缺月表示当月没有简报。
        财报为合并报表单季值，减值为资产减值与信用减值之和（正数为计提）。版号按国家新闻出版署名单发布月统计，公司按出版 / 运营单位归属上市公司。
        App Store 排名为苹果中国区游戏畅销 / 免费榜（每日抓取，海外为另外 25 个市场的畅销榜前 100），公司按开发者账号归属（config/app_publishers.yaml），排名表含账号已知的全部 A 股游戏公司，图表只画上方 6 家；排名图纵轴向上为更靠前。
        签约额同比为滚动 3 个月合计对去年同期，累计同比取简报的年初至今合计；70 城下跌城市数为环比指数低于 100 的城市数。
        估值分位为近 5 年（约 1,250 个交易日）当前估值的位置（房地产用 PB，游戏用 PE(TTM)，亏损时无 PE）；盈利预测修正为近 90 天券商对当年（5 月起，此前为上一年）净利润预测中位数相比 90 天前的变化；机构调研为每月有调研记录的天数。
        实际波动率为日对数收益的年化标准差，分位为近 3 年位置，≥90% 标橙；散户温度计 ≥0.9 标红、≤0.3 标绿。截至 {sector.as_of ?? "—"}。
      </p>
    </div>
  );
}

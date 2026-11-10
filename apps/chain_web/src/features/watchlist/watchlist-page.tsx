import type { ReactNode } from "react";
import type { Watchlist, WatchlistEntry } from "../../api/client";
import { useApp } from "../../components/context";
import { RangeBar, WeeklyChart } from "./watchlist-charts";
import { buyText, epsYearOf, gapPct, gapText, nearestEntry, pctOf, px, statusLabel, targetText, times, ymd } from "./watchlist-format";

/**
 * Purpose: the 观察账本 page (#watchlist, plan 15 phase 7): a headline with the stock nearest its buy price,
 * one card per stock (status, gap, valuation at the buy price, range bar, weekly chart, thesis) and a
 * valuation table. Read-only: targets are edited in config/local.watchlist.yaml and refreshed with make watchlist.
 * Contract: doc null while loading; error shows a message; every number is displayed as Python wrote it.
 */
export function WatchlistPage({ doc, error }: { doc: Watchlist | null; error: string | null }) {
  if (error) return <div className="wl-page"><p className="empty">观察账本没有加载出来：{error}</p></div>;
  if (!doc) return <div className="wl-page"><p className="empty">正在加载观察账本…</p></div>;
  const n = nearestEntry(doc.entries);
  return (
    <div className="wl-page" data-wl={doc.entries.length}>
      <header className="wl-head">
        <h2>目标价观察账本</h2>
        {n ? (
          <p>离买入价最近的是 <b>{n.name}</b>，{n.gap_to_buy >= 0 ? <>已在买入区间内</> : <>还要再跌 <b>{gapPct(n.gap_to_buy)}</b>（到 {px(n.buy_high)}）</>}。价格截至 <b>{ymd(doc.as_of)}</b> 收盘。</p>
        ) : (
          <p>还没有观察的股票。</p>
        )}
      </header>
      {doc.entries.length === 0 && <EmptyState />}
      {doc.missing.length > 0 && <p className="note">这些代码在数据湖里没有价格，没有显示：{doc.missing.join("、")}</p>}
      {doc.entries.length > 0 && (
        <>
          <div className="wl-cards">{doc.entries.map((e) => <EntryCard key={e.code} e={e} />)}</div>
          <ValuationTable entries={doc.entries} />
          <details className="wl-notes">
            <summary>数据来源和口径</summary>
            <dl>
              <dt>价格和估值</dt><dd>本地 Tushare 数据湖的日线和每日指标（不复权收盘价，和买入价同一口径）。不是实时行情：运行 make watchlist 刷新。</dd>
              <dt>还需下跌</dt><dd>现价跌到买入区间上沿所需的跌幅。到达区间显示“区间内”，差距 {pctOf(doc.near_pct)} 以内显示“接近”。</dd>
              <dt>每股收益预测</dt><dd>最近一个报告季以来券商盈利预测的中位数。</dd>
              <dt>股息率</dt><dd>过去 12 个月每股分红除以价格。</dd>
              <dt>价格区间条</dt><dd>灰线是近 52 周最低到最高；绿色是买入区间；虚线框是券商目标价区间；圆点是现价。</dd>
            </dl>
          </details>
        </>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="wl-empty">
      <p>在 <code>config/local.watchlist.yaml</code> 里写下股票代码和买入价（也可以直接告诉 Claude 帮你加），然后运行 <code>make watchlist</code> 刷新价格和估值，这里就会出现卡片。</p>
    </div>
  );
}

function Kv({ k, children }: { k: string; children: ReactNode }) {
  return <div><span className="wl-k">{k}</span><span className="wl-v">{children}</span></div>;
}

function EntryCard({ e }: { e: WatchlistEntry }) {
  const { select } = useApp();
  return (
    <article className="wl-card" data-code={e.code}>
      <div className="wl-row">
        <div>
          <button type="button" className="link wl-name" onClick={() => select({ kind: "company", id: e.code })}>{e.name}</button>
          <span className="wl-code">{e.code}</span>
        </div>
        <span className={`wl-pill ${e.status}`}>{statusLabel(e.status)}</span>
      </div>
      <div className="wl-row">
        <span className="wl-big num">{px(e.price)}</span>
        <span className={`wl-gap ${e.status}`}>{gapText(e.gap_to_buy)}</span>
      </div>
      <div className="wl-kv">
        <Kv k="买入价">{buyText(e)}</Kv>
        <Kv k="买入价对应 PE">{times(e.pe_at_buy)}</Kv>
        <Kv k="买入价对应股息率">{pctOf(e.yield_at_buy)}</Kv>
        <Kv k="现在 PE（TTM）">{times(e.pe_ttm)}</Kv>
        <Kv k="股息率">{pctOf(e.div_yield)}</Kv>
        <Kv k="券商目标价">{targetText(e)}</Kv>
      </div>
      <RangeBar e={e} />
      <WeeklyChart e={e} />
      {e.thesis && <p className="note"><strong>理由：</strong>{e.thesis}</p>}
      {e.watch && <p className="note"><strong>要盯的信号：</strong>{e.watch}</p>}
    </article>
  );
}

function ValuationTable({ entries }: { entries: WatchlistEntry[] }) {
  const year = epsYearOf(entries);
  const heads = ["股票", "现价", "买入价上沿", "还需下跌", "现在 PE", `${year ? year + "E" : "预测"} 每股收益`, "买入价对应 PE", "买入价对应股息率", "券商目标价最低", "券商目标价最高"];
  return (
    <section className="wl-section">
      <h3>买入价对应的估值</h3>
      <div className="scrollx">
        <table className="wl-table">
          <thead><tr>{heads.map((h, i) => <th key={h} className={i ? "num" : ""}>{h}</th>)}</tr></thead>
          <tbody>{entries.map((e) => (
            <tr key={e.code}>
              <td>{e.name}</td><td className="num">{px(e.price)}</td><td className="num">{px(e.buy_high)}</td>
              <td className="num">{gapPct(e.gap_to_buy)}</td><td className="num">{times(e.pe_ttm)}</td>
              <td className="num">{px(e.eps_fy)}{e.eps_year && e.eps_year !== year ? ` (${e.eps_year}E)` : ""}</td>
              <td className="num">{times(e.pe_at_buy)}</td><td className="num">{pctOf(e.yield_at_buy)}</td>
              <td className="num">{px(e.target_low)}</td><td className="num">{px(e.target_high)}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </section>
  );
}

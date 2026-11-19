import { useEffect, useMemo, useState } from "react";
import { api, type BuybackMonitor, type BuybackRow, type BuybackSection } from "../../api/client";
import { dayLabel } from "../volatility/volatility-format";
import { EVENT_LABEL, KIND_LABEL, LOAN, buybackHeadline, filterRows, formatPct, formatRange, formatYi } from "./buyback-format";
import { MonthChart } from "./month-chart";

const KINDS = ["buyback", "increase"] as const;
const SIZES = [[0, "全部"], [1, "≥1亿"], [5, "≥5亿"], [20, "≥20亿"]] as const;
const LIMIT = 200;
const EVENTS_SHOWN = 10;

/** Purpose: a programme's name cell: stock name and code, holders for 增持, 未标注 when no label. Contract: pure display. */
function NameCell({ r }: { r: BuybackRow }) {
  return (
    <td title={r.holders.join("、")}>
      <b>{r.name ?? r.code}</b> <span className="bb-code">{r.code}</span>
      {!r.labelled && <span className="bb-muted"> 未标注</span>}
    </td>
  );
}

/** Purpose: the table of programmes: dates, labels, funding, planned range, executed, % done, price cap vs close, % of market cap. Contract: event column only when asked. */
function ProgrammeTable({ rows, kind, event }: { rows: BuybackRow[]; kind: string; event?: boolean }) {
  const tagHead = kind === "buyback" ? "用途" : "增持主体";
  return (
    <div className="fm-scroll">
      <table className="fm-table bb-table" data-event={event ? "" : undefined}>
        <thead><tr>{event && <th>事件</th>}<th>股票</th><th>公告</th><th>截止</th><th>{tagHead}</th><th>资金</th><th>计划</th><th>已执行</th><th title="已执行 ÷ 计划下限（无下限时用上限）">进度</th><th title="现价相对回购价格上限">距上限</th><th title="计划上限占总市值">占市值</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.code}-${r.date}-${r.event ?? ""}`} data-code={r.code}>
              {event && <td className={`bb-ev ${r.event}`}>{EVENT_LABEL[r.event ?? ""] ?? r.event}</td>}
              <NameCell r={r} />
              <td>{dayLabel(r.date)}</td>
              <td>{dayLabel(r.end)}</td>
              <td>{r.tags.join("、") || "—"}</td>
              <td title={r.loan_bank ?? ""} className={r.funding.includes(LOAN) ? "bb-loan" : ""}>{r.funding.join("、") || "—"}{r.loan_yi != null && `（贷 ${formatYi(r.loan_yi)}）`}</td>
              <td>{formatRange(r.low_yi, r.high_yi)}</td>
              <td>{formatYi(r.executed_yi)}</td>
              <td className={r.done_pct != null && r.done_pct >= 1 ? "bb-done" : ""}>{formatPct(r.done_pct)}</td>
              <td title={r.price_cap == null ? "" : `现价 ${r.close ?? "—"}，上限 ${r.price_cap}`}>{formatPct(r.cap_gap, true)}</td>
              <td>{r.mv_pct == null ? "—" : `${(r.mv_pct * 100).toFixed(2)}%`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Purpose: totals of the live programmes by purpose / holder type or funding. Contract: counts overlap when a programme has several labels. */
function TotalsTable({ title, parts }: { title: string; parts: BuybackSection["totals"]["by_tag"] }) {
  return (
    <table className="fm-table bb-totals">
      <thead><tr><th>{title}</th><th>个数</th><th>计划</th><th>已执行</th></tr></thead>
      <tbody>{parts.map((p) => <tr key={p.label}><td>{p.label}</td><td>{p.count}</td><td>{formatRange(p.low_yi, p.high_yi)}</td><td>{formatYi(p.executed_yi)}</td></tr>)}</tbody>
    </table>
  );
}

/**
 * Purpose: the 回购增持 page at #buyback (plan 32, D-169): a 回购 / 增持 switch; per kind a headline, the window's events,
 * totals by purpose or holder type and by funding, new programmes per month, and the live programmes with purpose /
 * 专项贷款 / size filters.
 * Contract: read-only display of GET /api/buyback; no document → empty state with the command to run; at most LIMIT
 * live rows are drawn, largest first.
 */
export function BuybackPage() {
  const [doc, setDoc] = useState<BuybackMonitor | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [kind, setKind] = useState<(typeof KINDS)[number]>("buyback");
  const [tag, setTag] = useState("");
  const [loan, setLoan] = useState(false);
  const [minYi, setMinYi] = useState(0);
  const [allEvents, setAllEvents] = useState(false);
  useEffect(() => { api.getBuyback().then(setDoc).catch((e) => setError(e.message)); }, []);
  const section = doc?.[kind];
  const rows = useMemo(() => (section ? filterRows(section.live, { tag, loan, minYi }) : []), [section, tag, loan, minYi]);
  if (error) return <div className="wl-page" data-empty="buyback"><p className="wl-empty">回购增持数据没有加载出来：{error}。先运行 <code>make buyback-events</code>。</p></div>;
  if (!doc || !section) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  const pick = (k: (typeof KINDS)[number]) => { setKind(k); setTag(""); };
  return (
    <div className="wl-page mc-page" data-page="buyback">
      <div className="wl-head">
        <h2>回购增持</h2>
        <div className="seg">{KINDS.map((k) => <button key={k} type="button" data-kind={k} className={`chip ${k === kind ? "on" : ""}`} onClick={() => pick(k)}>{KIND_LABEL[k]}</button>)}</div>
        <p>{buybackHeadline(section, kind, doc.days)}</p>
      </div>
      <section className="wl-section bb-grid">
        <TotalsTable title={kind === "buyback" ? "用途" : "增持主体"} parts={section.totals.by_tag} />
        <TotalsTable title="资金来源" parts={section.totals.by_funding} />
      </section>
      <section className="wl-section"><h3>每月新公告（{dayLabel(doc.start).slice(0, 7)} 起）</h3><MonthChart months={section.months} /></section>
      <section className="wl-section">
        <h3>近 {doc.days} 天（{section.events.length}）</h3>
        {section.events.length ? <ProgrammeTable rows={allEvents ? section.events : section.events.slice(0, EVENTS_SHOWN)} kind={kind} event /> : <p className="wl-empty">没有新事件。</p>}
        {section.events.length > EVENTS_SHOWN && <button type="button" className="chip" data-more onClick={() => setAllEvents(!allEvents)}>{allEvents ? "收起" : `展开全部 ${section.events.length} 条`}</button>}
      </section>
      <section className="wl-section">
        <h3>在执行（{rows.length}{rows.length > LIMIT && `，显示前 ${LIMIT}`}）</h3>
        <div className="seg bb-filters">
          <button type="button" className={`chip ${tag === "" ? "on" : ""}`} onClick={() => setTag("")}>全部</button>
          {section.totals.by_tag.map((p) => <button key={p.label} type="button" data-tag={p.label} className={`chip ${tag === p.label ? "on" : ""}`} onClick={() => setTag(p.label)}>{p.label}</button>)}
          <button type="button" data-loan className={`chip ${loan ? "on" : ""}`} onClick={() => setLoan(!loan)}>只看{LOAN}</button>
          {SIZES.map(([v, l]) => <button key={v} type="button" className={`chip ${minYi === v ? "on" : ""}`} onClick={() => setMinYi(v)}>{l}</button>)}
        </div>
        <ProgrammeTable rows={rows.slice(0, LIMIT)} kind={kind} />
      </section>
      <p className="wl-note">回购：Tushare 回购公告整理成回购方案（2024 年起；限制性股票回购注销不计），已执行为累计回购金额。增持：巨潮增持计划公告；已执行 = 计划期内被点名股东的增持（股数 × 均价，缺均价用当日收盘价）。用途、增持主体、资金来源、贷款、金额区间和价格上限由方舟大模型从公告原文读取，每条都核对过原文引文；“未标注”为没有找到方案公告的回购。截至 {dayLabel(doc.as_of)}。</p>
    </div>
  );
}

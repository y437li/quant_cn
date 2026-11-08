import type { Company, CompanyBrief, CpTable } from "../../api/client";
import { Bar, CompanyLink, Empty, Kpis, Note, NodeLink, Row, Tag } from "../../components/ui";
import { HOW_ZH, pct, ROLE_ZH, yi } from "../../lib/format";
import { BrokerStatLine } from "./broker";
import { useApp } from "../../components/context";
import { FinancialTable } from "./financial-table";
import { QuarterlyTable } from "./quarterly-table";
import { rankOf } from "../node/leaders";
import { useState } from "react";

/** Purpose: the overview, products, customers, suppliers and evidence tabs of a company. */
type P = { c: Company; related: Record<string, CompanyBrief> };

export function OverviewTab({ c }: P) {
  const regions = c.regions || [];
  const overseas = regions.length ? regions.filter((r) => /境外|海外|国外/.test(r.item)).reduce((s, r) => s + r.pct, 0) : null;
  return (
    <>
      <Kpis items={[[pct(c.customers?.total_pct), "前五名客户占销售"], [pct(c.suppliers?.total_pct), "前五名供应商占采购"], [pct(overseas), "境外收入占比"]]} />
      <h3>营收结构（2025 年，主营构成，占合并营收）</h3>
      {[...c.revenue].sort((a, b) => b.pct - a.pct).map((r, i) => (
        <div key={r.item}><Row left={r.item} right={<span className="num">{pct(r.pct)}</span>} /><Bar value={r.pct} color={i} /></div>
      ))}
      <FinView c={c} />
      <h3>关联一览</h3>
      <Note>产品与服务 {c.revenue.length} 项 · 前五名客户 {c.customers?.rows.length || 0} 家 · 前五名供应商 {c.suppliers?.rows.length || 0} 家 · 同行 {(c.peers || []).length} 家 · 关联上市公司 {c.links.length} 条</Note>
    </>
  );
}

function FinView({ c }: { c: Company }) {
  const [mode, setMode] = useState<"y" | "q">("y");
  return (
    <>
      <div className="seg">{([["y", "年度"], ["q", "单季度"]] as const).map(([k, l]) => <button key={k} type="button" className={`chip ${mode === k ? "on" : ""}`} onClick={() => setMode(k)}>{l}</button>)}</div>
      {mode === "y" ? <FinancialTable c={c} /> : <QuarterlyTable c={c} />}
    </>
  );
}

export function ProductsTab({ c }: P) {
  const { boot, tx } = useApp();
  const leaders = (boot as unknown as { leaders?: Record<string, never> }).leaders;
  return (
    <>
      <table>
        <thead><tr><th>主营构成</th><th className="num">占营收</th><th className="num">毛利率</th></tr></thead>
        <tbody>
          {[...c.revenue].sort((a, b) => b.pct - a.pct).map((r) => (
            <tr key={r.item}>
              <td>
                {r.item}
                <div>{r.pids.length ? r.pids.map((p) => <div key={p}><NodeLink id={p} /></div>) : null}</div>
                <Tag>{HOW_ZH[r.how] || r.how}</Tag>
                {r.pids.map((p) => { const rk = rankOf(leaders, p, c.code) || rankOf(leaders, tx.N[p]?.s || "", c.code); return rk ? <span key={p}> <Tag kind="ev">细分第 {rk.rank} / {rk.n} 家 · 份额 {pct(rk.share * 100)}</Tag></span> : null; })}
                {((c.apps && c.apps[r.item]) || []).length > 0 && (
                  <div className="note">下游应用：{(c.apps![r.item]).map((a, i) => (
                    <span key={i}>{a.node_id && tx.N[a.node_id] ? <NodeLink id={a.node_id} plain /> : a.name} <Tag kind={a.weight === "主要" ? "ev" : undefined} title={a.evidence.quote}>{a.weight} · p{a.evidence.page}</Tag> </span>
                  ))}</div>
                )}
                {r.pids[0] && boot.broker_prod[r.pids[0]] && <BrokerStatLine v={boot.broker_prod[r.pids[0]]} scope="该产品" />}
              </td>
              <td className="num">{pct(r.pct)}</td>
              <td className="num">{r.gm == null ? "—" : r.gm + "%"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <Note>占比来自 Tushare 主营业务构成（按产品）。产品节点由 ProductMatcher 规则匹配（D-115）；下游应用由 DeepSeek 读年报业务章节得出，悬停页码看原文。</Note>
    </>
  );
}

function CpTableView({ t, kind, related, self }: { t?: CpTable; kind: "customer" | "supplier"; related: Record<string, CompanyBrief>; self: string }) {
  if (!t || (!t.total_pct && !t.rows.length)) return <Empty>报告未披露</Empty>;
  const word = kind === "customer" ? "销售" : "采购";
  return (
    <>
      <Kpis items={[[pct(t.total_pct), `前五名合计占${word}`], [yi(t.total), "前五名合计金额"], [t.rows.length ? (t.consistent ? "一致" : "不一致") : "仅合计", "明细与合计核对"]]} />
      {t.rows.length > 0 ? (
        <table>
          <thead><tr><th>#</th><th>名称</th><th className="num">金额</th><th className="num">占比</th></tr></thead>
          <tbody>{t.rows.map((r) => (
            <tr key={r.rank}>
              <td>{r.rank}</td>
              <td>{r.name} {r.anon ? <Tag>匿名</Tag> : <Tag kind="ev">实名</Tag>}
                {r.code && r.code !== self && related[r.code] && <> → <CompanyLink code={r.code} name={related[r.code].name} />{r.group && <> <Tag kind="prior">按简称前缀，可能是其子公司</Tag></>}</>}
                <Bar value={r.pct * 2} kind={kind === "customer" ? "cust" : "supp"} />
              </td>
              <td className="num">{yi(r.amount)}</td><td className="num">{pct(r.pct)}</td>
            </tr>
          ))}</tbody>
        </table>
      ) : <Note>只披露前五名合计，不列明细。</Note>}
    </>
  );
}

function Parties({ c, related }: P) {
  const list = c.llm?.counterparties || [];
  const groups = ["customer", "supplier", "partner", "competitor", "subsidiary"].map((r) => [r, list.filter((p) => p.role === r)] as const).filter(([, l]) => l.length);
  if (!groups.length) return null;
  return (
    <>
      <h3>年报 / 半年报正文提到的公司（DeepSeek 区分角色，原文已核对）</h3>
      {groups.map(([role, l]) => (
        <div key={role}>
          <div className="note" style={{ marginTop: 6 }}>{ROLE_ZH[role]} · {l.length}</div>
          <div className="list">{l.map((p, i) => (
            <Row key={i} left={<>{p.code && related[p.code] ? <CompanyLink code={p.code} name={related[p.code].name} /> : p.name} <Tag>{p.detail}</Tag></>}
              right={<Tag kind="ev" title={p.evidence.quote}>{p.src} 第 {p.evidence.page} 页</Tag>} />
          ))}</div>
        </div>
      ))}
    </>
  );
}

export function CustomersTab(p: P) {
  return <><h3>前五名客户</h3><CpTableView t={p.c.customers} kind="customer" related={p.related} self={p.c.code} /><Parties {...p} /></>;
}
export function SuppliersTab(p: P) {
  return <><h3>前五名供应商</h3><CpTableView t={p.c.suppliers} kind="supplier" related={p.related} self={p.c.code} /></>;
}

const SECTION_ZH: Record<string, string> = { chapter: "管理层讨论与分析", business: "主营业务", industry: "行业情况", competitiveness: "核心竞争力", revenue_mix: "营业收入构成", capacity: "产能 / 产销", costs_materials: "成本与原材料", counterparties: "前五名客户和供应商", competition: "竞争格局", risks: "风险" };
export function EvidenceTab({ c }: P) {
  const s = Object.entries(c.sections || {});
  return (
    <>
      <h3>{c.source || "年报"}：定位到的章节</h3>
      {s.length ? <table><tbody>{s.map(([k, [a, z]]) => <tr key={k}><td>{SECTION_ZH[k] || k}</td><td className="num">{a}–{z}</td></tr>)}</tbody></table> : <Empty>未定位到章节</Empty>}
      <h3>证据等级</h3>
      <div className="list">
        <Row left={<><Tag kind="ev">年报表格</Tag> 前五名客户、供应商、主营构成</>} right="规则解析" />
        <Row left={<><Tag kind="ev">年报正文</Tag> 下游应用、点名公司</>} right="DeepSeek，引文已核对" />
        <Row left={<><Tag kind="prior">先验</Tag> 产品之间的上下游</>} right="Opus 产业链骨架" />
      </div>
    </>
  );
}

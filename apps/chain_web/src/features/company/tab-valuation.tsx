import { useEffect, useState } from "react";
import { api, type BrokerView, type Company } from "../../api/client";
import { useApp } from "../../components/context";
import { Empty, Note, NodeLink, Tag } from "../../components/ui";
import { BrokerStatLine, BrokerViewCard } from "./broker";

/** Purpose: the 估值与指标 tab: company synthesis, product and industry patterns, sector KPIs, recent reports as evidence. */
export function ValuationTab({ c }: { c: Company }) {
  const { boot } = useApp();
  const prods = [...new Set(c.revenue.flatMap((r) => r.pids))];
  const [views, setViews] = useState<Record<string, BrokerView | null>>({});
  useEffect(() => {
    let live = true;
    Promise.all([...prods.map((p) => api.getView("product", p).then((v) => ["p:" + p, v] as const)),
      c.l3 ? api.getView("industry", c.l3).then((v) => ["i:" + c.l3, v] as const) : Promise.resolve(["i:", null] as const)])
      .then((list) => { if (live) setViews(Object.fromEntries(list)); });
    return () => { live = false; };
  }, [c.code]); // eslint-disable-line react-hooks/exhaustive-deps
  const shown = prods.filter((p) => views["p:" + p] || boot.broker_prod[p]);
  const ind = c.l3 ? views["i:" + c.l3] : null;
  return (
    <>
      {c.broker_view && <><h3>本公司：研报观点归纳</h3><BrokerViewCard v={c.broker_view} scope="本公司" /></>}
      <h3>按产品 / 服务：研报的估值规律</h3>
      {shown.length ? shown.map((p) => (
        <div key={p} style={{ marginTop: 10 }}><NodeLink id={p} /><BrokerViewCard v={views["p:" + p]} scope="该产品" /><BrokerStatLine v={boot.broker_prod[p]} scope="统计" /></div>
      )) : <Note>本公司的产品还没有足够的研报样本（每个产品至少 3 篇）。</Note>}
      <h3>所属行业（申万三级 {c.l3 || "—"}）</h3>
      <BrokerViewCard v={ind} scope="行业" />
      {c.l3 && boot.broker_ind[c.l3] ? <BrokerStatLine v={boot.broker_ind[c.l3]} scope="统计" /> : !ind && <Note>行业研报样本不足。</Note>}
      <SectorKpis c={c} />
      <h3>本公司最近的研报（证据）</h3>
      {(c.valuations || []).length ? (c.valuations || []).map((r, i) => {
        const v = r.valuation;
        const tp = v.target_price && v.target_price.value != null ? `${v.target_price.value} ${v.target_price.currency || ""}` : "未给出";
        return (
          <div key={i}>
            <h3>{r.org} · {r.date} · {v.rating || "—"}</h3>
            <div className="note">《{r.title}》</div>
            <table><tbody>
              <tr><td>方法</td><td>{(v.methods || []).map((m: any, j: number) => <div key={j}>{m.method}{m.multiple != null && ` ${m.multiple}x`} {m.base_year} {m.multiple_kind && <Tag kind={m.multiple_kind === "target" ? "ev" : undefined}>{m.multiple_kind === "target" ? "目标倍数" : "现价隐含"}</Tag>}</div>)}</td></tr>
              <tr><td>目标价</td><td>{tp}</td></tr>
            </tbody></table>
            <p className="note">{v.logic}</p>
          </div>
        );
      }) : <Empty>最近 12 个月没有该公司的个股研报</Empty>}
    </>
  );
}

function SectorKpis({ c }: { c: Company }) {
  const { boot } = useApp();
  const cfg = boot.kpis[c.l1];
  if (!cfg) return null;
  const groups = [...(cfg.kpis.length ? [{ name: `${boot.sectors[c.l1]}（全行业）`, sw: [], kpis: cfg.kpis }] : []), ...cfg.groups.filter((g) => g.sw.some((x) => (c.sw || []).includes(x)))];
  const FREQ: Record<string, string> = { monthly: "月", quarterly: "季", semiannual: "半年", annual: "年" };
  return (
    <>
      <h3>行业专属指标（配置 · Opus 先验，待研报与披露确认）</h3>
      {groups.length ? groups.map((g) => (
        <div key={g.name}>
          <div className="note" style={{ marginTop: 6 }}>{g.name}</div>
          <table><tbody>{g.kpis.map((k) => <tr key={k.id}><td>{k.name} {k.unit && <Tag>{k.unit}</Tag>}</td><td className="note">{k.definition}</td><td className="num">{FREQ[k.freq || ""] || ""}</td></tr>)}</tbody></table>
        </div>
      )) : <Note>该行业没有配置专属指标。</Note>}
    </>
  );
}

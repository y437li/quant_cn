import { useState } from "react";
import type { CompanyBrief } from "../../api/client";
import { useApp } from "../../components/context";
import { CompanyLink, Empty, Note, NodeLink, Row, Tabs, Tag } from "../../components/ui";
import { DupontPlane } from "../../components/dupont-plane";

/** Purpose: dossier of a Shenwan L1 sector: segments, inflows, outflows, companies. */
export function SectorDossier({ l1, companies }: { l1: string; companies: CompanyBrief[] }) {
  const { boot, tx, select } = useApp();
  const [tab, setTab] = useState("cos");
  const segs = Object.values(tx.N).filter((n) => n.t === "segment" && n.sec === l1);
  const agg = (m: Record<string, Record<string, number>>) => {
    const out: Record<string, number> = {};
    segs.forEach((s) => Object.entries(m[s.id] || {}).forEach(([g, k]) => { if (tx.N[g]?.sec !== l1) out[g] = (out[g] || 0) + k; }));
    return Object.entries(out).sort((a, b) => b[1] - a[1]);
  };
  const ups = agg(tx.GIN), downs = agg(tx.GOUT);
  const flow = (rows: [string, number][]) => rows.length ? <div className="list">{rows.map(([g, k]) => <Row key={g} left={<><NodeLink id={g} />{tx.N[g]?.sec && boot.sectors[tx.N[g].sec as string] && <> <Tag>{boot.sectors[tx.N[g].sec as string]}</Tag></>}</>} right={<Tag kind="prior">{k} 条</Tag>} />)}</div> : <Empty>无</Empty>;
  return (
    <>
      <div className="head"><div className="eyebrow">申万一级行业 · {l1}</div><h2>{boot.sectors[l1]}</h2><div className="meta"><span>{segs.length} 个细分</span><span>{companies.length} 家公司</span></div></div>
      <Tabs tabs={[{ key: "cos", label: "公司", n: companies.length }, { key: "dupont", label: "杜邦坐标" }, { key: "segs", label: "细分", n: segs.length }, { key: "up", label: "上游来自", n: ups.length }, { key: "down", label: "下游去向", n: downs.length }]} active={tab} onPick={setTab} />
      <div className="body" data-testid="tab-body">
        {tab === "cos" && (companies.length ? <div className="list">{companies.map((c) => <Row key={c.code} left={<><CompanyLink code={c.code} name={c.name} /> <Tag>{c.l3 || ""}</Tag></>} right={<Tag kind="ev">{c.n_links} 条关系</Tag>} />)}</div> : <Empty>无</Empty>)}
        {tab === "dupont" && <DupontPlane highlight={(m) => m[3] === l1} onPick={(code) => select({ kind: "company", id: code })} caption={`蓝点 = ${boot.sectors[l1]}行业的公司（点击打开）。`} />}
        {tab === "segs" && <div className="list">{segs.map((n) => <Row key={n.id} left={<NodeLink id={n.id} plain />} right={<span className="num">{(tx.SEGP[n.id] || []).length} 项</span>} />)}</div>}
        {tab === "up" && flow(ups)}
        {tab === "down" && flow(downs)}
        <Note>图中显示该行业的公司网络（关闭“行业看公司网络”则显示细分之间的产业链先验）。</Note>
      </div>
    </>
  );
}

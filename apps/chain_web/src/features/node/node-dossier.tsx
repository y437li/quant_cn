import { useEffect, useState } from "react";
import { api, type BrokerView, type Maker } from "../../api/client";
import { useApp } from "../../components/context";
import { CompanyLink, Empty, Note, NodeLink, Row, Tabs, Tag } from "../../components/ui";
import { typeOf } from "../../graph/taxonomy";
import { HOW_ZH, IMP_ZH, pct, REL_ZH, TYPE_ZH } from "../../lib/format";
import { BrokerStatLine, BrokerViewCard } from "../company/broker";
import { Leaders } from "./leaders";

/** Purpose: dossier of a taxonomy node (product, material, market) or a segment. */
export function NodeDossier({ id, makers }: { id: string; makers: Maker[] }) {
  const { boot, tx, select } = useApp();
  const n = tx.N[id];
  const [tab, setTab] = useState(n.t === "segment" ? "prods" : "up");
  const [view, setView] = useState<BrokerView | null>(null);
  useEffect(() => { api.getView("product", id).then(setView); }, [id]);
  const ups = (tx.IN[id] || []), downs = (tx.OUT[id] || []);
  const rel = (arr: { other: string; rel: string }[]) => arr.length ? <div className="list">{arr.map((e, i) => <Row key={i} left={<NodeLink id={e.other} />} right={<Tag kind="prior">{REL_ZH[e.rel] || e.rel}</Tag>} />)}</div> : <Empty>骨架中没有记录</Empty>;
  const bv = boot.broker_prod[id];
  const tabs = [
    ...(n.t === "segment" ? [{ key: "prods", label: "产品与服务", n: (tx.SEGP[id] || []).length }] : []),
    { key: "up", label: "上游", n: ups.length }, { key: "down", label: "下游", n: downs.length },
    { key: "makers", label: "生产公司", n: makers.length }, { key: "val", label: "估值与指标", n: view?.n_reports || bv?.n || 0 },
  ];
  const seg = n.s && tx.N[n.s] ? tx.N[n.s] : null;
  return (
    <>
      <div className="head">
        <div className="eyebrow">{TYPE_ZH[typeOf(n)]}{n.sec && boot.sectors[n.sec] ? " · 申万 " + boot.sectors[n.sec] : ""}</div>
        <h2>{n.n}</h2>
        <div className="meta">{n.en && <span>{n.en}</span>}{seg && <span>细分：<NodeLink id={seg.id} plain /></span>}{n.imp && <Tag kind="risk">{IMP_ZH[n.imp]}</Tag>}{n.sec && <button type="button" className="link" onClick={() => select({ kind: "sector", id: n.sec as string })}>所属行业</button>}</div>
      </div>
      <Tabs tabs={tabs} active={tab} onPick={setTab} />
      <div className="body" data-testid="tab-body">
        {tab === "prods" && <div className="list">{(tx.SEGP[id] || []).map((p) => <Row key={p} left={<NodeLink id={p} />} />)}</div>}
        {tab === "up" && rel(ups)}
        {tab === "down" && rel(downs)}
        {tab === "makers" && <Leaders id={id} />}
        {tab === "makers" && (makers.length ? (
          <table><thead><tr><th>公司</th><th>主营构成条目</th><th className="num">占其营收</th></tr></thead>
            <tbody>{makers.map((m) => <tr key={m.code + m.item}><td><CompanyLink code={m.code} name={m.name} /></td><td>{m.item} <Tag>{HOW_ZH[m.how] || m.how}</Tag></td><td className="num">{pct(m.pct)}</td></tr>)}</tbody></table>
        ) : <Empty>没有公司的营收条目匹配到该节点</Empty>)}
        {tab === "val" && (<>{view && <BrokerViewCard v={view} scope="该产品" />}{bv ? <BrokerStatLine v={bv} scope="统计" /> : !view && <Empty>该产品研报样本不足（少于 3 篇）</Empty>}<Note>来自生产该产品的公司的个股研报（最近 12 个月）。</Note></>)}
      </div>
    </>
  );
}

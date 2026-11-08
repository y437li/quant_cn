import type { Company, CompanyBrief } from "../../api/client";
import { useApp } from "../../components/context";
import { CompanyLink, Empty, Note, NodeLink, Row, Tag } from "../../components/ui";
import { walk } from "../../graph/taxonomy";

/** Purpose: the peers, chain and quarterly tabs of a company. Peers come precomputed from Python. */
type P = { c: Company; related: Record<string, CompanyBrief> };

export function PeersTab({ c, related }: P) {
  const comps = (c.llm?.counterparties || []).filter((p) => p.role === "competitor");
  const peers = c.peers || [];
  return (
    <>
      {comps.length > 0 && (<>
        <h3>年报点名的竞争对手（DeepSeek，原文已核对）</h3>
        <div className="list">{comps.map((p, i) => <Row key={i} left={<>{p.code && related[p.code] ? <CompanyLink code={p.code} name={related[p.code].name} /> : p.name} <Tag>{p.detail}</Tag></>} right={<Tag kind="ev" title={p.evidence.quote}>第 {p.evidence.page} 页</Tag>} />)}</div>
        <h3>产品结构相似的公司</h3>
      </>)}
      {peers.length ? (
        <table><thead><tr><th>公司</th><th>共同产品 / 服务</th><th className="num">相似度</th></tr></thead>
          <tbody>{peers.map((p) => <tr key={p.code}><td>{related[p.code] ? <CompanyLink code={p.code} name={related[p.code].name} /> : p.code}</td><td>{p.shared.map((s) => <div key={s}><NodeLink id={s} plain /></div>)}</td><td className="num">{p.score.toFixed(2)}</td></tr>)}</tbody>
        </table>
      ) : <Empty>没有找到产品结构相同的公司</Empty>}
      <Note>相似度 = 按营收占比加权的产品向量的余弦相似度（全市场，Python 预先计算）。</Note>
    </>
  );
}

export function ChainTab({ c }: P) {
  const { tx } = useApp();
  const seeds = [...new Set(c.revenue.flatMap((r) => r.pids))].filter((p) => tx.N[p]);
  const list = (dir: "up" | "down") => {
    const w = walk(tx, seeds, 2, dir, 30), out: [string, number][] = [];
    w.nodes.forEach((d, id) => { if (d !== 0) out.push([id, Math.abs(d)]); });
    return out.sort((a, b) => a[1] - b[1]);
  };
  const block = (arr: [string, number][], word: string) => arr.length ? <div className="list">{arr.map(([id, d]) => <Row key={id} left={<NodeLink id={id} />} right={<Tag kind="prior">{word}{d}层</Tag>} />)}</div> : <Empty>无</Empty>;
  return <><h3>上游：原料、部件、技术</h3>{block(list("up"), "上游")}<h3>下游：应用与终端市场</h3>{block(list("down"), "下游")}<Note>这些链接是 Opus 写的产业链先验，不是该公司的交易证据。</Note></>;
}

const KIND_ZH: Record<string, string> = { order: "订单 / 合同", customer: "客户", capacity: "产能", driver: "业绩驱动", product: "产品", other: "其他" };
export function QuarterlyTab({ c }: P) {
  const qs = c.quarterly || [];
  if (!qs.length) return <Empty>季报没有可读的经营信息（多数公司“其他提醒事项”为不适用）</Empty>;
  return (
    <>
      {Object.keys(KIND_ZH).map((k) => [k, qs.filter((q) => q.kind === k)] as const).filter(([, l]) => l.length).map(([k, l]) => (
        <div key={k}><h3>{KIND_ZH[k]} · {l.length}</h3>
          <div className="list">{l.map((q, i) => <Row key={i} left={<>{q.summary}{q.value && <> <Tag kind="ev">{q.value} {q.unit || ""}</Tag></>}{q.counterparty && <> <Tag>{q.counterparty}</Tag></>}</>} right={<Tag title={q.evidence.quote}>{q.period} p{q.evidence.page}</Tag>} />)}</div>
        </div>
      ))}
      <Note>DeepSeek 读 2026 年一季报、三季报的“其他提醒事项”和营收类变动原因；悬停页码看原文。</Note>
    </>
  );
}

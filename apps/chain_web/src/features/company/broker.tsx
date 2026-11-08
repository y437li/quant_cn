import type { BrokerStat, BrokerView } from "../../api/client";
import { Tag } from "../../components/ui";

/** Purpose: show a broker statistics line and a synthesized broker view (plan 13 ph4, D-109 amendment). */
export function BrokerStatLine({ v, scope }: { v?: BrokerStat; scope: string }) {
  if (!v) return null;
  const years = Object.entries(v.pe_by_year || {}).map(([y, [m, n]]) => `${y} ${m}x（${n}）`).join("、");
  const parts = [years && `现价隐含 PE 中位：${years}`, v.pe_target != null && `目标 PE 中位 ${v.pe_target}x（${v.pe_target_n}）`, v.pb != null && `PB 中位 ${v.pb}x（${v.pb_n}）`].filter(Boolean);
  return (
    <div className="note" style={{ marginTop: 4 }}>
      <Tag kind="ev">研报统计 · {scope} · {v.n} 篇</Tag>
      {(v.bare_share || 0) >= 0.2 && <> <Tag>{Math.round((v.bare_share || 0) * 100)}% 的研报未给估值倍数</Tag></>}
      {v.methods.length > 0 && <> 估值方法：{v.methods.map(([k, n]) => `${k} ${n}`).join("、")}</>}
      {parts.length > 0 && <>；{parts.join(" · ")}</>}
      {(v.loss_share || 0) >= 0.3 && <><br /><Tag kind="risk">{Math.round((v.loss_share || 0) * 100)}% 的研报预测近期亏损：PE 多基于之后扭亏年份，属于反转押注，不是常规估值</Tag></>}
      {v.metrics.length > 0 && <><br />关注指标：{v.metrics.map(([k, n]) => <Tag key={k}>{k} {n}</Tag>)}</>}
    </div>
  );
}

const VIEW_ZH: Record<string, string> = { multiple_reasons: "倍数高低的理由", drivers: "核心驱动", bull: "看多逻辑", risks: "主要风险", divergence: "券商分歧", recent_change: "近期变化" };
const range = (lo: unknown, hi: unknown) => (lo == null && hi == null ? "—" : `${lo ?? "?"}–${hi ?? "?"}x`);

export function BrokerViewCard({ v, scope }: { v?: BrokerView | null; scope: string }) {
  if (!v) return null;
  const mr = (v.multiple_range || {}) as Record<string, any>;
  return (
    <div className="viewcard">
      <div className="note" style={{ margin: "6px 0" }}><Tag kind="ev">{scope} · {v.n_reports} 篇研报归纳（送入 {v.n_sent} 篇）</Tag></div>
      <p>{v.summary}</p>
      <table><tbody>
        <tr><td>估值方法</td><td>{v.method_consensus || "—"}</td></tr>
        <tr><td>倍数（{mr.metric || ""} {mr.base_year || ""}）</td><td>现价隐含 {range(mr.implied_low, mr.implied_high)} · 目标 {range(mr.target_low, mr.target_high)}{mr.note && <div className="note">{mr.note}</div>}</td></tr>
      </tbody></table>
      {Object.entries(VIEW_ZH).map(([k, label]) => {
        const pts = v.points?.[k] || [];
        return pts.length ? (
          <div key={k}>
            <div className="note" style={{ marginTop: 8 }}><b>{label}</b></div>
            <div className="list">{pts.map((p, i) => (
              <div className="row" key={i}>
                <span>{p.metric && <Tag kind="ev">{p.metric}{p.unit ? " · " + p.unit : ""}</Tag>} {p.point}</span>
                <span>{p.sources.map((r) => <Tag key={r} title={v.refs[r] || r}>{r}</Tag>)}</span>
              </div>
            ))}</div>
          </div>
        ) : null;
      })}
    </div>
  );
}

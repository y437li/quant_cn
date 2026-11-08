import type { Company } from "../../api/client";
import { useApp } from "../../components/context";
import { Note, Tag } from "../../components/ui";

/** Purpose: pricing power (D-118, design §4.5) and the posterior archetype check (§4b.7); every number from Python. */
type Signal = { key: string; vote: "maker" | "taker" | null; detail: string };
type Llm = { label: string; confidence: string; reasons: { point: string; sources: string[] }[]; evidence: Record<string, string> };
type Check = { llm?: { archetype_ok: boolean | null; archetype: string | null; variant_note: string | null }; status: string; archetype?: string; checks: { name: string; ok: boolean; detail: string }[]; variant?: string | null; variant_quote?: string | null; proposed_variant?: string | null; pricing_text?: string | null; pass_through_text?: string | null };
const LABEL: Record<string, [string, "ev" | "risk" | undefined]> = { maker: ["定价者", "ev"], lean_maker: ["偏定价者", "ev"], taker: ["跟价者", "risk"], lean_taker: ["偏跟价者", "risk"], middle: ["中间", undefined], insufficient: ["数据不足", undefined] };
const CONF: Record<string, string> = { high: "高置信", medium: "中置信", low: "低置信" };
const SIG: Record<string, string> = { P1: "毛利率水平", P2: "毛利率稳定性", P3: "成本传导", P4: "利润随售价", P5: "细分份额", P6: "周期下行时的毛利率", T1: "年报 / 季报表述" };
const STATUS: Record<string, [string, "ev" | "risk" | undefined]> = { consistent: ["一致", "ev"], partial: ["部分一致", undefined], inconsistent: ["不一致（待复核）", "risk"], insufficient: ["数据不足", undefined] };
const PRICING: Record<string, string> = { market: "随市场价", spread: "加工价差", negotiated: "议价", bid: "招投标", brand: "品牌定价", regulated: "政府定价", contract: "合同定价" };
const PASS: Record<string, string> = { full: "可完全传导", lagged: "滞后传导", partial: "部分传导", none: "不能传导" };

export function PricingCard({ c }: { c: Company }) {
  const { boot } = useApp();
  const x = c as Company & { pricing_power?: { label: string; confidence?: string; signals: Signal[]; llm?: Llm }; archetype_check?: Check };
  const pp = x.pricing_power, ac = x.archetype_check;
  if (!pp) return null;
  const [lab, kind] = LABEL[pp.label];
  const arch = ac?.archetype ? boot.archetypes[ac.archetype] : null;
  const variantName = ac?.variant && arch?.variants?.[ac.variant]?.name;
  return (
    <>
      <h3>定价权（后验 · 规则）</h3>
      <div><Tag kind={kind} strong>{lab}</Tag> {pp.confidence && <Tag>{CONF[pp.confidence]}</Tag>} <span className="note">得分 = 偏定价者票数 − 偏跟价者票数：≥2 定价者，1 偏定价者，0 中间，−1 偏跟价者，≤−2 跟价者</span></div>
      <table className="fin"><tbody>{pp.signals.map((s) => (
        <tr key={s.key}><td>{SIG[s.key] || s.key}</td><td>{s.vote ? <Tag kind={s.vote === "maker" ? "ev" : "risk"}>{s.vote === "maker" ? "偏定价者" : "偏跟价者"}</Tag> : <Tag>中性</Tag>}</td><td className="note">{s.detail}</td></tr>
      ))}</tbody></table>
      {pp.llm && (
        <div className="viewcard">
          <div><Tag kind="ev">DeepSeek 裁决</Tag> <Tag kind={LABEL[pp.llm.label][1]} strong>{LABEL[pp.llm.label][0]}</Tag> <Tag>{CONF[pp.llm.confidence]}</Tag></div>
          <div className="list">{pp.llm.reasons.map((r, i) => <div className="row" key={i}><span>{r.point}</span><span>{r.sources.map((k) => <Tag key={k} title={pp.llm!.evidence[k]}>{k}</Tag>)}</span></div>)}</div>
          <Note>规则信号不足或原型不一致时，由 DeepSeek 依据上面的信号、年报表述和研报归纳作出判断；每条理由都引用证据编号（悬停查看）。</Note>
        </div>
      )}
      {ac && (<>
        <h3>商业模式后验检验（原型 {ac.archetype || "—"}{arch ? " " + arch.name : ""}）</h3>
        <div><Tag kind={STATUS[ac.status][1]} strong>{STATUS[ac.status][0]}</Tag>
          {ac.llm && ac.llm.archetype_ok === false && ac.llm.archetype && <> <Tag kind="risk">DeepSeek：应为 {ac.llm.archetype} {boot.archetypes[ac.llm.archetype]?.name}</Tag></>}
          {ac.llm && ac.llm.archetype_ok === true && <> <Tag kind="ev">DeepSeek：默认原型成立</Tag></>}</div>
        {ac.llm?.variant_note && <p className="note">实际经营模式：{ac.llm.variant_note}</p>}
        <table className="fin"><tbody>{ac.checks.map((k) => <tr key={k.name}><td>{k.name}</td><td>{k.ok ? <Tag kind="ev">符合</Tag> : <Tag kind="risk">不符</Tag>}</td><td className="note">{k.detail}</td></tr>)}</tbody></table>
        {(ac.variant || ac.proposed_variant || ac.pricing_text || ac.pass_through_text) && (
          <table className="fin"><tbody>
            {ac.variant && <tr><td>经营模式变体</td><td colSpan={2}><b>{variantName || ac.variant}</b>{ac.variant_quote && <div className="note">“{ac.variant_quote}”</div>}</td></tr>}
            {ac.proposed_variant && <tr><td>建议新变体</td><td colSpan={2}><Tag kind="risk">候选都不符</Tag> {ac.proposed_variant}</td></tr>}
            {ac.pricing_text && <tr><td>定价方式（年报）</td><td colSpan={2}>{PRICING[ac.pricing_text] || ac.pricing_text}</td></tr>}
            {ac.pass_through_text && <tr><td>成本传导（年报）</td><td colSpan={2}>{PASS[ac.pass_through_text] || ac.pass_through_text}</td></tr>}
          </tbody></table>
        )}
        <Note>原型来自申万三级行业的默认（先验）；这里用实测数据和 DeepSeek 读年报经营模式文字检验。“不一致”进入复核清单，确认后只改这家公司的标签。</Note>
      </>)}
    </>
  );
}

import type { Company } from "../../api/client";
import { Note, Tag } from "../../components/ui";

/** Purpose: moat per BUSINESS_MODEL_DESIGN §4.4: width and trend from ROIC, claims read by DeepSeek tested against numbers. */
type Claim = { subtype?: string; type: string; claim: string; figure?: string | null; evidence: { quote: string; page: number }; proven: boolean | null; test: string };
type Moat = { width: string; trend: string | null; trend_pp?: number; trend_rel_pp?: number; roic: Record<string, number>; above_floor?: number; wide_years?: number;
  gm_rank?: number | null; gm_stability?: number | null; share?: number; peer_roic?: number | null; claims: Claim[]; summary?: string; proven_types?: string[]; read?: boolean;
  sources?: { key: string; detail: string }[]; chain_position?: [string, string] | null };
const TYPE: Record<string, string> = { cost: "成本优势", switching: "转换成本", intangible: "无形资产", network: "网络效应", efficient_scale: "有效规模", brand: "品牌", patent: "专利/技术", license: "牌照/资质", franchise: "特许经营" };
const SOURCE: Record<string, string> = { pricing_power: "产业链定价权", market_share: "市场占有率", chain_position: "产业链地位（占用上下游资金、不依赖大客户）" };
const CHAIN: Record<string, [string, "ev" | "risk" | undefined]> = { strong: ["强势", "ev"], neutral: ["中性", undefined], weak: ["弱势 / 依赖", "risk"] };
const WIDTH: Record<string, [string, "ev" | "risk" | undefined]> = { wide: ["宽护城河", "ev"], narrow: ["窄护城河", undefined], none: ["无明显护城河", "risk"], insufficient: ["数据不足", undefined] };
const TREND: Record<string, [string, "ev" | "risk" | undefined]> = { widening: ["相对同行加宽", "ev"], stable: ["相对同行稳定", undefined], eroding: ["相对同行收窄", "risk"] };

export function MoatCard({ c }: { c: Company }) {
  const m = (c as Company & { moat?: Moat }).moat;
  if (!m) return null;
  const roic = Object.entries(m.roic || {}).slice(-6);
  return (
    <>
      <h3>护城河（声称 vs 数字证实，设计 §4.4）</h3>
      <div>
        <Tag kind={WIDTH[m.width][1]} strong>{WIDTH[m.width][0]}</Tag>
        {m.trend && <> <Tag kind={TREND[m.trend][1]}>{TREND[m.trend][0]}</Tag></>}
        {(m.proven_types || []).map((t) => <span key={t}> <Tag kind="ev">已证实：{TYPE[t]}</Tag></span>)}
      </div>
      <table className="fin"><tbody>
        <tr><td>ROIC（近 6 年）</td><td className="num">{roic.map(([y, v]) => `${y.slice(2)}: ${Number(v).toFixed(1)}%`).join(" · ") || "—"}</td></tr>
        <tr><td>高于 8% / 15% 的年数</td><td className="num">{m.above_floor ?? "—"} / {m.wide_years ?? "—"}（同行 ROIC 中位 {m.peer_roic != null ? m.peer_roic.toFixed(1) + "%" : "—"}）</td></tr>
        <tr><td>ROIC 变化（后 3 年 − 前 3 年）</td><td className="num">{m.trend_pp ?? "—"}pp，相对同行 {m.trend_rel_pp ?? "—"}pp</td></tr>
        <tr><td>毛利率分位 / 波动 / 份额</td><td className="num">{m.gm_rank != null ? Math.round(m.gm_rank * 100) + "%" : "—"} / {m.gm_stability != null ? m.gm_stability.toFixed(1) + " 倍同行" : "—"} / {m.share ? Math.round(m.share * 100) + "%" : "—"}</td></tr>
      </tbody></table>
      <div className="note" style={{ marginTop: 8 }}><b>数字衡量出的护城河来源</b>（不看公司怎么说）</div>
      {(m.sources || []).length ? <div className="list">{m.sources!.map((x) => <div className="row" key={x.key}><span><Tag kind="ev">{SOURCE[x.key]}</Tag> {x.detail}</span></div>)}</div> : <Note>没有测到定价权、细分第一或强势的产业链地位。</Note>}
      {m.chain_position && <p className="note">产业链地位：<Tag kind={CHAIN[m.chain_position[0]][1]}>{CHAIN[m.chain_position[0]][0]}</Tag> {m.chain_position[1]}</p>}
      {m.summary && <p className="note">公司自称：{m.summary}</p>}
      {m.claims.length > 0 ? (
        <table className="fin"><thead><tr><th>声称的优势（年报核心竞争力）</th><th>数字检验</th></tr></thead><tbody>
          {m.claims.map((x, i) => (
            <tr key={i}>
              <td><Tag>{TYPE[x.subtype || x.type] || x.type}</Tag> {x.claim}{x.figure && <> <Tag kind="ev">{x.figure}</Tag></>}<div className="note" title={x.evidence.quote}>“{x.evidence.quote}” 第 {x.evidence.page} 页</div></td>
              <td>{x.proven === true ? <Tag kind="ev">证实</Tag> : x.proven === false ? <Tag kind="risk">未证实</Tag> : <Tag>无法检验</Tag>}<div className="note">{x.test}</div></td>
            </tr>
          ))}
        </tbody></table>
      ) : <Note>{m.read ? "年报核心竞争力里没有可归类的具体优势。" : "年报核心竞争力尚未读取（DeepSeek 运行中或未定位到该章节）。"}</Note>}
      <Note>宽：近 6 年至少 5 年 ROIC ≥15%，且毛利率在同行前一半或细分份额 ≥30%；窄：至少 4 年 ROIC ≥8%（资本成本代理）。趋势按后 3 年减前 3 年 ROIC，并扣除同行的同期变化（剔除全市场周期）。品牌/专利需毛利率在同行前 1/3 且比同行稳；成本优势需在不靠高毛利的情况下 ROIC 高出同行 3pp 以上或份额 ≥30%；转换成本需毛利率波动低于同行的 0.8 倍且 ROIC ≥10%；专利/技术需研发费用率不低于同行中位且毛利率在同行前一半；牌照/资质需至少 4 年 ROIC ≥8%；特许经营需 ROIC 波动低于同行中位且至少 4 年 ≥8%。产业链地位：预收/合同负债 ≥10% 或应收 ≤5% 营收、且前五客户 &lt;30% 为强势；前五客户 ≥50%（公用事业、金融除外）或应收 ≥40% 为弱势。</Note>
    </>
  );
}

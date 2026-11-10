import type { Clock, Company } from "../../api/client";
import { useApp } from "../../components/context";
import { Kpis, Note, NodeLink, Tag } from "../../components/ui";
import { ratio, yi } from "../../lib/format";
import { DupontChart } from "./dupont-chart";
import { PricingCard } from "./pricing-card";
import { MoatCard } from "./moat-card";

/** Purpose: the 商业模式 tab: archetype default, drivers, variants, lifecycle, cycle clocks, moat numbers (BUSINESS_MODEL_DESIGN). */
const PRICING_ZH: Record<string, string> = { market: "随市场价", spread: "加工价差", negotiated: "议价", bid: "招投标", brand: "品牌定价", regulated: "政府定价", contract: "合同定价" };
const PASS_ZH: Record<string, string> = { full: "成本可完全传导", lagged: "滞后传导", partial: "部分传导", none: "不能传导" };
const MOAT_ZH: Record<string, string> = { cost: "成本", switching: "转换成本", intangible: "品牌/牌照/专利", network: "网络效应", efficient_scale: "有效规模" };
const DRIVER_ZH: Record<string, string> = { volume: "销量", price: "价格", unit_cost: "单位成本", unit_margin: "单位毛利", capacity: "产能", utilisation: "产能利用率", efficiency: "生产效率", reserves: "资源储量", self_sufficiency: "资源自给率", mix: "产品结构", revenue: "收入", margin: "毛利率", overseas_share: "境外收入占比", rd_ratio: "研发投入占比", customer_concentration: "客户集中度", market_share: "市场份额", orders: "新签订单", backlog: "在手订单", deliveries: "交付量", contract_liabilities: "合同负债", inventory: "存货", capex: "资本开支" };

function Phases({ v }: { v?: Clock }) {
  if (!v) return <Tag>样本不足</Tag>;
  return (
    <>
      <div>{["复苏", "扩张", "过剩", "出清", "过渡"].map((p) => <Tag key={p} kind={p === v.phase ? "ev" : undefined} strong={p === v.phase} dim={p !== v.phase}>{p}</Tag>)}</div>
      <div className="note">营收 {ratio(v.demand)} · 毛利率 {v.margin_pp > 0 ? "+" : ""}{v.margin_pp} 个百分点 · 资本开支 {ratio(v.capex)} · {v.n} 家（2025 对比 2024）</div>
    </>
  );
}

function kpiName(boot: ReturnType<typeof useApp>["boot"], id: string) {
  for (const sec of Object.values(boot.kpis)) for (const k of [...sec.kpis, ...sec.groups.flatMap((g) => g.kpis)]) if (k.id === id) return k.name + (k.unit ? `（${k.unit}）` : "");
  return id;
}

export function BusinessTab({ c }: { c: Company }) {
  const { boot } = useApp();
  const bz = c.business || {};
  const def = bz.default, a = def && boot.archetypes[def.archetype];
  const life = bz.life || {};
  const prods = [...new Set(c.revenue.flatMap((r) => r.pids))].filter((p) => boot.clock_prod[p]);
  return (
    <>
      <h3>商业模式（申万三级“{c.l3 || "—"}”的默认原型 · Opus 先验，待按公司经营模式文本确认）</h3>
      {a ? (
        <>
          <Kpis items={[[def.archetype, a.name], [PRICING_ZH[a.pricing] || a.pricing || "—", "定价方式"], [PASS_ZH[a.pass_through] || a.pass_through || "—", "成本传导"]]} />
          <table><tbody>
            <tr><td>收入公式</td><td>{a.revenue_formula}</td></tr>
            <tr><td>利润关键</td><td>{a.profit_hinge}</td></tr>
            <tr><td>常用估值</td><td>{(a.valuation_methods || []).map((x: string) => <Tag key={x}>{x}</Tag>)}</td></tr>
            <tr><td>典型护城河</td><td>{(a.moat_types || []).map((x: string) => <Tag key={x}>{MOAT_ZH[x] || x}</Tag>)}</td></tr>
          </tbody></table>
          {Object.keys(def.drivers || {}).length > 0 && (<>
            <h3>收入驱动 → 行业指标</h3>
            <table><tbody>{Object.entries(def.drivers as Record<string, string | string[]>).map(([role, ids]) => (
              <tr key={role}><td>{DRIVER_ZH[role] || role}</td><td>{([] as string[]).concat(ids).map((i) => <Tag key={i}>{kpiName(boot, i)}</Tag>)}</td></tr>
            ))}</tbody></table>
          </>)}
          {(def.common_variants || []).length > 0 && (<>
            <h3>行业里常见的经营模式变体</h3>
            <div className="list">{(def.common_variants as string[]).filter((v) => a.variants[v]).map((v) => (
              <div className="row" key={v}><span><b>{a.variants[v].name}</b><div className="note">{a.variants[v].description}</div></span></div>
            ))}</div>
          </>)}
        </>
      ) : <Note>该三级行业没有默认原型。</Note>}
      <h3>生命周期（规则 · 2025 年报）</h3>
      <div>{["扩张期", "运营期", "收缩期"].map((x) => <Tag key={x} kind={x === life.label ? "ev" : undefined} strong={x === life.label} dim={x !== life.label}>{x}</Tag>)}{life.label === "数据不足" && <Tag>数据不足</Tag>}</div>
      {life.capex_dep != null && (
        <table><tbody>
          <tr><td>资本开支 / 折旧</td><td className="num">{life.capex_dep}</td></tr>
          <tr><td>在建工程增速</td><td className="num">{ratio(life.cip_g)}</td></tr>
          <tr><td>营收增速（行业中位）</td><td className="num">{ratio(life.rev_g)}（{ratio(life.peer_rev_g)}）</td></tr>
          <tr><td>自由现金流</td><td className="num">{yi(life.fcf)}</td></tr>
        </tbody></table>
      )}
      <h3>周期时钟 · 行业（{c.l3 || "—"}）</h3>
      <Phases v={c.l3 ? boot.clock_l3[c.l3] : undefined} />
      {prods.length > 0 && <><h3>周期时钟 · 产品</h3>{prods.map((p) => <div key={p} style={{ marginTop: 8 }}><NodeLink id={p} /><Phases v={boot.clock_prod[p]} /></div>)}</>}
      <Note>需求 = 营收增速，盈利 = 毛利率变化，供给 = 资本开支增速（设计 §4.2）。</Note>
      <PricingCard c={c} />
      <h3>杜邦轨迹：ROE 与资产周转率</h3>
      <DupontChart c={c} />
      <MoatCard c={c} />
    </>
  );
}

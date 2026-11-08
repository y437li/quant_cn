/** Display formatters (no calculations beyond unit conversion). */
export const yi = (v: number | null | undefined) => v == null ? "—" : (v / 1e8).toLocaleString("zh-CN", { maximumFractionDigits: 2 }) + " 亿";
export const pct = (v: number | null | undefined) => v == null ? "—" : Number(v).toFixed(2) + "%";
export const ratio = (v: number | null | undefined) => v == null ? "—" : (v * 100).toFixed(1) + "%";
export const TYPE_ZH: Record<string, string> = { company: "公司", product: "产品", service: "服务", material: "材料", technology: "技术", end_market: "终端市场", segment: "细分" };
export const REL_ZH: Record<string, string> = { upstream_of: "上游", component_of: "部件", uses_material: "原料", used_in: "用于", enables: "技术支撑", serves: "服务于", substitute_for: "替代", operates: "运营" };
export const HOW_ZH: Record<string, string> = { manual: "人工映射", rule: "规则匹配", exact: "名称一致", contains: "名称包含", overlap: "名称相近（同行业）", part: "拆分匹配", sector: "按申万行业推断（低置信）", generic: "无法归类（其他 / 会计科目）", none: "未匹配" };
export const IMP_ZH: Record<string, string> = { high: "进口依赖高", medium: "进口依赖中", low: "进口依赖低" };
export const ROLE_ZH: Record<string, string> = { customer: "客户", supplier: "供应商", partner: "合作伙伴", competitor: "竞争对手 / 同行", subsidiary: "子公司 / 关联方", mention: "仅提及" };

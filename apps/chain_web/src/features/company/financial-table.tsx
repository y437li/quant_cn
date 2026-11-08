import type { Company } from "../../api/client";
import { Note } from "../../components/ui";
import { ratio, yi } from "../../lib/format";

/** Purpose: FY2023–FY2025 income-statement table with expense ratios (numbers from Python, D-117). */
const ROWS: [string, string, string?][] = [
  ["total_revenue", "营业总收入"], ["oper_cost", "营业成本"], ["gross_profit", "毛利", "gm"],
  ["sell_exp", "销售费用", "sell_exp_r"], ["admin_exp", "管理费用", "admin_exp_r"], ["rd_exp", "研发费用", "rd_exp_r"], ["fin_exp", "财务费用", "fin_exp_r"],
  ["biz_tax_surchg", "税金及附加"], ["assets_impair_loss", "资产减值损失"], ["credit_impa_loss", "信用减值损失"], ["invest_income", "投资收益"],
  ["operate_profit", "营业利润", "operate_profit_r"], ["income_tax", "所得税"], ["n_income", "净利润"], ["n_income_attr_p", "归母净利润", "n_income_attr_p_r"],
];
export function FinancialTable({ c }: { c: Company }) {
  const fin = (c as Company & { financials?: Record<string, Record<string, number>> }).financials || {};
  const years = Object.keys(fin).sort();
  if (!years.length) return null;
  return (
    <>
      <h3>财务明细（合并报表，亿元；小字为占营收比例）</h3>
      <table className="fin">
        <thead><tr><th>项目</th>{years.map((y) => <th key={y} className="num">{y}</th>)}</tr></thead>
        <tbody>
          {ROWS.filter(([k]) => years.some((y) => fin[y][k] != null)).map(([k, label, r]) => (
            <tr key={k} className={k === "n_income_attr_p" || k === "gross_profit" || k === "operate_profit" ? "strong" : ""}>
              <td>{label}</td>
              {years.map((y) => <td key={y} className="num">{yi(fin[y][k]).replace(" 亿", "")}{r && fin[y][r] != null && <div className="note">{ratio(fin[y][r])}</div>}</td>)}
            </tr>
          ))}
          {years.some((y) => fin[y].opex_r != null) && <tr><td>四项费用率合计</td>{years.map((y) => <td key={y} className="num">{ratio(fin[y].opex_r)}</td>)}</tr>}
        </tbody>
      </table>
      <Note>来源：Tushare 利润表（合并，最新修订版）。减值损失按报表口径列示（负数为损失）；财务费用为负表示利息收入大于支出。</Note>
    </>
  );
}

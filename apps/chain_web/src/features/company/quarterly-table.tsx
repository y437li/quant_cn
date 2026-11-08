import type { Company } from "../../api/client";
import { Note } from "../../components/ui";
import { ratio, yi } from "../../lib/format";

/** Purpose: last 8 single quarters (YTD differences, computed in Python): revenue, profit, margins, expense ratios, YoY. */
type Q = { q: string; rev?: number; np?: number; op?: number; gm?: number; npm?: number; sell_exp_r?: number; admin_exp_r?: number; rd_exp_r?: number; fin_exp_r?: number; rev_yoy?: number; np_yoy?: number };
const ROWS: [keyof Q, string, "yi" | "pct"][] = [
  ["rev", "营业总收入", "yi"], ["rev_yoy", "收入同比", "pct"], ["gm", "毛利率", "pct"], ["sell_exp_r", "销售费用率", "pct"], ["admin_exp_r", "管理费用率", "pct"],
  ["rd_exp_r", "研发费用率", "pct"], ["fin_exp_r", "财务费用率", "pct"], ["op", "营业利润", "yi"], ["np", "归母净利润", "yi"], ["np_yoy", "净利同比", "pct"], ["npm", "归母净利率", "pct"],
];
export function QuarterlyTable({ c }: { c: Company }) {
  const qs = ((c as Company & { quarters?: Q[] }).quarters || []);
  if (!qs.length) return <Note>没有季度数据。</Note>;
  const cls = (k: keyof Q, v: unknown) => (k.endsWith("yoy") && typeof v === "number" ? (v >= 0 ? "up" : "down") : "");
  return (
    <>
      <div className="scrollx">
        <table className="fin">
          <thead><tr><th>单季度</th>{qs.map((q) => <th key={q.q} className="num">{q.q}</th>)}</tr></thead>
          <tbody>{ROWS.map(([k, label, f]) => (
            <tr key={k} className={k === "np" || k === "rev" ? "strong" : ""}>
              <td>{label}</td>
              {qs.map((q) => <td key={q.q} className={`num ${cls(k, q[k])}`}>{f === "yi" ? yi(q[k] as number).replace(" 亿", "") : ratio(q[k] as number)}</td>)}
            </tr>
          ))}</tbody>
        </table>
      </div>
      <Note>单季度 = 本期累计 − 上期累计（同一年度）；金额单位亿元；同比与上年同季比较。</Note>
    </>
  );
}

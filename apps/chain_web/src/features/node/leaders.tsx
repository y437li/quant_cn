import { useApp } from "../../components/context";
import { Bar, CompanyLink, Note } from "../../components/ui";
import { pct, yi } from "../../lib/format";

/** Purpose: top companies of a product / segment by revenue on mapped lines (A-share listed only; computed in Python). */
type L = { n: number; total: number; top: { code: string; name: string; sales: number; share: number }[] };
export function Leaders({ id }: { id: string }) {
  const { boot } = useApp();
  const v = ((boot as unknown as { leaders?: Record<string, L> }).leaders || {})[id];
  if (!v || !v.top.length) return null;
  return (
    <>
      <h3>龙头（A 股上市公司，按该产品营收）</h3>
      <table><tbody>{v.top.map((t, i) => (
        <tr key={t.code}><td className="num">{i + 1}</td><td><CompanyLink code={t.code} name={t.name} /><Bar value={t.share * 100} color={i} /></td><td className="num">{yi(t.sales)}</td><td className="num">{pct(t.share * 100)}</td></tr>
      ))}</tbody></table>
      <Note>{v.n} 家公司合计 {yi(v.total)}；份额 = 公司映射到该节点的主营构成收入 / 全部 A 股生产公司合计。不含非上市公司和海外公司，也不含未映射到该节点的业务。</Note>
    </>
  );
}
export function rankOf(leaders: Record<string, L> | undefined, id: string, code: string) {
  const v = leaders?.[id];
  const i = v ? v.top.findIndex((t) => t.code === code) : -1;
  return v && i >= 0 ? { rank: i + 1, n: v.n, share: v.top[i].share } : null;
}

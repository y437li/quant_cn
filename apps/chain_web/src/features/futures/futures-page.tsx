import { useEffect, useState } from "react";
import { api, type FuturesFamily, type FuturesMonitor, type FuturesSpread, type IndexFuture } from "../../api/client";
import { FuturesChart } from "./futures-chart";
import { REGIME_ZH, SHAPE_ZH, groupFamilies, isExtreme, lotsText, moveClass, pctText, priceText, shortMonth, signedPct, spreadText, ymdText } from "./futures-format";

const pctFmt = (v: number) => signedPct(v, 1);
const FLAGS_KEY = "futures.flags.open";

/** Purpose: whether the signal list starts open (the viewer's last choice). Contract: open when nothing is stored or storage fails. */
function readFlagsOpen(): boolean {
  try { return localStorage.getItem(FLAGS_KEY) !== "0"; } catch { return true; }
}

/** Purpose: the families table: one row per family, grouped; a click picks the family shown in the charts. */
function FamilyTable({ rows, picked, pick }: { rows: FuturesFamily[]; picked: string; pick: (f: string) => void }) {
  return (
    <div className="fm-scroll">
      <table className="fm-table fu-table">
        <thead><tr>
          <th>品种</th><th>主力合约</th><th>价格</th><th>1周</th><th>3月</th><th title="主力连续价格，含换月">1年</th><th title="主力价格在近 1 年的分位">1年分位</th><th>5年分位</th>
          <th title="近月比第 4 个挂牌月 − 1；正 = 近高远低">近月 vs 第4月</th><th>5年分位</th><th title="近月比约 12 个月后的合约">近月 vs 12月</th><th>形态</th><th title="全部合约持仓 5 日变化（z 为相对近 1 年）">持仓 5日</th><th title="前20名期货公司（多 − 空）÷（多 + 空），括号内为 5 年分位">前20净多空</th>
        </tr></thead>
        <tbody>
          {groupFamilies(rows).map(([g, fams]) => [
            <tr key={g} className="fu-group"><td colSpan={14}>{g}</td></tr>,
            ...fams.map((f) => (
              <tr key={f.family} data-family={f.family} className={f.family === picked ? "on" : ""} onClick={() => pick(f.family)}>
                <td>{f.name}</td><td className="wl-code">{f.contract.split(".")[0]}</td><td>{priceText(f.price)}</td>
                <td className={moveClass(f.chg_1w)}>{signedPct(f.chg_1w)}</td><td className={moveClass(f.chg_3m)}>{signedPct(f.chg_3m)}</td><td className={moveClass(f.chg_1y)}>{signedPct(f.chg_1y)}</td>
                <td>{pctText(f.pct_1y)}</td><td className={isExtreme(f.pct_5y) ? "ext" : ""}>{pctText(f.pct_5y)}</td>
                <td>{signedPct(f.front_vs_4th)}</td><td className={isExtreme(f.front_vs_4th_pct) ? "ext" : ""}>{pctText(f.front_vs_4th_pct)}</td>
                <td>{signedPct(f.front_vs_12m)}</td><td>{SHAPE_ZH[f.shape] ?? f.shape}</td>
                <td className={f.oi_z != null && Math.abs(f.oi_z) >= 2 ? "ext" : ""}>{signedPct(f.oi_chg_5d)}{f.oi_z != null && <small> z {f.oi_z.toFixed(1)}</small>}</td>
                <td className={isExtreme(f.broker?.net_share_pct_5y ?? null) ? "ext" : moveClass(f.broker?.net_share ?? null)}>{f.broker ? <>{signedPct(f.broker.net_share)}<small> {pctText(f.broker.net_share_pct_5y)}</small></> : "—"}</td>
              </tr>
            )),
          ])}
        </tbody>
      </table>
    </div>
  );
}

/** Purpose: charts of the picked family: today's curve by contract month, dominant price over a year, front vs 4th over 5 years. */
function FamilyCharts({ f }: { f: FuturesFamily }) {
  return (
    <section className="wl-section">
      <h3>{f.name} <small className="wl-code">{f.family} · 主力 {f.contract} · {ymdText(f.as_of)}</small></h3>
      <div className="fu-charts">
        <figure><figcaption>今日期限结构（按交割月，持仓 ≥ 下限）</figcaption>
          <FuturesChart label={`${f.name} 期限结构`} dots points={f.curve.map((c) => ({ x: c.month, v: c.price }))} fmt={priceText} xfmt={shortMonth} /></figure>
        <figure><figcaption>主力合约价格（近 1 年）</figcaption>
          <FuturesChart label={`${f.name} 主力价格`} points={f.price_history.map((p) => ({ x: p.d, v: p.v }))} fmt={priceText} xfmt={(d) => ymdText(d).slice(0, 7)} /></figure>
        <figure><figcaption>近月 vs 第4月（近 5 年，周度；正 = 近高远低）</figcaption>
          <FuturesChart label={`${f.name} 近月 vs 第4月`} points={f.curve_history.map((p) => ({ x: p.d, v: p.v }))} fmt={pctFmt} xfmt={(d) => ymdText(d).slice(0, 7)} /></figure>
      </div>
    </section>
  );
}

/** Purpose: 股指期货: basis to the index (annualised to expiry) and top-20 broker nets per product, with the picked product's 5-year charts. */
function IndexFutures({ rows }: { rows: IndexFuture[] }) {
  const [picked, setPicked] = useState(rows[0]?.product ?? "");
  const p = rows.find((r) => r.product === picked) ?? rows[0];
  if (!p) return null;
  return (
    <section className="wl-section" data-section="index-futures">
      <h3>股指期货 <small className="wl-code">{ymdText(p.as_of)}</small></h3>
      <div className="fm-scroll">
        <table className="fm-table fu-table">
          <thead><tr><th>品种</th><th>主力合约</th><th>期货</th><th>指数</th><th title="主力合约 ÷ 指数 − 1">基差</th><th title="按到期日（第三个周五）年化；5-8 月分红季贴水会加深">年化基差</th><th>5年分位</th><th title="前20名期货公司多单 − 空单">前20净持仓</th><th>5日变化</th><th>5年分位</th><th>持仓 5日</th><th>持仓 × 价格</th></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.product} data-product={r.product} className={r.product === p.product ? "on" : ""} onClick={() => setPicked(r.product)}>
              <td>{r.name} <small className="wl-code">{r.product}</small></td><td className="wl-code">{r.main_contract}</td>
              <td>{priceText(r.price)}</td><td>{priceText(r.spot)}</td>
              <td className={moveClass(r.basis_pct)}>{r.basis_pct == null ? "—" : signedPct(r.basis_pct / 100, 2)}</td>
              <td className={moveClass(r.basis_annualised)}>{r.basis_annualised == null ? "—" : signedPct(r.basis_annualised / 100, 1)}</td>
              <td className={isExtreme(r.basis_pct_5y) ? "ext" : ""}>{pctText(r.basis_pct_5y)}</td>
              <td className={moveClass(r.net)}>{lotsText(r.net)}</td><td className={moveClass(r.net_chg_5d)}>{lotsText(r.net_chg_5d)}</td>
              <td className={isExtreme(r.net_pct_5y) ? "ext" : ""}>{pctText(r.net_pct_5y)}</td>
              <td className={moveClass(r.oi_chg_5d)}>{signedPct(r.oi_chg_5d)}</td><td>{REGIME_ZH[r.regime] ?? r.regime}</td>
            </tr>))}
          </tbody>
        </table>
      </div>
      <div className="fu-charts">
        <figure><figcaption>{p.name} 年化基差（近 5 年，周度，%）</figcaption>
          <FuturesChart label={`${p.name} 年化基差`} points={p.history.filter((h) => h.basis != null).map((h) => ({ x: h.d, v: h.basis as number }))} fmt={(v) => v.toFixed(1)} xfmt={(d) => ymdText(d).slice(0, 7)} /></figure>
        <figure><figcaption>{p.name} 前20名净持仓（近 5 年，周度，手）</figcaption>
          <FuturesChart label={`${p.name} 前20名净持仓`} points={p.history.filter((h) => h.net != null).map((h) => ({ x: h.d, v: h.net as number }))} fmt={(v) => lotsText(v, false)} xfmt={(d) => ymdText(d).slice(0, 7)} /></figure>
      </div>
    </section>
  );
}

/** Purpose: the spreads table and the picked spread's 5-year chart. */
function Spreads({ rows }: { rows: FuturesSpread[] }) {
  const [picked, setPicked] = useState(rows[0]?.key ?? "");
  const s = rows.find((r) => r.key === picked) ?? rows[0];
  if (!s) return null;
  const fmt = (v: number) => spreadText(s, v);
  return (
    <section className="wl-section" data-section="spreads">
      <h3>产业链价差</h3>
      <div className="fu-spreads">
        <table className="fm-table">
          <thead><tr><th>价差</th><th>最新</th><th>1周变化</th><th>5年分位</th></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.key} data-spread={r.key} className={r.key === s.key ? "on" : ""} onClick={() => setPicked(r.key)}>
              <td>{r.name}</td><td>{r.value == null ? "—" : `${spreadText(r, r.value)} ${r.unit}`}</td>
              <td className={moveClass(r.chg_1w)}>{r.chg_1w == null ? "—" : spreadText(r, r.chg_1w, true)}</td>
              <td className={isExtreme(r.pct_5y) ? "ext" : ""}>{pctText(r.pct_5y)}</td>
            </tr>))}
          </tbody>
        </table>
        <figure><figcaption>{s.name}（近 5 年，周度，{s.unit}）</figcaption>
          <FuturesChart label={s.name} points={s.history.map((p) => ({ x: p.d, v: p.v }))} fmt={fmt} xfmt={(d) => ymdText(d).slice(0, 7)} /></figure>
      </div>
    </section>
  );
}

/**
 * Purpose: the 期货监测 page at #futures (plan 15 ph7i, D-145): signals (collapsible; the choice is remembered per browser), families table grouped by sector with charts of
 * the picked family, value-chain spreads; notes on definitions.
 * Contract: read-only display of GET /api/futures; empty document → empty state with the command to run.
 */
export function FuturesPage() {
  const [doc, setDoc] = useState<FuturesMonitor | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [picked, setPicked] = useState("CU.SHF");
  const [flagsOpen, setFlagsOpen] = useState(readFlagsOpen());
  const keepOpen = (open: boolean) => { setFlagsOpen(open); try { localStorage.setItem(FLAGS_KEY, open ? "1" : "0"); } catch { /* storage blocked: keep for this view only */ } };
  useEffect(() => { api.getFutures().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page"><p className="wl-empty">期货数据没有加载出来：{error}</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  if (!doc.families.length) return <div className="wl-page" data-empty="futures"><p className="wl-empty">还没有期货数据。先运行 <code>make futures-monitor</code>。</p></div>;
  const f = doc.families.find((x) => x.family === picked) ?? doc.families[0];
  const isNew = new Set(doc.new_flags);
  return (
    <div className="wl-page fu-page" data-page="futures">
      <div className="wl-head">
        <h2>期货监测</h2>
        <p>数据截至 {ymdText(doc.as_of)}，{doc.families.length} 个品种、{doc.spreads.length} 个价差；{doc.flags.length} 个信号。{doc.missing.length > 0 && ` 缺少：${doc.missing.join("、")}。`}</p>
      </div>
      {doc.flags.length > 0 && (
        <details className="fu-flags" open={flagsOpen} onToggle={(e) => keepOpen(e.currentTarget.open)}>
          <summary>信号 {doc.flags.length} 个{isNew.size > 0 && `（新 ${isNew.size} 个）`}<span className="fu-toggle">{flagsOpen ? "收起" : "展开"}</span></summary>
          <ul>{doc.flags.map((x) => (
            <li key={x.key} className={isNew.has(x.key) ? "new" : ""}><b>{x.name}</b> {x.message}{isNew.has(x.key) && <span className="mc-new">新</span>}</li>
          ))}</ul>
        </details>
      )}
      <IndexFutures rows={doc.index_futures} />
      <section className="wl-section"><h3>商品</h3><FamilyTable rows={doc.families} picked={f.family} pick={setPicked} /></section>
      <FamilyCharts f={f} />
      <Spreads rows={doc.spreads} />
      <p className="wl-note">价格为主力合约（持仓最大）结算价；1周 / 3月变化按同一合约计算，避免换月跳空；1年变化按主力连续价格（含换月）。金银比 = 黄金(元/克)×1000 ÷ 白银(元/千克)；金油比 = 黄金(元/克)×31.1035 ÷ 原油(元/桶)，即一盎司黄金能换几桶油。近月 = 最近的未到期且持仓 ≥ 1000 手的合约；近月 vs 第4月为正表示近高远低（现货紧）。分位为最新值在近 5 年中的位置，≤5% 或 ≥95% 标橙并进入信号。股指期货基差 = 主力合约 ÷ 指数 − 1，年化按距到期日天数；贴水深说明对冲盘多。前20名净持仓是期货公司席位的多单减空单合计，不等于客户真实意图。价差系数是行业经验值（见 config/futures_monitor.yaml），只看相对位置，不等于真实利润。</p>
    </div>
  );
}

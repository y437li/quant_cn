import type { HoldingFactor, HoldingsRisk } from "../../api/client";
import { factorName, signedPct, volPct } from "../factors/factor-format";
import { ymd } from "../watchlist/watchlist-format";

/**
 * Purpose: pure display helpers of the 持仓 page (plan 15 phase 7d, D-132). Values and risk are computed in Python
 * (HoldingsRiskBuilder); this only formats, sorts and groups them.
 * Contract: CNY and fractions in, strings out; null / undefined → "—".
 */

/** Purpose: CNY without decimals. Contract: 1144171 → "1,144,171"; −191804.9 → "−191,805"; null → "—". */
export const yuan = (v: number | null | undefined): string =>
  v == null ? "—" : (v < 0 ? "−" : "") + Math.round(Math.abs(v)).toLocaleString("en-US");

/** Purpose: a share. Contract: 0.2664 → "26.6%"; null → "—". */
export const share = (v: number | null | undefined): string => (v == null ? "—" : (v * 100).toFixed(1) + "%");

/** Purpose: an exposure in standard deviations. Contract: −0.689 → "−0.69"; 0.3 → "+0.30"; null → "—". */
export const expo = (v: number | null | undefined): string => {
  if (v == null) return "—";
  const s = Math.abs(v).toFixed(2);
  return (Number(s) === 0 ? "" : v > 0 ? "+" : "−") + s;
};

/** Purpose: style rows (not country, not industries), largest |active| first. Contract: industries excluded. */
export const listStyles = (factors: HoldingFactor[]): HoldingFactor[] =>
  factors.filter((f) => f.kind === "style").sort((a, b) => Math.abs(b.active ?? b.exposure ?? 0) - Math.abs(a.active ?? a.exposure ?? 0));

/** Purpose: industry rows with a weight in the book, largest first. Contract: zero exposure dropped. */
export const listIndustries = (factors: HoldingFactor[]): HoldingFactor[] =>
  factors.filter((f) => f.kind === "industry" && (f.exposure ?? 0) > 0).sort((a, b) => (b.exposure ?? 0) - (a.exposure ?? 0));

/**
 * Purpose: the one-sentence headline of the page.
 * Contract: empty document → ""; otherwise value, P&L, total vol, tracking error, the market's share of risk and the biggest active style.
 */
export function holdingsHeadline(doc: HoldingsRisk): string {
  if (!doc.as_of) return "";
  const market = doc.factors.find((f) => f.kind === "country");
  const top = listStyles(doc.factors)[0];
  return `${ymd(doc.as_of)} 收盘：总资产 ${yuan(doc.value)} 元（股票 ${yuan(doc.stock_value)}，现金 ${yuan(doc.cash)}），浮动盈亏 ${yuan(doc.pnl)} 元。` +
    `组合年化波动 ${volPct(doc.risk.total)}` + (doc.risk.active_total != null ? `，相对 ${doc.benchmark} 跟踪误差 ${volPct(doc.risk.active_total)}` : "") +
    (market?.contrib != null ? `；大盘贡献 ${share(market.contrib)} 的风险` : "") +
    (top ? `；最大的风格偏离是 ${factorName(top)} ${expo(top.active ?? top.exposure)}` : "") + "。";
}

/** Purpose: colour class of P&L. Contract: > 0 → "up", < 0 → "down", else "flat". */
export const pnlClass = (v: number | null | undefined): "up" | "down" | "flat" => (v == null || v === 0 ? "flat" : v > 0 ? "up" : "down");

export { signedPct };
